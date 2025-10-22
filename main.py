"""
MCP-based Audit & Compliance Platform
Main application entry point using Model Context Protocol.
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from src.database import init_database, get_db_manager
from src.mcp_server import get_mcp_server
from src.mcp_client import get_mcp_client
from src.tracing import LangfuseTracer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Audit & Compliance Platform",
    description="Model Context Protocol-based audit and compliance system",
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

# Global instances
mcp_server = None
mcp_client = None
tracer = None

class QueryRequest(BaseModel):
    query: str
    include_tracing: bool = True

class QueryResponse(BaseModel):
    type: str
    query: str
    response: str
    tools_used: list
    tool_results: Dict[str, Any]
    metadata: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    """Initialize the MCP server and client on startup."""
    global mcp_server, mcp_client, tracer
    
    try:
        logger.info("🚀 Starting MCP Audit & Compliance Platform...")
        
        # Initialize database
        logger.info("📊 Initializing database...")
        init_database()
        logger.info("✅ Database initialized successfully")
        
        # Initialize MCP server
        logger.info("🔧 Initializing MCP server...")
        mcp_server = get_mcp_server()
        logger.info("✅ MCP server initialized successfully")
        
        # Initialize MCP client
        logger.info("🤖 Initializing MCP client...")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        mcp_client = get_mcp_client(openai_api_key)
        logger.info("✅ MCP client initialized successfully")
        
        # Initialize tracing
        logger.info("📈 Initializing tracing...")
        tracer = LangfuseTracer()
        logger.info("✅ Tracing initialized successfully")
        
        logger.info("🎉 MCP Audit & Compliance Platform started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        raise

@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "message": "MCP Audit & Compliance Platform",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "MCP Server with audit tools",
            "GPT-4 integration via MCP client",
            "Financial data queries",
            "Compliance validation",
            "Audit report generation",
            "Langfuse tracing"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        db_manager = get_db_manager()
        transactions_count = len(db_manager.get_transactions())
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "transactions_count": transactions_count,
            "mcp_server": "running" if mcp_server else "not_initialized",
            "mcp_client": "running" if mcp_client else "not_initialized"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process audit and compliance queries using MCP tools."""
    try:
        if not mcp_client:
            raise HTTPException(status_code=500, detail="MCP client not initialized")
        
        logger.info(f"Processing query: {request.query}")
        
        # Process query using MCP client
        result = await mcp_client.process_query(request.query)
        
        # Add tracing if requested
        if request.include_tracing and tracer:
            with tracer.trace("api_query") as span:
                span.set_attribute("query", request.query)
                span.set_attribute("tools_used", result.get("tools_used", []))
                span.set_attribute("response_type", result.get("type", "unknown"))
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.get("/tools")
async def get_available_tools():
    """Get list of available MCP tools."""
    try:
        if not mcp_client:
            raise HTTPException(status_code=500, detail="MCP client not initialized")
        
        tools = await mcp_client.get_available_tools()
        return {
            "tools": tools,
            "count": len(tools),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tools: {str(e)}")

@app.get("/resources")
async def get_available_resources():
    """Get list of available MCP resources."""
    try:
        if not mcp_server:
            raise HTTPException(status_code=500, detail="MCP server not initialized")
        
        resources = [
            {
                "uri": "audit://policies/aml",
                "name": "AML Policies",
                "description": "Anti-Money Laundering policies and rules"
            },
            {
                "uri": "audit://policies/compliance",
                "name": "Compliance Rules",
                "description": "General compliance rules and regulations"
            },
            {
                "uri": "audit://schema/database",
                "name": "Database Schema",
                "description": "Database schema and table structures"
            }
        ]
        
        return {
            "resources": resources,
            "count": len(resources),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting resources: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get resources: {str(e)}")

@app.get("/data/transactions")
async def get_transactions(limit: int = 100, country: str = None, risk_category: str = None):
    """Get transactions data (direct database access for testing)."""
    try:
        db_manager = get_db_manager()
        filters = {}
        
        if country:
            filters["country"] = country
        if risk_category:
            filters["risk_category"] = risk_category
        
        transactions = db_manager.get_transactions(**filters)
        limited_transactions = transactions[:limit]
        
        return {
            "transactions": limited_transactions,
            "total_count": len(transactions),
            "returned_count": len(limited_transactions),
            "filters": filters,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get transactions: {str(e)}")

@app.get("/data/suppliers")
async def get_suppliers():
    """Get suppliers data (direct database access for testing)."""
    try:
        db_manager = get_db_manager()
        suppliers = db_manager.get_suppliers()
        
        return {
            "suppliers": suppliers,
            "count": len(suppliers),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting suppliers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suppliers: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )