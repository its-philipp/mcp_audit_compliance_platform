# A2A Audit & Compliance Agent Network

**Simplified Agent-to-Agent Architecture using Google's A2A Framework**

This project implements a simplified Agent-to-Agent (A2A) architecture using Google's A2A framework as a foundation, with custom orchestration logic and LangChain GPT-4 integration for intelligent coordination.

## 🎯 Project Goals

- **A2A Foundation**: Using Google's A2A framework as base classes
- **Custom Orchestration**: Simplified agent coordination with LangChain GPT-4
- **Standard Agent Cards**: Following Google's A2A specifications
- **Agent-to-Agent Communication**: Custom request/response pattern

## 🏗️ Architecture Overview

### Agent-to-Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Natural Language Query                   │
│                    (User Input)                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              🎯 Orchestrator Agent                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Google A2A AgentExecutor (Base Class)                │ │
│  │ • LangChain GPT-4 Integration                          │ │
│  │ • Agent Discovery & Coordination                       │ │
│  │ • Request Parsing & Response Synthesis                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼─────────┐        ┌─────────▼─────────┐
│ 💰 Financial    │        │ ⚖️ Policy Engine  │
│ Data Agent      │        │ Agent             │
│                 │        │                   │
│ ┌──────────────┐│        │ ┌────────────────┐│
│ │ • A2A Base   ││        │ │ • A2A Base     ││
│ │ • SQLite DB  ││        │ │ • AML Policies ││
│ │ • Transaction││        │ │ • Compliance   ││
│ │   Analysis   ││        │ │   Validation   ││
│ └──────────────┘│        │ └────────────────┘│
└─────────────────┘        └───────────────────┘
```

### Agent Profiles

#### 🎯 Orchestrator Agent
- **Role**: Intelligent interface and agent coordinator
- **Technology**: Google A2A AgentExecutor (Base Class), LangChain GPT-4 integration
- **Architecture**: Simplified A2A agent with custom orchestration logic

#### 💰 Financial Data Agent
- **Role**: Secure data access and transaction analysis
- **Technology**: Google A2A Framework (Base Class), SQLite Database
- **Architecture**: Simplified A2A agent with database integration

#### ⚖️ Policy Engine Agent
- **Role**: Compliance validation and AML policy enforcement
- **Technology**: Google A2A Framework (Base Class), Custom Policy Engine
- **Architecture**: Simplified A2A agent with policy validation logic

## 📋 Implementation Status

**Current Status**: Implementation Complete ✅  
**Target Version**: v1.0.0-simplified-a2a  
**Dependencies**: Google A2A Framework (Base Classes), LangChain GPT-4 integration

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Google A2A Framework (a2a-sdk) - Base Classes Only
- LangChain with GPT-4 integration
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
- [x] Study Google A2A Framework (Base Classes)
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