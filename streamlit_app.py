"""
MCP Audit & Compliance Platform - Streamlit UI
Interactive web interface for the Model Context Protocol-based audit system.
"""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import time

from src.database import init_database, get_db_manager
from src.tracing import is_langfuse_enabled
from src.mcp_server import get_mcp_server

# Page configuration
st.set_page_config(
    page_title="MCP Audit & Compliance Platform",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .violation-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    .violation-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    .violation-critical {
        background-color: #fce4ec;
        border-left: 4px solid #e91e63;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    .compliance-pass {
        color: #4caf50;
        font-weight: bold;
    }
    .compliance-fail {
        color: #f44336;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def find_compliant_supplier():
    """Find a compliant supplier from the database."""
    try:
        db = get_db_manager()
        suppliers = db.get_suppliers()
        
        # Find a supplier with LOW risk category
        compliant_suppliers = [s for s in suppliers if s.get("risk_category") == "LOW"]
        
        if compliant_suppliers:
            supplier = compliant_suppliers[0]
            return {
                "name": supplier.get("name", "Unknown"),
                "country": supplier.get("country", "Unknown"),
                "risk_category": supplier.get("risk_category", "Unknown"),
                "compliance_status": "COMPLIANT"
            }
        else:
            return {
                "name": "No compliant suppliers found",
                "country": "N/A",
                "risk_category": "N/A",
                "compliance_status": "N/A"
            }
    except Exception as e:
        st.error(f"Error finding compliant supplier: {e}")
        return {
            "name": "Error",
            "country": "N/A",
            "risk_category": "N/A",
            "compliance_status": "ERROR"
        }

def run_audit_with_tracing(query: str) -> Dict[str, Any]:
    """Run audit with MCP tools and tracing."""
    try:
        # Call the MCP-based API
        response = requests.post(
            "http://localhost:8001/query",
            json={"query": query, "include_tracing": True},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Parse the MCP response
            response_data = result.get("response", "")
            tools_used = result.get("tools_used", [])
            tool_results = result.get("tool_results", {})
            
            # Extract transaction data from tool results
            transactions = []
            violations = []
            actual_violation_count = 0
            
            if "query_financial_data" in tool_results:
                try:
                    financial_data = json.loads(tool_results["query_financial_data"])
                    transactions = financial_data.get("data", [])
                except:
                    transactions = []
            
            # Get violations from multiple possible sources
            if "validate_compliance" in tool_results:
                try:
                    compliance_data = json.loads(tool_results["validate_compliance"])
                    violations = compliance_data.get("violations", [])
                    actual_violation_count = len(violations)
                except:
                    violations = []
            
            # Also check generate_audit_report for violations
            if "generate_audit_report" in tool_results:
                try:
                    report_data = json.loads(tool_results["generate_audit_report"])
                    if "violations" in report_data:
                        violations = report_data.get("violations", [])
                        actual_violation_count = len(violations)
                except:
                    pass
            
            # Check compliance status for violation count
            if "check_compliance_status" in tool_results:
                try:
                    status_data = json.loads(tool_results["check_compliance_status"])
                    if "violations_found" in status_data:
                        actual_violation_count = status_data.get("violations_found", 0)
                except:
                    pass
            
            # Generate dynamic report based on actual data
            total_transactions = len(transactions)
            
            # Generate detailed violations if we have transaction data
            detailed_violations = []
            if transactions:
                # Use static AML policies for Streamlit display
                try:
                    aml_policies = {
                        "high_value_transaction": {
                            "threshold": 100000,
                            "severity": "high"
                        },
                        "ctr_threshold": {
                            "threshold": 5000,
                            "severity": "medium",
                            "payment_methods": ["CASH", "CHECK"]
                        },
                        "sar_threshold": {
                            "threshold": 3000,
                            "severity": "high",
                            "risk_categories": ["HIGH"]
                        },
                        "high_risk_country": {
                            "countries": ["Russia", "Iran", "North Korea", "Syria"],
                            "severity": "critical"
                        }
                    }
                    
                    for transaction in transactions[:20]:  # Limit to first 20 for display
                        amount = transaction.get("amount", 0)
                        country = transaction.get("supplier_country", "")
                        risk_category = transaction.get("risk_category", "")
                        payment_method = transaction.get("payment_method", "")
                        
                        # High-value transaction check
                        if amount > aml_policies["high_value_transaction"]["threshold"]:
                            detailed_violations.append({
                                "Transaction ID": transaction.get("id"),
                                "Violation Type": "High Value Transaction",
                                "Description": f"Transaction amount €{amount:,.2f} exceeds €{aml_policies['high_value_transaction']['threshold']:,} threshold",
                                "Severity": aml_policies["high_value_transaction"]["severity"].upper(),
                                "Amount": f"€{amount:,.2f}",
                                "Currency": transaction.get("currency", "EUR"),
                                "Supplier": transaction.get("supplier_name", "Unknown"),
                                "Country": country,
                                "Payment Method": payment_method
                            })
                        
                        # High-risk country check
                        if country in aml_policies["high_risk_country"]["countries"]:
                            detailed_violations.append({
                                "Transaction ID": transaction.get("id"),
                                "Violation Type": "High Risk Country",
                                "Description": f"Transaction from high-risk country: {country}",
                                "Severity": aml_policies["high_risk_country"]["severity"].upper(),
                                "Amount": f"€{amount:,.2f}",
                                "Currency": transaction.get("currency", "EUR"),
                                "Supplier": transaction.get("supplier_name", "Unknown"),
                                "Country": country,
                                "Payment Method": payment_method
                            })
                        
                        # CTR threshold check
                        if payment_method in aml_policies["ctr_threshold"]["payment_methods"] and amount > aml_policies["ctr_threshold"]["threshold"]:
                            detailed_violations.append({
                                "Transaction ID": transaction.get("id"),
                                "Violation Type": "CTR Threshold",
                                "Description": f"CTR required for {payment_method} transaction €{amount:,.2f}",
                                "Severity": aml_policies["ctr_threshold"]["severity"].upper(),
                                "Amount": f"€{amount:,.2f}",
                                "Currency": transaction.get("currency", "EUR"),
                                "Supplier": transaction.get("supplier_name", "Unknown"),
                                "Country": country,
                                "Payment Method": payment_method
                            })
                        
                        # SAR threshold check
                        if risk_category in aml_policies["sar_threshold"]["risk_categories"] and amount > aml_policies["sar_threshold"]["threshold"]:
                            detailed_violations.append({
                                "Transaction ID": transaction.get("id"),
                                "Violation Type": "SAR Threshold",
                                "Description": f"SAR required for {risk_category} risk transaction €{amount:,.2f}",
                                "Severity": aml_policies["sar_threshold"]["severity"].upper(),
                                "Amount": f"€{amount:,.2f}",
                                "Currency": transaction.get("currency", "EUR"),
                                "Supplier": transaction.get("supplier_name", "Unknown"),
                                "Country": country,
                                "Payment Method": payment_method
                            })
                
                except Exception as e:
                    st.error(f"Error processing AML policies: {e}")
            
            # Determine compliance status based on actual violations from MCP tools
            total_violations = actual_violation_count if actual_violation_count > 0 else len(detailed_violations)
            compliance_status = "PASS" if total_violations == 0 else "FAIL"
            
            return {
                "type": "mcp_audit_report",
                "query": query,
                "response": response_data,
                "tools_used": tools_used,
                "summary": {
                    "total_transactions": total_transactions,
                    "violations_found": total_violations,
                    "compliance_status": compliance_status,
                    "tracing_enabled": is_langfuse_enabled()
                },
                "violations": violations if violations else detailed_violations,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "mcp_enabled": True,
                    "model": "gpt-4"
                }
            }
        else:
            return {
                "type": "error",
                "query": query,
                "error": f"API request failed with status {response.status_code}",
                "summary": {
                    "total_transactions": 0,
                    "violations_found": 0,
                    "compliance_status": "ERROR",
                    "tracing_enabled": False
                },
                "violations": [],
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "mcp_enabled": False
                }
            }
    
    except Exception as e:
        return {
            "type": "error",
            "query": query,
            "error": str(e),
            "summary": {
                "total_transactions": 0,
                "violations_found": 0,
                "compliance_status": "ERROR",
                "tracing_enabled": False
            },
            "violations": [],
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "mcp_enabled": False
            }
        }

