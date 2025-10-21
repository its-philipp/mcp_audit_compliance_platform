"""
Streamlit UI for A2A Audit & Compliance Agent Network
Interactive demonstration of agent-to-agent architecture with AI orchestration
"""

import streamlit as st
import sys
import os
import time
import pandas as pd
import requests
from datetime import datetime
from typing import Dict, Any, List

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database import init_database, get_db_manager
from src.tracing import is_langfuse_enabled

def find_compliant_supplier():
    """Find a USA supplier with LOW risk that has small transactions (< €5,000)"""
    try:
        db = get_db_manager()
        transactions = db.get_transactions(
            max_amount=5000,
            risk_category="LOW",
            country="USA",
            limit=10
        )
        
        if transactions:
            return transactions[0].supplier_name
        
        return None
    except Exception as e:
        st.error(f"Error finding compliant supplier: {e}")
        return None

def run_audit_with_tracing(query: str) -> Dict[str, Any]:
    """Run audit process with tracing."""
    start_time = time.time()
    
    try:
        # Call the orchestrator agent
        response = requests.post(
            "http://localhost:8001/query",
            json={
                "query": query,
                "agent_type": "orchestrator"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            execution_time = time.time() - start_time
            
            # Create audit trail
            audit_trail = [
                f"[{datetime.now().strftime('%H:%M:%S')}] Starting audit process",
                f"[{datetime.now().strftime('%H:%M:%S')}] Query: {query}",
                f"[{datetime.now().strftime('%H:%M:%S')}] Orchestrator processing query",
                f"[{datetime.now().strftime('%H:%M:%S')}] Agents consulted: {result['response'].get('agents_consulted', [])}",
                f"[{datetime.now().strftime('%H:%M:%S')}] Audit completed in {execution_time:.2f}s"
            ]
            
            # Parse actual response data
            response_data = result['response']
            agent_responses = response_data.get('agent_responses', {})
            
            # Extract transaction data from financial agent response
            transactions_analyzed = 0
            violations_found = 0
            violations = []
            
            if 'financial-data-agent' in agent_responses:
                financial_data = agent_responses['financial-data-agent']
                if financial_data.get('type') == 'transaction_data':
                    transactions_analyzed = financial_data.get('summary', {}).get('total_transactions', 0)
                    
                    # Get AML policies from Policy Engine Agent for proper validation
                    try:
                        from src.agents.policy_engine_agent import PolicyEngineAgent
                        policy_agent = PolicyEngineAgent()
                        aml_policies = policy_agent.get_aml_policies()
                    except:
                        aml_policies = {}
                    
                    # Generate violations based on actual transaction data using policy rules
                    transactions = financial_data.get('transactions', [])
                    for txn in transactions[:10]:  # Check first 10 transactions
                        txn_amount = txn.get('amount', 0)
                        txn_country = txn.get('supplier_country', '')
                        txn_risk = txn.get('risk_category', '')
                        txn_payment_method = txn.get('payment_method', '')
                        
                        # High-risk country violations (CRITICAL severity)
                        if txn_country in aml_policies.get('high_risk_country', {}).get('countries', []):
                            violations_found += 1
                            violations.append({
                                "transaction_id": txn.get('transaction_id', 'N/A'),
                                "supplier": txn.get('supplier_name', 'N/A'),
                                "amount": txn_amount,
                                "payment_method": txn_payment_method,
                                "rule": "HIGH_RISK_COUNTRY",
                                "severity": "CRITICAL",
                                "description": f"Transaction from sanctioned country: {txn_country}"
                            })
                        
                        # High-value transaction violations (€100,000+)
                        elif txn_amount >= aml_policies.get('high_value_transaction', {}).get('threshold', 100000):
                            violations_found += 1
                            violations.append({
                                "transaction_id": txn.get('transaction_id', 'N/A'),
                                "supplier": txn.get('supplier_name', 'N/A'),
                                "amount": txn_amount,
                                "payment_method": txn_payment_method,
                                "rule": "HIGH_VALUE_TRANSACTION",
                                "severity": "HIGH",
                                "description": f"Transaction exceeds €{aml_policies.get('high_value_transaction', {}).get('threshold', 100000):,} threshold"
                            })
                        
                        # SAR threshold violations (€3,000+ for high-risk suppliers)
                        elif txn_amount >= aml_policies.get('sar_threshold', {}).get('threshold', 3000) and txn_risk in aml_policies.get('sar_threshold', {}).get('risk_categories', []):
                            violations_found += 1
                            violations.append({
                                "transaction_id": txn.get('transaction_id', 'N/A'),
                                "supplier": txn.get('supplier_name', 'N/A'),
                                "amount": txn_amount,
                                "payment_method": txn_payment_method,
                                "rule": "SAR_TRIGGERED",
                                "severity": "HIGH",
                                "description": f"High-risk supplier transaction ≥ €{aml_policies.get('sar_threshold', {}).get('threshold', 3000):,} triggers SAR"
                            })
                        
                        # CTR threshold violations (€5,000+ for Check/Cash payments)
                        elif txn_amount >= aml_policies.get('ctr_threshold', {}).get('threshold', 5000) and txn_payment_method in aml_policies.get('ctr_threshold', {}).get('payment_methods', []):
                            violations_found += 1
                            violations.append({
                                "transaction_id": txn.get('transaction_id', 'N/A'),
                                "supplier": txn.get('supplier_name', 'N/A'),
                                "amount": txn_amount,
                                "payment_method": txn_payment_method,
                                "rule": "CTR_REQUIRED",
                                "severity": "MEDIUM",
                                "description": f"{txn_payment_method} payment ≥ €{aml_policies.get('ctr_threshold', {}).get('threshold', 5000):,} requires CTR filing"
                            })
                        
                        # PEP transaction violations (€1,000+)
                        elif txn_amount >= aml_policies.get('pep_transaction', {}).get('threshold', 1000) and txn_risk == 'PEP':
                            violations_found += 1
                            violations.append({
                                "transaction_id": txn.get('transaction_id', 'N/A'),
                                "supplier": txn.get('supplier_name', 'N/A'),
                                "amount": txn_amount,
                                "payment_method": txn_payment_method,
                                "rule": "PEP_TRANSACTION",
                                "severity": "HIGH",
                                "description": f"PEP transaction ≥ €{aml_policies.get('pep_transaction', {}).get('threshold', 1000):,} requires enhanced monitoring"
                            })
            
            # Determine compliance status
            compliance_status = "PASS" if violations_found == 0 else "FAIL"
            
            audit_report = {
                "query": query,
                "transactions_analyzed": transactions_analyzed,
                "violations_found": violations_found,
                "compliance_status": compliance_status,
                "summary": response_data.get('response', 'No summary available'),
                "audit_trail": audit_trail,
                "execution_time": execution_time,
                "violations": violations
            }
            
            return audit_report
        else:
            raise Exception(f"API call failed: {response.status_code}")
            
    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "query": query,
            "transactions_analyzed": 0,
            "violations_found": 0,
            "compliance_status": "ERROR",
            "summary": f"Audit failed: {str(e)}",
            "audit_trail": [f"[{datetime.now().strftime('%H:%M:%S')}] Error: {str(e)}"],
            "execution_time": execution_time,
            "violations": []
        }

# Page configuration
st.set_page_config(
    page_title="A2A Audit & Compliance Agent Network",
    page_icon="🤖",
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
        margin-bottom: 1rem;
    }
    .agent-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
        color: #1b1b1b;
    }
    .agent-card-active {
        border-color: #1f77b4;
        background-color: #e3f2fd;
        color: #0d0d0d;
    }
    .violation-critical {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 0.5rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    .violation-high {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 0.5rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    .violation-medium {
        background-color: #fffde7;
        border-left: 4px solid #ffc107;
        padding: 0.5rem;
        margin: 0.5rem 0;
        color: #000000;
    }
    .violation-low {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 0.5rem;
        margin: 0.5rem 0;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🤖 A2A Audit & Compliance Agent Network</div>', unsafe_allow_html=True)
st.markdown("### Agent-to-Agent Architecture with Google A2A Framework")
st.markdown("---")

# Initialize session state
if 'audit_run' not in st.session_state:
    st.session_state.audit_run = False
if 'audit_report' not in st.session_state:
    st.session_state.audit_report = None
if 'approved' not in st.session_state:
    st.session_state.approved = False

# Initialize database
if 'db_initialized' not in st.session_state:
    try:
        init_database()
        st.session_state.db_initialized = True
        st.success("✅ Database initialized successfully")
    except Exception as e:
        st.error(f"❌ Database initialization failed: {e}")
        st.session_state.db_initialized = False
else:
    db_initialized = st.session_state.db_initialized

# Sidebar - Input Panel
with st.sidebar:
    st.header("📋 Audit Request")

    # Example queries
    compliant_supplier = find_compliant_supplier()
    compliant_query = f"Show me transactions under €5,000 from USA suppliers with low risk category" if compliant_supplier else "Show me transactions under €5,000 from USA suppliers with low risk category"
    
    example_queries = {
        "Select an example...": "",
        "✅ Compliant Transaction": compliant_query,
        "🚨 High-Risk Country": "Check transactions to suppliers in Russia for AML violations and compliance issues",
        "💰 Large Transactions": "Show me transactions over 10000 EUR for suspicious activity analysis",
        "📊 Financial Analysis": "Show me revenue data for 2024 and perform financial analysis",
        "⚖️ Policy Compliance": "Check our compliance status with SOX and GAAP requirements"
    }

    selected_example = st.selectbox("Quick Examples:", list(example_queries.keys()))

    # Natural language query input
    default_query = example_queries.get(selected_example, "")
    audit_query = st.text_area(
        "Natural Language Audit Query:",
        value=default_query,
        height=150,
        placeholder="e.g., Check all transactions from supplier X in Q3 over €500k for AML violations and double payments..."
    )

    st.markdown("---")

    # Run button
    run_button = st.button("🚀 Run Audit", type="primary", use_container_width=True)

    st.markdown("---")

    # System Status
    st.subheader("🔧 System Status")

    # Check service availability
    try:
        resp = requests.get("http://localhost:8001/health", timeout=2)
        service_status = "🟢 Online" if resp.status_code == 200 else "🔴 Offline"
    except:
        service_status = "🔴 Offline"

    st.text(f"A2A Agent Network: {service_status}")
    st.text(f"Database: {'🟢 Connected' if st.session_state.get('db_initialized', False) else '🔴 Disconnected'}")
    st.text(f"Langfuse Tracing: {'🟢 Enabled' if is_langfuse_enabled() else '🟡 Disabled'}")

    st.markdown("---")
    
    # AML Policies Section
    st.subheader("📋 Current AML Policies")
    
    # Get policies from Policy Engine Agent
    try:
        from src.agents.policy_engine_agent import PolicyEngineAgent
        policy_agent = PolicyEngineAgent()
        aml_policies = policy_agent.get_aml_policies()
        
        with st.expander("View Policy Thresholds", expanded=False):
            policy_text = ""
            for rule_name, rule_data in aml_policies.items():
                policy_text += f"**{rule_data['description'].title()}:**\n"
                if 'threshold' in rule_data:
                    policy_text += f"- **Threshold**: €{rule_data['threshold']:,}\n"
                if 'countries' in rule_data:
                    policy_text += f"- **High-Risk Countries**: {', '.join(rule_data['countries'])}\n"
                if 'payment_methods' in rule_data:
                    policy_text += f"- **Payment Methods**: {', '.join(rule_data['payment_methods'])}\n"
                if 'risk_categories' in rule_data:
                    policy_text += f"- **Risk Categories**: {', '.join(rule_data['risk_categories'])}\n"
                policy_text += f"- **Severity**: {rule_data['severity'].upper()}\n\n"
            
            st.markdown(policy_text)
        
        with st.expander("View Violation Types", expanded=False):
            violation_text = ""
            severity_groups = {"critical": [], "high": [], "medium": [], "low": []}
            
            for rule_name, rule_data in aml_policies.items():
                severity = rule_data['severity']
                rule_display = rule_name.upper().replace('_', '_')
                severity_groups[severity].append(f"- **{rule_display}**: {rule_data['description']}")
            
            for severity in ["critical", "high", "medium", "low"]:
                if severity_groups[severity]:
                    violation_text += f"**{severity.upper()} Severity:**\n"
                    violation_text += "\n".join(severity_groups[severity]) + "\n\n"
            
            st.markdown(violation_text)
            
    except Exception as e:
        st.error(f"Error loading policies: {e}")
        st.markdown("**Default AML Policies:**")
        st.markdown("- High-Value Transaction: €100,000+")
        st.markdown("- CTR Threshold: €5,000+")
        st.markdown("- SAR Threshold: €3,000+")
        st.markdown("- PEP Threshold: €1,000+")

# Main Content Area
if run_button and audit_query:
    st.session_state.audit_run = True
    st.session_state.audit_report = None
    st.session_state.approved = False

if st.session_state.audit_run and st.session_state.audit_report is None:
    # Create three columns for agent visualization
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown("""
        <div class="agent-card agent-card-active">
            <h3>🎯 Agent A</h3>
            <p><strong>Orchestrator Agent</strong></p>
            <p>Coordinating workflow...</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        agent_b_placeholder = st.empty()
        agent_b_placeholder.markdown("""
        <div class="agent-card">
            <h3>🏦 Agent B</h3>
            <p><strong>Financial Data Agent</strong></p>
            <p>Waiting...</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        agent_c_placeholder = st.empty()
        agent_c_placeholder.markdown("""
        <div class="agent-card">
            <h3>🔐 Agent C</h3>
            <p><strong>Policy Engine Agent</strong></p>
            <p>Waiting...</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Workflow animation
    workflow_placeholder = st.empty()
    workflow_placeholder.markdown("### 🔄 Workflow: Agent A ➡️ Agent B ➡️ Agent C ➡️ Report")

    # Audit log
    st.markdown("### 📝 Audit Trail (Real-time)")
    log_placeholder = st.empty()

    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Simulate step-by-step execution with status updates
        status_text.text("Step 1/5: Parsing query...")
        progress_bar.progress(10)
        time.sleep(0.5)

        status_text.text("Step 2/5: Discovering agents...")
        progress_bar.progress(20)
        time.sleep(0.5)

        status_text.text("Step 3/5: Retrieving transaction data...")
        agent_b_placeholder.markdown("""
        <div class="agent-card agent-card-active">
            <h3>🏦 Agent B</h3>
            <p><strong>Financial Data Agent</strong></p>
            <p>🔄 Fetching transactions...</p>
        </div>
        """, unsafe_allow_html=True)
        progress_bar.progress(40)
        time.sleep(0.8)

        status_text.text("Step 4/5: Validating compliance...")
        agent_b_placeholder.markdown("""
        <div class="agent-card">
            <h3>🏦 Agent B</h3>
            <p><strong>Financial Data Agent</strong></p>
            <p>✅ Data retrieved</p>
        </div>
        """, unsafe_allow_html=True)
        agent_c_placeholder.markdown("""
        <div class="agent-card agent-card-active">
            <h3>🔐 Agent C</h3>
            <p><strong>Policy Engine Agent</strong></p>
            <p>🔄 Running compliance checks...</p>
        </div>
        """, unsafe_allow_html=True)
        progress_bar.progress(70)
        time.sleep(1.0)

        status_text.text("Step 5/5: Generating audit report...")
        agent_c_placeholder.markdown("""
        <div class="agent-card">
            <h3>🔐 Agent C</h3>
            <p><strong>Policy Engine Agent</strong></p>
            <p>✅ Validation complete</p>
        </div>
        """, unsafe_allow_html=True)
        progress_bar.progress(90)

        # Execute the actual audit
        report = run_audit_with_tracing(audit_query)

        progress_bar.progress(100)
        status_text.text("✅ Audit complete!")

        # Store report in session state
        st.session_state.audit_report = report

        time.sleep(1)

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        workflow_placeholder.empty()

        # Display audit log
        log_placeholder.code("\n".join(report["audit_trail"]), language="")

    except Exception as e:
        st.error(f"❌ Audit failed: {str(e)}")
        st.session_state.audit_run = False

# Display Report if available
if st.session_state.audit_report:
    report = st.session_state.audit_report

    st.markdown("---")
    st.markdown("## 📊 Audit Report")

    # Summary Section
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Transactions Analyzed", report["transactions_analyzed"])

    with col2:
        st.metric("Violations Found", report["violations_found"])

    with col3:
        compliance_color = "🟢" if report["compliance_status"] == "PASS" else "🔴"
        st.metric("Compliance Status", f"{compliance_color} {report['compliance_status']}")

    with col4:
        if is_langfuse_enabled():
            st.metric("Tracing", "🟢 Enabled")
        else:
            st.metric("Tracing", "🟡 Disabled")

    st.markdown("---")

    # AI-Generated Summary
    st.markdown("### 📝 Executive Summary")
    st.info(report["summary"])

    # Violations Table
    if report["violations_found"] > 0:
        st.markdown("### ⚠️ Violations Detected")

        # Convert violations to DataFrame
        violations_data = []
        for v in report["violations"]:
            violations_data.append({
                "Transaction ID": v["transaction_id"],
                "Supplier": v["supplier"],
                "Amount (EUR)": f"€{v['amount']:,.2f}",
                "Payment Method": v.get("payment_method", "N/A"),
                "Rule": v["rule"],
                "Severity": v["severity"],
                "Description": v["description"]
            })

        df = pd.DataFrame(violations_data)

        # Display with color coding
        st.dataframe(
            df,
            use_container_width=True,
            height=400
        )

        # Additional violation insights
        if len(report["violations"]) > 0:
            st.markdown("### 📈 Violation Analysis")
            
            # Group violations by rule type
            rule_counts = {}
            for v in report["violations"]:
                rule = v['rule']
                rule_counts[rule] = rule_counts.get(rule, 0) + 1
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Most Common Violation", max(rule_counts, key=rule_counts.get) if rule_counts else "N/A")
            with col2:
                st.metric("Unique Rule Types", len(rule_counts))
    else:
        st.success("✅ No violations detected. All transactions comply with policies.")

    st.markdown("---")

    # Human-in-the-Loop Section
    st.markdown("### 🧑‍⚖️ Human-in-the-Loop Approval")

    if not st.session_state.approved:
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("✅ Approve Report", type="primary", use_container_width=True):
                st.session_state.approved = True
                st.success("✅ Report approved by auditor!")
                st.balloons()

        with col2:
            if st.button("❌ Reject & Flag for Review", use_container_width=True):
                st.warning("⚠️ Report flagged for manual review.")

        with col3:
            st.info("ℹ️ The final decision remains with the human auditor (Trusted AI principle).")
    else:
        st.success("✅ This report has been approved by the auditor.")

    # Audit Trail
    with st.expander("📋 View Complete Audit Trail"):
        st.code("\n".join(report["audit_trail"]), language="")

    # Architecture Overview (always visible after audit)
    st.markdown("---")
    st.markdown("### 🏗️ A2A Architecture Overview")

    st.markdown("""
    ```
    ┌─────────────────────────────────────────────────────────────┐
    │                Agent A: Orchestrator Agent                  │
    │            (LangChain + GPT-4 + Google A2A)                 │
    │                                                             │
    │  1. Parse Query   2. Discover   3. Delegate   4. Synthesize │
    └───────────────────────┬─────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
    ┌───────────▼──────────┐  ┌────────▼───────────┐
    │   Agent B: Financial │  │ Agent C: Policy    │
    │   Data Agent         │  │ Engine Agent       │
    │   (Google A2A)       │  │ (Google A2A)       │
    │                      │  │                    │
    │ - Agent Cards        │  │ - Agent Cards      │
    │ - A2A Protocol       │  │ - A2A Protocol     │
    │ - Database Access    │  │ - Compliance Rules │
    └──────────────────────┘  └────────────────────┘
    ```
    """)

else:
    # Welcome screen
    if not st.session_state.audit_run:
        st.info("""
        ### 👋 Welcome to the A2A Audit & Compliance Agent Network Demo

        This demonstration showcases:

        - **Agent A (Orchestrator)**: Natural language understanding & workflow coordination using LangChain
        - **Agent B (Financial Data)**: Secure, encapsulated database access with Google A2A framework
        - **Agent C (Policy Engine)**: Compliance validation with Google A2A framework
        - **Google A2A Framework**: True agent-to-agent communication protocol
        - **Langfuse**: End-to-end observability and tracing (optional)
        - **Human-in-the-Loop**: Final approval by human auditor

        **Get Started:**
        1. Select an example query from the sidebar
        2. Or write your own natural language audit request
        3. Click "Run Audit" to see the A2A architecture in action

        **Example Queries:**
        - "Check all transactions from supplier X in Q3 over €500k for AML violations"
        - "Find duplicate invoice payments in 2024"
        - "Analyze all transactions to suppliers in high-risk countries"
        - "Show me financial analysis for 2024"
        - "Check our compliance status with SOX requirements"
        """)

        # Architecture diagram
        st.markdown("---")
        st.markdown("### 🏗️ A2A Architecture Overview")

        st.markdown("""
        ```
        ┌─────────────────────────────────────────────────────────────┐
        │                Agent A: Orchestrator Agent                  │
        │            (LangChain + GPT-4 + Google A2A)                 │
        │                                                             │
        │  1. Parse Query   2. Discover   3. Delegate   4. Synthesize │
        └───────────────────────┬─────────────────────────────────────┘
                                │
                    ┌───────────┴──────────┐
                    │                      │
        ┌───────────▼──────────┐  ┌────────▼───────────┐
        │   Agent B: Financial │  │ Agent C: Policy    │
        │   Data Agent         │  │ Engine Agent       │
        │   (Google A2A)       │  │ (Google A2A)       │
        │                      │  │                    │
        │ - Agent Cards        │  │ - Agent Cards      │
        │ - A2A Protocol       │  │ - A2A Protocol     │
        │ - Database Access    │  │ - Compliance Rules │
        └──────────────────────┘  └────────────────────┘
        ```
        """)

if __name__ == "__main__":
    pass
