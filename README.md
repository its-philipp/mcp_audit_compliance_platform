# A2A Audit & Compliance Agent Network

**Agent-to-Agent Architecture using Google's A2A Framework and LangChain AgentExecutor**

This project implements a proper Agent-to-Agent (A2A) architecture following Google's A2A protocol specifications, using LangChain AgentExecutor for agent management and coordination.

## 🎯 Project Goals

- **A2A Implementation**: Using Google's official A2A framework
- **AgentExecutor Integration**: Proper LangChain agent lifecycle management
- **Standard Agent Cards**: Following Google's A2A specifications
- **Agent-to-Agent Communication**: Not just microservices with REST APIs

## 🏗️ Architecture Overview

### Agent-to-Agent Architecture

```
Natural Language Query
        ↓
   Agent A (Orchestrator)
   - LangChain AgentExecutor
   - GPT-4 query parsing
   - Agent discovery
        ↓
   ┌────┴────┐
   ↓         ↓
Agent B    Agent C
(Data)     (Policy)
- A2A Agent - A2A Agent
- Agent Card - Agent Card
- A2A Protocol - A2A Protocol
```

### Agent Profiles

#### Agent A: Audit Orchestrator Agent
- **Role**: Intelligent interface and agent coordinator
- **Technology**: LangChain AgentExecutor, Google A2A Framework
- **Architecture**: True agent with A2A protocol communication

#### Agent B: Financial Data Agent
- **Role**: Secure data access agent
- **Technology**: Google A2A Framework, Agent Cards
- **Architecture**: A2A agent with proper agent cards

#### Agent C: Policy Engine Agent
- **Role**: Compliance validation agent
- **Technology**: Google A2A Framework, Agent Cards
- **Architecture**: A2A agent with proper agent cards

## 📋 Implementation Status

**Current Status**: Implementation Complete ✅  
**Target Version**: v1.0.0-a2a  
**Dependencies**: Google A2A Framework, LangChain AgentExecutor

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Google A2A Framework
- LangChain with AgentExecutor
- OpenAI API Key

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd kpmg_a2a_audit_compliance

# Install dependencies
pip install -e .

# Run the application
python main.py
```

## 🧪 Testing

Run the test suite to verify everything is working:

```bash
# Start the server (in one terminal)
python main.py

# Run tests (in another terminal)
python test_agents.py
```

## 📡 API Usage

### Basic Queries

```bash
# Health check
curl http://localhost:8000/health

# Agent discovery
curl http://localhost:8000/agents/discover

# Process a query through the orchestrator
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is our revenue for 2024?", "agent_type": "orchestrator"}'

# Query financial data directly
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me Q1 revenue data", "agent_type": "financial"}'

# Check compliance
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Check SOX compliance", "agent_type": "policy"}'
```

## 📚 Research and Planning

This project is based on research and planning from our [A2A Implementation Plan](../kpmg_a2a_audit_compliance_network/A2A_IMPLEMENTATION_PLAN.md).

## 🔗 Related Projects

- **Microservices Version**: [kpmg_audit_compliance_microservices](../kpmg_a2a_audit_compliance_network/) - Current microservices implementation
- **A2A Implementation Plan**: [A2A_IMPLEMENTATION_PLAN.md](../kpmg_a2a_audit_compliance_network/A2A_IMPLEMENTATION_PLAN.md) - Detailed planning document

## 📈 Development Roadmap

### Phase 1: Research and Setup ✅
- [x] Research Google A2A Framework
- [x] Study LangChain AgentExecutor
- [x] Set up development environment

### Phase 2: Architecture Design ✅
- [x] Design agent architecture
- [x] Plan agent-to-agent communication
- [x] Design agent cards

### Phase 3: Implementation ✅
- [x] Implement base A2A framework
- [x] Convert services to agents
- [x] Implement agent communication

### Phase 4: Testing and Validation ✅
- [x] Unit testing
- [x] Integration testing
- [x] Performance testing

## 🤝 Contributing

This project is in the planning phase. Contributions are welcome once the research phase is complete.

## 📄 License

[License information]

## 📞 Contact

[Contact information]