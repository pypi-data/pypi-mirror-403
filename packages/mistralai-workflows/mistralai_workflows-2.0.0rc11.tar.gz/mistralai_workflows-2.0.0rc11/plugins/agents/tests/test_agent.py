"""Tests for Agent class."""

from mistralai_workflows.plugins.agents import Agent


class TestAgent:
    def test_agent_creation_with_defaults(self):
        """Test creating an agent with default values."""
        agent = Agent(name="test-agent")
        assert agent.name == "test-agent"
        assert agent.model == "mistral-medium-latest"
        assert agent.tools is None
        assert agent.handoffs is None
        assert agent.mcp_clients is None

    def test_agent_creation_with_custom_model(self):
        """Test creating an agent with a custom model."""
        agent = Agent(name="test-agent", model="mistral-large-latest")
        assert agent.model == "mistral-large-latest"

    def test_agent_creation_with_instructions(self):
        """Test creating an agent with instructions."""
        instructions = "You are a helpful assistant."
        agent = Agent(name="test-agent", instructions=instructions)
        assert agent.instructions == instructions

    def test_agent_hash(self):
        """Test that agents can be hashed (for use in dicts/sets)."""
        agent1 = Agent(name="test-agent")
        agent2 = Agent(name="test-agent")
        assert hash(agent1) != hash(agent2)

    def test_iterate_agents_deeply_single_agent(self):
        """Test iterating over a single agent with no handoffs."""
        agent = Agent(name="test-agent")
        agents = list(Agent.iterate_agents_deeply_in_handoffs(agent))
        assert len(agents) == 1
        assert agents[0] is agent

    def test_iterate_agents_deeply_with_handoffs(self):
        """Test iterating over agents with handoffs."""
        child1 = Agent(name="child1")
        child2 = Agent(name="child2")
        parent = Agent(name="parent", handoffs=[child1, child2])

        agents = list(Agent.iterate_agents_deeply_in_handoffs(parent))
        assert len(agents) == 3
        assert parent in agents
        assert child1 in agents
        assert child2 in agents

    def test_iterate_agents_deeply_avoids_cycles(self):
        """Test that iteration handles circular handoffs."""
        agent1 = Agent(name="agent1")
        agent2 = Agent(name="agent2")
        agent1.handoffs = [agent2]
        agent2.handoffs = [agent1]

        agents = list(Agent.iterate_agents_deeply_in_handoffs(agent1))
        assert len(agents) == 2
