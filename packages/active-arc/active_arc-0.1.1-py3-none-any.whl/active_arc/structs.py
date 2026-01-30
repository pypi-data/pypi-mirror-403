import json
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, computed_field, field_validator

MAX_REASONING_BYTES = 16 * 1024  # 16KB Max

Grid = list[list[int]]


class Metadata(BaseModel):
    grid_size_limit: int = 30
    color_range: list[int] = Field(default_factory=lambda: [0, 9])


class SessionPhase(str, Enum):
    """Phase of an Active-ARC session."""

    LEARNING = "learning"
    TEST = "test"
    COMPLETED = "completed"


class TaskCard(BaseModel):
    """
    Tracks a single task attempt within a scorecard.
    Unlike ARC-AGI-3, each task is attempted only once per scorecard.
    """

    model_config = {"populate_by_name": True}

    task_id: str = ""
    session_id: Optional[str] = None
    phase: SessionPhase = SessionPhase.LEARNING
    query_count: int = Field(default=0, alias="queries")
    correct: Optional[bool] = Field(default=None, alias="solved")

    @property
    def attempted(self) -> bool:
        return self.session_id is not None or self.query_count > 0

    @property
    def is_solved(self) -> bool:
        return self.correct is True

    @property
    def score(self) -> int:
        return 1 if self.correct else 0


class Scorecard(BaseModel):
    """
    Tracks and holds the scorecard for all tasks in an evaluation run.
    """

    card_id: str = ""
    agent_name: str = ""
    tasks: list[str] = Field(default_factory=list, exclude=True)
    cards: dict[str, TaskCard] = Field(default_factory=dict)
    source_url: Optional[str] = None
    tags: Optional[list[str]] = None
    opaque: Optional[Any] = Field(default=None)
    closed: bool = False

    def model_post_init(self, __context: Any) -> None:
        if not self.cards:
            self.cards = {}

    @computed_field(return_type=int)
    def solved(self) -> int:
        return sum(1 for c in self.cards.values() if c.is_solved)

    @computed_field(return_type=int)
    def attempted(self) -> int:
        return sum(1 for c in self.cards.values() if c.attempted)

    @computed_field(return_type=int)
    def total_queries(self) -> int:
        return sum(c.query_count for c in self.cards.values())

    def get(self, task_id: Optional[str] = None) -> dict[str, Any]:
        if task_id is not None:
            card = self.cards.get(task_id)
            return {task_id: card.model_dump()} if card else {}
        return {k: v.model_dump() for k, v in self.cards.items()}

    def get_json_for(self, task_id: str) -> dict[str, Any]:
        card = self.cards.get(task_id)
        return {
            "solved": self.solved,
            "attempted": self.attempted,
            "total_queries": self.total_queries,
            "cards": {task_id: card.model_dump()} if card else {},
        }


class QueryRecord(BaseModel):
    """A single oracle query record."""

    input: Grid
    output: Optional[Grid] = None
    reasoning: Optional[Any] = None
    timestamp: Optional[str] = None


class TestRecord(BaseModel):
    input: Grid
    submitted_answer: Grid
    expected_output: Grid
    reasoning: Optional[Any] = None
    timestamp: Optional[str] = None


class SessionReplay(BaseModel):
    """Full replay data for a session."""

    queries: list[QueryRecord] = Field(default_factory=list)
    test: Optional[TestRecord] = None


class StartRequest(BaseModel):
    """Request body for START command."""

    card_id: str
    task_id: str


class StartResponse(BaseModel):
    """Response from START command."""

    session_id: str
    task_id: str
    phase: SessionPhase = SessionPhase.LEARNING
    query_count: int = 0
    metadata: Optional[Metadata] = None


class QueryRequest(BaseModel):
    """Request body for QUERY command."""

    session_id: str
    input: Grid
    reasoning: Optional[Any] = Field(
        default=None,
        description="Opaque client-supplied blob; stored & echoed back verbatim.",
    )

    @field_validator("reasoning")
    @classmethod
    def _check_reasoning(cls, v: Any) -> Any:
        if v is None:
            return v
        try:
            raw = json.dumps(v, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError):
            raise ValueError("reasoning must be JSON-serialisable")
        if len(raw) > MAX_REASONING_BYTES:
            raise ValueError(f"reasoning exceeds {MAX_REASONING_BYTES} bytes")
        return v


class QueryResponse(BaseModel):
    """Response from QUERY command."""

    output: Optional[Grid] = None
    query_count: int
    phase: SessionPhase = SessionPhase.LEARNING


class EnterTestRequest(BaseModel):
    """Request body for ENTER_TEST command."""

    session_id: str
    reasoning: Optional[Any] = None


class EnterTestResponse(BaseModel):
    """Response from ENTER_TEST command."""

    test_input: Grid
    query_count: int
    phase: SessionPhase = SessionPhase.TEST


class SubmitRequest(BaseModel):
    """Request body for SUBMIT command."""

    session_id: str
    answer: Grid
    reasoning: Optional[Any] = Field(
        default=None,
        description="Opaque client-supplied blob; stored & echoed back verbatim.",
    )

    @field_validator("reasoning")
    @classmethod
    def _check_reasoning(cls, v: Any) -> Any:
        if v is None:
            return v
        try:
            raw = json.dumps(v, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError):
            raise ValueError("reasoning must be JSON-serialisable")
        if len(raw) > MAX_REASONING_BYTES:
            raise ValueError(f"reasoning exceeds {MAX_REASONING_BYTES} bytes")
        return v


class SubmitResponse(BaseModel):
    """Response from SUBMIT command."""

    correct: bool
    query_count: int
    phase: SessionPhase = SessionPhase.COMPLETED
    score: int


class TaskReplayResponse(BaseModel):
    card_id: str
    task_id: str
    session_id: str
    solved: Optional[bool]
    query_count: int
    replay: SessionReplay


class SessionState(BaseModel):
    """
    Current state of an Active-ARC session, maintained by the agent.
    This replaces FrameData from ARC-AGI-3.
    """

    session_id: str = ""
    task_id: str = ""
    phase: SessionPhase = SessionPhase.LEARNING
    query_count: int = 0

    queries: list[QueryRecord] = Field(default_factory=list)

    test_input: Optional[Grid] = None

    metadata: Optional[Metadata] = None

    correct: Optional[bool] = None
    submitted_answer: Optional[Grid] = None

    def add_query(
        self, input_grid: Grid, output: Optional[Grid], reasoning: Optional[Any] = None
    ) -> None:
        """Add a query to the session history."""
        self.queries.append(
            QueryRecord(input=input_grid, output=output, reasoning=reasoning)
        )
        self.query_count = len(self.queries)

    @property
    def last_query(self) -> Optional[QueryRecord]:
        return self.queries[-1] if self.queries else None

    @property
    def is_learning(self) -> bool:
        return self.phase == SessionPhase.LEARNING

    @property
    def is_test(self) -> bool:
        return self.phase == SessionPhase.TEST

    @property
    def is_completed(self) -> bool:
        return self.phase == SessionPhase.COMPLETED
