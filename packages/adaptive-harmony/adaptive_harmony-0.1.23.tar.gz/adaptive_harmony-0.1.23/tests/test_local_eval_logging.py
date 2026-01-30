#!/usr/bin/env python3
"""
Test script for the save_detailed_eval_table class method.
This script creates mock evaluation data and tests the table generation functionality.
"""

import sys
from adaptive_harmony.runtime.context import RecipeContext
from adaptive_harmony import StringThread, EvalSample, Grade, EvalSampleInteraction


def create_mock_eval_samples():
    """Create mock evaluation samples for testing."""
    eval_samples = []

    # Create some test prompts and models - including repeated prompts with different completions
    test_data = [
        # First instance of "What is 2 + 2?" prompt
        ([("user", "What is 2 + 2?"), ("assistant", "2 + 2 equals 4")], "gpt-4"),
        # Second instance of the SAME prompt with different completion and model
        ([("user", "What is 2 + 2?"), ("assistant", "The answer is 4")], "gpt-3.5"),
        # Third instance of the SAME prompt with yet another completion and model
        ([("user", "What is 2 + 2?"), ("assistant", "Four")], "claude-3"),
        # First instance of photosynthesis prompt
        (
            [
                ("user", "Explain photosynthesis"),
                ("assistant", "Photosynthesis is the process by which plants convert sunlight into energy"),
            ],
            "llama-2",
        ),
        # Second instance of the SAME photosynthesis prompt with different completion
        (
            [
                ("user", "Explain photosynthesis"),
                ("assistant", "Plants use sunlight, water, and CO2 to make glucose and oxygen"),
            ],
            "gemini",
        ),
        # Unique prompt to test mixed grouping
        (
            [
                ("user", "Write a short poem"),
                ("assistant", "Roses are red, violets are blue, this is a test, for me and you"),
            ],
            "gpt-4",
        ),
    ]

    for i, (turns, model) in enumerate(test_data):
        # Create grades for different graders with varying scores
        grades = [
            Grade(
                grader_key="accuracy_grader",
                value=0.8 + (i * 0.03),  # Varying scores
                reasoning=f"Good accuracy for sample {i+1} using {model}",
            ),
            Grade(
                grader_key="helpfulness_grader",
                value=0.7 + (i * 0.02),
                reasoning=f"Helpful response for sample {i+1} from {model}",
            ),
            Grade(
                grader_key="clarity_grader",
                value=0.9 - (i * 0.01),
                reasoning=f"Clear and well-structured answer for sample {i+1} by {model}",
            ),
            # Add a grade without reasoning
            Grade(
                grader_key="speed_grader",
                value=0.6 + (i * 0.04),
                reasoning=None,  # No reasoning provided
            ),
        ]

        # Create EvalSample using MockStringThread
        eval_sample = EvalSample(
            interaction=EvalSampleInteraction(thread=StringThread(turns), source=f"{model}"),
            grades=grades,
            dataset_key="test_dataset",
        )

        eval_samples.append(eval_sample)

    return eval_samples


def extract_prompt_for_grouping(thread):
    """Extract prompt part for grouping (same logic as in the implementation)."""
    turns = thread.get_turns()
    prompt_turns = []

    for i, (role, content) in enumerate(turns):
        if role.lower() == "assistant" and i == len(turns) - 1:
            # This is the completion, skip it for grouping
            continue
        else:
            # This is part of the prompt
            prompt_turns.append((role, content))

    return " | ".join([f"[{role}] {content}" for role, content in prompt_turns])


def main():
    """Main test function."""
    print("🧪 Testing eval results logging ...")
    print("=" * 60)

    # Create mock data
    print("📝 Creating mock evaluation samples...")
    eval_samples = create_mock_eval_samples()
    print(f"   Created {len(eval_samples)} samples")

    # Test the actual class method
    print("\n💾 Testing RecipeContext.log_eval_result...")
    try:
        RecipeContext.log_eval_result(eval_samples)

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
