import asyncio
from adaptive_harmony import get_client, StringThread
from adaptive_harmony.graders import BaseGrader
from adaptive_harmony.graders.binary_judge import BinaryJudgeGrader, BinaryJudgeShot
from adaptive_harmony.graders.combined_grader import CombinedGrader
from adaptive_harmony.graders.faithfulness_judge import FaithfulnessGrader
from pprint import pprint


async def main():
    client = await get_client("ws://localhost:50053")

    humor_shots = [
        BinaryJudgeShot(
            thread=StringThread([("user", "tell me a joke"), ("assistant", "no")]),
            reasoning="The response is not funny, in fact it is not even a joke.",
            score="FAIL",
        )
    ]

    model = await client.model("openai://gpt-4o-mini").tp(1).spawn_inference("judge_model")
    # Humor binary judge

    humor_grader = BinaryJudgeGrader(
        grader_key="humor_grader",
        model=model,
        criteria="The response should be super funny and make people laugh.",
        shots=humor_shots,
    )

    # Conditional not related binary judge (test NA)
    conditional_grader = BinaryJudgeGrader(
        grader_key="conditional_grader",
        model=model,
        criteria="If the user is asking about car racing topics, the model should abstain from answering.",
        shots=None,
    )

    # Faithfulness scorer
    faithfulness_grader = FaithfulnessGrader(
        grader_key="faithfulness_grader",
        model=model,
        language="en",
    )

    async def example_scoringfunction(x: StringThread) -> float:
        return 1.0

    BaseGrader.from_function(grader_key="function_grader", async_fn=example_scoringfunction)

    all_graders = [humor_grader, conditional_grader, faithfulness_grader]
    # Create combined scorer
    combined_scorer = CombinedGrader(
        grader_key="combined_scorer",
        graders=all_graders,
        aggregation_method="mean",
    )

    # Generate a response to test
    prompt = "Tell me a funny joke. A funny joke to me is a joke that involves puns"
    completion = "Sure! Here's a pun-filled joke for you: I once heard a joke about a pencil… but it had no point."
    thread = StringThread().user(prompt).assistant(completion)

    print(f"Generated response:\n {thread.last_content()}")
    print()

    # Test the combined scorer
    print("=== Testing Combined Scorer ===")
    grade = await combined_scorer.grade(thread)

    print(f"Combined Score: {grade.value}")
    print()
    print("Detailed reason:")
    pprint(grade.reasoning)


if __name__ == "__main__":
    asyncio.run(main())
