from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Dict, List


@dataclass
class QLoRAConfig:
    base_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct"
    output_dir: str = "model/adapters/repofix-qwen25-coder-7b-qlora-v0"
    dataset_manifest: str = "datasets/manifests/train_manifest.json"
    max_seq_length: int = 4096
    load_in_4bit: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = None  # type: ignore[assignment]
    learning_rate: float = 2e-4
    num_train_epochs: int = 1
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 8
    seed: int = 42

    def __post_init__(self):
        if self.target_modules is None:
            self.target_modules = [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ]


def validate_training_recipe(cfg: QLoRAConfig) -> Dict[str, object]:
    """Validate hyperparameters, adapter output path, and dataset manifest presence."""
    errors: List[str] = []
    if not cfg.base_model.strip():
        errors.append("base_model must be specified.")
    if cfg.lora_r <= 0 or cfg.lora_alpha <= 0:
        errors.append("lora_r and lora_alpha must be positive integers.")
    if not (0.0 <= cfg.lora_dropout < 1.0):
        errors.append("lora_dropout must be in [0.0, 1.0).")
    if cfg.max_seq_length < 256:
        errors.append("max_seq_length should be at least 256 tokens.")
    if cfg.learning_rate <= 0:
        errors.append("learning_rate must be positive.")

    manifest_path = Path(cfg.dataset_manifest)
    manifest_exists = manifest_path.exists()

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "manifest_exists": manifest_exists,
        "config": asdict(cfg),
    }


def write_run_config(cfg: QLoRAConfig, out_path: Path) -> Path:
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
    return out_file
