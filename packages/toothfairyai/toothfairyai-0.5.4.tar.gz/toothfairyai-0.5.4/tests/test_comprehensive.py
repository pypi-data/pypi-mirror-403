"""Comprehensive tests for the ToothFairyAI SDK."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from toothfairyai import (
    Agent,
    AgentFunction,
    AgentMode,
    Authorisation,
    Benchmark,
    Channel,
    ChartingSettings,
    Chat,
    Connection,
    DictionaryEntry,
    Document,
    Embedding,
    EmbeddingsSettings,
    Entity,
    Folder,
    Hook,
    Member,
    Message,
    MonthCostsResponse,
    OutputStream,
    Prompt,
    RequestLog,
    ScheduledJob,
    Secret,
    Site,
    ToothFairyClient,
)


class TestToothFairyClient:
    """Test the main ToothFairyClient class."""

    def test_client_initialization(self):
        """Test client initialization with required parameters."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        assert client.config.api_key == "test-api-key"
        assert client.config.workspace_id == "test-workspace-id"

    def test_client_initialization_with_custom_urls(self):
        """Test client initialization with custom URLs."""
        client = ToothFairyClient(
            api_key="test-api-key",
            workspace_id="test-workspace-id",
            base_url="https://custom.api.com",
            ai_url="https://custom.ai.com",
            ai_stream_url="https://custom.stream.com",
        )
        assert client.config.base_url == "https://custom.api.com"
        assert client.config.ai_url == "https://custom.ai.com"
        assert client.config.ai_stream_url == "https://custom.stream.com"

    def test_client_missing_api_key(self):
        """Test that missing API key raises error."""
        with pytest.raises(Exception):
            ToothFairyClient(api_key="", workspace_id="test-workspace-id")

    def test_client_missing_workspace_id(self):
        """Test that missing workspace ID raises error."""
        with pytest.raises(Exception):
            ToothFairyClient(api_key="test-api-key", workspace_id="")

    def test_all_managers_accessible(self):
        """Test that all managers are accessible."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        assert hasattr(client, "agents")
        assert hasattr(client, "agent_functions")
        assert hasattr(client, "chat")
        assert hasattr(client, "documents")
        assert hasattr(client, "entities")
        assert hasattr(client, "folders")
        assert hasattr(client, "prompts")
        assert hasattr(client, "members")
        assert hasattr(client, "authorisations")
        assert hasattr(client, "channels")
        assert hasattr(client, "connections")
        assert hasattr(client, "benchmarks")
        assert hasattr(client, "hooks")
        assert hasattr(client, "scheduled_jobs")
        assert hasattr(client, "sites")
        assert hasattr(client, "secrets")
        assert hasattr(client, "dictionary")
        assert hasattr(client, "embeddings")
        assert hasattr(client, "embeddings_settings")
        assert hasattr(client, "charting_settings")
        assert hasattr(client, "billing")
        assert hasattr(client, "request_logs")
        assert hasattr(client, "streaming")


class TestAgentManager:
    """Test the AgentManager."""

    def test_create_agent(self):
        """Test creating an agent."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "id": "agent-123",
                "label": "Test Agent",
                "mode": "retriever",
                "interpolationString": "You are helpful",
                "goals": "Help users",
                "temperature": 0.7,
                "maxTokens": 1000,
                "maxHistory": 10,
                "topK": 10,
                "docTopK": 5,
            }

            agent = client.agents.create(
                label="Test Agent",
                mode="retriever",
                interpolation_string="You are helpful",
                goals="Help users",
                temperature=0.7,
                max_tokens=1000,
                max_history=10,
                top_k=10,
                doc_top_k=5,
            )

            assert isinstance(agent, Agent)
            assert agent.label == "Test Agent"
            assert agent.mode == "retriever"
            mock_request.assert_called_once()

    def test_get_agent(self):
        """Test getting an agent."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "id": "agent-123",
                "label": "Test Agent",
                "mode": "retriever",
            }

            agent = client.agents.get("agent-123")

            assert isinstance(agent, Agent)
            assert agent.id == "agent-123"
            mock_request.assert_called_once_with("GET", "/agent/get/agent-123")

    def test_list_agents(self):
        """Test listing agents."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = [
                {"id": "agent-1", "label": "Agent 1", "mode": "retriever"},
                {"id": "agent-2", "label": "Agent 2", "mode": "chatter"},
            ]

            result = client.agents.list()

            assert len(result.items) == 2
            assert all(isinstance(agent, Agent) for agent in result.items)
            mock_request.assert_called_once()

    def test_get_by_mode(self):
        """Test filtering agents by mode."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client.agents, "list") as mock_list:
            mock_list.return_value = type(
                "obj",
                (object,),
                {
                    "items": [
                        Agent.from_dict({"id": "agent-1", "label": "Agent 1", "mode": "retriever"}),
                        Agent.from_dict({"id": "agent-2", "label": "Agent 2", "mode": "chatter"}),
                        Agent.from_dict({"id": "agent-3", "label": "Agent 3", "mode": "retriever"}),
                    ]
                },
            )()

            retriever_agents = client.agents.get_by_mode("retriever")

            assert len(retriever_agents) == 2
            assert all(agent.mode == "retriever" for agent in retriever_agents)

    def test_search_agents(self):
        """Test searching agents by label."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client.agents, "list") as mock_list:
            mock_list.return_value = type(
                "obj",
                (object,),
                {
                    "items": [
                        Agent.from_dict(
                            {"id": "agent-1", "label": "Customer Support", "mode": "retriever"}
                        ),
                        Agent.from_dict({"id": "agent-2", "label": "Sales Bot", "mode": "chatter"}),
                    ]
                },
            )()

            results = client.agents.search("support")

            assert len(results) == 1
            assert results[0].label == "Customer Support"


