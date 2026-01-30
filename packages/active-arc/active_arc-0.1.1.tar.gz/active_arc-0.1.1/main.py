# ruff: noqa: E402
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.example")
load_dotenv(dotenv_path=".env", override=True)

import argparse
import json
import logging
import os
import signal
import sys
import threading
from functools import partial
from types import FrameType
from typing import Optional

import requests

from active_arc import AVAILABLE_AGENTS, Swarm
from active_arc.tracing import initialize as init_agentops

logger = logging.getLogger()

SCHEME = os.environ.get("SCHEME", "http")
HOST = os.environ.get("HOST", "localhost")
PORT = os.environ.get("PORT", 8001)

if (SCHEME == "http" and str(PORT) == "80") or (
    SCHEME == "https" and str(PORT) == "443"
):
    ROOT_URL = f"{SCHEME}://{HOST}"
else:
    ROOT_URL = f"{SCHEME}://{HOST}:{PORT}"
HEADERS = {
    "X-Api-Key": os.getenv("ACTIVE_ARC_API_KEY", ""),
    "Accept": "application/json",
}


def run_agent(swarm: Swarm) -> None:
    swarm.main()
    os.kill(os.getpid(), signal.SIGINT)


def cleanup(
    swarm: Swarm,
    signum: Optional[int],
    frame: Optional[FrameType],
) -> None:
    logger.info("Received SIGINT, exiting...")
    card_id = swarm.card_id
    if card_id:
        scorecard = swarm.close_scorecard(card_id)
        if scorecard:
            logger.info("--- EXISTING SCORECARD REPORT ---")
            logger.info(json.dumps(scorecard.model_dump(), indent=2))
            swarm.cleanup(scorecard)

        # Provide web link to scorecard
        if card_id:
            scorecard_url = f"{ROOT_URL}/scorecard/{card_id}"
            logger.info(f"View your scorecard online: {scorecard_url}")

    sys.exit(0)


def main() -> None:
    log_level = logging.INFO
    if os.environ.get("DEBUG", "False") == "True":
        log_level = logging.DEBUG

    logger.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("logs.log", mode="w")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    # logging.getLogger("requests").setLevel(logging.CRITICAL)
    # logging.getLogger("werkzeug").setLevel(logging.CRITICAL)

    parser = argparse.ArgumentParser(description="Active-ARC Agents")
    parser.add_argument(
        "-a",
        "--agent",
        choices=AVAILABLE_AGENTS.keys(),
        help="Choose which agent to run.",
    )
    parser.add_argument(
        "-t",
        "--task",
        help="Choose a specific task_id for the agent to solve. If none specified, an agent swarm will solve all available tasks.",
    )
    parser.add_argument(
        "--tags",
        type=str,
        help="Comma-separated list of tags for the scorecard (e.g., 'experiment,v1.0')",
        default=None,
    )

    args = parser.parse_args()

    if not args.agent:
        logger.error("An Agent must be specified")
        return

    print(f"{ROOT_URL}/api/tasks")

    full_tasks = []
    try:
        with requests.Session() as session:
            session.headers.update(HEADERS)
            r = session.get(f"{ROOT_URL}/api/tasks", timeout=10)

        if r.status_code == 200:
            try:
                data = r.json()
                full_tasks = data.get("tasks", []) if isinstance(data, dict) else data
            except (ValueError, KeyError) as e:
                logger.error(f"Failed to parse tasks response: {e}")
                logger.error(f"Response content: {r.text[:200]}")
        else:
            logger.error(
                f"API request failed with status {r.status_code}: {r.text[:200]}"
            )

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to API server: {e}")

    if not full_tasks and args.agent and args.agent.endswith(".recording.jsonl"):
        from active_arc.recorder import Recorder

        task_prefix = Recorder.get_prefix_one(args.agent)
        full_tasks = [task_prefix]
        logger.info(
            f"Using task '{task_prefix}' derived from playback recording filename"
        )
    tasks = full_tasks[:]
    if args.task:
        filters = args.task.split(",")
        tasks = [
            tid
            for tid in full_tasks
            if any(tid.startswith(prefix) for prefix in filters)
        ]

    logger.info(f"Task list: {tasks}")

    if not tasks:
        if full_tasks:
            logger.error(
                f"The specified task '{args.task}' does not exist or is not available with your API key. Please try a different task."
            )
        else:
            logger.error(
                "No tasks available. Check API connection or recording file."
            )
        return

    tags = []

    if args.tags:
        user_tags = [tag.strip() for tag in args.tags.split(",")]
        tags.extend(user_tags)

    init_agentops(api_key=os.getenv("AGENTOPS_API_KEY"), log_level=log_level)

    swarm = Swarm(
        tasks=tasks,
        root_url=ROOT_URL,
        agent=args.agent,
        tags=tags,
    )
    agent_thread = threading.Thread(target=partial(run_agent, swarm))
    agent_thread.daemon = True  # die when the main thread dies
    agent_thread.start()

    signal.signal(signal.SIGINT, partial(cleanup, swarm))  # handler for Ctrl+C

    try:
        # Wait for the agent thread to complete
        while agent_thread.is_alive():
            agent_thread.join(timeout=5)  # Check every 5 second
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received in main thread")
        cleanup(swarm, signal.SIGINT, None)
    except Exception as e:
        logger.error(f"Unexpected error in main thread: {e}")
        cleanup(swarm, None, None)


if __name__ == "__main__":
    os.environ["TESTING"] = "False"
    main()
