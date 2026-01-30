# ruff: noqa: F403, F401
from typing import TYPE_CHECKING

from harmony_client import (
    EvalSample as EvalSample,
)
from harmony_client import (
    EvalSampleInteraction as EvalSampleInteraction,
)
from harmony_client import (
    Grade as Grade,
)
from harmony_client import (
    HarmonyClient as HarmonyClient,
)
from harmony_client import (
    HarmonyJobNotifier as HarmonyJobNotifier,
)
from harmony_client import (
    InferenceModel as InferenceModel,
)
from harmony_client import (
    JobArtifact as JobArtifact,
)
from harmony_client import (
    JobNotifier as JobNotifier,
)
from harmony_client import (
    ModelBuilder as ModelBuilder,
)
from harmony_client import (
    StageNotifier as StageNotifier,
)
from harmony_client import (
    StringThread as StringThread,
)
from harmony_client import (
    TokenizedThread as TokenizedThread,
)
from harmony_client import (
    TrainingModel as TrainingModel,
)
from harmony_client import (
    get_client as get_client,
)
from harmony_client import parameters as parameters
from harmony_client import runtime as runtime
from rich.progress import Progress

if TYPE_CHECKING:
    from harmony_client import StringTurn as StringTurn
else:
    from typing import NamedTuple

    class StringTurn(NamedTuple):
        role: str
        content: str


from harmony_client.artifacts.custom_artifact import CustomArtifact
from harmony_client.artifacts.dataset_artifact import DatasetArtifact
from harmony_client.file_storage import (
    FileStorage,
    FileStorageConfig,
    LocalFileStorageConfig,
    S3FileStorageConfig,
    StoredFile,
)

import adaptive_harmony.core.rl_utils as rl_utils
from adaptive_harmony.core.dataset import DataSet
from adaptive_harmony.core.schedulers import CombinedSchedule, CosineScheduler, CosineSchedulerWithoutWarmup, Scheduler
from adaptive_harmony.evaluation.evaluation_artifact import EvaluationArtifact
from adaptive_harmony.metric_logger import Logger, WandbLogger

# Ensure key classes are available at module level
__all__ = [
    "StringThread",
    "StringTurn",
    "TokenizedThread",
    "InferenceModel",
    "ModelBuilder",
    "TrainingModel",
    "HarmonyClient",
    "get_client",
    "DataSet",
    "CosineScheduler",
    "CombinedSchedule",
    "CosineSchedulerWithoutWarmup",
    "Scheduler",
    "WandbLogger",
    "Logger",
    "FileStorage",
    "FileStorageConfig",
    "LocalFileStorageConfig",
    "S3FileStorageConfig",
    "StoredFile",
    "EvaluationArtifact",
    "CustomArtifact",
    "DatasetArtifact",
    "rl_utils",
    "Grade",
    "EvalSample",
    "EvalSampleInteraction",
    "JobArtifact",
]


# Patch StringThread to use rich for display
from harmony_client.runtime.model_artifact_save import save_with_artifact

from adaptive_harmony.core.display import _stringthread_repr, _tokenizedthread_repr
from adaptive_harmony.core.image_utils import string_thread_to_html_string

# Patch InferenceModel to have json output capabilities
from adaptive_harmony.core.structured_output import generate_and_validate, render_pydantic_model, render_schema

StringThread.__repr__ = _stringthread_repr  # type: ignore
TokenizedThread.__repr__ = _tokenizedthread_repr  # type: ignore
setattr(StringThread, "_repr_html_", string_thread_to_html_string)
setattr(InferenceModel, "generate_and_validate", generate_and_validate)
setattr(InferenceModel, "render_schema", staticmethod(render_schema))
setattr(InferenceModel, "render_pydantic_model", staticmethod(render_pydantic_model))

_original_training_model_save = TrainingModel.save


async def _save_with_artifact_wrapper(model: TrainingModel, model_name: str, inference_only: bool = True, ctx=None):
    return await save_with_artifact(model, model_name, inference_only, ctx, _original_training_model_save)


setattr(TrainingModel, "save", _save_with_artifact_wrapper)


async def spawn_train(self: ModelBuilder, name: str, max_batch_size: int) -> TrainingModel:
    fut = await self.spawn_train_with_progress(name, max_batch_size)  # type:ignore

    with Progress() as pbar:
        task = pbar.add_task("Loading model", total=1000)

        while (prog := await fut._await_progress()) != 1.0:
            pbar.update(task, completed=prog, total=1.0)
        pbar.update(task, completed=1.0, total=1.0)

    return await fut.get()


async def spawn_inference(self: ModelBuilder, name: str) -> InferenceModel:
    fut = await self.spawn_inference_with_progress(name)  # type:ignore

    with Progress() as pbar:
        task = pbar.add_task("Loading model", total=1000)

        while (prog := await fut._await_progress()) != 1.0:
            pbar.update(task, completed=prog, total=1.0)
        pbar.update(task, completed=1.0, total=1.0)

    return await fut.get()


setattr(ModelBuilder, "spawn_inference", spawn_inference)
setattr(ModelBuilder, "spawn_train", spawn_train)
