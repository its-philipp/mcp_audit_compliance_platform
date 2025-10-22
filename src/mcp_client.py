"""
MCP Client for Audit & Compliance Platform
Integrates with GPT-4 to provide intelligent audit and compliance analysis.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from mcp.client.session import ClientSession
from mcp.types import Tool, TextContent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from .mcp_server import get_mcp_server
from .tracing import LangfuseTracer

logger = logging.getLogger(__name__)

class AuditComplianceMCPClient:
    """MCP Client that integrates GPT-4 with audit and compliance tools."""
    
    def __init__(self, openai_api_key: str, mcp_server_url: str = "http://localhost:8000"):
        self.openai_api_key = openai_api_key
        self.mcp_server_url = mcp_server_url
        self.llm = ChatOpenAI(
            model="gpt-4",
            api_key=openai_api_key,
            temperature=0.1
        )
        self.tracer = LangfuseTracer()
        self.mcp_server = get_mcp_server()
        self.available_tools = {}
        self._setup_prompt_template()
    
    def _setup_prompt_template(self):
        """Setup the prompt template for MCP tool integration."""
        self.prompt_template = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an AI assistant specialized in audit and compliance analysis. 
You have access to several tools through the Model Context Protocol (MCP):

1. query_financial_data - Query financial transactions, revenue, expenses, and assets
2. validate_compliance - Validate transactions against AML policies and compliance rules
3. generate_audit_report - Generate comprehensive audit reports with violations and recommendations
4. check_compliance_status - Check overall compliance status and identify violations
5. get_audit_trail - Retrieve audit trail and compliance history

When a user asks about financial data, compliance, or audit reports, you should:
1. Use the appropriate MCP tools to gather data
2. Analyze the results intelligently
3. Provide comprehensive insights and recommendations
4. Always explain what tools you used and why

Be thorough in your analysis and provide actionable insights."""),
            HumanMessage(content="{user_query}")
        ])
    
    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process user query using MCP tools and GPT-4."""
        try:
            with self.tracer.trace("mcp_client_process_query") as span:
                span.set_attribute("user_query", user_query)
                
                # Determine which tools to use based on the query
                tools_to_use = self._determine_tools_needed(user_query)
                
                # Execute tools and collect results
                tool_results = {}
                for tool_name, tool_params in tools_to_use.items():
                    try:
                        result = await self._execute_tool(tool_name, tool_params, tool_results)
                        tool_results[tool_name] = result
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        tool_results[tool_name] = {"error": str(e)}
                
                # Use GPT-4 to synthesize the results
                synthesis_prompt = self._create_synthesis_prompt(user_query, tool_results)
                
                # Use a simple approach with the LLM
                try:
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: self.llm.invoke(synthesis_prompt)
                    )
                    
                    final_answer = response.content if hasattr(response, 'content') else str(response)
                    
                    # If the response is empty or None, provide a fallback
                    if not final_answer or final_answer.strip() == "":
                        final_answer = f"Based on the analysis of {len(tool_results)} MCP tools, I found relevant data for your query: '{user_query}'. The tools executed successfully and returned data, but I need to provide a more detailed analysis. Please check the tool results for specific findings."
                        
                except Exception as e:
                    logger.error(f"Error with LLM: {e}")
                    final_answer = f"Analysis completed for query: '{user_query}'. MCP tools executed successfully. Error in AI synthesis: {str(e)}"
                
                return {
                    "type": "mcp_response",
                    "query": user_query,
                    "response": final_answer,
                    "tools_used": list(tools_to_use.keys()),
                    "tool_results": tool_results,
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "model": "gpt-4",
                        "mcp_enabled": True
                    }
                }
                
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "type": "error",
                "query": user_query,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _determine_tools_needed(self, user_query: str) -> Dict[str, Dict[str, Any]]:
        """Determine which MCP tools are needed based on the user query."""
        user_query_lower = user_query.lower()
        tools_to_use = {}
        
        # Check for financial data queries
        if any(keyword in user_query_lower for keyword in [
            "transaction", "revenue", "expense", "asset", "financial", "money", 
            "amount", "eur", "usd", "currency", "supplier", "payment"
        ]):
            tools_to_use["query_financial_data"] = self._parse_financial_query(user_query)
        
        # Check for compliance validation
        if any(keyword in user_query_lower for keyword in [
            "compliance", "aml", "policy", "violation", "rule", "regulation",
            "validate", "check", "monitor"
        ]):
            if "query_financial_data" not in tools_to_use:
                # If we need compliance validation, we likely need financial data first
                tools_to_use["query_financial_data"] = {"query_type": "transactions", "limit": 100}
            
            tools_to_use["validate_compliance"] = {
                "policy_type": "aml" if "aml" in user_query_lower else "compliance"
            }
        
        # Check for audit report requests
        if any(keyword in user_query_lower for keyword in [
            "report", "audit", "summary", "analysis", "overview"
        ]):
            tools_to_use["generate_audit_report"] = self._parse_report_query(user_query)
        
        # Check for compliance status
        if any(keyword in user_query_lower for keyword in [
            "status", "compliant", "non-compliant", "overall", "check compliance", "compliance status"
        ]):
            tools_to_use["check_compliance_status"] = {
                "scope": "all",
                "severity_threshold": "medium"
            }
        
        # Check for audit trail requests
        if any(keyword in user_query_lower for keyword in [
            "trail", "history", "log", "track", "audit trail", "violations in the last"
        ]):
            tools_to_use["get_audit_trail"] = {
                "entity_type": "transaction"
            }
        
        return tools_to_use
    
    def _parse_financial_query(self, user_query: str) -> Dict[str, Any]:
        """Parse financial query parameters."""
        user_query_lower = user_query.lower()
        
        # Determine query type
        if any(word in user_query_lower for word in ["transaction", "payment", "invoice", "supplier"]):
            query_type = "transactions"
        elif any(word in user_query_lower for word in ["revenue", "income", "sales"]):
            query_type = "revenue"
        elif any(word in user_query_lower for word in ["expense", "cost", "expenditure"]):
            query_type = "expenses"
        elif any(word in user_query_lower for word in ["asset", "property", "equipment"]):
            query_type = "assets"
        else:
            query_type = "transactions"
        
        # Parse filters
        filters = {}
        
        # Amount filters
        if "under" in user_query_lower or "below" in user_query_lower:
            # Look for amount patterns like "under €5,000" or "below $10,000"
            import re
            amount_match = re.search(r'(?:under|below)\s*[€$]?([\d,]+)', user_query_lower)
            if amount_match:
                amount = float(amount_match.group(1).replace(',', ''))
                filters["max_amount"] = amount
        
        if "over" in user_query_lower or "above" in user_query_lower:
            amount_match = re.search(r'(?:over|above)\s*[€$]?([\d,]+)', user_query_lower)
            if amount_match:
                amount = float(amount_match.group(1).replace(',', ''))
                filters["min_amount"] = amount
        
        # Country filters
        country_mapping = {
            "usa": "USA", "united states": "USA", "america": "USA",
            "russia": "Russia", "russian": "Russia",
            "germany": "Germany", "german": "Germany",
            "france": "France", "french": "France",
            "china": "China", "chinese": "China",
            "japan": "Japan", "japanese": "Japan",
            "uk": "UK", "united kingdom": "UK", "britain": "UK",
            "canada": "Canada", "canadian": "Canada",
            "australia": "Australia", "australian": "Australia"
        }
        
        for country_key, country_value in country_mapping.items():
            if country_key in user_query_lower:
                filters["country"] = country_value
                break
        
        # Risk category filters
        if "low risk" in user_query_lower:
            filters["risk_category"] = "LOW"
        elif "high risk" in user_query_lower:
            filters["risk_category"] = "HIGH"
        elif "medium risk" in user_query_lower:
            filters["risk_category"] = "MEDIUM"
        elif "pep" in user_query_lower:
            filters["risk_category"] = "PEP"
        
        # Payment method filters
        if "cash" in user_query_lower:
            filters["payment_method"] = "CASH"
        elif "check" in user_query_lower:
            filters["payment_method"] = "CHECK"
        elif "wire" in user_query_lower:
            filters["payment_method"] = "WIRE"
        elif "card" in user_query_lower:
            filters["payment_method"] = "CARD"
        
        return {
            "query_type": query_type,
            "filters": filters,
            "limit": 100
        }
    
    def _parse_report_query(self, user_query: str) -> Dict[str, Any]:
        """Parse report query parameters."""
        user_query_lower = user_query.lower()
        
        # Determine report type
        if "aml" in user_query_lower:
            report_type = "aml"
        elif "financial" in user_query_lower:
            report_type = "financial"
        elif "risk" in user_query_lower:
            report_type = "risk"
        else:
            report_type = "compliance"
        
        # Parse period
        period = None
        if "last 30 days" in user_query_lower or "past month" in user_query_lower:
            period = "last_30_days"
        elif "last quarter" in user_query_lower or "q4" in user_query_lower:
            period = "last_quarter"
        elif "2024" in user_query_lower:
            period = "2024"
        
        return {
            "report_type": report_type,
            "period": period,
            "include_recommendations": True
        }
    
    async def _execute_tool(self, tool_name: str, tool_params: Dict[str, Any], previous_results: Dict[str, Any] = None) -> Any:
        """Execute an MCP tool."""
        try:
            if tool_name == "query_financial_data":
                return await self.mcp_server._query_financial_data(**tool_params)
            elif tool_name == "validate_compliance":
                # For compliance validation, use transactions from previous query_financial_data if available
                if "transactions" not in tool_params and previous_results and "query_financial_data" in previous_results:
                    try:
                        financial_data = json.loads(previous_results["query_financial_data"])
                        transactions = financial_data.get("data", [])
                        tool_params["transactions"] = transactions
                    except Exception as e:
                        logger.error(f"Error parsing financial data for validate_compliance: {e}")
                        # Fallback to getting all transactions
                        financial_result = await self.mcp_server._query_financial_data(
                            query_type="transactions", 
                            limit=100
                        )
                        financial_data = json.loads(financial_result)
                        tool_params["transactions"] = financial_data.get("data", [])
                elif "transactions" not in tool_params:
                    # Fallback to getting all transactions
                    financial_result = await self.mcp_server._query_financial_data(
                        query_type="transactions", 
                        limit=100
                    )
                    financial_data = json.loads(financial_result)
                    tool_params["transactions"] = financial_data.get("data", [])
                
                return await self.mcp_server._validate_compliance(**tool_params)
            elif tool_name == "generate_audit_report":
                return await self.mcp_server._generate_audit_report(**tool_params)
            elif tool_name == "check_compliance_status":
                return await self.mcp_server._check_compliance_status(**tool_params)
            elif tool_name == "get_audit_trail":
                return await self.mcp_server._get_audit_trail(**tool_params)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}
    
    def _create_synthesis_prompt(self, user_query: str, tool_results: Dict[str, Any]) -> str:
        """Create a synthesis prompt for GPT-4."""
        prompt = f"""Analyze this audit data for query: "{user_query}"