# Initialize session state
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False
if 'audit_result' not in st.session_state:
    st.session_state.audit_result = None

# Main header
st.markdown('<h1 class="main-header">🔍 MCP Audit & Compliance Platform</h1>', unsafe_allow_html=True)

# Initialize database (with session state caching)
if not st.session_state.db_initialized:
    try:
        init_database()
        st.session_state.db_initialized = True
        st.success("✅ Database initialized successfully")
    except Exception as e:
        st.error(f"❌ Database initialization failed: {e}")
        st.session_state.db_initialized = False
else:
    db_initialized = st.session_state.db_initialized

# Sidebar
with st.sidebar:
    st.header("🎛️ Control Panel")
    
    # Example queries
    st.subheader("📝 Example Queries")
    example_queries = [
        "Show me all transactions from Russia for AML compliance analysis",
        "Analyze transactions under €5,000 from USA suppliers with low risk category for AML compliance assessment",
        "Generate a comprehensive AML compliance report for all high-risk transactions",
        "Check compliance status for all transactions and identify violations",
        "Find all transactions from high-risk countries and validate against AML policies",
        "Generate an audit trail for all compliance violations in the last 30 days"
    ]
    
    selected_query = st.selectbox("Select an example query:", example_queries)
    
    # Show the selected query immediately
    st.info(f"🔍 **Selected Query:** {selected_query}")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        if st.button("🚀 Run Selected Query", type="primary", use_container_width=True):
            with st.spinner("Running audit with MCP tools..."):
                result = run_audit_with_tracing(selected_query)
                st.session_state.audit_result = result
                st.rerun()
    
    with col2:
        if st.button("🗑️ Clear", use_container_width=True, help="Clear audit results"):
            if 'audit_result' in st.session_state:
                del st.session_state.audit_result
            st.rerun()
    
    # Custom query
    st.subheader("✍️ Custom Query")
    custom_query = st.text_area("Enter your custom query:", height=100)
    
    if st.button("🔍 Run Custom Query"):
        if custom_query.strip():
            with st.spinner("Processing custom query..."):
                result = run_audit_with_tracing(custom_query)
                st.session_state.audit_result = result
        else:
            st.warning("Please enter a query first.")
    
    # System Status
    st.subheader("📊 System Status")
    st.text(f"Database: {'🟢 Connected' if st.session_state.get('db_initialized', False) else '🔴 Disconnected'}")
    st.text(f"MCP Server: {'🟢 Running' if st.session_state.get('mcp_server_running', True) else '🔴 Stopped'}")
    st.text(f"Tracing: {'🟢 Enabled' if is_langfuse_enabled() else '🔴 Disabled'}")
    
    # AML Policies
    st.subheader("⚖️ AML Policies")
    aml_policies = {
        "high_value_transaction": {
            "description": "High-value transactions require additional documentation",
            "threshold": 100000,
            "severity": "high",
            "currency": "EUR"
        },
        "ctr_threshold": {
            "description": "Currency Transaction Report threshold",
            "threshold": 5000,
            "severity": "medium",
            "currency": "EUR"
        },
        "sar_threshold": {
            "description": "Suspicious Activity Report threshold",
            "threshold": 3000,
            "severity": "high",
            "currency": "EUR"
        },
        "pep_transaction": {
            "description": "Politically Exposed Person transaction monitoring",
            "threshold": 1000,
            "severity": "high",
            "currency": "EUR"
        },
        "high_risk_country": {
            "description": "High-risk country transaction monitoring",
            "severity": "critical",
            "countries": ["Russia", "Iran", "North Korea", "Syria"]
        }
    }
    
    for policy_name, policy_data in aml_policies.items():
        with st.expander(f"📋 {policy_data['description']}", expanded=False):
            # Handle threshold formatting safely
            threshold = policy_data.get('threshold')
            if threshold is not None:
                st.write(f"**Threshold:** €{threshold:,}")
            else:
                st.write(f"**Threshold:** N/A")
            
            st.write(f"**Severity:** {policy_data.get('severity', 'N/A').upper()}")
            st.write(f"**Currency:** {policy_data.get('currency', 'EUR')}")
            
            if 'countries' in policy_data:
                st.write(f"**Countries:** {', '.join(policy_data['countries'])}")
            
            if 'payment_methods' in policy_data:
                st.write(f"**Payment Methods:** {', '.join(policy_data['payment_methods'])}")
            
            if 'rules' in policy_data:
                st.write("**Rules:**")
                for rule in policy_data['rules']:
                    st.write(f"• {rule}")

