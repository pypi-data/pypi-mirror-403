import pytest
import shutil
import os
from unittest.mock import Mock
import json
from adaptive_harmony import EvalSample
from adaptive_harmony import EvalSampleInteraction, Grade, StringThread
from adaptive_harmony.evaluation.evaluation_artifact import EvaluationArtifact
from adaptive_harmony.runtime.context import RecipeContext


@pytest.fixture
def mock_ctx():
    """Create a mock RecipeContext for testing."""
    ctx = Mock(spec=RecipeContext)

    # Mock config
    ctx.config = Mock()
    ctx.config.job_id = "test-job-id"

    # Mock file_storage with mk_url method
    ctx.file_storage = Mock()
    ctx.file_storage.mk_url = Mock(side_effect=lambda path: f"file://recipes/test-job-id/{path}")

    # Mock job
    ctx.job = Mock()
    ctx.job.register_artifact = Mock()

    return ctx


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test"""
    yield
    # Remove test directory if it exists
    test_dir = "recipes/test-job-id"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


def test_eval_artifact_base_creation(mock_ctx):
    # Test creating the base artifact
    eval_artifact = EvaluationArtifact(name="test-artifact", ctx=mock_ctx)
    assert eval_artifact.name == "test-artifact"
    assert eval_artifact.kind == "eval"
    assert "test-job-id" in eval_artifact.uri
    print(f"Created artifact: {eval_artifact}")


def test_record_samples(mock_ctx):
    eval_artifact = EvaluationArtifact(name="test-artifact", ctx=mock_ctx)

    sample = EvalSample(
        interaction=EvalSampleInteraction(thread=StringThread(turns=[("user", "Hello, how are you?")])),
        grades=[Grade(value=0.95, grader_key="test-grader", reasoning="Test reasoning")],
        dataset_key="test-dataset",
    )

    eval_artifact.add_samples([sample])

    # URI contains a UUID, so we check it starts with the expected path and contains job_id
    assert eval_artifact.uri.startswith("file://recipes/test-job-id/")
    assert eval_artifact.id != "test-artifact"  # ID is a UUID, not the name
    assert eval_artifact.name == "test-artifact"
    assert eval_artifact.kind == "eval"
    assert "test-job-id" in eval_artifact.uri
    print(f"Created artifact: {eval_artifact}")


def test_metadata_persisted_in_saved_json(mock_ctx):
    eval_artifact = EvaluationArtifact(name="test-artifact", ctx=mock_ctx)

    thread = StringThread(turns=[("user", "Hello, world!")])
    original_metadata = {
        "foo": "bar",
        "num": 42,
        "flag": True,
        "arr": [1, 2],
        "none": None,
        "nested": {"a": 1, "b": {"c": "deep"}},
    }
    thread.metadata = original_metadata

    sample = EvalSample(
        interaction=EvalSampleInteraction(thread=thread),
        grades=[Grade(value=1.0, grader_key="grader")],
        dataset_key="dataset-key",
    )
    eval_artifact.add_samples([sample])

    assert mock_ctx.file_storage.append.called
    args, kwargs = mock_ctx.file_storage.append.call_args
    data_bytes = args[0]
    json_str = data_bytes.decode("utf-8").rstrip("\n")
    obj = json.loads(json_str)

    interaction = obj.get("interaction")
    assert interaction is not None

    metadata = None
    if isinstance(interaction, dict) and "New" in interaction:
        thread_obj = interaction["New"]
        metadata = thread_obj.get("metadata")
    elif isinstance(interaction, dict) and "metadata" in interaction:
        metadata = interaction.get("metadata")

    assert metadata == original_metadata
