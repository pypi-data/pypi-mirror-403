from adaptive_harmony.core.structured_output import pydantic_parse
from adaptive_harmony.core.reasoning import remove_reasoning
from adaptive_harmony.graders.binary_judge.binary_judge import BinaryJudgeOutput


class TestRemoveReasoning:
    """Test cases for the remove_reasoning function."""

    def test_remove_simple_think_tags(self):
        """Test removal of simple think tags."""
        completion = "<think>I need to think about this carefully.</think>This is the final answer."
        expected = "This is the final answer."
        result = remove_reasoning(completion)
        assert result == expected

    def test_remove_simple_think_tags_with_multiple_tags(self):
        """Test removal of simple think tags with multiple tags (only first one removed)."""
        completion = "<think>I need to think about this carefully.</think><think>I need to think about this carefully.</think>This is the final answer."
        expected = "<think>I need to think about this carefully.</think>This is the final answer."
        result = remove_reasoning(completion)
        assert result == expected

    def test_remove_think_tags_with_newlines(self):
        """Test removal of think tags that span multiple lines."""
        completion = """<think>
This is a multi-line
thinking process
with various details.
</think>
This is the final answer."""
        expected = "This is the final answer."
        result = remove_reasoning(completion)
        assert result == expected

    def test_no_think_tags(self):
        """Test that text without think tags is unchanged."""
        completion = "This is a simple answer without any think tags."
        result = remove_reasoning(completion)
        assert result == completion

    def test_empty_think_tags(self):
        """Test removal of empty think tags."""
        completion = "<think></think>answer."
        expected = "answer."
        result = remove_reasoning(completion)
        assert result == expected

    def test_only_think_tags(self):
        """Test text that contains only think tags."""
        completion = "<think>Only thinking here</think>"
        expected = ""
        result = remove_reasoning(completion)
        assert result == expected

    def test_think_tags_with_special_characters(self):
        """Test removal of think tags containing special characters."""
        completion = "<think>Special chars: !@#$%^&*()</think>answer."
        expected = "answer."
        result = remove_reasoning(completion)
        assert result == expected

    def test_qwen_model_no_opening_tag(self):
        """Test removal of reasoning content from start to </think> (Qwen models)."""
        completion = """I need to think about this carefully:
1. First, I need to understand the criteria
2. Then I need to evaluate the completion
3. Finally, I need to provide a score

Based on my analysis, the completion meets the criteria.
</think>

This is the final answer."""
        expected = "This is the final answer."
        result = remove_reasoning(completion)
        assert result == expected

    def test_qwen_model_multiline_reasoning(self):
        """Test removal of multiline reasoning content ending with </think>."""
        completion = """Let me analyze this step by step:

The user is asking for help with their code.
I should provide a clear and helpful response.
The solution involves updating the regex pattern.
</think>

Here's the updated code you need."""
        expected = "Here's the updated code you need."
        result = remove_reasoning(completion)
        assert result == expected

    def test_structured_output_example(self):
        """Test a complete workflow example."""
        # Simulate a completion with think tags
        completion_with_thinking = """<think>
Let me think about this carefully:
1. First, I need to understand the criteria
2. Then I need to evaluate the completion
3. Finally, I need to provide a score

Based on my analysis, the completion meets the criteria.
</think>

```json
{
    "reasoning": "The completion meets the criteria and follows the guidelines",
    "score": "PASS"
}
```"""

        # Create BinaryJudgeOutput with the cleaned completion
        parsed = pydantic_parse(completion_with_thinking, BinaryJudgeOutput)

        # Verify the results
        assert parsed.score == "PASS"
        assert "meets the criteria" in parsed.reasoning
