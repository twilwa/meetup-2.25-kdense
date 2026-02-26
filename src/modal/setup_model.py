# ABOUTME: Model download and optimization for Wan 2.1 video generation.
# ABOUTME: Handles HuggingFace download, fp16 conversion, and volume persistence on Modal.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelInfo:
    """Metadata about a downloaded and optimized model.

    Attributes:
        model_path: Filesystem path where the model weights are stored.
        size_gb: Total size of the model files in gigabytes.
        dtype: Data type of the stored weights (e.g. "float16").
        attention_type: Attention implementation variant (e.g. "sdpa", "flash_attention_2").
    """

    model_path: str
    size_gb: float
    dtype: str
    attention_type: str


def download_model(volume_path: str = "/models/wan2.1-fp16") -> ModelInfo:
    """Download Wan 2.1 from HuggingFace, convert to fp16, and save to the volume.

    Downloads the full model weights, converts them to float16 precision for
    reduced VRAM usage, and writes the result to the specified volume path.

    Args:
        volume_path: Destination path on the Modal volume for the converted model.

    Returns:
        ModelInfo with the path, size, dtype, and attention type of the saved model.
    """
    raise NotImplementedError()


def verify_model(volume_path: str = "/models/wan2.1-fp16") -> bool:
    """Verify that model files exist at the given path and are loadable.

    Checks for the presence of required model files (config, weights, tokenizer)
    and performs a minimal load test to confirm they are not corrupted.

    Args:
        volume_path: Path to the model directory to verify.

    Returns:
        True if the model is present and loadable, False otherwise.
    """
    raise NotImplementedError()
