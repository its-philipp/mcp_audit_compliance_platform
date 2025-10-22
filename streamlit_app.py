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
            
            if "query_financial_data" in tool_results:
                try:
                    financial_data = json.loads(tool_results["query_financial_data"])
                    transactions = financial_data.get("data", [])
                except:
                    transactions = []
            
            if "validate_compliance" in tool_results:
                try:
                    compliance_data = json.loads(tool_results["validate_compliance"])
                    violations = compliance_data.get("violations", [])
                except:
                    violations = []
            
            # Generate dynamic report based on actual data
            total_transactions = len(transactions)
            total_violations = len(violations)
            
            # Determine compliance status
            compliance_status = "PASS" if total_violations == 0 else "FAIL"
            
            # Generate detailed violations if we have transaction data
            detailed_violations = []
            if transactions:
                # Get AML policies from MCP server
                try:
                    mcp_server = get_mcp_server()
                    aml_policies = json.loads(mcp_server._get_aml_policies())
                    
                    for transaction in transactions[:20]:  # Limit to first 20 for display
                        amount = transaction.get("amount", 0)
                        country = transaction.get("country", "")
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
            
            return {
                "type": "mcp_audit_report",
                "query": query,
                "response": response_data,
                "tools_used": tools_used,
                "summary": {
                    "total_transactions": total_transactions,
                    "violations_found": len(detailed_violations),
                    "compliance_status": compliance_status,
                    "tracing_enabled": is_langfuse_enabled()
                },
                "violations": detailed_violations,
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
    
    if st.button("🚀 Run Selected Query", type="primary"):
        with st.spinner("Running audit with MCP tools..."):
            result = run_audit_with_tracing(selected_query)
            st.session_state.audit_result = result
    
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
    
    # MCP Tools Status
    st.subheader("🔧 MCP Tools")
    mcp_tools = [
        "query_financial_data",
        "validate_compliance", 
        "generate_audit_report",
        "check_compliance_status",
        "get_audit_trail"
    ]
    
    for tool in mcp_tools:
        st.text(f"• {tool}")

# Main content area
if st.session_state.audit_result:
    result = st.session_state.audit_result
    
    # Display results
    st.header("📋 Audit Results")
    
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
    st.markdown(result["response"])
    
    # Tools Used
    if result.get("tools_used"):
        st.subheader("🔧 MCP Tools Used")
        for tool in result["tools_used"]:
            st.text(f"• {tool}")
    
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
    <div class="feature-box">
        <h3>🎯 Welcome to the MCP Audit & Compliance Platform</h3>
        <p>This platform uses the <strong>Model Context Protocol (MCP)</strong> to provide intelligent audit and compliance analysis.</p>
        
        <h4>🔧 Available MCP Tools:</h4>
        <ul>
            <li><strong>query_financial_data</strong> - Query financial transactions, revenue, expenses, and assets</li>
            <li><strong>validate_compliance</strong> - Validate transactions against AML policies and compliance rules</li>
            <li><strong>generate_audit_report</strong> - Generate comprehensive audit reports with violations and recommendations</li>
            <li><strong>check_compliance_status</strong> - Check overall compliance status and identify violations</li>
            <li><strong>get_audit_trail</strong> - Retrieve audit trail and compliance history</li>
        </ul>
        
        <h4>🚀 How to Use:</h4>
        <ol>
            <li>Select an example query from the sidebar</li>
            <li>Click "Run Selected Query" to execute</li>
            <li>Or enter your own custom query</li>
            <li>View the AI-powered analysis and compliance results</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # AML Policies Section (dynamic loading)
    st.subheader("⚖️ AML Policies")
    try:
        mcp_server = get_mcp_server()
        aml_policies = json.loads(mcp_server._get_aml_policies())
        
        for policy_name, policy_data in aml_policies.items():
            with st.expander(f"📋 {policy_data['description']}"):
                st.write(f"**Threshold:** €{policy_data.get('threshold', 'N/A'):,}")
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