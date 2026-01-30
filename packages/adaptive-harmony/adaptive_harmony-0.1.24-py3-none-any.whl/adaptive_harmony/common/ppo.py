import os
from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from adaptive_harmony import (
    CombinedSchedule,
    CosineScheduler,
    DataSet,
    InferenceModel,
    JobNotifier,
    Logger,
    StageNotifier,
    StringThread,
    TokenizedThread,
    TrainingModel,
)
from adaptive_harmony.common.callbacks import RecipeCallback
from adaptive_harmony.common.checkpointing import CheckpointManager
from adaptive_harmony.core import rl_utils
from adaptive_harmony.core.utils import async_map, async_map_batch, get_minibatches, hash_hyperparams, log_args
from adaptive_harmony.graders import BaseGrader
from adaptive_harmony.metric_logger import StdoutLogger


@dataclass
class Sample:
    sample: TokenizedThread
    string_sample: StringThread
    logprobs: list[float]
    ref_logprobs: list[float]
    advantages: list[float]
    returns: list[float]
    score: float
    kl_div: list[float]
    values: list[float]
    kl_pen: float
    cumulative_reward: float


PPO_HYPERPARAMS = {
    "max_num_ppo_steps",
    "value_only_fraction",
    "lr_policy",
    "lr_scheduler_policy",
    "lr_scheduler_value",
    "lr_value",
    "samples_per_batch",
    "samples_per_mini_batch",
    "mini_epochs_per_batch",
    "max_grad_norm",
    "clip_range",
    "kl_beta",
    "gae_lambda",
    "gae_gamma",
    "weight_decay",
    "skip_nan_gradients",
}


