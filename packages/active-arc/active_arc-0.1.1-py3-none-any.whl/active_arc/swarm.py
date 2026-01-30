from __future__ import annotations

import json
import logging
import os
from threading import Thread
from typing import TYPE_CHECKING, Optional, Type, Union

import requests

from .structs import Scorecard

if TYPE_CHECKING:
    from .agent import Agent

logger = logging.getLogger()


class Swarm:
    TASKS: list[str]
    ROOT_URL: str
    agent_name: str
    agent_class: Type[Agent]
    threads: list[Thread]
    agents: list[Agent]
    headers: dict[str, str]
    card_id: Optional[str]
    _session: requests.Session

    def __init__(
        self,
        tasks: list[str],
        root_url: Optional[str] = None,
        agent: Optional[str] = None,
        agent_class: Optional[Type[Agent]] = None,
        tags: Optional[list[str]] = None,
        # Backwards compatibility
        ROOT_URL: Optional[str] = None,
    ) -> None:
        if agent_class is None and agent is None:
            raise ValueError("Either 'agent' (name) or 'agent_class' must be provided")

        if agent_class is not None:
            self.agent_class = agent_class
            self.agent_name = agent_class.__name__.lower()
        else:
            from . import AVAILABLE_AGENTS
            if agent not in AVAILABLE_AGENTS:
                raise ValueError(f"Unknown agent: {agent}. Available: {list(AVAILABLE_AGENTS.keys())}")
            self.agent_class = AVAILABLE_AGENTS[agent]
            self.agent_name = agent

        url = root_url or ROOT_URL
        if url is None:
            scheme = os.environ.get("SCHEME", "https")
            host = os.environ.get("HOST", "api.active-arc.com")
            port = os.environ.get("PORT", "443")
            if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
                url = f"{scheme}://{host}"
            else:
                url = f"{scheme}://{host}:{port}"

        self.TASKS = tasks
        self.ROOT_URL = url
        self.threads = []
        self.agents = []
        self.headers = {
            "X-Api-Key": os.getenv("ACTIVE_ARC_API_KEY", ""),
            "Accept": "application/json",
        }
        self._session = requests.Session()
        self._session.headers.update(self.headers)
        self.tags = list(tags) if tags else []

        if self.agent_name.endswith(".recording.jsonl"):
            parts = self.agent_name.split(".")
            guid = parts[-3] if len(parts) >= 4 else "unknown"
            self.tags.extend(["playback", guid])
        else:
            self.tags.extend(["agent", self.agent_name])

    def run(self) -> Scorecard | None:
        """Run the agent swarm on all tasks. Returns the final scorecard."""
        return self.main()

    def main(self) -> Scorecard | None:
        self.card_id = self.open_scorecard()

        for task_id in self.TASKS:
            a = self.agent_class(
                card_id=self.card_id,
                task_id=task_id,
                agent_name=self.agent_name,
                ROOT_URL=self.ROOT_URL,
                record=True,
                cookies=self._session.cookies,
                tags=self.tags,
            )
            self.agents.append(a)

        for a in self.agents:
            self.threads.append(Thread(target=a.main, daemon=True))

        for t in self.threads:
            t.start()

        for t in self.threads:
            t.join()

        card_id = self.card_id
        scorecard = self.close_scorecard(card_id)
        if scorecard:
            logger.info("--- FINAL SCORECARD REPORT ---")
            logger.info(json.dumps(scorecard.model_dump(), indent=2))

        if card_id:
            scorecard_url = f"{self.ROOT_URL}/scorecard/{card_id}"
            logger.info(f"View your scorecard online: {scorecard_url}")

        self.cleanup(scorecard)

        return scorecard

    def open_scorecard(self) -> str:
        payload = {
            "agent_name": self.agent_name,
            "tags": self.tags,
        }

        r = self._session.post(
            f"{self.ROOT_URL}/api/scorecard/open",
            json=payload,
            headers=self.headers,
        )

        try:
            response_data = r.json()
        except ValueError:
            raise Exception(f"Failed to open scorecard: {r.status_code} - {r.text}")

        if not r.ok:
            raise Exception(
                f"API error during open scorecard: {r.status_code} - {response_data}"
            )

        return str(response_data["card_id"])

    def close_scorecard(self, card_id: str) -> Optional[Scorecard]:
        self.card_id = None
        r = self._session.post(
            f"{self.ROOT_URL}/api/scorecard/close",
            json={"card_id": card_id},
            headers=self.headers,
        )

        try:
            response_data = r.json()
        except ValueError:
            logger.warning(f"Failed to close scorecard: {r.status_code} - {r.text}")
            return None

        if not r.ok:
            logger.warning(
                f"API error during close scorecard: {r.status_code} - {response_data}"
            )
            return None

        return Scorecard.model_validate(response_data)

    def cleanup(self, scorecard: Optional[Scorecard] = None) -> None:
        for a in self.agents:
            a.cleanup(scorecard)
        if hasattr(self, "_session"):
            self._session.close()
