from typing import Type, cast

from dotenv import load_dotenv

from .agent import Agent, Playback
from .recorder import Recorder
from .structs import (
    Grid,
    SessionState,
    SessionPhase,
    Scorecard,
    TaskCard,
    QueryRecord,
    Metadata,
    TestRecord,
    TaskReplayResponse,
)
from .swarm import Swarm
from .templates.llm_agent import LLM
from .templates.random_agent import Random

load_dotenv()

AVAILABLE_AGENTS: dict[str, Type[Agent]] = {
    cls.__name__.lower(): cast(Type[Agent], cls)
    for cls in Agent.__subclasses__()
    if cls.__name__ != "Playback"
}

for rec in Recorder.list():
    AVAILABLE_AGENTS[rec] = Playback

__all__ = [
    # Core classes
    "Agent",
    "Swarm",
    # Data types
    "Grid",
    "SessionState",
    "SessionPhase",
    "Scorecard",
    "TaskCard",
    "QueryRecord",
    "Metadata",
    "TestRecord",
    "TaskReplayResponse",
    # Built-in agents
    "Random",
    "LLM",
    # Utilities
    "Recorder",
    "Playback",
    "AVAILABLE_AGENTS",
]
