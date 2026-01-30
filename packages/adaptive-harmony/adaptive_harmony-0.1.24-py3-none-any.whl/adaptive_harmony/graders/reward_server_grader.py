import asyncio

from adaptive_harmony import StringThread
from adaptive_harmony.core.reward_client.client import Request, RewardClient, Turn
from adaptive_harmony.graders.base_grader import BaseGrader, Grade


class RewardServerGrader(BaseGrader):
    def __init__(self, grader_key: str, grader_id: str, reward_server_ip: str):
        super().__init__(grader_key)
        self.reward_client = RewardClient(reward_server_ip)
        self.grader_id_or_key = grader_id or grader_key
        self._setup_task = None
        self._setup_lock = None

    async def _ensure_setup(self):
        if self._setup_lock is None:
            self._setup_lock = asyncio.Lock()

        if self._setup_task is None:
            async with self._setup_lock:
                if self._setup_task is None:
                    self._setup_task = asyncio.create_task(self.reward_client.setup())

        await self._setup_task

    async def grade(self, sample: StringThread) -> Grade:
        await self._ensure_setup()

        response = await self.reward_client.score(
            Request(
                turns=[Turn(content=turn.content, role=turn.role) for turn in sample.get_turns()],
                metadata=sample.metadata,
            )
        )
        return Grade(value=response.reward, grader_key=self.grader_id_or_key, reasoning=response.metadata.get("reason"))
