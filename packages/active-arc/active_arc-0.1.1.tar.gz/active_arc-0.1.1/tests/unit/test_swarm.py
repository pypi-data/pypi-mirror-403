from unittest.mock import Mock, patch

import pytest
import requests

from active_arc.structs import TaskCard, SessionPhase, Scorecard
from active_arc.swarm import Swarm
from active_arc.templates.random_agent import Random


@pytest.mark.unit
class TestSwarmInitialization:
    def test_swarm_init_with_agent_name(self):
        with patch.dict("os.environ", {"ACTIVE_ARC_API_KEY": "test-api-key"}):
            swarm = Swarm(
                tasks=["task1", "task2"],
                root_url="https://example.com",
                agent="random",
            )

            assert swarm.agent_name == "random"
            assert swarm.ROOT_URL == "https://example.com"
            assert swarm.TASKS == ["task1", "task2"]
            assert swarm.agent_class == Random
            assert len(swarm.threads) == 0
            assert len(swarm.agents) == 0

            assert swarm.headers["X-Api-Key"] == "test-api-key"
            assert swarm.headers["Accept"] == "application/json"
            assert isinstance(swarm._session, requests.Session)
            assert swarm._session.headers["Accept"] == "application/json"

    def test_swarm_init_with_agent_class(self):
        with patch.dict("os.environ", {"ACTIVE_ARC_API_KEY": "test-api-key"}):
            swarm = Swarm(
                tasks=["task1", "task2"],
                root_url="https://example.com",
                agent_class=Random,
            )

            assert swarm.agent_name == "random"
            assert swarm.agent_class == Random
            assert swarm.TASKS == ["task1", "task2"]

    def test_swarm_init_requires_agent(self):
        with pytest.raises(ValueError, match="Either 'agent'"):
            Swarm(tasks=["task1"], root_url="https://example.com")


@pytest.mark.unit
class TestSwarmScorecard:
    @patch("active_arc.swarm.requests.Session.post")
    def test_open_scorecard(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"card_id": "test-card-123"}
        mock_post.return_value = mock_response

        swarm = Swarm(tasks=["task1"], root_url="https://example.com", agent="random")

        card_id = swarm.open_scorecard()
        assert card_id == "test-card-123"

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/api/scorecard/open" in call_args[0][0]

        json_data = call_args[1]["json"]
        assert "agent_name" in json_data
        assert json_data["agent_name"] == "random"

    @patch("active_arc.swarm.requests.Session.post")
    def test_close_scorecard(self, mock_post):
        card = TaskCard(
            task_id="test-task",
            session_id="session-123",
            phase=SessionPhase.COMPLETED,
            correct=True,
            query_count=10,
        )

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "card_id": "test-card-123",
            "cards": {"test-task": card.model_dump()},
        }
        mock_post.return_value = mock_response

        swarm = Swarm(tasks=["task1"], root_url="https://example.com", agent="random")

        scorecard = swarm.close_scorecard("test-card-123")
        assert isinstance(scorecard, Scorecard)
        assert scorecard.card_id == "test-card-123"
        assert swarm.card_id is None


@pytest.mark.unit
class TestSwarmAgentManagement:
    @patch("active_arc.swarm.Swarm.open_scorecard")
    @patch("active_arc.swarm.Swarm.close_scorecard")
    @patch("active_arc.swarm.Thread")
    def test_agent_threading(self, mock_thread, mock_close, mock_open):
        mock_open.return_value = "test-card-123"
        mock_close.return_value = Scorecard()

        mock_thread_instances = [Mock() for _ in range(3)]
        mock_thread.side_effect = mock_thread_instances

        swarm = Swarm(
            tasks=["task1", "task2", "task3"],
            root_url="https://example.com",
            agent="random",
        )

        assert swarm.agent_name == "random"
        assert swarm.agent_class == Random
        assert swarm.TASKS == ["task1", "task2", "task3"]

        with patch.object(Random, "main") as mock_agent_main:
            mock_agent_main.return_value = None

            swarm.main()

            assert mock_thread.call_count == 3
            for mock_thread_instance in mock_thread_instances:
                mock_thread_instance.start.assert_called_once()
                mock_thread_instance.join.assert_called_once()


@pytest.mark.unit
class TestSwarmCleanup:
    def test_cleanup(self):
        swarm = Swarm(
            tasks=["task1", "task2"],
            root_url="https://example.com",
            agent="random",
        )

        mock_agent1 = Mock()
        mock_agent2 = Mock()
        swarm.agents = [mock_agent1, mock_agent2]

        mock_session = Mock()
        swarm._session = mock_session

        scorecard = Scorecard()
        swarm.cleanup(scorecard)

        mock_agent1.cleanup.assert_called_once_with(scorecard)
        mock_agent2.cleanup.assert_called_once_with(scorecard)

        mock_session.close.assert_called_once()


@pytest.mark.unit
class TestSwarmTags:
    @patch("active_arc.swarm.requests.Session.post")
    def test_open_scorecard_with_custom_tags(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"card_id": "test-card-123"}
        mock_post.return_value = mock_response

        custom_tags = ["experiment1", "version2", "test"]

        swarm = Swarm(
            tasks=["task1"],
            root_url="https://example.com",
            agent="random",
            tags=custom_tags,
        )

        card_id = swarm.open_scorecard()
        assert card_id == "test-card-123"

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        json_data = call_args[1]["json"]

        assert "tags" in json_data
        for tag in custom_tags:
            assert tag in json_data["tags"]
