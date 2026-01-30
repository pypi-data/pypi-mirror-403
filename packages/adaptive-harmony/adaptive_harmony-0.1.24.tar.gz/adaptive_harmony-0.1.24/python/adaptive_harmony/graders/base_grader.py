import statistics
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, cast

from harmony_client import InferenceModel
from harmony_client.runtime.data import (
    AdaptiveGrader,
    CustomJudge,
    PrebuiltConfigKey,
    PrebuiltJudge,
    RemoteRewardEndpoint,
)

from adaptive_harmony import Grade, StringThread
from adaptive_harmony.graders.utils import FailedJudgeLog, SuccessJudgeLog
from adaptive_harmony.logging_table import Table
from adaptive_harmony.parameters import Model
from adaptive_harmony.runtime import RecipeContext


class BaseGrader[LogType](ABC):
    """
    Base Grader to inherit from when building a scoring function.
    """

    def __init__(self, grader_key: str):
        self._logs: list[LogType] = []
        self.grader_key = grader_key

    @abstractmethod
    async def grade(self, sample: StringThread) -> Grade:
        """
        Grade a single sample.
        Returns a single float score, with optional metadata.
        Metadata can be useful for evals when LLM reasoning regarding the score is available.
        """
        pass

    async def score_float_value(self, sample: StringThread) -> float:
        """Returns only the float score from .score"""
        return (await self.grade(sample)).value

    def add_log(self, log_data: LogType) -> None:
        """Add a log entry to the scorer's log collection."""
        self._logs.append(log_data)

    def get_logs(self, clear: bool = False, log_all_samples: bool = False) -> dict[str, float | Table]:
        """
        Get aggregated logs from all score calls.
        Base implementation computes statistics for "score" keys in individual logs.
        If there are none, returns empty dict.
        """
        if not self._logs:
            return {}

        scores = [s for s in [cast(dict[str, Any], log).get("score") for log in self._logs] if s is not None]
        logs = {}
        if scores:
            logs.update(
                dict(
                    **{
                        f"score/{key}": value
                        for key, value in dict(
                            mean=statistics.mean(scores),
                            std=statistics.stdev(scores) if len(scores) > 1 else 0.0,
                            min=min(scores),
                            max=max(scores),
                            count=len(scores),
                        ).items()
                    },
                )
            )
        if clear:
            self.clear_logs()
        return logs

    def clear_logs(self) -> None:
        """
        Clear all accumulated logs.
        """
        self._logs.clear()

    def get_sample_tables(
        self, successful_samples: list[SuccessJudgeLog], failed_samples: list[FailedJudgeLog] | None = None
    ):
        table_logs = {}
        scored_samples = (
            Table()
            .add_column("Prompt", [log["prompt"] for log in successful_samples])
            .add_column("Reasoning", [log.get("reasoning") for log in successful_samples])
            .add_column("Score", [float(log["score"]) for log in successful_samples])
        )
        if failed_samples:
            unscored_samples = (
                Table()
                .add_column("Prompt", [log.get("prompt") for log in failed_samples])
                .add_column("Error", [str(log["error"]) for log in failed_samples])
            )
            table_logs["score/unscored_samples"] = unscored_samples
        table_logs["score/scored_samples"] = scored_samples
        table_logs["score/unscored_samples_count"] = len(failed_samples) if failed_samples else 0
        table_logs["score/scored_samples_count"] = len(successful_samples)
        return table_logs

    @classmethod
    def from_function(
        cls, grader_key: str, async_fn: Callable[[StringThread], Awaitable[float]]
    ) -> "BaseGrader[dict[str, Any]]":
        class FunctionScorer(BaseGrader[dict[str, float]]):
            def __init__(self):
                super().__init__(grader_key)

            async def grade(self, sample: StringThread) -> Grade:
                result = await async_fn(sample)
                grade = Grade(value=result, grader_key=self.grader_key)
                self.add_log({"score": result})
                return grade

        return FunctionScorer()

    @classmethod
    async def from_config(
        cls,
        grader_config: AdaptiveGrader,
        ctx: RecipeContext,
        tp: int | None = None,
        kv_cache_len: int | None = None,
        max_tokens: int | None = None,
    ) -> "BaseGrader[dict[str, Any]]":
        match grader_config.config.type:
            case "Judge":
                config = cast(CustomJudge, grader_config.config)
                return await cls.from_templated_judge(
                    grader_config.key, str(grader_config.grader_id), config, ctx, tp, kv_cache_len, max_tokens
                )
            case "Prebuilt":
                config = cast(PrebuiltJudge, grader_config.config)
                return await cls.from_prebuilt_judge(
                    grader_config.key, str(grader_config.grader_id), config, ctx, tp, kv_cache_len
                )
            case "Remote":
                config = cast(RemoteRewardEndpoint, grader_config.config)
                return cls.from_remote_reward_endpoint(grader_config.key, str(grader_config.grader_id), config)
            case _:
                raise ValueError(f"Invalid grader type: {grader_config.config.type}")

    @classmethod
    async def from_templated_judge(
        cls,
        grader_key: str,
        grader_id: str,
        config: CustomJudge,
        ctx: RecipeContext,
        tp: int | None = None,
        kv_cache_len: int | None = None,
        max_tokens: int | None = None,
    ) -> "BaseGrader[dict[str, Any]]":
        # Import here to avoid circular dependency
        from adaptive_harmony.graders.templated_prompt_judge import (
            BinaryJudgeOutput,
            TemplatedPromptJudgeGrader,
        )

        # Convert examples to template variables
        examples = []
        for example in config.examples:
            examples.append(
                {
                    "context_str": (
                        "\n".join(f"{msg.role}:\n{msg.content}" for msg in example.input[:-1])
                        if len(example.input) > 1
                        else ""
                    ),
                    "user_question": example.input[-1].content if example.input else "",
                    "completion": example.output,
                    "output_json": f'{{"reasoning": "{example.reasoning or ""}", "score": "{"PASS" if example.pass_ else "FAIL"}"}}',
                }
            )

        template_vars = {
            "criteria": config.criteria,
            "examples": examples,
        }

        model = await get_model(ctx, grader_key, config.model_key, kv_cache_len, max_tokens, tp)

        return TemplatedPromptJudgeGrader(
            grader_key=grader_key,
            model=model,
            grader_id=grader_id,
            system_template=config.system_template,
            user_template=config.user_template,
            output_model=BinaryJudgeOutput,
            template_variables=template_vars,
        )  # type: ignore[return-value]

    @classmethod
    async def from_prebuilt_judge(
        cls,
        grader_key: str,
        grader_id: str,
        config: PrebuiltJudge,
        ctx: RecipeContext,
        tp: int | None = None,
        kv_cache_len: int | None = None,
        max_tokens: int | None = None,
    ) -> "BaseGrader[dict[str, Any]]":
        model = await get_model(ctx, grader_key, config.model_key, kv_cache_len, max_tokens, tp)

        match config.prebuilt_config_key:
            case PrebuiltConfigKey.Faithfulness:
                # Import here to avoid circular dependency
                from adaptive_harmony.graders.faithfulness_judge.faithfulness_judge import FaithfulnessGrader

                return FaithfulnessGrader(
                    grader_key=grader_key,
                    grader_id=grader_id,
                    model=model,
                )
            case PrebuiltConfigKey.AnswerRelevancy:
                # Import here to avoid circular dependency
                from adaptive_harmony.graders.answer_relevancy_judge.answer_relevancy_judge import AnswerRelevancyGrader

                return AnswerRelevancyGrader(
                    grader_key=grader_key,
                    grader_id=grader_id,
                    model=model,
                )
            case PrebuiltConfigKey.ContextRelevancy:
                # Import here to avoid circular dependency
                from adaptive_harmony.graders.context_relevancy_judge.context_relevancy_judge import (
                    ContextRelevancyGrader,
                )

                return ContextRelevancyGrader(
                    grader_key=grader_key,
                    grader_id=grader_id,
                    model=model,
                )
            case _:
                raise ValueError(f"Invalid prebuilt judge type: {config.prebuilt_config_key}")

    @classmethod
    def from_remote_reward_endpoint(
        cls, grader_key: str, grader_id: str, config: RemoteRewardEndpoint
    ) -> "BaseGrader[dict[str, Any]]":
        # Import here to avoid circular dependency
        from adaptive_harmony.graders.reward_server_grader import RewardServerGrader

        return RewardServerGrader(grader_key=grader_key, grader_id=grader_id, reward_server_ip=config.url)


async def get_model(
    ctx: RecipeContext,
    grader_key: str,
    model_key: str,
    kv_cache_len: int | None,
    max_tokens: int | None,
    tp: int | None,
) -> InferenceModel:
    model_builder = await Model(model_key=model_key).to_builder(
        ctx, kv_cache_len=kv_cache_len, tokens_to_generate=max_tokens, tp=tp
    )
    model = await model_builder.spawn_inference(grader_key)
    return model
