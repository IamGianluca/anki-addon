import json
from pathlib import Path

import pytest

from addon.infrastructure.persistence.training_dataset import JSONLTrainingDataset


@pytest.fixture
def temp_dataset_path(tmp_path: Path) -> Path:
    return tmp_path / "test_dataset.jsonl"


@pytest.fixture
def dataset(temp_dataset_path: Path) -> JSONLTrainingDataset:
    return JSONLTrainingDataset(temp_dataset_path)


def test_creates_file_on_first_save(dataset: JSONLTrainingDataset) -> None:
    """Test that the dataset file is created when saving first example"""
    # Given
    original = {"Front": "What is 2+2?", "Back": "4"}
    updated = {"Front": "What is 2+2?", "Back": "Four"}

    # When
    dataset.save_example(note_id=123, original_fields=original, updated_fields=updated)

    # Then
    assert dataset.file_path.exists()


def test_saves_example_with_all_fields(
    dataset: JSONLTrainingDataset, temp_dataset_path: Path
) -> None:
    """Test that saved example contains all expected fields"""
    # Given
    original = {"Front": "Original question", "Back": "Original answer", "__tags__": "tag1 tag2"}
    updated = {"Front": "Updated question", "Back": "Updated answer", "__tags__": "tag1 tag2 tag3"}
    note_id = 456

    # When
    dataset.save_example(
        note_id=note_id, original_fields=original, updated_fields=updated
    )

    # Then
    with temp_dataset_path.open("r", encoding="utf-8") as f:
        line = f.readline()
        saved_example = json.loads(line)

    assert saved_example["note_id"] == note_id
    assert saved_example["original"] == original
    assert saved_example["updated"] == updated
    assert saved_example["original"]["__tags__"] == "tag1 tag2"
    assert saved_example["updated"]["__tags__"] == "tag1 tag2 tag3"
    assert "timestamp" in saved_example


def test_appends_multiple_examples(
    dataset: JSONLTrainingDataset, temp_dataset_path: Path
) -> None:
    """Test that multiple examples are appended as separate lines"""
    # Given
    example1_original = {"Front": "Q1", "Back": "A1"}
    example1_updated = {"Front": "Q1 improved", "Back": "A1 improved"}

    example2_original = {"Front": "Q2", "Back": "A2"}
    example2_updated = {"Front": "Q2 improved", "Back": "A2 improved"}

    # When
    dataset.save_example(
        note_id=1, original_fields=example1_original, updated_fields=example1_updated
    )
    dataset.save_example(
        note_id=2, original_fields=example2_original, updated_fields=example2_updated
    )

    # Then
    with temp_dataset_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) == 2

    first_example = json.loads(lines[0])
    assert first_example["note_id"] == 1
    assert first_example["original"] == example1_original

    second_example = json.loads(lines[1])
    assert second_example["note_id"] == 2
    assert second_example["original"] == example2_original


def test_handles_unicode_content(
    dataset: JSONLTrainingDataset, temp_dataset_path: Path
) -> None:
    """Test that unicode characters are preserved correctly"""
    # Given
    original = {"Front": "日本語", "Back": "Japanese"}
    updated = {"Front": "日本語 (にほんご)", "Back": "Japanese language"}

    # When
    dataset.save_example(note_id=789, original_fields=original, updated_fields=updated)

    # Then
    with temp_dataset_path.open("r", encoding="utf-8") as f:
        line = f.readline()
        saved_example = json.loads(line)

    assert saved_example["original"]["Front"] == "日本語"
    assert saved_example["updated"]["Front"] == "日本語 (にほんご)"


def test_captures_tag_changes(
    dataset: JSONLTrainingDataset, temp_dataset_path: Path
) -> None:
    """Test that changes to tags are captured in the dataset"""
    # Given - user adds a tag during review
    original = {"Front": "Question", "Back": "Answer", "__tags__": ""}
    updated = {"Front": "Question", "Back": "Answer", "__tags__": "reviewed important"}

    # When
    dataset.save_example(note_id=999, original_fields=original, updated_fields=updated)

    # Then
    with temp_dataset_path.open("r", encoding="utf-8") as f:
        saved_example = json.loads(f.readline())

    assert saved_example["original"]["__tags__"] == ""
    assert saved_example["updated"]["__tags__"] == "reviewed important"


def test_creates_parent_directories(tmp_path: Path) -> None:
    """Test that parent directories are created if they don't exist"""
    # Given
    nested_path = tmp_path / "level1" / "level2" / "dataset.jsonl"
    dataset = JSONLTrainingDataset(nested_path)

    # When
    dataset.save_example(
        note_id=1,
        original_fields={"Front": "Q", "Back": "A"},
        updated_fields={"Front": "Q improved", "Back": "A improved"},
    )

    # Then
    assert nested_path.exists()
    assert nested_path.parent.exists()
