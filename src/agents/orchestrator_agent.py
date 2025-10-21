"""
Orchestrator Agent using Google A2A framework with LangChain integration.

This agent coordinates between other agents and provides intelligent
query processing using LangChain and GPT-4.
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.events import Event

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .base import BaseAuditAgent
from .financial_data_agent import FinancialDataAgent
from .policy_engine_agent import PolicyEngineAgent


class OrchestratorAgent(BaseAuditAgent):
    """
    Orchestrator agent that coordinates between other agents using LangChain.
    
    This agent:
    - Processes natural language queries using GPT-4
    - Discovers and communicates with other A2A agents
    - Orchestrates complex workflows across multiple agents
    - Provides intelligent responses by combining agent outputs
    """
    
    def __init__(self, openai_api_key: str):
        super().__init__("orchestrator-agent", "1.0.0")
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model="gpt-4",
            api_key=openai_api_key,
            temperature=0.1
        )
        
        # Initialize other agents
        self.financial_agent = FinancialDataAgent()
        self.policy_agent = PolicyEngineAgent()
        
        # Create LangChain prompt template
        self.prompt_template = self._create_prompt_template()
        
        # Agent registry for discovery
        self.agent_registry = {
            "financial-data-agent": self.financial_agent,
            "policy-engine-agent": self.policy_agent
        }
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create the LangChain prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent audit and compliance assistant. You can help with:

1. Financial Data Analysis: Revenue, expenses, assets, transaction analysis
2. Policy Compliance: SOX, GAAP, IFRS compliance checking
3. Audit Reports: Generate comprehensive audit reports

When a user asks a question, provide helpful and accurate responses based on your knowledge of audit and compliance processes.

Always be professional and provide actionable insights."""),
            ("human", "{input}"),
        ])
    
    async def _process_request(self, context: RequestContext) -> Any:
        """
        Process orchestration requests using LangChain.
        
        Args:
            context: Request context containing the query
            
        Returns:
            Orchestrated response from multiple agents
        """
        user_input = context.get_user_input()
        self.logger.info(f"Processing orchestration request: {user_input}")
        
        try:
            # Determine which agents to consult based on the query
            agents_to_consult = self._get_agents_consulted(user_input)
            
            # Get responses from relevant agents
            agent_responses = {}
            for agent_name in agents_to_consult:
                if agent_name == "financial-data-agent":
                    agent_responses[agent_name] = await self.financial_agent._process_request(context)
                elif agent_name == "policy-engine-agent":
                    agent_responses[agent_name] = await self.policy_agent._process_request(context)
            
            # Use LangChain to synthesize the responses
            chain = self.prompt_template | self.llm
            
            # Create a comprehensive prompt with agent responses
            synthesis_prompt = f"""
            User Query: {user_input}
            
            Agent Responses:
            {json.dumps(agent_responses, indent=2)}
            
            Please synthesize these responses into a comprehensive answer.
            """
            
            # Get the response from the LLM
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: chain.invoke({"input": synthesis_prompt})
            )
            
            # Extract the final answer
            final_answer = response.content if hasattr(response, 'content') else str(response)
            
            # Create comprehensive response
            orchestrated_response = {
                "type": "orchestrated_response",
                "query": user_input,
                "response": final_answer,
                "agents_consulted": agents_to_consult,
                "agent_responses": agent_responses,
                "metadata": {
                    "orchestrator_version": self.agent_version,
                    "processing_time": datetime.utcnow().isoformat(),
                    "langchain_model": "gpt-4"
                }
            }
            
            return orchestrated_response
            
        except Exception as e:
            self.logger.error(f"Error in orchestration: {str(e)}")
            return {
                "type": "error",
                "error": str(e),
                "query": user_input,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    
    def _get_agents_consulted(self, user_input: str) -> List[str]:
        """Determine which agents would be consulted for a given query."""
        agents = []
        user_input_lower = user_input.lower()
        
        # Check if financial data is needed
        financial_keywords = ["revenue", "expense", "asset", "profit", "financial", "money", "cost", "income", "transaction", "payment", "amount", "eur", "usd", "currency"]
        if any(keyword in user_input_lower for keyword in financial_keywords):
            agents.append("financial-data-agent")
        
        # Check if policy/compliance is needed
        policy_keywords = ["compliance", "policy", "regulation", "audit", "validate", "sox", "gaap", "ifrs"]
        if any(keyword in user_input_lower for keyword in policy_keywords):
            agents.append("policy-engine-agent")
        
        return agents
    
    async def discover_agents(self) -> Dict[str, Any]:
        """Discover available agents and their capabilities."""
        discovered_agents = {}
        
        for agent_name, agent in self.agent_registry.items():
            discovered_agents[agent_name] = {
                "agent_card": agent.get_agent_card(),
                "capabilities": agent._get_capabilities(),
                "endpoints": agent._get_endpoints(),
                "status": "available"
            }
        
        return {
            "type": "agent_discovery",
            "discovered_agents": discovered_agents,
            "total_agents": len(discovered_agents),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get the status of all registered agents."""
        agent_status = {}
        
        for agent_name, agent in self.agent_registry.items():
            agent_status[agent_name] = {
                "name": agent.agent_name,
                "version": agent.agent_version,
                "status": "running",
                "last_activity": datetime.utcnow().isoformat()
            }
        
        return {
            "type": "agent_status",
            "agents": agent_status,
            "orchestrator_status": "running",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of the orchestrator agent."""
        return {
            "input_types": ["text", "json"],
            "output_types": ["text", "json"],
            "supported_operations": [
                "orchestrate_agent_communication",
                "process_natural_language_queries",
                "discover_agents",
                "get_agent_status",
                "coordinate_workflows"
            ],
            "integrated_agents": list(self.agent_registry.keys()),
            "llm_model": "gpt-4",
            "framework": "langchain"
        }
    
    def _get_endpoints(self) -> Dict[str, Any]:
        """Get the endpoints this agent exposes."""
        return {
            "execute": {
                "method": "POST",
                "description": "Execute orchestrated agent operations",
                "parameters": {
                    "query": "Natural language query to be processed by multiple agents"
                }
            },
            "discover_agents": {
                "method": "GET",
                "description": "Discover available agents and their capabilities"
            },
            "get_status": {
                "method": "GET", 
                "description": "Get status of all registered agents"
            },
            "cancel": {
                "method": "POST",
                "description": "Cancel ongoing orchestration operation"
            }
        }
