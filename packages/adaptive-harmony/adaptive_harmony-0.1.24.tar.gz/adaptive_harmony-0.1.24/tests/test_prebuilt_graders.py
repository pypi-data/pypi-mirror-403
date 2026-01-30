import pytest
from unittest.mock import Mock, AsyncMock
from adaptive_harmony import InferenceModel, StringThread, Grade, HarmonyClient, get_client
from adaptive_harmony.graders.answer_relevancy_judge.answer_relevancy_judge import (
    AnswerRelevancyGrader,
    StatementRelevancy,
    AnswerRelevancyResults,
)
from adaptive_harmony.graders.context_relevancy_judge.context_relevancy_judge import (
    ContextRelevancyGrader,
    DocumentRelevancyResult,
)


@pytest.fixture
async def harmony_client():
    """Create a mock HarmonyClient."""
    return await get_client("ws://localhost:50053", num_gpus=0)


@pytest.mark.harmony
class TestAnswerRelevancyGrader:
    """Test suite for AnswerRelevancyGrader."""

    @pytest.fixture
    async def mock_model(self):
        """Create a mock InferenceModel."""
        mock_model = Mock(spec=InferenceModel)
        mock_model.render_schema.return_value = "{}"
        mock_model.temperature.return_value = mock_model
        mock_model.generate_and_validate = AsyncMock(return_value=(None, AnswerRelevancyResults(results=[])))
        return mock_model

    @pytest.fixture
    async def grader(self, harmony_client: HarmonyClient):
        """Create an AnswerRelevancyGrader instance for testing with a mock setup method."""
        model = await harmony_client.model("openai://gpt-5-nano", kv_cache_len=100).spawn_inference("test_grader")
        grader = AnswerRelevancyGrader(
            model=model,
            language="en",
            grader_key="test_grader",
            grader_id="test_id",
        )
        return grader

    def test_sentence_splitting_english(self, grader: AnswerRelevancyGrader):
        """Test sentence splitting functionality with English text."""
        text = "This is the first sentence. This is the second sentence! This is the third sentence?"
        sentences = grader.sentence_splitter.segment(text)

        assert len(sentences) == 3
        assert "This is the first sentence" in sentences[0]
        assert "This is the second sentence" in sentences[1]
        assert "This is the third sentence" in sentences[2]

    async def test_get_judge_thread_simple(self, grader: AnswerRelevancyGrader, mock_model):
        """Test get_judge_thread method with a simple thread."""
        thread = (
            StringThread()
            .user("What is Python?")
            .assistant("Python is a programming language. It is very popular. It has many libraries.")
        )
        grader.model = mock_model
        await grader.grade(thread)
        judge_prompt = grader._logs[0]["prompt"]

        assert "What is Python?" in judge_prompt
        assert "0: Python is a programming language" in judge_prompt
        assert "1: It is very popular" in judge_prompt
        assert "2: It has many libraries" in judge_prompt

    @pytest.mark.asyncio
    async def test_grade_successful(self, grader, mock_model):
        """Test successful grading with mock response."""
        # Mock the model response
        mock_response = AnswerRelevancyResults(
            results=[
                StatementRelevancy(reason="Directly answers the question", score=1),
                StatementRelevancy(reason="Provides additional relevant information", score=1),
                StatementRelevancy(reason="Unrelated statement", score=0),
            ]
        )

        thread = (
            StringThread()
            .user("What is Python?")
            .assistant("Python is a programming language. It is very popular. The weather is nice today.")
        )

        mock_model.generate_and_validate = AsyncMock(return_value=(None, mock_response))
        grader.model = mock_model
        grade = await grader.grade(thread)
        logs = grader.get_logs()

        assert isinstance(grade, Grade)
        assert grade.value == pytest.approx(2 / 3, abs=0.01)  # (1+1+0)/3
        assert "✅" in grade.reasoning
        assert "❌" in grade.reasoning
        assert "Python is a programming language" in grade.reasoning
        assert logs["score/scored_samples_count"] == 1
        assert logs["score/unscored_samples_count"] == 0

    @pytest.mark.asyncio
    async def test_grade_with_error(self, grader):
        """Test grading when model raises an exception."""
        # Mock the model to raise an exception

        thread = StringThread().user("What is Python?").assistant("Python is a programming language.")
        mock_model = Mock(spec=InferenceModel)
        mock_model.render_schema.return_value = "{}"
        mock_model.temperature.return_value = mock_model
        mock_model.generate_and_validate = AsyncMock(side_effect=Exception("Model error"))
        grader.model = mock_model
        with pytest.raises(Exception, match="Model error"):
            await grader.grade(thread)

        # Check that error was logged
        logs = grader.get_logs()
        assert logs["score/unscored_samples_count"] == 1

    @pytest.mark.asyncio
    async def test_grade_empty_sentences(self, grader, mock_model):
        """Test grading with empty or whitespace-only sentences."""
        # Mock the model response for empty sentences

        thread = StringThread().user("What is Python?").assistant("   .   .   ")

        grader.model = mock_model
        grade = await grader.grade(thread)

        assert grade.value == 0.0

    @pytest.mark.asyncio
    async def test_grade_invalid_thread(self, grader):
        """Test grading with invalid thread (no assistant message)."""
        thread = StringThread().user("What is Python?")
        with pytest.raises(AssertionError):
            await grader.grade(thread)


