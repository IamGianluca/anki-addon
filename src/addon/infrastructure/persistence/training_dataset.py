import json
from datetime import datetime
from pathlib import Path
from typing import Protocol


class TrainingDatasetRepository(Protocol):
    """Stores note improvement examples for model training."""

    def save_example(
        self,
        note_id: int,
        original_fields: dict[str, str],
        updated_fields: dict[str, str],
    ) -> None:
        """Append a training example to the dataset."""
        ...


class JSONLTrainingDataset:
    """Stores training examples in JSONL format for easy consumption by ML tools."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save_example(
        self,
        note_id: int,
        original_fields: dict[str, str],
        updated_fields: dict[str, str],
    ) -> None:
        """Append a training example as a new line in the JSONL file."""
        example = {
            "timestamp": datetime.now().isoformat(),
            "note_id": note_id,
            "original": original_fields,
            "updated": updated_fields,
        }

        with self.file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")


def create_training_dataset() -> JSONLTrainingDataset:
    """Factory function to create the default training dataset."""
    # Store in addon's parent directory
    addon_dir = Path(__file__).parents[4]
    data_dir = addon_dir / "data"
    dataset_path = data_dir / "training_dataset.jsonl"
    return JSONLTrainingDataset(dataset_path)
