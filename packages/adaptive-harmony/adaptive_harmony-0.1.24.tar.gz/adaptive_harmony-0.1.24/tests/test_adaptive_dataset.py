import asyncio
import pytest
import json
import tempfile
import os
from adaptive_harmony import StringThread
from adaptive_harmony.parameters import Dataset, dataset_kinds
from adaptive_harmony.runtime.context import RecipeContext
from unittest.mock import AsyncMock, Mock


@pytest.fixture
def mock_ctx():
    """Create a mock RecipeContext for testing."""
    ctx = Mock(spec=RecipeContext)
    ctx.file_storage = Mock()
    ctx.file_storage.mk_url = Mock(return_value="file://test_file.jsonl")

    # Create a mock for dataset config response
    mock_dataset_config = Mock()
    mock_dataset_config.file_path = None

    ctx.client = Mock()
    ctx.client.get_dataset_config = AsyncMock(return_value=mock_dataset_config)
    return ctx


def create_temp_dataset_file(data, mock_ctx):
    """Helper function to create a temporary dataset file and configure the mock."""
    if isinstance(data, list):
        content = "\n".join(json.dumps(item) for item in data) + "\n"
    else:
        content = json.dumps(data) + "\n"

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
        f.write(content)
        temp_file = f.name

    # Configure mock to return file content
    mock_ctx.file_storage.read.return_value = content.encode("utf-8")

    return temp_file


