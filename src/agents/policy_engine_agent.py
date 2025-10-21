"""
Policy Engine Agent using Google A2A framework.

This agent handles compliance validation, policy enforcement,
and regulatory requirements checking.
"""

import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import asyncio
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.events import Event

from .base import BaseAuditAgent


class PolicyEngineAgent(BaseAuditAgent):
    """
    Agent responsible for policy enforcement and compliance validation.
    
    Capabilities:
    - Validate financial data against compliance rules
    - Check regulatory requirements
    - Generate compliance reports
    - Provide policy recommendations
    """
    
    def __init__(self):
        super().__init__("policy-engine-agent", "1.0.0")
        
        # AML and Compliance policy rules - in production, this would connect to OPA or similar
        self.compliance_rules = {
            # AML Transaction Monitoring Rules
            "high_value_transaction": {
                "description": "High-value transactions require additional documentation",
                "threshold": 100000,
                "currency": "EUR",
                "rules": [
                    "Transactions ≥ €100,000 require additional documentation",
                    "Enhanced due diligence required for high-value transactions",
                    "Management approval required for transactions ≥ €100,000"
                ],
                "severity": "high"
            },
            "ctr_threshold": {
                "description": "Currency Transaction Report requirements",
                "threshold": 5000,
                "currency": "EUR",
                "payment_methods": ["CHECK", "CASH"],
                "rules": [
                    "Check payments ≥ €5,000 require CTR filing",
                    "Cash transactions ≥ €5,000 require CTR filing",
                    "Wire transfers are exempt from CTR requirements"
                ],
                "severity": "medium"
            },
            "sar_threshold": {
                "description": "Suspicious Activity Report triggers",
                "threshold": 3000,
                "currency": "EUR",
                "risk_categories": ["HIGH", "PEP"],
                "rules": [
                    "High-risk suppliers ≥ €3,000 trigger SAR",
                    "PEP transactions ≥ €3,000 trigger SAR",
                    "Suspicious patterns require SAR filing"
                ],
                "severity": "high"
            },
            "pep_transaction": {
                "description": "Politically Exposed Person transaction monitoring",
                "threshold": 1000,
                "currency": "EUR",
                "rules": [
                    "PEP transactions ≥ €1,000 require enhanced monitoring",
                    "Senior management approval required for PEP transactions",
                    "Additional documentation required for PEP relationships"
                ],
                "severity": "high"
            },
            "high_risk_country": {
                "description": "Transactions from high-risk countries",
                "countries": ["North Korea", "Iran", "Syria", "Sudan", "Cuba", 
                           "Afghanistan", "Myanmar", "Russia", "Belarus", "Venezuela"],
                "rules": [
                    "Transactions from sanctioned countries are prohibited",
                    "Enhanced due diligence required for high-risk countries",
                    "Management approval required for high-risk country transactions"
                ],
                "severity": "critical"
            },
            # Financial Reporting Compliance Rules
            "revenue_recognition": {
                "description": "Revenue must be recognized when earned",
                "rules": [
                    "Revenue must be recorded in the period when goods/services are delivered",
                    "Revenue must be measurable and collectible",
                    "Revenue recognition must follow GAAP principles"
                ],
                "severity": "high"
            },
            "expense_classification": {
                "description": "Expenses must be properly classified",
                "rules": [
                    "Operating expenses must be separated from capital expenditures",
                    "Expenses must be recorded in the correct accounting period",
                    "Expense classification must follow company policies"
                ],
                "severity": "medium"
            },
            "asset_valuation": {
                "description": "Assets must be valued according to accounting standards",
                "rules": [
                    "Assets must be recorded at historical cost",
                    "Asset depreciation must be calculated correctly",
                    "Asset impairment must be recognized when appropriate"
                ],
                "severity": "high"
            },
            "financial_reporting": {
                "description": "Financial reports must meet regulatory requirements",
                "rules": [
                    "Financial statements must be prepared according to GAAP",
                    "Reports must be filed within regulatory deadlines",
                    "All material transactions must be disclosed"
                ],
                "severity": "critical"
            }
        }
        
        # Regulatory requirements
        self.regulatory_requirements = {
            "sox_compliance": {
                "description": "Sarbanes-Oxley Act compliance requirements",
                "requirements": [
                    "Internal controls over financial reporting",
                    "Management assessment of internal controls",
                    "Independent auditor attestation",
                    "Disclosure controls and procedures"
                ]
            },
            "gaap_compliance": {
                "description": "Generally Accepted Accounting Principles",
                "requirements": [
                    "Revenue recognition standards",
                    "Expense matching principle",
                    "Asset valuation standards",
                    "Financial statement presentation"
                ]
            },
            "ifrs_compliance": {
                "description": "International Financial Reporting Standards",
                "requirements": [
                    "Fair value measurement",
                    "Revenue from contracts with customers",
                    "Lease accounting standards",
                    "Financial instruments standards"
                ]
            }
        }
    
    async def _process_request(self, context: RequestContext) -> Any:
        """
        Process policy and compliance requests.
        
        Args:
            context: Request context containing the query
            
        Returns:
            Policy validation results or compliance information
        """
        user_input = context.get_user_input()
        self.logger.info(f"Processing policy request: {user_input}")
        
        # Parse the request to determine what validation is needed
        request_type = self._parse_request_type(user_input)
        
        if request_type == "validate_data":
            return await self._validate_financial_data(user_input)
        elif request_type == "check_compliance":
            return await self._check_compliance(user_input)
        elif request_type == "policy_recommendations":
            return await self._get_policy_recommendations(user_input)
        elif request_type == "regulatory_check":
            return await self._check_regulatory_requirements(user_input)
        elif request_type == "compliance_report":
            return await self._generate_compliance_report(user_input)
        else:
            return await self._get_all_policies()
    
    def _parse_request_type(self, user_input: str) -> str:
        """
        Parse the user input to determine the type of request.
        
        Args:
            user_input: Natural language input from user
            
        Returns:
            Type of request (validate_data, check_compliance, etc.)
        """
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ["validate", "check", "verify", "audit"]):
            return "validate_data"
        elif any(word in user_input_lower for word in ["compliance", "compliant", "regulation"]):
            return "check_compliance"
        elif any(word in user_input_lower for word in ["recommend", "suggest", "policy"]):
            return "policy_recommendations"
        elif any(word in user_input_lower for word in ["regulatory", "sox", "gaap", "ifrs"]):
            return "regulatory_check"
        elif any(word in user_input_lower for word in ["report", "summary", "overview"]):
            return "compliance_report"
        else:
            return "all"
    
    async def _validate_financial_data(self, user_input: str) -> Dict[str, Any]:
        """Validate financial data against compliance rules."""
        # Mock validation - in production, this would analyze actual data
        validation_results = {
            "revenue_recognition": {
                "status": "compliant",
                "issues": [],
                "recommendations": ["Continue current revenue recognition practices"]
            },
            "expense_classification": {
                "status": "warning",
                "issues": ["Some expenses may need reclassification"],
                "recommendations": ["Review expense categorization quarterly"]
            },
            "asset_valuation": {
                "status": "compliant",
                "issues": [],
                "recommendations": ["Maintain current asset valuation methods"]
            },
            "financial_reporting": {
                "status": "compliant",
                "issues": [],
                "recommendations": ["Continue following GAAP standards"]
            }
        }
        
        return {
            "type": "data_validation",
            "validation_results": validation_results,
            "overall_status": "compliant",
            "summary": {
                "total_rules_checked": len(validation_results),
                "compliant_rules": sum(1 for r in validation_results.values() if r["status"] == "compliant"),
                "warning_rules": sum(1 for r in validation_results.values() if r["status"] == "warning"),
                "failed_rules": sum(1 for r in validation_results.values() if r["status"] == "failed")
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _check_compliance(self, user_input: str) -> Dict[str, Any]:
        """Check compliance against regulatory requirements."""
        compliance_status = {
            "sox_compliance": {
                "status": "compliant",
                "last_assessment": "2024-01-15",
                "next_assessment": "2024-07-15",
                "requirements_met": 4,
                "total_requirements": 4
            },
            "gaap_compliance": {
                "status": "compliant",
                "last_assessment": "2024-01-10",
                "next_assessment": "2024-04-10",
                "requirements_met": 4,
                "total_requirements": 4
            },
            "ifrs_compliance": {
                "status": "partial",
                "last_assessment": "2024-01-05",
                "next_assessment": "2024-03-05",
                "requirements_met": 3,
                "total_requirements": 4,
                "pending_requirements": ["Financial instruments standards"]
            }
        }
        
        return {
            "type": "compliance_check",
            "compliance_status": compliance_status,
            "overall_compliance_score": 85.0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_policy_recommendations(self, user_input: str) -> Dict[str, Any]:
        """Get policy recommendations based on current state."""
        recommendations = [
            {
                "category": "revenue_recognition",
                "priority": "high",
                "recommendation": "Implement automated revenue recognition controls",
                "rationale": "Reduce manual errors and improve compliance",
                "implementation_effort": "medium"
            },
            {
                "category": "expense_management",
                "priority": "medium",
                "recommendation": "Establish quarterly expense review process",
                "rationale": "Ensure proper expense classification and timing",
                "implementation_effort": "low"
            },
            {
                "category": "asset_management",
                "priority": "medium",
                "recommendation": "Implement asset tracking system",
                "rationale": "Improve asset valuation accuracy and compliance",
                "implementation_effort": "high"
            }
        ]
        
        return {
            "type": "policy_recommendations",
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "high_priority_count": sum(1 for r in recommendations if r["priority"] == "high"),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _check_regulatory_requirements(self, user_input: str) -> Dict[str, Any]:
        """Check specific regulatory requirements."""
        return {
            "type": "regulatory_check",
            "regulatory_requirements": self.regulatory_requirements,
            "compliance_summary": {
                "sox": "compliant",
                "gaap": "compliant", 
                "ifrs": "partial_compliance"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_compliance_report(self, user_input: str) -> Dict[str, Any]:
        """Generate a comprehensive compliance report."""
        validation = await self._validate_financial_data(user_input)
        compliance = await self._check_compliance(user_input)
        recommendations = await self._get_policy_recommendations(user_input)
        
        return {
            "type": "compliance_report",
            "report": {
                "executive_summary": {
                    "overall_compliance_status": "compliant",
                    "compliance_score": compliance["overall_compliance_score"],
                    "critical_issues": 0,
                    "recommendations_count": recommendations["total_recommendations"]
                },
                "detailed_findings": {
                    "data_validation": validation,
                    "compliance_status": compliance,
                    "recommendations": recommendations
                },
                "action_items": [
                    "Review expense classification quarterly",
                    "Implement automated revenue recognition controls",
                    "Complete IFRS compliance assessment"
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_all_policies(self) -> Dict[str, Any]:
        """Get all available policies and rules."""
        return {
            "type": "all_policies",
            "compliance_rules": self.compliance_rules,
            "regulatory_requirements": self.regulatory_requirements,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_aml_policies(self) -> Dict[str, Any]:
        """Get AML-specific policies for display."""
        aml_policies = {}
        for rule_name, rule_data in self.compliance_rules.items():
            if rule_name in ["high_value_transaction", "ctr_threshold", "sar_threshold", 
                           "pep_transaction", "high_risk_country"]:
                aml_policies[rule_name] = rule_data
        return aml_policies
    
    def _get_capabilities(self) -> Dict[str, Any]:
        """Get the capabilities of the policy engine agent."""
        return {
            "input_types": ["text", "json"],
            "output_types": ["text", "json"],
            "supported_operations": [
                "validate_financial_data",
                "check_compliance",
                "get_policy_recommendations",
                "check_regulatory_requirements",
                "generate_compliance_report",
                "get_all_policies"
            ],
            "compliance_frameworks": [
                "SOX",
                "GAAP",
                "IFRS"
            ],
            "validation_types": [
                "revenue_recognition",
                "expense_classification",
                "asset_valuation",
                "financial_reporting"
            ]
        }
    
    def _get_endpoints(self) -> Dict[str, Any]:
        """Get the endpoints this agent exposes."""
        return {
            "execute": {
                "method": "POST",
                "description": "Execute policy and compliance operations",
                "parameters": {
                    "query": "Natural language query for policy validation or compliance checking"
                }
            },
            "cancel": {
                "method": "POST",
                "description": "Cancel ongoing policy operation"
            }
        }
