import pytest

from active_arc.structs import (
    SessionPhase,
    SessionState,
    TaskCard,
    Scorecard,
    QueryRecord,
)
from active_arc.templates.random_agent import Random


@pytest.mark.unit
class TestSessionState:
    def test_session_init(self):
        session = SessionState(
            session_id="test-123",
            task_id="task-abc",
        )
        assert session.session_id == "test-123"
        assert session.task_id == "task-abc"
        assert session.phase == SessionPhase.LEARNING
        assert session.query_count == 0
        assert session.queries == []
        assert session.test_input is None
        assert session.correct is None

    def test_add_query(self):
        session = SessionState(task_id="test")
        session.add_query([[1, 2], [3, 4]], [[5, 6], [7, 8]], {"note": "test"})

        assert session.query_count == 1
        assert len(session.queries) == 1
        assert session.last_query is not None
        assert session.last_query.input == [[1, 2], [3, 4]]
        assert session.last_query.output == [[5, 6], [7, 8]]
        assert session.last_query.reasoning == {"note": "test"}

    def test_phase_properties(self):
        session = SessionState(task_id="test")
        assert session.is_learning is True
        assert session.is_test is False
        assert session.is_completed is False

        session.phase = SessionPhase.TEST
        assert session.is_learning is False
        assert session.is_test is True

        session.phase = SessionPhase.COMPLETED
        assert session.is_completed is True


@pytest.mark.unit
class TestTaskCard:
    def test_task_card_init(self):
        card = TaskCard(task_id="test-task")
        assert card.task_id == "test-task"
        assert card.session_id is None
        assert card.phase == SessionPhase.LEARNING
        assert card.query_count == 0
        assert card.correct is None
        assert card.attempted is False
        assert card.is_solved is False
        assert card.score == 0

    def test_task_card_solved(self):
        card = TaskCard(
            task_id="test-task",
            session_id="session-123",
            phase=SessionPhase.COMPLETED,
            correct=True,
            query_count=5,
        )
        assert card.attempted is True
        assert card.is_solved is True
        assert card.score == 1


@pytest.mark.unit
class TestScorecard:
    def test_scorecard_init(self):
        scorecard = Scorecard(card_id="test-card")
        assert scorecard.card_id == "test-card"
        assert scorecard.solved == 0
        assert scorecard.attempted == 0
        assert scorecard.total_queries == 0

    def test_scorecard_with_cards(self):
        card1 = TaskCard(
            task_id="task1",
            session_id="s1",
            phase=SessionPhase.COMPLETED,
            correct=True,
            query_count=10,
        )
        card2 = TaskCard(
            task_id="task2",
            session_id="s2",
            phase=SessionPhase.COMPLETED,
            correct=False,
            query_count=15,
        )

        scorecard = Scorecard(card_id="test", cards={"task1": card1, "task2": card2})

        assert scorecard.solved == 1
        assert scorecard.attempted == 2
        assert scorecard.total_queries == 25


@pytest.mark.unit
class TestQueryRecord:
    def test_query_record_init(self):
        record = QueryRecord(
            input=[[1, 2], [3, 4]],
            output=[[5, 6], [7, 8]],
            reasoning={"model": "test"},
        )
        assert record.input == [[1, 2], [3, 4]]
        assert record.output == [[5, 6], [7, 8]]
        assert record.reasoning == {"model": "test"}

    def test_query_record_null_output(self):
        record = QueryRecord(input=[[0]], output=None)
        assert record.output is None


@pytest.mark.unit
class TestRandomAgent:
    def test_agent_init(self):
        agent = Random(
            card_id="test-card",
            task_id="test-task",
            agent_name="test-agent",
            ROOT_URL="https://example.com",
            record=False,
        )

        assert agent.task_id == "test-task"
        assert agent.card_id == "test-card"
        assert agent.MAX_QUERIES == 10

        name = agent.name
        assert "test-task" in name
        assert "random" in name

    def test_agent_query(self, sample_session):
        agent = Random(
            card_id="test-card",
            task_id="test-task",
            agent_name="test-agent",
            ROOT_URL="https://example.com",
            record=False,
        )

        result = agent.query(sample_session)
        assert result is not None
        assert isinstance(result, list)
        assert all(isinstance(row, list) for row in result)
        assert all(0 <= cell <= 9 for row in result for cell in row)

    def test_agent_submit(self, sample_session):
        agent = Random(
            card_id="test-card",
            task_id="test-task",
            agent_name="test-agent",
            ROOT_URL="https://example.com",
            record=False,
        )

        sample_session.test_input = [[1, 2], [3, 4]]
        prediction = agent.submit(sample_session)
        assert prediction == [[1, 2], [3, 4]]

    def test_agent_max_queries(self, sample_session):
        agent = Random(
            card_id="test-card",
            task_id="test-task",
            agent_name="test-agent",
            ROOT_URL="https://example.com",
            record=False,
        )

        sample_session.query_count = agent.MAX_QUERIES
        result = agent.query(sample_session)
        assert result is None
