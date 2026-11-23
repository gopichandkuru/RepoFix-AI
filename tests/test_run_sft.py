import json
from pathlib import Path

from model.run_sft import build_sft_corpus, run_qlora_training
from model.train_qlora import QLoRAConfig


def test_build_sft_corpus_and_dry_run(tmp_path: Path):
    norm_jsonl = tmp_path / "norm.jsonl"
    norm_jsonl.write_text(
        json.dumps(
            {
                "example_id": "ex1",
                "task_type": "repair",
                "repo": "org/repo",
                "issue": "Fix zero division in ratio()",
                "files_context": ["src/math.py"],
                "diff": "",
                "split": "train",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    sft_jsonl = tmp_path / "sft_train.jsonl"
    written = build_sft_corpus(norm_jsonl, sft_jsonl, split_filter="train")
    assert written == 1

    res = run_qlora_training(QLoRAConfig(), sft_jsonl, dry_run=True)
    assert res["status"] == "dry_run_ok"
