"""
Financial Data Agent using Google A2A framework.

This agent handles secure access to financial data and provides
data retrieval and analysis capabilities.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.events import Event

from .base import BaseAuditAgent
from ..database import get_db_manager


class FinancialDataAgent(BaseAuditAgent):
    """
    Agent responsible for financial data access and analysis.
    
    Capabilities:
    - Retrieve financial data from various sources
    - Perform data analysis and calculations
    - Generate financial reports
    - Validate data integrity
    """
    
    def __init__(self):
        super().__init__("financial-data-agent", "1.0.0")
        self.db_manager = get_db_manager()
        
        # Mock financial data for demonstration
        self.financial_data = {
            "revenue": {
                "2024": {"Q1": 1500000, "Q2": 1600000, "Q3": 1700000, "Q4": 1800000},
                "2023": {"Q1": 1400000, "Q2": 1450000, "Q3": 1500000, "Q4": 1550000}
            },
            "expenses": {
                "2024": {"Q1": 1200000, "Q2": 1250000, "Q3": 1300000, "Q4": 1350000},
                "2023": {"Q1": 1150000, "Q2": 1180000, "Q3": 1200000, "Q4": 1220000}
            },
            "assets": {
                "2024": {"total": 5000000, "current": 2000000, "fixed": 3000000},
                "2023": {"total": 4800000, "current": 1900000, "fixed": 2900000}
            }
        }
    
    async def _process_request(self, context: RequestContext) -> Any:
        """
        Process financial data requests.
        
        Args:
            context: Request context containing the query
            
        Returns:
            Financial data or analysis results
        """
        user_input = context.get_user_input()
        self.logger.info(f"Processing financial data request: {user_input}")
        
        # Parse the request to determine what data is needed
        request_type = self._parse_request_type(user_input)
        
        if request_type == "revenue":
            return await self._get_revenue_data(user_input)
        elif request_type == "expenses":
            return await self._get_expenses_data(user_input)
        elif request_type == "assets":
            return await self._get_assets_data(user_input)
        elif request_type == "analysis":
            return await self._perform_analysis(user_input)
        elif request_type == "report":
            return await self._generate_report(user_input)
        elif request_type == "transactions":
            return await self._get_transactions(user_input)
        else:
            return await self._get_all_data()
    
    def _parse_request_type(self, user_input: str) -> str:
        """
        Parse the user input to determine the type of request.
        
        Args:
            user_input: Natural language input from user
            
        Returns:
            Type of request (revenue, expenses, assets, analysis, report, transactions)
        """
        user_input_lower = user_input.lower()
        
        # Prioritize transaction keywords first
        if any(word in user_input_lower for word in ["transaction", "payment", "invoice", "supplier", "eur", "usd", "currency", "amount"]):
            return "transactions"
        elif any(word in user_input_lower for word in ["revenue", "income", "sales"]):
            return "revenue"
        elif any(word in user_input_lower for word in ["expense", "cost", "spending"]):
            return "expenses"
        elif any(word in user_input_lower for word in ["asset", "property", "equipment"]):
            return "assets"
        elif any(word in user_input_lower for word in ["analyze", "analysis", "calculate", "compare"]):
            return "analysis"
        elif any(word in user_input_lower for word in ["report", "summary", "overview"]):
            return "report"
        else:
            return "all"
    
    async def _get_transactions(self, user_input: str) -> Dict[str, Any]:
        """Get transaction data based on user input."""
        # Parse filters from user input
        filters = self._parse_transaction_filters(user_input)
        
        transactions = self.db_manager.get_transactions(**filters)
        
        # Convert to serializable format (limit to first 10 transactions for API response)
        transaction_data = []
        total_amount = 0
        transaction_count = 0
        
        for txn in transactions:
            if transaction_count < 10:  # Limit to first 10 transactions
                transaction_data.append({
                    "transaction_id": txn.transaction_id,
                    "supplier_name": txn.supplier_name,
                    "supplier_country": txn.supplier_country,
                    "amount": txn.amount,
                    "currency": txn.currency,
                    "transaction_date": txn.transaction_date.isoformat(),
                    "payment_method": txn.payment_method,
                    "risk_category": txn.risk_category,
                    "description": txn.description
                })
            total_amount += txn.amount
            transaction_count += 1
        
        return {
            "type": "transaction_data",
            "transactions": transaction_data,
            "summary": {
                "total_transactions": transaction_count,
                "displayed_transactions": len(transaction_data),
                "total_amount": round(total_amount, 2),
                "average_amount": round(total_amount / transaction_count, 2) if transaction_count > 0 else 0,
                "filters_applied": filters,
                "note": f"Showing first 10 of {transaction_count} transactions" if transaction_count > 10 else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _parse_transaction_filters(self, user_input: str) -> Dict[str, Any]:
        """Parse transaction filters from user input."""
        filters = {}
        user_input_lower = user_input.lower()
        
        # Parse amount filters
        if "over" in user_input_lower or "above" in user_input_lower:
            # Extract amount after "over" or "above"
            words = user_input_lower.split()
            for i, word in enumerate(words):
                if word in ["over", "above"] and i + 1 < len(words):
                    try:
                        amount_str = words[i + 1].replace("€", "").replace(",", "").replace("k", "000")
                        filters["min_amount"] = float(amount_str)
                    except:
                        pass
        
        if "under" in user_input_lower or "below" in user_input_lower:
            words = user_input_lower.split()
            for i, word in enumerate(words):
                if word in ["under", "below"] and i + 1 < len(words):
                    try:
                        amount_str = words[i + 1].replace("€", "").replace(",", "").replace("k", "000")
                        filters["max_amount"] = float(amount_str)
                    except:
                        pass
        
        # Parse country filters
        country_mapping = {
            "usa": "USA", "russia": "Russia", "germany": "Germany", 
            "france": "France", "uk": "UK", "canada": "Canada", 
            "australia": "Australia", "japan": "Japan", "north korea": "North Korea",
            "iran": "Iran", "syria": "Syria", "sudan": "Sudan", "cuba": "Cuba",
            "afghanistan": "Afghanistan", "myanmar": "Myanmar", "belarus": "Belarus",
            "venezuela": "Venezuela", "netherlands": "Netherlands", "sweden": "Sweden",
            "norway": "Norway", "switzerland": "Switzerland"
        }
        for country_key, country_value in country_mapping.items():
            if country_key in user_input_lower:
                filters["country"] = country_value
                break
        
        # Parse risk category
        if "low risk" in user_input_lower:
            filters["risk_category"] = "LOW"
        elif "medium risk" in user_input_lower:
            filters["risk_category"] = "MEDIUM"
        elif "high risk" in user_input_lower:
            filters["risk_category"] = "HIGH"
        
        # Parse supplier name
        if "supplier" in user_input_lower:
            # Try to extract supplier name
            words = user_input_lower.split()
            for i, word in enumerate(words):
                if word == "supplier" and i + 1 < len(words):
                    filters["supplier_name"] = words[i + 1]
                    break
        
        return filters
    
    async def _get_revenue_data(self, user_input: str) -> Dict[str, Any]:
        """Get revenue data based on user input."""
        # Get transactions from database and calculate revenue
        transactions = self.db_manager.get_transactions()
        
        # Group by year and quarter
        revenue_data = {}
        for txn in transactions:
            year = txn.transaction_date.year
            quarter = f"Q{(txn.transaction_date.month - 1) // 3 + 1}"
            
            if year not in revenue_data:
                revenue_data[year] = {}
            if quarter not in revenue_data[year]:
                revenue_data[year][quarter] = 0
            
            revenue_data[year][quarter] += txn.amount
        
        return {
            "type": "revenue_data",
            "data": revenue_data,
            "summary": {
                "total_2024": sum(revenue_data.get(2024, {}).values()) if 2024 in revenue_data else 0,
                "total_2023": sum(revenue_data.get(2023, {}).values()) if 2023 in revenue_data else 0,
                "growth_rate": self._calculate_growth_rate(
                    sum(revenue_data.get(2023, {}).values()) if 2023 in revenue_data else 0,
                    sum(revenue_data.get(2024, {}).values()) if 2024 in revenue_data else 0
                )
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_expenses_data(self, user_input: str) -> Dict[str, Any]:
        """Get expenses data based on user input."""
        return {
            "type": "expenses_data",
            "data": self.financial_data["expenses"],
            "summary": {
                "total_2024": sum(self.financial_data["expenses"]["2024"].values()),
                "total_2023": sum(self.financial_data["expenses"]["2023"].values()),
                "growth_rate": self._calculate_growth_rate(
                    sum(self.financial_data["expenses"]["2023"].values()),
                    sum(self.financial_data["expenses"]["2024"].values())
                )
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_assets_data(self, user_input: str) -> Dict[str, Any]:
        """Get assets data based on user input."""
        return {
            "type": "assets_data",
            "data": self.financial_data["assets"],
            "summary": {
                "total_2024": self.financial_data["assets"]["2024"]["total"],
                "total_2023": self.financial_data["assets"]["2023"]["total"],
                "growth_rate": self._calculate_growth_rate(
                    self.financial_data["assets"]["2023"]["total"],
                    self.financial_data["assets"]["2024"]["total"]
                )
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _perform_analysis(self, user_input: str) -> Dict[str, Any]:
        """Perform financial analysis based on user input."""
        revenue_2024 = sum(self.financial_data["revenue"]["2024"].values())
        expenses_2024 = sum(self.financial_data["expenses"]["2024"].values())
        revenue_2023 = sum(self.financial_data["revenue"]["2023"].values())
        expenses_2023 = sum(self.financial_data["expenses"]["2023"].values())
        
        profit_2024 = revenue_2024 - expenses_2024
        profit_2023 = revenue_2023 - expenses_2023
        
        return {
            "type": "financial_analysis",
            "analysis": {
                "profitability": {
                    "2024": {
                        "revenue": revenue_2024,
                        "expenses": expenses_2024,
                        "profit": profit_2024,
                        "profit_margin": (profit_2024 / revenue_2024) * 100
                    },
                    "2023": {
                        "revenue": revenue_2023,
                        "expenses": expenses_2023,
                        "profit": profit_2023,
                        "profit_margin": (profit_2023 / revenue_2023) * 100
                    }
                },
                "growth_metrics": {
                    "revenue_growth": self._calculate_growth_rate(revenue_2023, revenue_2024),
                    "expense_growth": self._calculate_growth_rate(expenses_2023, expenses_2024),
                    "profit_growth": self._calculate_growth_rate(profit_2023, profit_2024)
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_report(self, user_input: str) -> Dict[str, Any]:
        """Generate a comprehensive financial report."""
        analysis = await self._perform_analysis(user_input)
        
        return {
            "type": "financial_report",
            "report": {
                "executive_summary": {
                    "total_revenue_2024": sum(self.financial_data["revenue"]["2024"].values()),
                    "total_expenses_2024": sum(self.financial_data["expenses"]["2024"].values()),
                    "net_profit_2024": analysis["analysis"]["profitability"]["2024"]["profit"],
                    "profit_margin_2024": analysis["analysis"]["profitability"]["2024"]["profit_margin"]
                },
                "detailed_analysis": analysis["analysis"],
                "recommendations": [
                    "Monitor expense growth to maintain profitability",
                    "Consider revenue diversification strategies",
                    "Review asset allocation for optimal returns"
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_all_data(self) -> Dict[str, Any]:
        """Get all available financial data."""
        return {
            "type": "complete_financial_data",
            "data": self.financial_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_growth_rate(self, old_value: float, new_value: float) -> float:
        """Calculate growth rate between two values."""
        if old_value == 0:
            return 0.0
        return ((new_value - old_value) / old_value) * 100
    
    def _get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of the financial data agent."""
        return {
            "input_types": ["text", "json"],
            "output_types": ["text", "json"],
            "supported_operations": [
                "get_revenue_data",
                "get_expenses_data", 
                "get_assets_data",
                "perform_financial_analysis",
                "generate_financial_report",
                "get_all_financial_data"
            ],
            "data_sources": [
                "revenue_data",
                "expense_data",
                "asset_data"
            ],
            "analysis_types": [
                "profitability_analysis",
                "growth_analysis",
                "trend_analysis"
            ]
        }
    
    def _get_endpoints(self) -> Dict[str, Any]:
        """Get the endpoints this agent exposes."""
        return {
            "execute": {
                "method": "POST",
                "description": "Execute financial data operations",
                "parameters": {
                    "query": "Natural language query for financial data"
                }
            },
            "cancel": {
                "method": "POST",
                "description": "Cancel ongoing financial data operation"
            }
        }