Data:
"""
        
        for tool_name, result in tool_results.items():
            prompt += f"\n{tool_name.upper()}:\n"
            if isinstance(result, str):
                try:
                    parsed_result = json.loads(result)
                    
                    # Create a summary instead of full data
                    if isinstance(parsed_result, dict):
                        summary = {}
                        for key, value in parsed_result.items():
                            if key == 'data' and isinstance(value, list):
                                summary[key] = f"{len(value)} items"
                                if len(value) > 0:
                                    summary['sample'] = value[0] if len(value) > 0 else None
                            elif key in ['total_count', 'returned_count', 'type', 'timestamp', 'violations_found', 'total_transactions', 'compliance_status']:
                                summary[key] = value
                            elif isinstance(value, (str, int, float, bool)):
                                summary[key] = value
                        
                        prompt += json.dumps(summary, indent=1)
                    else:
                        prompt += json.dumps(parsed_result, indent=1)
                except:
                    # Truncate string results
                    prompt += result[:500] + "..." if len(result) > 500 else result
            else:
                prompt += json.dumps(result, indent=1)
        
        prompt += f"""

Provide analysis:
1. Summary of findings (use exact numbers from data)
2. Compliance violations (use exact violation count)
3. Key insights
4. Recommendations
5. Overall status (use exact compliance status)

