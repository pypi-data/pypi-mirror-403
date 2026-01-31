"""Bundled Whisper model for meeting-noter offline use."""

from pathlib import Path

__version__ = "0.1.0"

MODEL_NAME = "tiny.en"


def get_model_path() -> Path:
    """Get the path to the bundled Whisper model.

    Returns:
        Path to the model directory containing model.bin, config.json, etc.
    """
    return Path(__file__).parent / "model"
