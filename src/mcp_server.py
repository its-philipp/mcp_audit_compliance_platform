"""
MCP Server for Audit & Compliance Platform
Provides tools for financial data queries, policy validation, and audit reporting.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from mcp.server import FastMCP
from mcp.types import Tool, TextContent, Resource
from pydantic import BaseModel

from .database import get_db_manager
from .tracing import LangfuseTracer

logger = logging.getLogger(__name__)

class FinancialQueryRequest(BaseModel):
    query_type: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 100

class ComplianceValidationRequest(BaseModel):
    transactions: List[Dict[str, Any]]
    policy_type: str

class AuditReportRequest(BaseModel):
    report_type: str
    period: Optional[str] = None
    include_recommendations: bool = True

class AuditComplianceMCPServer:
    """MCP Server providing audit and compliance tools."""
    
    def __init__(self):
        self.server = FastMCP(
            name="audit-compliance-mcp",
            instructions="Audit and compliance analysis tools for financial data and AML policy validation"
        )
        self.db_manager = get_db_manager()
        self.tracer = LangfuseTracer()
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self):
        """Register all MCP tools."""
        
        # Financial Data Tool
        self.server.add_tool(
            self._query_financial_data,
            name="query_financial_data",
            description="Query financial transactions, revenue, expenses, and assets from the database"
        )
        
        # Policy Engine Tool
        self.server.add_tool(
            self._validate_compliance,
            name="validate_compliance",
            description="Validate transactions against AML policies and compliance rules"
        )
        
        # Report Generation Tool
        self.server.add_tool(
            self._generate_audit_report,
            name="generate_audit_report",
            description="Generate comprehensive audit reports with violations and recommendations"
        )
        
        # Compliance Check Tool
        self.server.add_tool(
            self._check_compliance_status,
            name="check_compliance_status",
            description="Check overall compliance status and identify violations"
        )
        
        # Audit Trail Tool
        self.server.add_tool(
            self._get_audit_trail,
            name="get_audit_trail",
            description="Retrieve audit trail and compliance history"
        )
    
    def _register_resources(self):
        """Register MCP resources."""
        
        # AML Policies Resource
        @self.server.resource(
            uri="audit://policies/aml",
            name="AML Policies",
            description="Anti-Money Laundering policies and rules",
            mime_type="application/json"
        )
        def get_aml_policies() -> str:
            return self._get_aml_policies()
        
        # Compliance Rules Resource
        @self.server.resource(
            uri="audit://policies/compliance",
            name="Compliance Rules",
            description="General compliance rules and regulations",
            mime_type="application/json"
        )
        def get_compliance_rules() -> str:
            return self._get_compliance_rules()
        
        # Database Schema Resource
        @self.server.resource(
            uri="audit://schema/database",
            name="Database Schema",
            description="Database schema and table structures",
            mime_type="application/json"
        )
        def get_database_schema() -> str:
            return self._get_database_schema()
    
    async def _query_financial_data(self, query_type: str, filters: Dict[str, Any] = None, limit: int = 100) -> str:
        """Query financial data using the database manager."""
        try:
            with self.tracer.trace("mcp_query_financial_data") as span:
                span.set_attribute("query_type", query_type)
                span.set_attribute("filters", str(filters))
                span.set_attribute("limit", limit)
                
                if query_type == "transactions":
                    transactions = self.db_manager.get_transactions(**(filters or {}))
                    # Limit results for API response
                    limited_transactions = transactions[:limit]
                    
                    result = {
                        "type": "transactions",
                        "total_count": len(transactions),
                        "returned_count": len(limited_transactions),
                        "data": limited_transactions,
                        "filters_applied": filters or {},
                        "timestamp": datetime.now().isoformat()
                    }
                    
                elif query_type == "suppliers":
                    suppliers = self.db_manager.get_suppliers()
                    limited_suppliers = suppliers[:limit]
                    
                    result = {
                        "type": "suppliers",
                        "total_count": len(suppliers),
                        "returned_count": len(limited_suppliers),
                        "data": limited_suppliers,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                else:
                    # Mock data for other query types
                    result = {
                        "type": query_type,
                        "data": self._get_mock_financial_data(query_type),
                        "timestamp": datetime.now().isoformat()
                    }
                
                return json.dumps(result, indent=2)
                
        except Exception as e:
            logger.error(f"Error querying financial data: {e}")
            return json.dumps({
                "error": f"Failed to query financial data: {str(e)}",
                "type": query_type,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _validate_compliance(self, transactions: List[Dict[str, Any]], policy_type: str) -> str:
        """Validate transactions against compliance policies."""
        try:
            with self.tracer.trace("mcp_validate_compliance") as span:
                span.set_attribute("policy_type", policy_type)
                span.set_attribute("transaction_count", len(transactions))
                
                violations = []
                
                if policy_type == "aml":
                    violations = self._check_aml_compliance(transactions)
                elif policy_type == "financial":
                    violations = self._check_financial_compliance(transactions)
                elif policy_type == "regulatory":
                    violations = self._check_regulatory_compliance(transactions)
                
                result = {
                    "type": "compliance_validation",
                    "policy_type": policy_type,
                    "transactions_checked": len(transactions),
                    "violations_found": len(violations),
                    "violations": violations,
                    "compliance_status": "PASS" if len(violations) == 0 else "FAIL",
                    "timestamp": datetime.now().isoformat()
                }
                
                return json.dumps(result, indent=2)
                
        except Exception as e:
            logger.error(f"Error validating compliance: {e}")
            return json.dumps({
                "error": f"Failed to validate compliance: {str(e)}",
                "policy_type": policy_type,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _generate_audit_report(self, report_type: str, period: str = None, include_recommendations: bool = True) -> str:
        """Generate audit reports."""
        try:
            with self.tracer.trace("mcp_generate_audit_report") as span:
                span.set_attribute("report_type", report_type)
                span.set_attribute("period", period or "all")
                span.set_attribute("include_recommendations", include_recommendations)
                
                # Get relevant data based on report type
                if report_type == "compliance":
                    transactions = self.db_manager.get_transactions()
                    violations = self._check_aml_compliance(transactions)
                elif report_type == "financial":
                    transactions = self.db_manager.get_transactions()
                    violations = self._check_financial_compliance(transactions)
                elif report_type == "risk":
                    transactions = self.db_manager.get_transactions()
                    violations = self._check_risk_compliance(transactions)
                elif report_type == "aml":
                    transactions = self.db_manager.get_transactions()
                    violations = self._check_aml_compliance(transactions)
                else:
                    transactions = []
                    violations = []
                
                # Generate recommendations if requested
                recommendations = []
                if include_recommendations:
                    recommendations = self._generate_recommendations(violations)
                
                result = {
                    "type": "audit_report",
                    "report_type": report_type,
                    "period": period or "all",
                    "summary": {
                        "total_transactions": len(transactions),
                        "violations_found": len(violations),
                        "compliance_rate": f"{((len(transactions) - len(violations)) / max(len(transactions), 1) * 100):.1f}%"
                    },
                    "violations": violations,
                    "recommendations": recommendations,
                    "timestamp": datetime.now().isoformat()
                }
                
                return json.dumps(result, indent=2)
                
        except Exception as e:
            logger.error(f"Error generating audit report: {e}")
            return json.dumps({
                "error": f"Failed to generate audit report: {str(e)}",
                "report_type": report_type,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _check_compliance_status(self, scope: str, severity_threshold: str = "medium") -> str:
        """Check overall compliance status."""
        try:
            with self.tracer.trace("mcp_check_compliance_status") as span:
                span.set_attribute("scope", scope)
                span.set_attribute("severity_threshold", severity_threshold)
                
                transactions = self.db_manager.get_transactions()
                violations = self._check_aml_compliance(transactions)
                
                # Filter by severity threshold
                severity_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                threshold_level = severity_levels.get(severity_threshold, 2)
                
                filtered_violations = [
                    v for v in violations 
                    if severity_levels.get(v.get("severity", "low"), 1) >= threshold_level
                ]
                
                result = {
                    "type": "compliance_status",
                    "scope": scope,
                    "severity_threshold": severity_threshold,
                    "status": "COMPLIANT" if len(filtered_violations) == 0 else "NON_COMPLIANT",
                    "total_violations": len(filtered_violations),
                    "violations": filtered_violations,
                    "timestamp": datetime.now().isoformat()
                }
                
                return json.dumps(result, indent=2)
                
        except Exception as e:
            logger.error(f"Error checking compliance status: {e}")
            return json.dumps({
                "error": f"Failed to check compliance status: {str(e)}",
                "scope": scope,
                "timestamp": datetime.now().isoformat()
            })
    
    async def _get_audit_trail(self, entity_type: str, entity_id: str = None, start_date: str = None, end_date: str = None) -> str:
        """Retrieve audit trail."""
        try:
            with self.tracer.trace("mcp_get_audit_trail") as span:
                span.set_attribute("entity_type", entity_type)
                span.set_attribute("entity_id", entity_id or "all")
                
                # Mock audit trail data
                audit_trail = self._generate_mock_audit_trail(entity_type, entity_id, start_date, end_date)
                
                result = {
                    "type": "audit_trail",
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "entries": audit_trail,
                    "timestamp": datetime.now().isoformat()
                }
                
                return json.dumps(result, indent=2)
                
        except Exception as e:
            logger.error(f"Error getting audit trail: {e}")
            return json.dumps({
                "error": f"Failed to get audit trail: {str(e)}",
                "entity_type": entity_type,
                "timestamp": datetime.now().isoformat()
            })
    
    # Resource handlers
    async def _get_aml_policies(self) -> str:
        """Get AML policies resource."""
        policies = {
            "high_value_transaction": {
                "description": "High-value transactions require additional documentation",
                "threshold": 100000,
                "currency": "EUR",
                "rules": [
                    "Require additional documentation for transactions > €100,000",
                    "Enhanced due diligence required",
                    "Senior management approval needed"
                ],
                "severity": "high"
            },
            "ctr_threshold": {
                "description": "Currency Transaction Report requirements",
                "threshold": 5000,
                "currency": "EUR",
                "payment_methods": ["CHECK", "CASH"],
                "rules": [
                    "CTR required for cash transactions > €5,000",
                    "Check transactions > €5,000 require reporting"
                ],
                "severity": "medium"
            },
            "sar_threshold": {
                "description": "Suspicious Activity Report triggers",
                "threshold": 3000,
                "currency": "EUR",
                "risk_categories": ["HIGH", "PEP"],
                "rules": [
                    "SAR required for high-risk transactions > €3,000",
                    "PEP transactions > €3,000 require SAR"
                ],
                "severity": "high"
            },
            "pep_transaction": {
                "description": "Politically Exposed Person transaction monitoring",
                "threshold": 1000,
                "currency": "EUR",
                "rules": [
                    "Enhanced monitoring for PEP transactions",
                    "Additional documentation required",
                    "Regular review and reporting"
                ],
                "severity": "high"
            },
            "high_risk_country": {
                "description": "Transactions from high-risk countries",
                "countries": ["North Korea", "Iran", "Syria", "Sudan", "Cuba", "Russia", "Belarus"],
                "rules": [
                    "Enhanced due diligence required",
                    "Additional documentation needed",
                    "Regular monitoring and reporting"
                ],
                "severity": "critical"
            }
        }
        return json.dumps(policies, indent=2)
    
    async def _get_compliance_rules(self) -> str:
        """Get compliance rules resource."""
        rules = {
            "revenue_recognition": {
                "description": "Revenue recognition compliance",
                "rules": ["Recognize revenue when earned", "Document revenue sources"]
            },
            "expense_classification": {
                "description": "Expense classification rules",
                "rules": ["Proper expense categorization", "Documentation requirements"]
            },
            "asset_valuation": {
                "description": "Asset valuation standards",
                "rules": ["Fair value assessment", "Regular revaluation"]
            }
        }
        return json.dumps(rules, indent=2)
    
    async def _get_database_schema(self) -> str:
        """Get database schema resource."""
        schema = {
            "tables": {
                "transactions": {
                    "columns": {
                        "id": "INTEGER PRIMARY KEY",
                        "amount": "DECIMAL(15,2)",
                        "currency": "VARCHAR(3)",
                        "country": "VARCHAR(100)",
                        "supplier_name": "VARCHAR(255)",
                        "risk_category": "VARCHAR(50)",
                        "payment_method": "VARCHAR(50)",
                        "transaction_date": "DATE",
                        "created_at": "TIMESTAMP"
                    }
                },
                "suppliers": {
                    "columns": {
                        "id": "INTEGER PRIMARY KEY",
                        "name": "VARCHAR(255)",
                        "country": "VARCHAR(100)",
                        "risk_category": "VARCHAR(50)",
                        "created_at": "TIMESTAMP"
                    }
                }
            }
        }
        return json.dumps(schema, indent=2)
    
    # Helper methods
    def _get_mock_financial_data(self, query_type: str) -> Dict[str, Any]:
        """Get mock financial data."""
        if query_type == "revenue":
            return {
                "total_revenue": 2500000.00,
                "currency": "EUR",
                "period": "2024",
                "breakdown": {
                    "Q1": 600000.00,
                    "Q2": 650000.00,
                    "Q3": 700000.00,
                    "Q4": 550000.00
                }
            }
        elif query_type == "expenses":
            return {
                "total_expenses": 1800000.00,
                "currency": "EUR",
                "period": "2024",
                "categories": {
                    "operating": 1200000.00,
                    "administrative": 400000.00,
                    "compliance": 200000.00
                }
            }
        elif query_type == "assets":
            return {
                "total_assets": 5000000.00,
                "currency": "EUR",
                "as_of": "2024-12-31",
                "breakdown": {
                    "current_assets": 2000000.00,
                    "fixed_assets": 2500000.00,
                    "intangible_assets": 500000.00
                }
            }
        return {}
    
    def _check_aml_compliance(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check AML compliance for transactions."""
        violations = []
        
        for transaction in transactions:
            # High-value transaction check
            if transaction.get("amount", 0) > 100000:
                violations.append({
                    "transaction_id": transaction.get("id"),
                    "violation_type": "high_value_transaction",
                    "description": f"Transaction amount €{transaction.get('amount'):,.2f} exceeds €100,000 threshold",
                    "severity": "high",
                    "amount": transaction.get("amount"),
                    "currency": transaction.get("currency"),
                    "supplier": transaction.get("supplier_name"),
                    "country": transaction.get("country"),
                    "payment_method": transaction.get("payment_method")
                })
            
            # High-risk country check
            high_risk_countries = ["North Korea", "Iran", "Syria", "Sudan", "Cuba", "Russia", "Belarus"]
            if transaction.get("country") in high_risk_countries:
                violations.append({
                    "transaction_id": transaction.get("id"),
                    "violation_type": "high_risk_country",
                    "description": f"Transaction from high-risk country: {transaction.get('country')}",
                    "severity": "critical",
                    "amount": transaction.get("amount"),
                    "currency": transaction.get("currency"),
                    "supplier": transaction.get("supplier_name"),
                    "country": transaction.get("country"),
                    "payment_method": transaction.get("payment_method")
                })
            
            # CTR threshold check
            if transaction.get("payment_method") in ["CHECK", "CASH"] and transaction.get("amount", 0) > 5000:
                violations.append({
                    "transaction_id": transaction.get("id"),
                    "violation_type": "ctr_threshold",
                    "description": f"CTR required for {transaction.get('payment_method')} transaction €{transaction.get('amount'):,.2f}",
                    "severity": "medium",
                    "amount": transaction.get("amount"),
                    "currency": transaction.get("currency"),
                    "supplier": transaction.get("supplier_name"),
                    "country": transaction.get("country"),
                    "payment_method": transaction.get("payment_method")
                })
            
            # SAR threshold check
            if transaction.get("risk_category") in ["HIGH", "PEP"] and transaction.get("amount", 0) > 3000:
                violations.append({
                    "transaction_id": transaction.get("id"),
                    "violation_type": "sar_threshold",
                    "description": f"SAR required for {transaction.get('risk_category')} risk transaction €{transaction.get('amount'):,.2f}",
                    "severity": "high",
                    "amount": transaction.get("amount"),
                    "currency": transaction.get("currency"),
                    "supplier": transaction.get("supplier_name"),
                    "country": transaction.get("country"),
                    "payment_method": transaction.get("payment_method")
                })
        
        return violations
    
    def _check_financial_compliance(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check financial compliance."""
        violations = []
        # Add financial compliance checks here
        return violations
    
    def _check_regulatory_compliance(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check regulatory compliance."""
        violations = []
        # Add regulatory compliance checks here
        return violations
    
    def _check_risk_compliance(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check risk compliance."""
        violations = []
        # Add risk compliance checks here
        return violations
    
    def _generate_recommendations(self, violations: List[Dict[str, Any]]) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []
        
        if any(v["violation_type"] == "high_value_transaction" for v in violations):
            recommendations.append("Implement enhanced due diligence procedures for high-value transactions")
        
        if any(v["violation_type"] == "high_risk_country" for v in violations):
            recommendations.append("Establish additional monitoring for high-risk country transactions")
        
        if any(v["violation_type"] == "ctr_threshold" for v in violations):
            recommendations.append("Ensure CTR reporting procedures are properly implemented")
        
        if any(v["violation_type"] == "sar_threshold" for v in violations):
            recommendations.append("Review SAR reporting thresholds and procedures")
        
        return recommendations
    
    def _generate_mock_audit_trail(self, entity_type: str, entity_id: str = None, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Generate mock audit trail."""
        return [
            {
                "id": 1,
                "entity_type": entity_type,
                "entity_id": entity_id or "N/A",
                "action": "created",
                "user": "system",
                "timestamp": "2024-01-15T10:30:00Z",
                "details": f"{entity_type} record created"
            },
            {
                "id": 2,
                "entity_type": entity_type,
                "entity_id": entity_id or "N/A",
                "action": "updated",
                "user": "admin",
                "timestamp": "2024-01-20T14:45:00Z",
                "details": f"{entity_type} record updated"
            }
        ]

# Global MCP server instance
mcp_server = None

def get_mcp_server() -> AuditComplianceMCPServer:
    """Get the global MCP server instance."""
    global mcp_server
    if mcp_server is None:
        mcp_server = AuditComplianceMCPServer()
    return mcp_server
