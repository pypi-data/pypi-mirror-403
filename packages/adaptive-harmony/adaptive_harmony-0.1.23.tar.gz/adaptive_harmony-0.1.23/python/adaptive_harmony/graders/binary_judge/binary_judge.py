from random import shuffle
from typing import Literal, TypedDict

from pydantic import BaseModel, Field

from adaptive_harmony import InferenceModel, StringThread
from adaptive_harmony.core.reasoning import remove_reasoning
from adaptive_harmony.core.structured_output import JsonParseError, render_pydantic_model, render_schema
from adaptive_harmony.core.utils import SingleTurnShot, stringify_thread
from adaptive_harmony.graders import BaseGrader, Grade
from adaptive_harmony.graders.binary_judge.prompts import DEFAULT_SHOTS, SYSTEM, USER, BinaryJudgeShot
from adaptive_harmony.graders.exceptions import IgnoreScoreException
from adaptive_harmony.graders.utils import (
    FailedJudgeLog,
    SuccessJudgeLog,
    separate_context_from_last_user_turn,
    validate_thread_last_assistant,
)
from adaptive_harmony.logging_table import Table


class BinaryJudgeOutput(BaseModel):
    reasoning: str = Field(description="Reasoning to support the rationale behind the score")
    score: Literal["PASS", "FAIL", "NA"] = Field(description="The score for the sample")


class ScoresMap(TypedDict):
    PASS: float
    FAIL: float


OPENAI_MODEL_FAMILIES_TEMPERATURE_1_ONLY = ["gpt-5", "o1", "o3", "o4"]


