from pathlib import Path
from model.train_qlora import QLoRAConfig, validate_training_recipe, write_run_config


def test_qlora_config_validation_and_export(tmp_path: Path):
    cfg = QLoRAConfig(lora_r=16, lora_alpha=32, seed=42)
    res = validate_training_recipe(cfg)
    assert res["valid"] is True
    assert "q_proj" in cfg.target_modules

    out = write_run_config(cfg, tmp_path / "qlora_cfg.json")
    assert out.exists()
