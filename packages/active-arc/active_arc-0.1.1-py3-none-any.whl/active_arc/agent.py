import json
import logging
import os
import time
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Optional

import requests
import requests.cookies
from pydantic import ValidationError
from requests.cookies import RequestsCookieJar

from .recorder import Recorder
from .structs import (
    EnterTestResponse,
    Grid,
    QueryResponse,
    Scorecard,
    SessionPhase,
    SessionState,
    StartResponse,
    SubmitResponse,
)
from .tracing import trace_agent_session

logger = logging.getLogger()


class Agent(ABC):
    MAX_QUERIES: int = 100
    ROOT_URL: str

    timer: float = 0
    agent_name: str
    card_id: str
    task_id: str
    session: SessionState

    recorder: Recorder
    headers: dict[str, str]
    _session: requests.Session

    trace: Any = None
    tags: list[str]

    def __init__(
        self,
        card_id: str,
        task_id: str,
        agent_name: str,
        ROOT_URL: str,
        record: bool,
        tags: Optional[list[str]] = None,
        cookies: requests.cookies.RequestsCookieJar = RequestsCookieJar(),
    ) -> None:
        self.ROOT_URL = ROOT_URL
        self.card_id = card_id
        self.task_id = task_id
        self.agent_name = agent_name
        self.tags = tags or []
        self.session = SessionState(task_id=task_id)
        self._cleanup = True

        if record:
            self.start_recording()

        self.headers = {
            "X-Api-Key": os.getenv("ACTIVE_ARC_API_KEY", ""),
            "Accept": "application/json",
        }
        self._session = requests.Session()
        self._session.cookies = deepcopy(cookies)
        self._session.headers.update(self.headers)

    @trace_agent_session
    def main(self) -> None:
        self.timer = time.time()

        start_response = self.cmd_start()
        if not start_response:
            logger.error(f"{self.task_id} - Failed to start session")
            return

        self.session.session_id = start_response.session_id
        self.session.metadata = start_response.metadata
        logger.info(f"{self.task_id} - Started session {self.session.session_id}")

        while self.session.is_learning and self.session.query_count < self.MAX_QUERIES:
            query_input = self.query(self.session)
            if query_input is None:
                break

            reasoning = self.get_query_reasoning(self.session, query_input)
            response = self.cmd_query(query_input, reasoning)

            if response:
                self.session.add_query(query_input, response.output, reasoning)
                self.record_query(query_input, response.output, reasoning)
                logger.info(
                    f"{self.task_id} - QUERY #{self.session.query_count}: "
                    f"output={'null' if response.output is None else 'grid'}, "
                    f"fps={self.fps}"
                )

        if not self.session.is_learning:
            logger.warning(f"{self.task_id} - Session ended during learning phase")
            self.cleanup()
            return

        reasoning = self.get_enter_test_reasoning(self.session)
        test_response = self.cmd_enter_test(reasoning)
        if not test_response:
            logger.error(f"{self.task_id} - Failed to enter test phase")
            self.cleanup()
            return

        self.session.test_input = test_response.test_input
        self.session.phase = SessionPhase.TEST
        logger.info(f"{self.task_id} - Entered test phase")

        answer = self.submit(self.session)
        reasoning = self.get_submit_reasoning(self.session, answer)
        submit_response = self.cmd_submit(answer, reasoning)

        if submit_response:
            self.session.submitted_answer = answer
            self.session.correct = submit_response.correct
            self.session.phase = SessionPhase.COMPLETED
            logger.info(
                f"{self.task_id} - {'CORRECT' if submit_response.correct else 'INCORRECT'} "
                f"(queries={self.session.query_count}, time={self.seconds}s)"
            )

        self.cleanup()

    @property
    def seconds(self) -> float:
        return round(time.time() - self.timer, 2)

    @property
    def fps(self) -> float:
        if self.session.query_count == 0:
            return 0.0
        elapsed = max(self.seconds, 0.1)
        return round(self.session.query_count / elapsed, 2)

    @property
    def is_playback(self) -> bool:
        return type(self) is Playback

    @property
    def name(self) -> str:
        return f"{self.task_id}.{self.__class__.__name__.lower()}"

    def start_recording(self) -> None:
        filename = self.agent_name if self.is_playback else None
        self.recorder = Recorder(prefix=self.name, filename=filename)
        logger.info(f"Recording to {self.recorder.filename}")

    def record_query(self, input_grid: Grid, output: Optional[Grid], reasoning: Any) -> None:
        if hasattr(self, "recorder") and not self.is_playback:
            self.recorder.record({
                "type": "query",
                "input": input_grid,
                "output": output,
                "reasoning": reasoning,
            })

    def cmd_start(self) -> Optional[StartResponse]:
        try:
            r = self._session.post(
                f"{self.ROOT_URL}/api/cmd/START",
                json={"card_id": self.card_id, "task_id": self.task_id},
                headers=self.headers,
            )
            return StartResponse.model_validate(r.json())
        except (ValidationError, Exception) as e:
            logger.warning(f"START failed: {e}")
            return None

    def cmd_query(self, input_grid: Grid, reasoning: Any = None) -> Optional[QueryResponse]:
        try:
            payload: dict[str, Any] = {"session_id": self.session.session_id, "input": input_grid}
            if reasoning is not None:
                payload["reasoning"] = reasoning
            r = self._session.post(
                f"{self.ROOT_URL}/api/cmd/QUERY",
                json=payload,
                headers=self.headers,
            )
            return QueryResponse.model_validate(r.json())
        except (ValidationError, Exception) as e:
            logger.warning(f"QUERY failed: {e}")
            return None

    def cmd_enter_test(self, reasoning: Any = None) -> Optional[EnterTestResponse]:
        try:
            payload: dict[str, Any] = {"session_id": self.session.session_id}
            if reasoning is not None:
                payload["reasoning"] = reasoning
            r = self._session.post(
                f"{self.ROOT_URL}/api/cmd/ENTER_TEST",
                json=payload,
                headers=self.headers,
            )
            return EnterTestResponse.model_validate(r.json())
        except (ValidationError, Exception) as e:
            logger.warning(f"ENTER_TEST failed: {e}")
            return None

    def cmd_submit(self, answer: Grid, reasoning: Any = None) -> Optional[SubmitResponse]:
        try:
            payload: dict[str, Any] = {"session_id": self.session.session_id, "answer": answer}
            if reasoning is not None:
                payload["reasoning"] = reasoning
            r = self._session.post(
                f"{self.ROOT_URL}/api/cmd/SUBMIT",
                json=payload,
                headers=self.headers,
            )
            return SubmitResponse.model_validate(r.json())
        except (ValidationError, Exception) as e:
            logger.warning(f"SUBMIT failed: {e}")
            return None

    def get_scorecard(self) -> Optional[Scorecard]:
        try:
            r = self._session.get(
                f"{self.ROOT_URL}/api/scorecard/{self.card_id}",
                timeout=5,
                headers=self.headers,
            )
            return Scorecard.model_validate(r.json())
        except Exception as e:
            logger.warning(f"Failed to get scorecard: {e}")
            return None

    def cleanup(self, scorecard: Optional[Scorecard] = None) -> None:
        if self._cleanup:
            self._cleanup = False
            if hasattr(self, "recorder") and not self.is_playback:
                payload: dict[str, Any] = {
                    "type": "result",
                    "task_id": self.task_id,
                    "correct": self.session.correct,
                    "query_count": self.session.query_count,
                }
                if self.session.submitted_answer is not None:
                    payload["answer"] = self.session.submitted_answer
                self.recorder.record(payload)
                logger.info(f"Recording saved to {self.recorder.filename}")

            logger.info(
                f"{self.task_id} - Finished: queries={self.session.query_count}, "
                f"time={self.seconds}s, fps={self.fps}"
            )

            if hasattr(self, "_session"):
                self._session.close()

    def get_query_reasoning(self, session: SessionState, query_input: Grid) -> Any:
        return None

    def get_submit_reasoning(self, session: SessionState, answer: Grid) -> Any:
        return None

    def get_enter_test_reasoning(self, session: SessionState) -> Any:
        return None

    @abstractmethod
    def query(self, session: SessionState) -> Optional[Grid]:
        """Choose an input grid to query the oracle. Return None to stop querying."""
        raise NotImplementedError

    @abstractmethod
    def submit(self, session: SessionState) -> Grid:
        """Predict the output grid for session.test_input."""
        raise NotImplementedError


