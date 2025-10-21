"""
Main application for the A2A Audit & Compliance Agent Network.

This module provides the main entry point and agent server implementation.
"""

import asyncio
import logging
import os
from typing import Dict, Any
from datetime import datetime
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.financial_data_agent import FinancialDataAgent
from src.agents.policy_engine_agent import PolicyEngineAgent
from src.database import init_database
from src.tracing import get_tracer, is_langfuse_enabled

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for API
class QueryRequest(BaseModel):
    query: str
    agent_type: str = "orchestrator"  # orchestrator, financial, policy

class AgentDiscoveryResponse(BaseModel):
    agents: Dict[str, Any]
    timestamp: str

class AgentStatusResponse(BaseModel):
    status: str
    agents: Dict[str, Any]
    timestamp: str

# Initialize FastAPI app
app = FastAPI(
    title="A2A Audit & Compliance Agent Network",
    description="Agent-to-Agent architecture using Google's A2A framework and LangChain",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instances
agents: Dict[str, Any] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup."""
    logger.info("Starting A2A Audit & Compliance Agent Network")
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.warning("OPENAI_API_KEY not found in environment variables")
        openai_api_key = "dummy-key"  # For development
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        logger.info("Database initialized successfully")
        
        # Initialize tracing
        tracer = get_tracer()
        if is_langfuse_enabled():
            logger.info("Langfuse tracing enabled")
        else:
            logger.info("Langfuse tracing disabled")
        
        # Initialize agents
        logger.info("Initializing agents...")
        agents["orchestrator"] = OrchestratorAgent(openai_api_key)
        agents["financial"] = FinancialDataAgent()
        agents["policy"] = PolicyEngineAgent()
        
        logger.info("All agents initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing system: {str(e)}")
        raise

@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "A2A Audit & Compliance Agent Network",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {
            agent_name: "running" 
            for agent_name in agents.keys()
        }
    }

@app.post("/query")
async def process_query(request: QueryRequest):
    """
    Process a natural language query using the specified agent.
    
    Args:
        request: Query request containing the query and agent type
        
    Returns:
        Response from the agent
    """
    try:
        logger.info(f"Processing query: {request.query} with agent: {request.agent_type}")
        
        if request.agent_type not in agents:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown agent type: {request.agent_type}"
            )
        
        agent = agents[request.agent_type]
        
        # Create a mock context for the agent
        # In a real A2A implementation, this would be properly structured
        class MockContext:
            def __init__(self, query: str):
                self.query = query
                self.request_id = f"req_{datetime.utcnow().timestamp()}"
            
            def get_user_input(self) -> str:
                return self.query
            
            def get_request_id(self) -> str:
                return self.request_id
            
            def get_task_id(self) -> str:
                return f"task_{self.request_id}"
        
        context = MockContext(request.query)
        
        # Process the request
        if request.agent_type == "orchestrator":
            result = await agent._process_request(context)
        else:
            result = await agent._process_request(context)
        
        return {
            "query": request.query,
            "agent_type": request.agent_type,
            "response": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/discover")
async def discover_agents():
    """Discover all available agents and their capabilities."""
    try:
        orchestrator = agents["orchestrator"]
        discovery_result = await orchestrator.discover_agents()
        
        return AgentDiscoveryResponse(
            agents=discovery_result["discovered_agents"],
            timestamp=discovery_result["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Error discovering agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/status")
async def get_agent_status():
    """Get the status of all agents."""
    try:
        orchestrator = agents["orchestrator"]
        status_result = await orchestrator.get_agent_status()
        
        return AgentStatusResponse(
            status="running",
            agents=status_result["agents"],
            timestamp=status_result["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent_name}/card")
async def get_agent_card(agent_name: str):
    """Get the agent card for a specific agent."""
    try:
        if agent_name not in agents:
            raise HTTPException(
                status_code=404, 
                detail=f"Agent not found: {agent_name}"
            )
        
        agent = agents[agent_name]
        agent_card = agent.get_agent_card()
        
        return agent_card
        
    except Exception as e:
        logger.error(f"Error getting agent card: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent_name}/capabilities")
async def get_agent_capabilities(agent_name: str):
    """Get the capabilities of a specific agent."""
    try:
        if agent_name not in agents:
            raise HTTPException(
                status_code=404, 
                detail=f"Agent not found: {agent_name}"
            )
        
        agent = agents[agent_name]
        capabilities = agent._get_capabilities()
        
        return capabilities
        
    except Exception as e:
        logger.error(f"Error getting agent capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
