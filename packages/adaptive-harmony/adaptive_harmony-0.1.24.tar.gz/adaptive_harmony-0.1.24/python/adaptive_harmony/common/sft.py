import os
from typing import Callable, Sequence

from tqdm.auto import tqdm

from adaptive_harmony import CosineScheduler, DataSet, JobNotifier, Logger, StageNotifier, StringThread, TrainingModel
from adaptive_harmony.common.callbacks import RecipeCallback
from adaptive_harmony.common.checkpointing import CheckpointManager
from adaptive_harmony.core.utils import async_map_batch, hash_hyperparams, log_args
from adaptive_harmony.metric_logger import StdoutLogger

SFT_HYPERPARAMS = {
    "lr",
    "lr_scheduler",
    "samples_per_batch",
    "max_grad_norm",
    "epochs",
    "weight_decay",
    "skip_nan_gradients",
}


class SFT:
    @log_args
    @hash_hyperparams(include=SFT_HYPERPARAMS)
    def __init__(
        self,
        dataset: list[StringThread],
        model: TrainingModel,
        logger: Logger = StdoutLogger(),
        stage_notifier: StageNotifier = JobNotifier().stage_notifier("SFT Training"),
        callbacks: Sequence[RecipeCallback] = [],
        lr: float = 1e-5,
        lr_scheduler: Callable[[float], float] | None = None,
        samples_per_batch=512,  # axel magic number: "pretty well validated across different scales"
        max_grad_norm=1.0,
        epochs: int = 1,
        weight_decay: float = 0,
        skip_nan_gradients: bool = False,
        restart_from_checkpoint: str | None = None,
        checkpoint_frequency: float = 0.2,
    ):
        self.dataset = DataSet(dataset, allow_looping=epochs != 1)
        self.lr_schedule = lr_scheduler or CosineScheduler(lr)
        self.model = model
        self.logger = logger
        self.stage_notifier = stage_notifier
        self.callbacks = callbacks
        self.samples_per_batch = samples_per_batch
        self.max_grad_norm = max_grad_norm
        self.epochs = epochs
        self.weight_decay = weight_decay
        self.skip_nan_gradients = skip_nan_gradients

        self.checkpoint_manager = CheckpointManager(
            recipe_name="SFT",
            dataset=self.dataset,
            threads_dataset=dataset,
            callbacks=self.callbacks,
            hyperparams_hash=self._hyperparams_hash,  # type: ignore
            job_id=os.environ.get("HARMONY_JOB_ID"),
            checkpoint_frequency=checkpoint_frequency,
            restart_from_checkpoint=restart_from_checkpoint,
        )

    @property
    def training_completion_percentage(self):
        return self.dataset.completion_percentage() / self.epochs

    async def _recipe_specific_checkpoint_loading(self, checkpoint_data: dict) -> None:
        model_checkpoint_name = checkpoint_data["model_checkpoint_name"]
        await self.model.load(f"model_registry://{model_checkpoint_name}")
        self.model.set_optim_step(checkpoint_data["optim_step"])

    async def _recipe_specific_checkpoint_saving(self) -> dict:
        progress_pct = int(self.training_completion_percentage * 100)
        model_checkpoint_name = f"checkpoint-{self.checkpoint_manager.job_id}-{progress_pct}"
        model_checkpoint_name = await self.model.save(model_checkpoint_name, inference_only=False)

        return {
            "model_checkpoint_name": model_checkpoint_name,
            "optim_step": self.model.get_optim_step(),
        }

    async def run(self):
        await self.checkpoint_manager.maybe_restore_checkpoint(self._recipe_specific_checkpoint_loading)

        self.stage_notifier.report_progress(
            tot_num_samples=len(self.dataset) * self.epochs,
            processed_num_samples=self.dataset.idx,
            monitoring_link=self.logger.training_monitoring_link,
        )

        with tqdm(total=100) as pbar:
            while self.training_completion_percentage < 1.0:
                for callback in self.callbacks:
                    if logs := await callback.maybe_call(self.training_completion_percentage):
                        self.logger(logs)

                await async_map_batch(self.model.train_language_modelling, self.dataset, self.samples_per_batch)
                cp = self.training_completion_percentage
                current_lr = self.lr_schedule(cp)
                pbar.update(cp * 100.0 - pbar.n)

                logs = await self.model.optim_step(
                    current_lr,
                    wd=self.weight_decay,
                    max_grad_norm=self.max_grad_norm,
                    skip_nan_gradients=self.skip_nan_gradients,
                )

                self.logger(logs | dict(completion_percentage=cp))

                self.stage_notifier.report_progress(
                    tot_num_samples=len(self.dataset) * self.epochs,
                    processed_num_samples=self.dataset.idx,
                    monitoring_link=self.logger.training_monitoring_link,
                )

                if await self.checkpoint_manager.maybe_checkpoint(cp, self._recipe_specific_checkpoint_saving):
                    break
