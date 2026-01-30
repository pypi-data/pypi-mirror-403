import pytest
from adaptive_harmony import JobArtifact


def test_job_artifact_basic_creation():
    """Test basic JobArtifact creation without metadata."""
    artifact = JobArtifact(id="test-id", name="test-artifact", kind="model", uri="s3://bucket/path")

    assert artifact.id == "test-id"
    assert artifact.name == "test-artifact"
    assert artifact.kind == "model"
    assert artifact.uri == "s3://bucket/path"


def test_job_artifact_complex_metadata():
    """Test JobArtifact with complex nested metadata structures."""
    complex_metadata = {
        "model_config": {"architecture": "transformer", "layers": 12, "hidden_size": 768, "attention_heads": 12},
        "training_stats": {"epochs": 10, "final_loss": 0.123, "best_accuracy": 0.956, "convergence_epoch": 8},
        "evaluation_metrics": [
            {"metric": "accuracy", "value": 0.95},
            {"metric": "f1_score", "value": 0.94},
            {"metric": "precision", "value": 0.96},
        ],
    }

    artifact = JobArtifact(
        id="complex-model", name="complex-test-model", kind="model", uri="s3://models/complex-model", **complex_metadata
    )

    assert artifact.id == "complex-model"
    assert artifact.name == "complex-test-model"
    assert artifact.kind == "model"


def test_job_artifact_special_characters_in_metadata():
    """Test JobArtifact with special characters and unicode in metadata."""
    artifact = JobArtifact(
        id="unicode-test",
        name="test-artifact",
        kind="dataset",
        description="Test with émojis 🚀 and special chars: !@#$%^&*()",
        unicode_text="Тест на русском языке",
        chinese_text="测试中文字符",
        emoji_tags=["🔥", "⭐", "🎯"],
    )

    assert artifact.id == "unicode-test"
    assert artifact.name == "test-artifact"


def test_job_artifact_metadata_with_none_values():
    """Test JobArtifact with None values in metadata."""
    artifact = JobArtifact(
        id="test-id",
        name="test-artifact",
        kind="dataset",
        uri=None,  # Test None URI
        description="Test dataset",
        size=None,  # Test None in metadata
        validated=True,
        creation_date="2025-01-01",
    )

    assert artifact.id == "test-id"
    assert artifact.uri is None


def test_job_artifact_invalid_metadata():
    """Test JobArtifact with non-serializable metadata should raise an error."""

    # Test with non-JSON serializable object
    class NonSerializable:
        pass

    with pytest.raises(TypeError, match="Object of type NonSerializable is not JSON serializable"):
        JobArtifact(id="test-id", name="test-artifact", kind="model", invalid_object=NonSerializable())