class TestAdaptiveDatasetLoadDataset:

    def test_load_dataset_prompt_format(self, mock_ctx):
        prompt_data = {
            "prompt": [
                ["user", "What is the capital of France?"],
                ["assistant", "The capital of France is Paris."],
            ],
            "metadata": {"id": "b2761a88-0662-453b-aba7-27846434dc55", "created_at": 1234567890},
        }

        temp_file = create_temp_dataset_file(prompt_data, mock_ctx)
        try:
            dataset = Dataset[dataset_kinds.Prompt](dataset_key="test_prompt", local_file_path=temp_file)
            threads = asyncio.run(dataset.load(mock_ctx))

            assert len(threads) == 1
            assert isinstance(threads[0], StringThread)
            assert str(threads[0].metadata["id"]) == "b2761a88-0662-453b-aba7-27846434dc55"
        finally:
            os.unlink(temp_file)

    def test_load_dataset_completion_format(self, mock_ctx):
        completion_data = {
            "prompt": [["user", "Write a haiku about coding."]],
            "completion": ["assistant", "Code flows like water,\nBugs hide in silent corners,\nDebug light reveals."],
            "metadata": {"id": "b2761a88-0662-453b-aba7-27846434dc56", "created_at": 1234567890},
        }

        temp_file = create_temp_dataset_file(completion_data, mock_ctx)
        try:
            dataset = Dataset[dataset_kinds.Prompt](dataset_key="test_completion", local_file_path=temp_file)
            threads = asyncio.run(dataset.load(mock_ctx))

            assert len(threads) == 1
            assert isinstance(threads[0], StringThread)
            assert str(threads[0].metadata["id"]) == "b2761a88-0662-453b-aba7-27846434dc56"
            assert "Code flows like water" in threads[0].last_content()
        finally:
            os.unlink(temp_file)

    def test_load_dataset_metric_format(self, mock_ctx):
        metric_data = {
            "prompt": [["user", "Rate this response quality."]],
            "completion": ["assistant", "This is a high-quality response."],
            "metrics": {"quality_score": 0.95, "helpfulness": 0.88},
            "metadata": {
                "id": "b2761a88-0662-453b-aba7-27846434dc57",
                "created_at": 1234567890,
                "annotator": "expert_1",
            },
        }

        temp_file = create_temp_dataset_file(metric_data, mock_ctx)
        try:
            dataset = Dataset[dataset_kinds.Metric](
                dataset_key="test_metric", local_file_path=temp_file, feedback_key="quality_score"
            )
            threads = asyncio.run(dataset.load(mock_ctx))

            assert len(threads) == 1
            assert isinstance(threads[0], StringThread)
            assert str(threads[0].metadata["id"]) == "b2761a88-0662-453b-aba7-27846434dc57"
            assert threads[0].metadata["res"] == 0.95
        finally:
            os.unlink(temp_file)

    def test_load_dataset_preference_format(self, mock_ctx):
        preference_data = {
            "prompt": [["user", "Explain quantum computing."]],
            "good_completion": ["assistant", "Quantum computing uses quantum mechanical phenomena..."],
            "bad_completion": ["assistant", "I don't know."],
            "metadata": {
                "id": "b2761a88-0662-453b-aba7-27846434dc58",
                "created_at": 1234567890,
                "preference_strength": "strong",
            },
        }

        temp_file = create_temp_dataset_file(preference_data, mock_ctx)
        try:
            dataset = Dataset[dataset_kinds.Preference](dataset_key="test_preference", local_file_path=temp_file)
            threads = asyncio.run(dataset.load(mock_ctx))

            assert len(threads) == 1
            assert isinstance(threads[0], StringThread)
            assert str(threads[0].metadata["id"]) == "b2761a88-0662-453b-aba7-27846434dc58"
            assert "Quantum computing uses" in threads[0].metadata["preferred_completion"]
            assert "I don't know" in threads[0].metadata["other_completion"]
        finally:
            os.unlink(temp_file)

    def test_load_dataset_external_format(self, mock_ctx):
        external_data = {
            "messages": [
                {"role": "user", "content": "Hello, how are you?"},
                {"role": "assistant", "content": "I'm doing well, thank you!"},
            ],
            "completion": "What a nice day",
            "metadata": {"source": "external_dataset", "quality": "high"},
        }

        temp_file = create_temp_dataset_file(external_data, mock_ctx)
        try:
            dataset = Dataset[dataset_kinds.Prompt](dataset_key="test_external", local_file_path=temp_file)
            threads = asyncio.run(dataset.load(mock_ctx))

            assert len(threads) == 1
            assert isinstance(threads[0], StringThread)
            assert threads[0].metadata["source"] == "external_dataset"
            assert threads[0].metadata["quality"] == "high"
            assert "What a nice day" in threads[0].last_content()
        finally:
            os.unlink(temp_file)

    def test_load_dataset_external_format_with_preferences(self, mock_ctx):
        """Test loading dataset with external format including preference data."""
        external_data = {
            "messages": [{"role": "user", "content": "Tell me about AI."}],
            "other_completion": "AI is bad.",
            "preferred_completion": "AI is a powerful technology that can help solve complex problems.",
            "metadata": {"topic": "AI_discussion"},
        }

        temp_file = create_temp_dataset_file(external_data, mock_ctx)
        try:
            dataset = Dataset[dataset_kinds.Preference](dataset_key="test_external_pref", local_file_path=temp_file)
            threads = asyncio.run(dataset.load(mock_ctx))

            assert len(threads) == 1
            assert isinstance(threads[0], StringThread)
            assert threads[0].metadata["topic"] == "AI_discussion"
            assert threads[0].metadata["other_completion"] == "AI is bad."
            assert (
                threads[0].metadata["preferred_completion"]
                == "AI is a powerful technology that can help solve complex problems."
            )
        finally:
            os.unlink(temp_file)

    def test_load_dataset_multiple_lines(self, mock_ctx):
        """Test loading dataset with multiple lines."""
        data_lines = [
            {"input": [{"role": "user", "content": "Question 1?"}], "completion": "Answer 1", "metadata": {"id": 1}},
            {"input": [{"role": "user", "content": "Question 2?"}], "completion": "Answer 2", "metadata": {"id": 2}},
        ]

        temp_file = create_temp_dataset_file(data_lines, mock_ctx)
        try:
            dataset = Dataset[dataset_kinds.Completion](dataset_key="test_multiple", local_file_path=temp_file)
            threads = asyncio.run(dataset.load(mock_ctx))

            assert len(threads) == 2
            assert all(isinstance(thread, StringThread) for thread in threads)
            assert threads[0].metadata["id"] == 1
            assert threads[1].metadata["id"] == 2
            assert "Answer 1" in threads[0].last_content()
            assert "Answer 2" in threads[1].last_content()
        finally:
            os.unlink(temp_file)

    def test_load_dataset_no_valid_samples_raises_error(self, mock_ctx):
        """Test that loading a dataset with no valid samples raises ValueError."""
        empty_content = "\n   \n"  # Only empty lines
        mock_ctx.file_storage.read.return_value = empty_content.encode("utf-8")

        dataset = Dataset[dataset_kinds.Prompt](dataset_key="test_empty", local_file_path="dummy_file")

        with pytest.raises(ValueError, match="Did not find any valid format samples in the dataset"):
            asyncio.run(dataset.load(mock_ctx))

    def test_load_dataset_external_metadata_with_external_data(self, mock_ctx):
        """Test that external_data in metadata is merged correctly."""
        internal_data = {
            "prompt": [["user", "Test prompt"]],
            "metadata": {
                "id": "b2761a88-0662-453b-aba7-27846434dc59",
                "created_at": 1234567890,
                "external_data": {"source_dataset": "custom", "annotation_quality": "high"},
            },
        }

        temp_file = create_temp_dataset_file(internal_data, mock_ctx)
        try:
            dataset = Dataset[dataset_kinds.Prompt](dataset_key="test_external_data", local_file_path=temp_file)
            threads = asyncio.run(dataset.load(mock_ctx))

            assert len(threads) == 1
            assert str(threads[0].metadata["id"]) == "b2761a88-0662-453b-aba7-27846434dc59"
            assert threads[0].metadata["source_dataset"] == "custom"
            assert threads[0].metadata["annotation_quality"] == "high"
        finally:
            os.unlink(temp_file)

    def test_load_dataset_any_format(self, mock_ctx):
        data_lines = [
            {"input": [{"role": "user", "content": "Question 1?"}], "completion": "Answer 1", "metadata": {"id": 1}},
            {"input": [{"role": "user", "content": "Question 2?"}], "completion": "Answer 2", "metadata": {"id": 2}},
        ]

        temp_file = create_temp_dataset_file(data_lines, mock_ctx)
        try:
            dataset = Dataset(dataset_key="test_external_data", local_file_path=temp_file)
            threads = asyncio.run(dataset.load(mock_ctx))

            assert len(threads) == 2
            assert all(isinstance(thread, StringThread) for thread in threads)
            assert threads[0].metadata["id"] == 1
            assert threads[1].metadata["id"] == 2
            assert "Answer 1" in threads[0].last_content()
            assert "Answer 2" in threads[1].last_content()
        finally:
            os.unlink(temp_file)