class BinaryJudgeGrader(BaseGrader):
    """
    Binary judge for scoring samples as PASS, FAIL or NA using few-shot prompting.
    If custom shots are provided, they are used instead of the default shots.
    """

    def __init__(
        self,
        grader_key: str,
        model: InferenceModel,
        criteria: str,
        shots: list[BinaryJudgeShot] | None = None,
        temperature: float = 0.0,
        grader_id: str | None = None,
    ):
        super().__init__(grader_key)
        self._logs: list[SuccessJudgeLog | FailedJudgeLog] = []  # type: ignore[assignment]
        self.criteria = criteria
        self.model = model
        self.temperature = temperature
        # Set temperature to 1.0 if model_key is an OpenAI model in the temperature-1-only list
        model_path: str = model.get_builder_args().get("path")  # type: ignore[assignment]
        if model_path.startswith("openai://"):
            model_name = model_path.removeprefix("openai://").split("?")[0]
            if any(model_name.startswith(model) for model in OPENAI_MODEL_FAMILIES_TEMPERATURE_1_ONLY):
                temperature = 1.0
        self.model = model.temperature(temperature)
        # Score mapping
        self.scores_map: ScoresMap = {"PASS": 1.0, "FAIL": 0.0}
        self.grader_id_or_key = grader_id or grader_key

        self._original_shots = shots or DEFAULT_SHOTS
        self._shots = self._format_user_shots(shots or DEFAULT_SHOTS)

    @property
    def shots(self) -> list[BinaryJudgeShot]:
        return self._original_shots

    @shots.setter
    def shots(self, shots: list[BinaryJudgeShot]):
        self._original_shots = shots
        self._shots = self._format_user_shots(shots)

    @staticmethod
    def _extract_user_template_kwargs(thread: StringThread) -> dict[str, str]:
        validate_thread_last_assistant(thread)
        # Separate conversation context from last user turn
        context_turns, user_question = separate_context_from_last_user_turn(thread)
        context_str = stringify_thread(StringThread(context_turns))
        completion = remove_reasoning(thread.last_content())

        assert user_question, "There must be at least one user turn"
        return dict(
            context=context_str,
            user_question=user_question,
            completion=completion,
        )

    def _get_placeholder_reasoning(self, score: Literal["PASS", "FAIL", "NA"]) -> str:
        if score == "PASS":
            return "The completions complies with the criteria"
        elif score == "FAIL":
            return "The completion does not comply with the criteria"
        else:
            return "The criteria is not applicable to the completion"

    def _format_user_shots(self, shots: list[BinaryJudgeShot]) -> list[SingleTurnShot]:
        """
        Turn a possibly multi turn example into a single turn one,
        with appropriate kwargs to format the task's prompt templates
        """
        new_shots: list[SingleTurnShot] = []
        for shot in shots:
            placeholder_reasoning = self._get_placeholder_reasoning(shot.score)

            user_template_kwargs = self._extract_user_template_kwargs(shot.thread)
            user_template_kwargs["criteria"] = shot.criteria or self.criteria
            single_turn_shot = SingleTurnShot(
                user=user_template_kwargs,
                assistant={
                    "json_answer": render_pydantic_model(
                        BinaryJudgeOutput(
                            reasoning=shot.reasoning or placeholder_reasoning,
                            score=shot.score,
                        )
                    )
                },
            )
            new_shots.append(single_turn_shot)

        return new_shots

    def _get_judge_prompt(self, thread: StringThread) -> StringThread:
        """Build the judging prompt for a given sample."""
        # build the real user template kwargs
        user_template_kwargs = self._extract_user_template_kwargs(thread)
        user_template_kwargs["criteria"] = self.criteria
        # system kwarg
        output_json_schema = render_schema(BinaryJudgeOutput)

        # system
        prompt = StringThread().system(SYSTEM.format(json_schema=output_json_schema))
        # shots
        for shot in self._shots:
            prompt = prompt.user(USER.format(**shot["user"]))
            prompt = prompt.assistant(shot["assistant"]["json_answer"])
        # real input
        prompt = prompt.user(USER.format(**user_template_kwargs))

        return prompt

    async def grade(self, sample: StringThread) -> Grade:
        judging_prompt = self._get_judge_prompt(sample)
        str_prompt = stringify_thread(judging_prompt, sep=f"\n\n{'-' * 10}\n\n")

        try:
            _, parsed_output = await self.model.generate_and_validate(judging_prompt, BinaryJudgeOutput)
        except JsonParseError as e:
            self.add_log({"prompt": str_prompt, "error": f"{str(e)}\n\nCOMPLETION:\n{e.completion}"})
            raise
        except Exception as e:
            self.add_log({"prompt": str_prompt, "error": str(e)})
            raise

        float_score = self.scores_map.get(parsed_output.score)

        # NA case, ignore score
        if float_score is None:
            self.add_log({"prompt": str_prompt, "error": f"Non applicable score: {parsed_output.reasoning}"})
            raise IgnoreScoreException(f"Non applicable score: {parsed_output.reasoning}")

        else:
            grade = Grade(value=float_score, grader_key=self.grader_id_or_key, reasoning=parsed_output.reasoning)
            self.add_log({"score": float_score, "prompt": str_prompt, "reasoning": parsed_output.reasoning})

            return grade

    def add_log(self, log: SuccessJudgeLog | FailedJudgeLog) -> None:  # type: ignore[override]
        self._logs.append(log)

    def get_logs(self, clear: bool = False, log_all_samples: bool = False) -> dict[str, float | Table]:
        # Only clear logs at the end if clear is True
        logs = super().get_logs(clear=False)

        # get sample of PASS and FAIL samples to log in table
        successfully_scored_samples = [log for log in self._logs if "score" in log]
        if not log_all_samples:
            shuffle(successfully_scored_samples)
            samples_score_0 = [log for log in successfully_scored_samples if log["score"] == self.scores_map["FAIL"]][
                :5
            ]
            samples_score_1 = [log for log in successfully_scored_samples if log["score"] == self.scores_map["PASS"]][
                :5
            ]
            subset_successfully_scored_samples = samples_score_0 + samples_score_1
        else:
            subset_successfully_scored_samples = successfully_scored_samples

        # get failed samples to log in table
        failed_scored_samples = [log for log in self._logs if "error" in log]

        sample_logs = self.get_sample_tables(subset_successfully_scored_samples, failed_scored_samples)
        logs.update(sample_logs)

        if clear:
            self.clear_logs()

        return logs