class PPO:
    @log_args
    @hash_hyperparams(include=PPO_HYPERPARAMS)
    def __init__(
        self,
        dataset: list[StringThread],
        model: TrainingModel,
        value_model: TrainingModel,
        grader: BaseGrader,
        logger: Logger = StdoutLogger(),
        stage_notifier: StageNotifier = JobNotifier().stage_notifier("PPO Training"),
        callbacks: Sequence[RecipeCallback] = [],
        max_num_ppo_steps: int | None = None,
        value_only_fraction=0.25,
        lr_policy: float = 0.75e-6,
        lr_scheduler_policy: Callable[[float], float] | None = None,
        lr_scheduler_value: Callable[[float], float] | None = None,
        lr_value: float = 1e-6,
        samples_per_batch=128,
        samples_per_mini_batch=128,
        mini_epochs_per_batch=1,
        max_grad_norm=1.0,
        clip_range=0.1,
        kl_beta=0.1,
        gae_lambda=0.95,
        gae_gamma=1.0,
        weight_decay: float = 0,
        skip_nan_gradients: bool = False,
        restart_from_checkpoint: str | None = None,
        checkpoint_frequency: float = 0.2,
    ):
        assert value_model.is_scalar(), "You must give a scalar model to PPO for the value network"
        # Core components
        self.model_ref: InferenceModel | None = None  # Instantiated when run() is called
        self.dataset = DataSet(dataset, allow_looping=True)
        self.model = model
        self.value_model = value_model
        self.grader = grader
        self.scoring_fn = grader.score_float_value
        self.logger = logger
        self.stage_notifier = stage_notifier
        self.callbacks = callbacks
        self.skip_nan_gradients = skip_nan_gradients
        # PPO HP's
        self.max_num_batches = max_num_ppo_steps
        self.lr_schedule_policy = lr_scheduler_policy or CombinedSchedule(
            lambda _: 0, CosineScheduler(lr_policy), value_only_fraction
        )
        self.lr_schedule_value = lr_scheduler_value or CosineScheduler(lr_value)
        self.samples_per_batch = samples_per_batch
        self.samples_per_mini_batch = samples_per_mini_batch
        self.total_num_samples = (
            self.max_num_batches * self.samples_per_batch if self.max_num_batches else len(self.dataset)
        )
        self.mini_epochs_per_batch = mini_epochs_per_batch
        self.max_grad_norm = max_grad_norm
        self.clip_range = clip_range
        self.kl_beta = kl_beta
        self.gae_lambda = gae_lambda
        self.gae_gamma = gae_gamma
        self.weight_decay = weight_decay

        self.num_batches_processed = 0

        self.checkpoint_manager = CheckpointManager(
            recipe_name="PPO",
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
        return (
            self.dataset.completion_percentage()
            if self.max_num_batches is None
            else min(self.num_batches_processed / self.max_num_batches, 1.0)
        )

    async def generate_sample(self, prompt: StringThread):
        assert self.model_ref is not None, "Calling `generate_sample` before reference model has been set"

        sample = await self.model.generate_tokens(prompt)
        string_sample = await self.model.detokenize_thread(sample)
        score = await self.scoring_fn(string_sample)
        values = await self.value_model.score(sample)

        logprobs = await self.model.logprobs_per_token(sample)
        ref_logprobs = await self.model_ref.logprobs_per_token(sample)

        kl = np.array(logprobs, dtype=np.float32) - np.array(ref_logprobs, dtype=np.float32)
        kl_pen = -kl * self.kl_beta
        rewards = np.array(kl_pen)
        rewards[-1] += score

        advantages = rl_utils.gae_advantages(values, rewards.tolist(), self.gae_lambda, self.gae_gamma)
        returns = rl_utils.discounted_cumulative_rewards(rewards.tolist(), self.gae_gamma)

        return Sample(
            sample=sample,
            string_sample=string_sample,
            logprobs=logprobs,
            ref_logprobs=ref_logprobs,
            advantages=advantages,
            returns=returns,
            score=score,
            values=values,
            cumulative_reward=sum(rewards),
            kl_div=kl.tolist(),
            kl_pen=np.sum(kl_pen).item(),
        )

    async def train_ppo(self, sample: Sample):
        await self.model.train_ppo(sample.sample, sample.logprobs, sample.advantages, self.clip_range)

    async def train_value(self, sample: Sample):
        await self.value_model.train_mse_per_token(sample.sample, sample.returns)

    async def _recipe_specific_checkpoint_loading(self, checkpoint_data: dict) -> None:
        self.num_batches_processed = checkpoint_data["num_batches_processed"]

        model_checkpoint_name = checkpoint_data["model_checkpoint_name"]
        await self.model.load(f"model_registry://{model_checkpoint_name}")
        value_model_checkpoint_name = checkpoint_data["value_model_checkpoint_name"]
        await self.value_model.load(f"model_registry://{value_model_checkpoint_name}")

        self.model.set_optim_step(checkpoint_data["optim_step"])
        self.value_model.set_optim_step(checkpoint_data["value_optim_step"])

    async def _recipe_specific_checkpoint_saving(self) -> dict:
        progress_pct = int(self.training_completion_percentage * 100)
        model_checkpoint_name = f"checkpoint-{self.checkpoint_manager.job_id}-{progress_pct}-policy"
        model_checkpoint_name = await self.model.save(model_checkpoint_name, inference_only=False)

        value_model_checkpoint_name = f"checkpoint-{self.checkpoint_manager.job_id}-{progress_pct}-value"
        value_model_checkpoint_name = await self.value_model.save(value_model_checkpoint_name, inference_only=False)

        return {
            "num_batches_processed": self.num_batches_processed,
            "model_checkpoint_name": model_checkpoint_name,
            "value_model_checkpoint_name": value_model_checkpoint_name,
            "optim_step": self.model.get_optim_step(),
            "value_optim_step": self.value_model.get_optim_step(),
        }

    async def run(self):
        self.model_ref = await self.model.clone_inf()
        await self.checkpoint_manager.maybe_restore_checkpoint(self._recipe_specific_checkpoint_loading)

        self.stage_notifier.report_progress(
            tot_num_samples=self.total_num_samples,
            processed_num_samples=self.dataset.idx,
            monitoring_link=self.logger.training_monitoring_link,
        )

        while self.training_completion_percentage < 1.0:
            self.num_batches_processed += 1

            for callback in self.callbacks:
                if logs := await callback.maybe_call(self.training_completion_percentage):
                    self.logger(logs)

            # Generate training samples
            data = await async_map_batch(
                self.generate_sample,
                self.dataset,
                self.samples_per_batch,
            )
            scorer_logs = self.grader.get_logs(clear=True)
            batch_logs = {
                **{f"rewards/{key}": value for key, value in scorer_logs.items()},
                **self.get_train_batch_logs(data),
            }

            lr_policy = self.lr_schedule_policy(self.training_completion_percentage)
            lr_value = self.lr_schedule_value(self.training_completion_percentage)

            # Train on generated samples
            if lr_policy > 0:
                minibatches = get_minibatches(data, self.samples_per_mini_batch, self.mini_epochs_per_batch)
                for idx, mini_batch in enumerate(minibatches):
                    await async_map(self.train_ppo, mini_batch)
                    optim_logs = await self.model.optim_step(
                        lr_policy,
                        wd=self.weight_decay,
                        max_grad_norm=self.max_grad_norm,
                        skip_nan_gradients=self.skip_nan_gradients,
                    )
                    if idx == len(minibatches) - 1:
                        # only log tables and full batch-related logs on the final minibatch
                        self.logger(optim_logs | batch_logs)
                    else:
                        self.logger(optim_logs | dict(completion_percentage=self.training_completion_percentage))

            for mini_batch in get_minibatches(data, self.samples_per_mini_batch, self.mini_epochs_per_batch):
                await async_map(self.train_value, mini_batch)
                batch_logs |= await self.value_model.optim_step(
                    lr_value, wd=0, max_grad_norm=self.max_grad_norm, skip_nan_gradients=self.skip_nan_gradients
                )
                self.logger(batch_logs)

            self.stage_notifier.report_progress(
                tot_num_samples=self.total_num_samples,
                processed_num_samples=self.dataset.idx,
                monitoring_link=self.logger.training_monitoring_link,
            )

            if await self.checkpoint_manager.maybe_checkpoint(
                self.training_completion_percentage, self._recipe_specific_checkpoint_saving
            ):
                break

    def get_train_batch_logs(self, data: list[Sample]) -> dict:
        returns = np.concatenate([batch.returns for batch in data])
        cur_values = np.concatenate([batch.values for batch in data])

        var_return = returns.var()
        mean_error = ((cur_values - returns) ** 2).mean()
        explained_variance = (1 - mean_error / (var_return + 1e-8)).item()

        logs = dict(
            completion_percentage=self.training_completion_percentage,
            score_mean=np.mean([batch.score for batch in data]).item(),
            score_std=np.std([batch.score for batch in data]).item(),
            returns=np.mean(np.concatenate([batch.returns for batch in data])),
            kl_div=np.mean(np.concatenate([batch.kl_div for batch in data])),
            advantages=np.mean(np.concatenate([batch.advantages for batch in data])),
            generation_length=np.mean([batch.sample.len_last_turn() for batch in data]),
            logprobs=np.mean(np.concatenate([batch.logprobs for batch in data])),
            ref_logprobs=np.mean(np.concatenate([batch.ref_logprobs for batch in data])),
            kl_penalty=np.mean([batch.kl_pen for batch in data]),
            explained_variance=explained_variance,
            cumulative_reward=np.mean([batch.cumulative_reward for batch in data]),
        ) | {
            "training/completion_percentage": self.training_completion_percentage
        }  # to have an comparable axis with prior runs

        return logs