class Playback(Agent):
    MAX_QUERIES = 1000000
    PLAYBACK_FPS = 5

    recorded_queries: list[dict[str, Any]]
    recorded_answer: Optional[Grid]
    query_index: int

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.recorder = Recorder(
            prefix=Recorder.get_prefix(self.agent_name),
            guid=Recorder.get_guid(self.agent_name),
        )
        self.recorded_queries = []
        self.recorded_answer = None
        self.query_index = 0

        if self.agent_name in Recorder.list():
            try:
                self._load_recording()
                logger.info(f"Loaded {len(self.recorded_queries)} queries from {self.agent_name}")
            except Exception as e:
                logger.error(f"Failed to load recording {self.agent_name}: {e}")

    def _load_recording(self) -> None:
        for entry in self.recorder.get():
            if "data" not in entry:
                continue
            data = entry["data"]
            if data.get("type") == "query":
                self.recorded_queries.append(data)
            elif data.get("type") == "result" and "answer" in data:
                self.recorded_answer = data["answer"]

    def query(self, session: SessionState) -> Optional[Grid]:
        if self.query_index >= len(self.recorded_queries):
            return None

        time.sleep(1.0 / self.PLAYBACK_FPS)

        recorded = self.recorded_queries[self.query_index]
        self.query_index += 1
        return recorded["input"]

    def submit(self, session: SessionState) -> Grid:
        if self.recorded_answer:
            return self.recorded_answer
        return [[0]]

    def get_query_reasoning(self, session: SessionState, query_input: Grid) -> Any:
        if self.query_index > 0 and self.query_index <= len(self.recorded_queries):
            return self.recorded_queries[self.query_index - 1].get("reasoning")
        return None