class TestChatManager:
    """Test the ChatManager."""

    def test_create_chat(self):
        """Test creating a chat."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "id": "chat-123",
                "name": "Test Chat",
                "customerId": "cust-123",
            }

            chat = client.chat.create(name="Test Chat", customer_id="cust-123")

            assert isinstance(chat, Chat)
            assert chat.id == "chat-123"
            mock_request.assert_called_once()

    def test_create_message(self):
        """Test creating a message."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "id": "msg-123",
                "chatID": "chat-123",
                "text": "Hello",
                "role": "user",
            }

            message = client.chat.create_message(chat_id="chat-123", text="Hello", role="user")

            assert isinstance(message, Message)
            assert message.text == "Hello"
            mock_request.assert_called_once()

    def test_update_message(self):
        """Test updating a message."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "id": "msg-123",
                "chatID": "chat-123",
                "text": "Updated text",
                "role": "user",
            }

            message = client.chat.update_message(message_id="msg-123", text="Updated text")

            assert isinstance(message, Message)
            assert message.text == "Updated text"
            mock_request.assert_called_once()

    def test_list_messages(self):
        """Test listing messages in a chat."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = [
                {"id": "msg-1", "chatID": "chat-123", "text": "Hello", "role": "user"},
                {"id": "msg-2", "chatID": "chat-123", "text": "Hi there!", "role": "assistant"},
            ]

            result = client.chat.list_messages(chat_id="chat-123")

            assert len(result.items) == 2
            assert all(isinstance(msg, Message) for msg in result.items)
            mock_request.assert_called_once()


class TestDocumentManager:
    """Test the DocumentManager."""

    def test_create_document(self):
        """Test creating a document."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "id": "doc-123",
                "title": "Test Document",
                "type": "readComprehensionFile",
            }

            document = client.documents.create(user_id="user-123", title="Test Document")

            assert isinstance(document, Document)
            assert document.title == "Test Document"
            mock_request.assert_called_once()


class TestEntityManager:
    """Test the EntityManager."""

    def test_create_entity(self):
        """Test creating an entity."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "id": "entity-123",
                "label": "Test Entity",
                "type": "topic",
            }

            entity = client.entities.create(
                user_id="user-123", label="Test Entity", entity_type="topic"
            )

            assert isinstance(entity, Entity)
            assert entity.label == "Test Entity"
            mock_request.assert_called_once()


