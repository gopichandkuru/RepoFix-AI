import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Dict, List

from model.train_qlora import QLoRAConfig, validate_training_recipe


SYSTEM_PROMPT = (
    "You are RepoFix AI, a repository-aware software engineering assistant. "
    "Analyze repository context carefully, cite file/symbol evidence, and output valid structured JSON or unified diffs."
)


def format_sft_example(record: Dict[str, object]) -> Dict[str, str]:
    """Convert a normalized RepoFix record into chat-formatted SFT prompt/completion pairs."""
    task_type = str(record.get("task_type", "repair"))
    repo = str(record.get("repo", "unknown/repo"))
    issue = str(record.get("issue", ""))
    files_ctx = ", ".join(record.get("files_context") or [])
    diff = str(record.get("diff", ""))

    user_prompt = (
        f"Task: {task_type}\n"
        f"Repository: {repo}\n"
        f"Candidate Context Files: {files_ctx or 'None'}\n\n"
        f"Issue / Description:\n{issue}"
    )

    if diff.strip():
        assistant_target = diff.strip()
    else:
        assistant_target = json.dumps(
            {
                "task": "bug_diagnosis",
                "summary": f"Investigate {files_ctx or repo} for reported issue.",
                "confidence": 0.75,
                "findings": [
                    {
                        "file": (record.get("files_context") or ["unknown.py"])[0],
                        "symbol": None,
                        "line_hint": 1,
                        "severity": "high",
                        "evidence": issue[:240],
                        "recommendation": "Inspect logic and run isolated unit tests.",
                    }
                ],
                "missing_information": [],
                "patch": "",
            },
            indent=2,
        )

    return {
        "system": SYSTEM_PROMPT,
        "user": user_prompt,
        "assistant": assistant_target,
    }


def build_sft_corpus(input_jsonl: Path, output_jsonl: Path, split_filter: str = "train") -> int:
    """Filter normalized records by split and write formatted SFT JSONL."""
    in_path = Path(input_jsonl)
    out_path = Path(output_jsonl)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with open(in_path, "r", encoding="utf-8") as src, open(out_path, "w", encoding="utf-8") as dst:
        for line in src:
            if not line.strip():
                continue
            rec = json.loads(line)
            if split_filter and rec.get("split") != split_filter:
                continue
            formatted = format_sft_example(rec)
            dst.write(json.dumps(formatted) + "\n")
            count += 1
    return count


def run_qlora_training(cfg: QLoRAConfig, train_jsonl: Path, dry_run: bool = True) -> Dict[str, object]:
    """Validate recipe and execute QLoRA SFT via PyTorch + Transformers + PEFT + TRL."""
    check = validate_training_recipe(cfg)
    if not check["valid"]:
        raise ValueError(f"Invalid QLoRA config: {check['errors']}")

    train_path = Path(train_jsonl)
    if not train_path.exists():
        raise FileNotFoundError(f"Training JSONL not found: {train_path}")

    if dry_run:
        return {
            "status": "dry_run_ok",
            "train_file": str(train_path),
            "config": asdict(cfg),
        }

    # Lazy-import heavy GPU training libraries only during live training
    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=cfg.load_in_4bit,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
    )

    tokenizer = AutoTokenizer.from_pretrained(cfg.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        cfg.base_model,
        quantization_config=bnb_config,
        device_map="auto",
    )

    peft_config = LoraConfig(
        r=cfg.lora_r,
        lora_alpha=cfg.lora_alpha,
        lora_dropout=cfg.lora_dropout,
        target_modules=cfg.target_modules,
        task_type="CAUSAL_LM",
    )

    dataset = load_dataset("json", data_files=str(train_path), split="train")

    def to_text(ex):
        return {
            "text": f"<|im_start|>system\n{ex['system']}<|im_end|>\n"
                    f"<|im_start|>user\n{ex['user']}<|im_end|>\n"
                    f"<|im_start|>assistant\n{ex['assistant']}<|im_end|>"
        }

    dataset = dataset.map(to_text)

    sft_args = SFTConfig(
        output_dir=cfg.output_dir,
        max_seq_length=cfg.max_seq_length,
        learning_rate=cfg.learning_rate,
        num_train_epochs=cfg.num_train_epochs,
        per_device_train_batch_size=cfg.per_device_train_batch_size,
        gradient_accumulation_steps=cfg.gradient_accumulation_steps,
        seed=cfg.seed,
        logging_steps=5,
        save_strategy="epoch",
        dataset_text_field="text",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        args=sft_args,
    )
    trainer.train()
    trainer.save_model(cfg.output_dir)
    tokenizer.save_pretrained(cfg.output_dir)
    return {"status": "trained", "output_dir": cfg.output_dir}


def main():
    parser = argparse.ArgumentParser(description="RepoFix AI QLoRA SFT Runner")
    parser.add_argument("--train-jsonl", type=Path, required=True)
    parser.add_argument("--live", action="store_true", help="Run live GPU training instead of dry-run")
    args = parser.parse_args()

    cfg = QLoRAConfig()
    res = run_qlora_training(cfg, args.train_jsonl, dry_run=not args.live)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
