import json
import os
from pathlib import Path
from typing import Awaitable, Callable, Sequence

import anyio
import numpy as np
from loguru import logger as loguru

from adaptive_harmony import DataSet, StringThread
from adaptive_harmony.common.callbacks import RecipeCallback
from adaptive_harmony.core.utils import hash_dataset


class CheckpointManager:
    def __init__(
        self,
        recipe_name: str,
        dataset: DataSet,
        threads_dataset: Sequence[StringThread],
        callbacks: Sequence[RecipeCallback],
        hyperparams_hash: str,
        job_id: str | None = None,
        checkpoint_frequency: float = 0.2,
        restart_from_checkpoint: str | None = None,
    ):
        self.recipe_name = recipe_name
        self.dataset = dataset
        self.dataset_hash = hash_dataset(threads_dataset)
        self.hyperparams_hash = hyperparams_hash
        self.callbacks = callbacks
        self.checkpoint_frequency = checkpoint_frequency
        self.last_checkpoint_percentage = 0.0
        self.restart_from_checkpoint = restart_from_checkpoint
        self.job_id = job_id
        self.checkpointing_folder = self._init_folder()

    def _init_folder(self) -> str | None:
        if self.job_id is None or os.getenv("HARMONY_NO_CHECKPOINTING") is not None:
            loguru.warning("Checkpointing is disabled for this recipe.")
            return None
        return os.path.join(os.getenv("RECIPE_CHECKPOINTS_DIR", "/checkpoints"), self.job_id)

    async def maybe_restore_checkpoint(
        self,
        recipe_specific_checkpoint_loading: Callable[[dict], Awaitable[None]],
    ) -> None:
        if self.restart_from_checkpoint is None:
            return

        checkpoint_path = Path(self.restart_from_checkpoint)
        checkpoint_file = self._resolve_checkpoint_file(checkpoint_path)

        assert checkpoint_file, f"Checkpoint file not found: {checkpoint_path}."

        loguru.info(f"Loading {self.recipe_name} checkpoint from: {checkpoint_file}")

        contents = ""
        async with await anyio.open_file(checkpoint_file, "r") as f:
            contents = await f.read()
        checkpoint_data = json.loads(contents)

        assert checkpoint_data.get("recipe_type") == self.recipe_name, (
            f"Recipe type mismatch: checkpoint is '{checkpoint_data.get('recipe_type')}', "
            f"but trying to load into {self.recipe_name}"
        )

        assert checkpoint_data.get("dataset_hash") == self.dataset_hash, (
            "Dataset hash mismatch between checkpoint and current dataset."
        )

        assert checkpoint_data.get("hyperparams_hash") == self.hyperparams_hash, (
            "Hyperparameters hash mismatch between checkpoint and current recipe configuration."
        )

        self.dataset.idx = checkpoint_data.get("dataset_idx", 0)

        access_indices_list = checkpoint_data.get("dataset_access_indices", [])
        if access_indices_list:
            self.dataset.access_indices = np.array(access_indices_list)

        rng_state = checkpoint_data.get("dataset_rng_state")
        if rng_state:
            self.dataset.rng.bit_generator.state = rng_state

        callback_states = checkpoint_data.get("callback_last_calls", [])
        assert len(callback_states) == len(self.callbacks), "Mismatch in number of callbacks when loading checkpoint"
        for i, callback in enumerate(self.callbacks):
            callback.last_call = callback_states[i]

        await recipe_specific_checkpoint_loading(checkpoint_data)

        self.last_checkpoint_percentage = checkpoint_data.get("completion_percentage", 0.0)

        loguru.info(f"Checkpoint restored: starting {self.recipe_name} from {self.last_checkpoint_percentage:.2%}.")

    async def maybe_checkpoint(
        self,
        completion_percentage: float,
        recipe_specific_checkpoint_saving: Callable[[], Awaitable[dict]],
    ) -> bool:
        if self.checkpointing_folder is None:
            return False

        if completion_percentage >= 1.0:
            return False

        if await self._check_graceful_exit_file():
            loguru.info(f"Graceful exit requested. Saving checkpoint and exiting {self.recipe_name} training loop.")
            await self._save_checkpoint(completion_percentage, recipe_specific_checkpoint_saving)
            return True

        if completion_percentage - self.last_checkpoint_percentage >= self.checkpoint_frequency:
            await self._save_checkpoint(completion_percentage, recipe_specific_checkpoint_saving)
            self.last_checkpoint_percentage = completion_percentage

        return False

    async def _save_checkpoint(
        self,
        completion_percentage: float,
        get_save_config: Callable[[], Awaitable[dict]],
    ) -> None:
        assert self.checkpointing_folder is not None  # will never be called outside of this condition
        progress_pct = int(completion_percentage * 100)
        checkpoint_dir = Path(self.checkpointing_folder)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        loguru.info(f"Checkpointing {self.recipe_name} at {checkpoint_dir} ({progress_pct}%)...")

        recipe_data = await get_save_config()

        checkpoint_data = {
            "recipe_type": self.recipe_name,
            "dataset_hash": self.dataset_hash,
            "hyperparams_hash": self.hyperparams_hash,
            "dataset_idx": self.dataset.idx,
            "dataset_access_indices": self.dataset.access_indices.tolist(),
            "dataset_rng_state": self.dataset.rng.bit_generator.state,
            "callback_last_calls": [callback.last_call for callback in self.callbacks],
            "completion_percentage": completion_percentage,
            **recipe_data,
        }

        checkpoint_file = checkpoint_dir / f"checkpoint-{progress_pct}.json"

        data_dump = json.dumps(checkpoint_data, indent=2)
        async with await anyio.open_file(checkpoint_file, "w") as f:
            await f.write(data_dump)

        loguru.info(f"Checkpoint saved: {checkpoint_file}")

    async def _check_graceful_exit_file(self) -> bool:
        if self.checkpointing_folder is None:
            return False
        return (Path(self.checkpointing_folder) / "GRACEFUL_EXIT").exists()

    @staticmethod
    def _resolve_checkpoint_file(path: Path) -> Path | None:
        if path.is_dir():
            files = sorted(path.glob("checkpoint-*.json"), key=lambda p: int(p.stem.split("-")[1]))
            return files[-1] if files else None
        return path if path.exists() else None
