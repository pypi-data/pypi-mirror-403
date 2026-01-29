"""
NC1709 Model Loader
Downloads and loads the fine-tuned NC1709 model for local inference
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Model configuration
MODEL_CONFIG = {
    "model_name": "nc1709-qwen2.5-coder-7b-tool-calling",
    "model_version": "v2.1.0",
    "hf_repo": "lafzusa/nc1709-tool-calling",  # HuggingFace repo
    "model_size_gb": 15,
    "lora_size_mb": 632,
    "base_model": "Qwen/Qwen2.5-Coder-7B",
}

# Default model paths
DEFAULT_MODEL_DIR = Path.home() / ".nc1709" / "models"
LORA_WEIGHTS_DIR = DEFAULT_MODEL_DIR / "lora_weights"
MERGED_MODEL_DIR = DEFAULT_MODEL_DIR / "merged_model"


def get_model_path(model_type: str = "lora") -> Path:
    """Get the path to the model directory

    Args:
        model_type: "lora" for lightweight LoRA weights, "merged" for full model

    Returns:
        Path to the model directory
    """
    if model_type == "lora":
        return LORA_WEIGHTS_DIR
    elif model_type == "merged":
        return MERGED_MODEL_DIR
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def is_model_downloaded(model_type: str = "lora") -> bool:
    """Check if the model is already downloaded

    Args:
        model_type: "lora" or "merged"

    Returns:
        True if model exists locally
    """
    model_path = get_model_path(model_type)

    if model_type == "lora":
        # Check for adapter_model.safetensors or adapter_model.bin
        return (model_path / "adapter_model.safetensors").exists() or \
               (model_path / "adapter_model.bin").exists()
    else:
        # Check for model files
        return (model_path / "model.safetensors").exists() or \
               any(model_path.glob("model-*.safetensors"))


def download_model(
    model_type: str = "lora",
    force: bool = False,
    progress_callback: Optional[callable] = None
) -> Path:
    """Download the NC1709 fine-tuned model

    Args:
        model_type: "lora" for lightweight (632MB) or "merged" for full (15GB)
        force: Force re-download even if exists
        progress_callback: Optional callback for progress updates

    Returns:
        Path to the downloaded model
    """
    model_path = get_model_path(model_type)

    if is_model_downloaded(model_type) and not force:
        logger.info(f"Model already downloaded at {model_path}")
        return model_path

    # Create directory
    model_path.mkdir(parents=True, exist_ok=True)

    try:
        from huggingface_hub import snapshot_download

        logger.info(f"Downloading NC1709 {model_type} model...")
        logger.info(f"This may take a while ({MODEL_CONFIG['lora_size_mb']}MB for LoRA, {MODEL_CONFIG['model_size_gb']}GB for merged)")

        # Determine subfolder based on model type
        subfolder = "lora" if model_type == "lora" else "merged"

        snapshot_download(
            repo_id=MODEL_CONFIG["hf_repo"],
            local_dir=model_path,
            subfolder=subfolder,
            local_dir_use_symlinks=False,
        )

        logger.info(f"Model downloaded successfully to {model_path}")
        return model_path

    except ImportError:
        logger.error("huggingface_hub not installed. Run: pip install huggingface_hub")
        raise
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        raise


def load_model_for_inference(
    model_type: str = "lora",
    device: str = "auto",
    quantization: str = "4bit"
):
    """Load the NC1709 model for inference

    Args:
        model_type: "lora" or "merged"
        device: Device to load on ("auto", "cuda", "cpu")
        quantization: "4bit", "8bit", or "none"

    Returns:
        Tuple of (model, tokenizer)
    """
    import torch

    # Ensure model is downloaded
    model_path = download_model(model_type)

    try:
        if model_type == "lora":
            # Load base model + LoRA adapter
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel

            logger.info(f"Loading base model: {MODEL_CONFIG['base_model']}")

            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                MODEL_CONFIG['base_model'],
                trust_remote_code=True
            )

            # Load base model with quantization
            load_kwargs = {"trust_remote_code": True}

            if quantization == "4bit":
                from transformers import BitsAndBytesConfig
                load_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                )
            elif quantization == "8bit":
                load_kwargs["load_in_8bit"] = True

            if device != "auto":
                load_kwargs["device_map"] = device
            else:
                load_kwargs["device_map"] = "auto"

            base_model = AutoModelForCausalLM.from_pretrained(
                MODEL_CONFIG['base_model'],
                **load_kwargs
            )

            # Load LoRA adapter
            logger.info(f"Loading LoRA adapter from {model_path}")
            model = PeftModel.from_pretrained(base_model, model_path)

        else:
            # Load merged model directly
            from transformers import AutoModelForCausalLM, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )

            load_kwargs = {"trust_remote_code": True}

            if quantization == "4bit":
                from transformers import BitsAndBytesConfig
                load_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                )
            elif quantization == "8bit":
                load_kwargs["load_in_8bit"] = True

            if device != "auto":
                load_kwargs["device_map"] = device
            else:
                load_kwargs["device_map"] = "auto"

            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                **load_kwargs
            )

        logger.info("Model loaded successfully!")
        return model, tokenizer

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


def get_model_info() -> dict:
    """Get information about the NC1709 model

    Returns:
        Dictionary with model information
    """
    return {
        **MODEL_CONFIG,
        "lora_downloaded": is_model_downloaded("lora"),
        "merged_downloaded": is_model_downloaded("merged"),
        "lora_path": str(LORA_WEIGHTS_DIR),
        "merged_path": str(MERGED_MODEL_DIR),
    }


# CLI commands for model management
def cli_download_model(model_type: str = "lora"):
    """CLI command to download the model"""
    print(f"Downloading NC1709 {model_type} model...")
    path = download_model(model_type)
    print(f"Model downloaded to: {path}")


def cli_model_info():
    """CLI command to show model info"""
    info = get_model_info()
    print("\nNC1709 Model Information")
    print("=" * 40)
    for key, value in info.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "download":
            model_type = sys.argv[2] if len(sys.argv) > 2 else "lora"
            cli_download_model(model_type)
        elif sys.argv[1] == "info":
            cli_model_info()
        else:
            print("Usage: python model_loader.py [download|info] [lora|merged]")
    else:
        cli_model_info()