IMPORTANT: Use only the exact numbers and data provided above. Do not make assumptions or use previous data."""
        
        return prompt
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools."""
        return [
            {
                "name": "query_financial_data",
                "description": "Query financial transactions, revenue, expenses, and assets",
                "parameters": ["query_type", "filters", "limit"]
            },
            {
                "name": "validate_compliance",
                "description": "Validate transactions against AML policies and compliance rules",
                "parameters": ["transactions", "policy_type"]
            },
            {
                "name": "generate_audit_report",
                "description": "Generate comprehensive audit reports with violations and recommendations",
                "parameters": ["report_type", "period", "include_recommendations"]
            },
            {
                "name": "check_compliance_status",
                "description": "Check overall compliance status and identify violations",
                "parameters": ["scope", "severity_threshold"]
            },
            {
                "name": "get_audit_trail",
                "description": "Retrieve audit trail and compliance history",
                "parameters": ["entity_type", "entity_id", "start_date", "end_date"]
            }
        ]

# Global MCP client instance
mcp_client = None

def get_mcp_client(openai_api_key: str) -> AuditComplianceMCPClient:
    """Get the global MCP client instance."""
    global mcp_client
    if mcp_client is None:
        mcp_client = AuditComplianceMCPClient(openai_api_key)
    return mcp_client