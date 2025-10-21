"""
Langfuse integration for observability and tracing.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError as e:
    LANGFUSE_AVAILABLE = False
    print(f"Langfuse import error: {e}")

class LangfuseTracer:
    """Langfuse tracing wrapper for the A2A agent network."""
    
    def __init__(self):
        self.enabled = False
        self.langfuse = None
        
        if LANGFUSE_AVAILABLE:
            # Check for Langfuse credentials
            public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            
            if public_key and secret_key:
                try:
                    self.langfuse = Langfuse(
                        public_key=public_key,
                        secret_key=secret_key,
                        host=host
                    )
                    self.enabled = True
                    print("✅ Langfuse tracing enabled")
                except Exception as e:
                    print(f"❌ Failed to initialize Langfuse: {e}")
            else:
                print("⚠️ Langfuse credentials not found. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
        else:
            print("⚠️ Langfuse not installed. Tracing disabled.")
    
    def trace_agent_execution(self, agent_name: str, query: str, response: Any, 
                             execution_time: float, metadata: Dict[str, Any] = None):
        """Trace agent execution."""
        if not self.enabled or not self.langfuse:
            return
        
        try:
            trace = self.langfuse.trace(
                name=f"{agent_name}_execution",
                input=query,
                output=response,
                metadata={
                    "agent_name": agent_name,
                    "execution_time": execution_time,
                    "timestamp": datetime.utcnow().isoformat(),
                    **(metadata or {})
                }
            )
            
            # Add spans for different phases
            trace.span(
                name="query_parsing",
                input=query,
                output={"parsed_query": query, "agent": agent_name}
            )
            
            trace.span(
                name="response_generation",
                input={"query": query},
                output=response
            )
            
            trace.update(
                output=response,
                metadata={
                    "execution_time": execution_time,
                    "status": "completed"
                }
            )
            
        except Exception as e:
            print(f"Error tracing agent execution: {e}")
    
    def trace_orchestration(self, query: str, agents_used: List[str], 
                           final_response: Any, execution_time: float):
        """Trace orchestration workflow."""
        if not self.enabled or not self.langfuse:
            return
        
        try:
            trace = self.langfuse.trace(
                name="orchestration_workflow",
                input=query,
                output=final_response,
                metadata={
                    "agents_used": agents_used,
                    "execution_time": execution_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Add spans for each agent interaction
            for agent in agents_used:
                trace.span(
                    name=f"{agent}_interaction",
                    input={"query": query},
                    output={"agent_consulted": agent}
                )
            
            trace.update(
                output=final_response,
                metadata={
                    "total_agents": len(agents_used),
                    "execution_time": execution_time,
                    "status": "completed"
                }
            )
            
        except Exception as e:
            print(f"Error tracing orchestration: {e}")
    
    def trace_audit_process(self, audit_query: str, transactions_analyzed: int,
                           violations_found: int, compliance_status: str,
                           execution_time: float, audit_trail: List[str]):
        """Trace complete audit process."""
        if not self.enabled or not self.langfuse:
            return
        
        try:
            trace = self.langfuse.trace(
                name="audit_process",
                input=audit_query,
                output={
                    "transactions_analyzed": transactions_analyzed,
                    "violations_found": violations_found,
                    "compliance_status": compliance_status,
                    "audit_trail": audit_trail
                },
                metadata={
                    "execution_time": execution_time,
                    "timestamp": datetime.utcnow().isoformat(),
                    "audit_type": "compliance_check"
                }
            )
            
            # Add spans for different audit phases
            trace.span(
                name="data_retrieval",
                input={"query": audit_query},
                output={"transactions_retrieved": transactions_analyzed}
            )
            
            trace.span(
                name="compliance_validation",
                input={"transactions": transactions_analyzed},
                output={"violations_found": violations_found}
            )
            
            trace.span(
                name="report_generation",
                input={"violations": violations_found},
                output={"compliance_status": compliance_status}
            )
            
            trace.update(
                metadata={
                    "execution_time": execution_time,
                    "status": "completed",
                    "compliance_status": compliance_status
                }
            )
            
        except Exception as e:
            print(f"Error tracing audit process: {e}")

# Global tracer instance
tracer = LangfuseTracer()

def get_tracer() -> LangfuseTracer:
    """Get the global tracer instance."""
    return tracer

def is_langfuse_enabled() -> bool:
    """Check if Langfuse tracing is enabled."""
    return tracer.enabled