@pytest.mark.harmony
class TestContextRelevancyGrader:
    """Test suite for ContextRelevancyGrader."""

    @pytest.fixture
    async def mock_model(self):
        """Create a mock InferenceModel."""
        mock_model = Mock(spec=InferenceModel)
        mock_model.render_schema.return_value = "{}"
        mock_model.temperature.return_value = mock_model
        mock_model.generate_and_validate = AsyncMock(
            return_value=(None, DocumentRelevancyResult(reason="Test", score=1))
        )
        return mock_model

    @pytest.fixture
    async def context_grader(self, harmony_client):
        """Create a ContextRelevancyGrader instance for testing."""
        model = (
            await harmony_client.model("openai://gpt-5-nano", kv_cache_len=100)
            .tp(1)
            .spawn_inference("test_context_grader")
        )
        grader = ContextRelevancyGrader(
            model=model,
            language="en",
            grader_key="test_context_grader",
            grader_id="test_context_id",
        )
        return grader

    @pytest.mark.asyncio
    async def test_grade_successful_single_document(self, context_grader, mock_model):
        """Test successful grading with a single document."""
        # Mock the model response
        mock_response = DocumentRelevancyResult(reason="Document contains relevant information", score=1)
        mock_model.generate_and_validate = AsyncMock(return_value=(None, mock_response))
        context_grader.model = mock_model

        thread = StringThread(
            [("user", "What is Python?")],
            {"documents": ["Python is a high-level programming language known for its simplicity and readability."]},
        )

        grade = await context_grader.grade(thread)
        logs = context_grader.get_logs()

        assert isinstance(grade, Grade)
        assert grade.value == 1.0
        assert grade.grader_key == "test_context_id"
        assert "✅" in grade.reasoning
        assert "Document contains relevant information" in grade.reasoning
        print(logs)
        assert logs["score/scored_samples_count"] == 1
        assert logs["score/unscored_samples_count"] == 0

    @pytest.mark.asyncio
    async def test_grade_successful_multiple_documents(self, context_grader, mock_model):
        """Test successful grading with multiple documents."""
        # Mock different responses for different documents
        mock_responses = [
            (None, DocumentRelevancyResult(reason="Highly relevant", score=1)),
            (None, DocumentRelevancyResult(reason="Not relevant", score=0)),
            (None, DocumentRelevancyResult(reason="Somewhat relevant", score=1)),
        ]

        mock_model.generate_and_validate = AsyncMock(side_effect=mock_responses)
        context_grader.model = mock_model

        thread = StringThread(
            [("user", "What is Python?")],
            {
                "documents": [
                    "Python is a programming language.",
                    "The weather is nice today.",
                    "Programming languages are tools for developers.",
                ]
            },
        )

        grade = await context_grader.grade(thread)
        logs = context_grader.get_logs()

        assert isinstance(grade, Grade)
        assert grade.value == pytest.approx(2 / 3, abs=0.01)  # (1+0+1)/3
        assert "✅" in grade.reasoning
        assert "❌" in grade.reasoning
        print(logs)
        assert logs["score/scored_samples_count"] == 1
        assert logs["score/unscored_samples_count"] == 0

    @pytest.mark.asyncio
    async def test_grade_no_documents(self, context_grader):
        """Test grading with no documents in metadata raises ValueError."""
        thread = StringThread().user("What is Python?")

        with pytest.raises(ValueError, match="No document turns found in thread"):
            await context_grader.grade(thread)

    @pytest.mark.asyncio
    async def test_grade_model_error(self, context_grader, mock_model):
        """Test grading when model raises an exception."""
        mock_model.generate_and_validate = AsyncMock(side_effect=Exception("Model error"))
        context_grader.model = mock_model

        thread = StringThread().user("What is Python?")
        thread.metadata = {"documents": ["Python is a programming language."]}

        with pytest.raises(Exception, match="Model error"):
            await context_grader.grade(thread)

        # Check that error was logged
        logs = context_grader.get_logs()
        assert logs["score/unscored_samples_count"] == 1

    @pytest.mark.asyncio
    async def test_grade_empty_documents(self, context_grader, mock_model):
        """Test grading with empty document content."""
        mock_response = DocumentRelevancyResult(reason="Empty document", score=0)
        mock_model.generate_and_validate = AsyncMock(return_value=(None, mock_response))
        context_grader.model = mock_model

        thread = StringThread().user("What is Python?")
        thread.metadata = {"documents": [""]}

        grade = await context_grader.grade(thread)

        assert grade.value == 0.0
        assert "Empty document" in grade.reasoning


if __name__ == "__main__":
    pytest.main([__file__])
