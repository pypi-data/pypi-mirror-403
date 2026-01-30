import random
import time
from typing import Any, Optional

from ..agent import Agent
from ..structs import Grid, SessionState


class Random(Agent):
    MAX_QUERIES = 10

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        seed = int(time.time() * 1000000) + hash(self.task_id) % 1000000
        random.seed(seed)

    @property
    def name(self) -> str:
        return f"{super().name}.{self.MAX_QUERIES}"

    def query(self, session: SessionState) -> Optional[Grid]:
        if session.query_count >= self.MAX_QUERIES:
            return None
        rows = random.randint(1, 10)
        cols = random.randint(1, 10)
        return [[random.randint(0, 9) for _ in range(cols)] for _ in range(rows)]

    def submit(self, session: SessionState) -> Grid:
        if session.test_input:
            return [row[:] for row in session.test_input]
        return [[0]]