# Main content area

# MCP Architecture Diagram - Always visible
st.markdown("### 🏗️ MCP Architecture")
st.markdown("""
<div style="background-color: #1a202c; padding: 1.5rem; border-radius: 0.5rem; margin: 1rem 0; border: 1px solid #4a5568;">
    <div style="text-align: center; color: #e2e8f0; margin-bottom: 1rem;">
        <h4 style="color: #63b3ed; margin: 0;">Model Context Protocol (MCP) Architecture</h4>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
        <div style="background-color: #2d3748; padding: 1rem; border-radius: 0.5rem; border: 1px solid #4a5568; flex: 1; min-width: 200px;">
            <h5 style="color: #90cdf4; margin: 0 0 0.5rem 0;">🤖 GPT-4 Client</h5>
            <p style="color: #cbd5e0; margin: 0; font-size: 0.9rem;">AI Assistant with MCP Client</p>
        </div>
        <div style="color: #63b3ed; font-size: 1.5rem;">↔️</div>
        <div style="background-color: #2d3748; padding: 1rem; border-radius: 0.5rem; border: 1px solid #4a5568; flex: 1; min-width: 200px;">
            <h5 style="color: #90cdf4; margin: 0 0 0.5rem 0;">🔧 MCP Server</h5>
            <p style="color: #cbd5e0; margin: 0; font-size: 0.9rem;">Audit & Compliance Tools</p>
        </div>
        <div style="color: #63b3ed; font-size: 1.5rem;">↔️</div>
        <div style="background-color: #2d3748; padding: 1rem; border-radius: 0.5rem; border: 1px solid #4a5568; flex: 1; min-width: 200px;">
            <h5 style="color: #90cdf4; margin: 0 0 0.5rem 0;">📊 Database</h5>
            <p style="color: #cbd5e0; margin: 0; font-size: 0.9rem;">Financial Data & Policies</p>
        </div>
    </div>
    <div style="margin-top: 1rem; padding: 1rem; background-color: #2d3748; border-radius: 0.5rem; border: 1px solid #4a5568;">
        <h6 style="color: #90cdf4; margin: 0 0 0.5rem 0;">🔧 Available MCP Tools:</h6>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 0.5rem;">
            <div style="color: #cbd5e0; font-size: 0.85rem;">• query_financial_data</div>
            <div style="color: #cbd5e0; font-size: 0.85rem;">• validate_compliance</div>
            <div style="color: #cbd5e0; font-size: 0.85rem;">• generate_audit_report</div>
            <div style="color: #cbd5e0; font-size: 0.85rem;">• check_compliance_status</div>
            <div style="color: #cbd5e0; font-size: 0.85rem;">• get_audit_trail</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if st.session_state.audit_result:
    result = st.session_state.audit_result
    
    # Display results
    st.header("📋 Audit Results")
    
    # Show the query that was executed
    if "query" in result:
        st.info(f"🔍 **Query Executed:** {result['query']}")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Transactions Analyzed",
            result["summary"]["total_transactions"],
            delta=None
        )
    
    with col2:
        st.metric(
            "Violations Found",
            result["summary"]["violations_found"],
            delta=None
        )
    
    with col3:
        compliance_status = result["summary"]["compliance_status"]
        if compliance_status == "PASS":
            st.metric("Compliance Status", "✅ PASS", delta=None)
        elif compliance_status == "FAIL":
            st.metric("Compliance Status", "❌ FAIL", delta=None)
        else:
            st.metric("Compliance Status", f"⚠️ {compliance_status}", delta=None)
    
    with col4:
        tracing_status = "✅ Enabled" if result["summary"]["tracing_enabled"] else "❌ Disabled"
        st.metric("Tracing", tracing_status, delta=None)
    
    # MCP Response
    st.subheader("🤖 MCP AI Response")
    response_text = result.get("response", "No response available")
    if response_text:
        st.markdown(response_text)
    else:
        st.info("No AI response available for this query.")
    
    # Tools Used
    if result.get("tools_used"):
        with st.expander("🔧 MCP Tools Used", expanded=False):
            for tool in result["tools_used"]:
                st.text(f"• {tool}")
            
            # Add tool descriptions
            tool_descriptions = {
                "query_financial_data": "Queries financial transactions, revenue, expenses, and assets",
                "validate_compliance": "Validates transactions against AML policies and compliance rules",
                "generate_audit_report": "Generates comprehensive audit reports with violations and recommendations",
                "check_compliance_status": "Checks overall compliance status and identifies violations",
                "get_audit_trail": "Retrieves audit trail and compliance history"
            }
            
            st.markdown("**Tool Descriptions:**")
            for tool in result["tools_used"]:
                if tool in tool_descriptions:
                    st.markdown(f"• **{tool}**: {tool_descriptions[tool]}")
    
    # Violations Table
    if result["violations"]:
        st.subheader("⚠️ Violations Detected")
        
        # Convert violations to DataFrame
        violations_df = pd.DataFrame(result["violations"])
        
        # Display violations table
        st.dataframe(
            violations_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Download button for violations
        csv = violations_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Violations CSV",
            data=csv,
            file_name=f"violations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.success("✅ No violations detected!")
    
    # Metadata
    with st.expander("🔍 Technical Details"):
        st.json(result["metadata"])

else:
    # Welcome message
    st.markdown("""
    <div class="feature-box" style="background-color: #2d3748; color: #e2e8f0; padding: 2rem; border-radius: 0.5rem; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border: 1px solid #4a5568;">
        <h3 style="color: #63b3ed; margin-top: 0; font-size: 1.5rem;">🎯 Welcome to the MCP Audit & Compliance Platform</h3>
        <p style="color: #cbd5e0; font-size: 1.1rem; line-height: 1.6;">This platform uses the <strong style="color: #90cdf4;">Model Context Protocol (MCP)</strong> to provide intelligent audit and compliance analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Available MCP Tools
    st.markdown("### 🔧 Available MCP Tools")
    tools_info = [
        ("**query_financial_data**", "Query financial transactions, revenue, expenses, and assets"),
        ("**validate_compliance**", "Validate transactions against AML policies and compliance rules"),
        ("**generate_audit_report**", "Generate comprehensive audit reports with violations and recommendations"),
        ("**check_compliance_status**", "Check overall compliance status and identify violations"),
        ("**get_audit_trail**", "Retrieve audit trail and compliance history")
    ]
    
    for tool_name, description in tools_info:
        st.markdown(f"• {tool_name} - {description}")
    
    # How to Use
    st.markdown("### 🚀 How to Use")
    steps = [
        "Select an example query from the sidebar",
        "Click \"Run Selected Query\" to execute",
        "Or enter your own custom query",
        "View the AI-powered analysis and compliance results"
    ]
    
    for i, step in enumerate(steps, 1):
        st.markdown(f"{i}. {step}")
    
    # AML Policies Section (dynamic loading)
    st.subheader("⚖️ AML Policies")
    try:
        mcp_server = get_mcp_server()
        # Get AML policies synchronously - create a simple version for display
        aml_policies = {
            "high_value_transaction": {
                "description": "High-value transactions require additional documentation",
                "threshold": 100000,
                "severity": "high",
                "currency": "EUR"
            },
            "ctr_threshold": {
                "description": "Currency Transaction Report threshold",
                "threshold": 5000,
                "severity": "medium",
                "currency": "EUR"
            },
            "sar_threshold": {
                "description": "Suspicious Activity Report threshold",
                "threshold": 3000,
                "severity": "high",
                "currency": "EUR"
            },
            "pep_transaction": {
                "description": "Politically Exposed Person transaction monitoring",
                "threshold": 1000,
                "severity": "high",
                "currency": "EUR"
            },
            "high_risk_country": {
                "description": "High-risk country transaction monitoring",
                "severity": "critical",
                "countries": ["Russia", "Iran", "North Korea", "Syria"]
            }
        }
        
        for policy_name, policy_data in aml_policies.items():
            with st.expander(f"📋 {policy_data['description']}"):
                # Handle threshold formatting safely
                threshold = policy_data.get('threshold')
                if threshold is not None:
                    st.write(f"**Threshold:** €{threshold:,}")
                else:
                    st.write(f"**Threshold:** N/A")
                
                st.write(f"**Severity:** {policy_data.get('severity', 'N/A').upper()}")
                st.write(f"**Currency:** {policy_data.get('currency', 'EUR')}")
                
                if 'rules' in policy_data:
                    st.write("**Rules:**")
                    for rule in policy_data['rules']:
                        st.write(f"• {rule}")
                
                if 'countries' in policy_data:
                    st.write(f"**Countries:** {', '.join(policy_data['countries'])}")
                
                if 'payment_methods' in policy_data:
                    st.write(f"**Payment Methods:** {', '.join(policy_data['payment_methods'])}")
                
                if 'risk_categories' in policy_data:
                    st.write(f"**Risk Categories:** {', '.join(policy_data['risk_categories'])}")
    
    except Exception as e:
        st.error(f"Error loading policies: {e}")
        # Fallback static policies
        st.info("Using fallback policy information...")
        st.write("**High Value Transaction:** €100,000 threshold, High severity")
        st.write("**CTR Threshold:** €5,000 threshold, Medium severity")
        st.write("**SAR Threshold:** €3,000 threshold, High severity")
        st.write("**PEP Transaction:** €1,000 threshold, High severity")
        st.write("**High Risk Country:** Critical severity for specific countries")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8rem;">
    <p>🔍 MCP Audit & Compliance Platform | Powered by Model Context Protocol & GPT-4</p>
    <p>Built with Streamlit, FastAPI, and LangChain</p>
</div>
""", unsafe_allow_html=True)