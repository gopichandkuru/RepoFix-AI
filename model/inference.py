from pathlib import Path
import re
from typing import Optional

from model.run_sft import SYSTEM_PROMPT

_CODE_BLOCK_RE = re.compile(r"```(?:diff)?\s*\n(.*?)```", re.DOTALL)


def extract_clean_diff(raw_output: str) -> str:
    """Strip markdown fences and prose so only the unified diff remains."""
    m = _CODE_BLOCK_RE.search(raw_output)
    text = m.group(1).strip() if m else raw_output.strip()
    lines = text.splitlines()
    start_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("--- "):
            start_idx = i
            break
    return "\n".join(lines[start_idx:]).strip() + "\n"


def generate_with_qlora_adapter(
    user_prompt: str,
    base_model: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct",
    adapter_dir: Optional[str] = "model/adapters/repofix-qwen25-coder-1.5b-qlora-v0",
    max_new_tokens: int = 256,
) -> str:
    """Run 4-bit inference with the fine-tuned QLoRA adapter (or base model if no adapter exists)."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
    )

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map="auto",
    )

    if adapter_dir and Path(adapter_dir).exists():
        model = PeftModel.from_pretrained(model, adapter_dir)

    model.eval()
    strict_system = (
        SYSTEM_PROMPT
        + " When generating a patch, output ONLY a valid unified diff starting with `--- a/<path>` and `+++ b/<path>` using exact line numbers from the provided file content."
    )
    prompt = (
        f"<|im_start|>system\n{strict_system}<|im_end|>\n"
        f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            top_k=None,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    raw = tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
    return extract_clean_diff(raw)