class TestFolderManager:
    """Test the FolderManager."""

    def test_create_folder(self):
        """Test creating a folder."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {"id": "folder-123", "name": "Test Folder"}

            folder = client.folders.create(user_id="user-123", name="Test Folder")

            assert isinstance(folder, Folder)
            assert folder.name == "Test Folder"
            mock_request.assert_called_once()


class TestPromptManager:
    """Test the PromptManager."""

    def test_create_prompt(self):
        """Test creating a prompt."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "id": "prompt-123",
                "label": "Test Prompt",
                "type": "greeting",
                "interpolationString": "Hello {{name}}!",
            }

            prompt = client.prompts.create(
                user_id="user-123",
                label="Test Prompt",
                prompt_type="greeting",
                interpolation_string="Hello {{name}}!",
            )

            assert isinstance(prompt, Prompt)
            assert prompt.label == "Test Prompt"
            mock_request.assert_called_once()


class TestMembersManager:
    """Test the MembersManager."""

    def test_get_by_role(self):
        """Test filtering members by role."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "items": [
                    {"id": "member-1", "userID": "user-1", "role": "admin"},
                    {"id": "member-2", "userID": "user-2", "role": "member"},
                    {"id": "member-3", "userID": "user-3", "role": "admin"},
                ]
            }

            admins = client.members.get_by_role("admin")

            assert len(admins) == 2
            assert all(member.role == "admin" for member in admins)


class TestAuthorisationsManager:
    """Test the AuthorisationsManager."""

    def test_create_authorisation(self):
        """Test creating an authorisation."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {"id": "auth-123", "name": "Test Auth", "type": "apikey"}

            auth = client.authorisations.create(
                name="Test Auth", auth_type="apikey", token_secret="secret-123"
            )

            assert isinstance(auth, Authorisation)
            assert auth.name == "Test Auth"
            mock_request.assert_called_once()


class TestChannelsManager:
    """Test the ChannelsManager."""

    def test_create_channel(self):
        """Test creating a channel."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "id": "channel-123",
                "name": "Test Channel",
                "channel": "sms",
                "provider": "twilio",
            }

            channel = client.channels.create(name="Test Channel", channel="sms", provider="twilio")

            assert isinstance(channel, Channel)
            assert channel.name == "Test Channel"
            mock_request.assert_called_once()


class TestBenchmarksManager:
    """Test the BenchmarksManager."""

    def test_create_benchmark(self):
        """Test creating a benchmark."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "id": "benchmark-123",
                "name": "Test Benchmark",
                "questions": [],
            }

            benchmark = client.benchmarks.create(name="Test Benchmark")

            assert isinstance(benchmark, Benchmark)
            assert benchmark.name == "Test Benchmark"
            mock_request.assert_called_once()


class TestHooksManager:
    """Test the HooksManager."""

    def test_create_hook(self):
        """Test creating a hook."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "id": "hook-123",
                "name": "Test Hook",
                "customExecutionCode": "def test(): pass",
            }

            hook = client.hooks.create(name="Test Hook", custom_execution_code="def test(): pass")

            assert isinstance(hook, Hook)
            assert hook.name == "Test Hook"
            mock_request.assert_called_once()


class TestScheduledJobsManager:
    """Test the ScheduledJobsManager."""

    def test_create_scheduled_job(self):
        """Test creating a scheduled job."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "id": "job-123",
                "name": "Test Job",
                "schedule": {"cron": "0 9 * * *"},
                "isActive": True,
            }

            job = client.scheduled_jobs.create(name="Test Job", schedule={"cron": "0 9 * * *"})

            assert isinstance(job, ScheduledJob)
            assert job.name == "Test Job"
            mock_request.assert_called_once()


class TestSecretsManager:
    """Test the SecretsManager."""

    def test_create_secret(self):
        """Test creating a secret."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {"id": "secret-123", "name": "Test Secret"}

            secret = client.secrets.create(name="Test Secret")

            assert isinstance(secret, Secret)
            assert secret.name == "Test Secret"
            mock_request.assert_called_once()


class TestBillingManager:
    """Test the BillingManager."""

    def test_get_month_costs(self):
        """Test getting monthly costs."""
        client = ToothFairyClient(api_key="test-api-key", workspace_id="test-workspace-id")
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {
                "apiUsage": {"tokens": 1000, "cost": 0.01},
                "trainingUsage": {"tokens": 500, "cost": 0.005},
            }

            costs = client.billing.get_month_costs()

            assert isinstance(costs, MonthCostsResponse)
            assert "tokens" in costs.api_usage
            mock_request.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
