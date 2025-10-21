"""
Test script for the A2A Audit & Compliance Agent Network.

This script demonstrates the functionality of the agent network.
"""

import asyncio
import json
import requests
from typing import Dict, Any
import time


class A2AAgentTester:
    """Test client for the A2A Agent Network."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def test_health_check(self) -> bool:
        """Test the health check endpoint."""
        print("Testing health check...")
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                print(f"Response: {response.json()}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False
    
    def test_agent_discovery(self) -> bool:
        """Test agent discovery functionality."""
        print("\nTesting agent discovery...")
        try:
            response = requests.get(f"{self.base_url}/agents/discover")
            if response.status_code == 200:
                print("✅ Agent discovery passed")
                data = response.json()
                print(f"Discovered {len(data['agents'])} agents:")
                for agent_name, agent_info in data['agents'].items():
                    print(f"  - {agent_name}: {agent_info['agent_card']['name']}")
                return True
            else:
                print(f"❌ Agent discovery failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Agent discovery error: {str(e)}")
            return False
    
    def test_agent_status(self) -> bool:
        """Test agent status functionality."""
        print("\nTesting agent status...")
        try:
            response = requests.get(f"{self.base_url}/agents/status")
            if response.status_code == 200:
                print("✅ Agent status passed")
                data = response.json()
                print(f"Agent status: {data['status']}")
                for agent_name, status in data['agents'].items():
                    print(f"  - {agent_name}: {status['status']}")
                return True
            else:
                print(f"❌ Agent status failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Agent status error: {str(e)}")
            return False
    
    def test_orchestrator_query(self, query: str) -> bool:
        """Test orchestrator agent with a query."""
        print(f"\nTesting orchestrator query: '{query}'")
        try:
            payload = {
                "query": query,
                "agent_type": "orchestrator"
            }
            response = requests.post(f"{self.base_url}/query", json=payload)
            if response.status_code == 200:
                print("✅ Orchestrator query passed")
                data = response.json()
                print(f"Response type: {data['response']['type']}")
                print(f"Agents consulted: {data['response'].get('agents_consulted', [])}")
                return True
            else:
                print(f"❌ Orchestrator query failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Orchestrator query error: {str(e)}")
            return False
    
    def test_financial_agent_query(self, query: str) -> bool:
        """Test financial data agent with a query."""
        print(f"\nTesting financial agent query: '{query}'")
        try:
            payload = {
                "query": query,
                "agent_type": "financial"
            }
            response = requests.post(f"{self.base_url}/query", json=payload)
            if response.status_code == 200:
                print("✅ Financial agent query passed")
                data = response.json()
                print(f"Response type: {data['response']['type']}")
                return True
            else:
                print(f"❌ Financial agent query failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Financial agent query error: {str(e)}")
            return False
    
    def test_policy_agent_query(self, query: str) -> bool:
        """Test policy engine agent with a query."""
        print(f"\nTesting policy agent query: '{query}'")
        try:
            payload = {
                "query": query,
                "agent_type": "policy"
            }
            response = requests.post(f"{self.base_url}/query", json=payload)
            if response.status_code == 200:
                print("✅ Policy agent query passed")
                data = response.json()
                print(f"Response type: {data['response']['type']}")
                return True
            else:
                print(f"❌ Policy agent query failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Policy agent query error: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests."""
        print("🚀 Starting A2A Agent Network Tests")
        print("=" * 50)
        
        tests_passed = 0
        total_tests = 0
        
        # Basic connectivity tests
        total_tests += 1
        if self.test_health_check():
            tests_passed += 1
        
        total_tests += 1
        if self.test_agent_discovery():
            tests_passed += 1
        
        total_tests += 1
        if self.test_agent_status():
            tests_passed += 1
        
        # Agent functionality tests
        test_queries = [
            "What is our revenue for 2024?",
            "Check compliance with SOX requirements",
            "Generate a financial analysis report",
            "Validate our expense classification",
            "What are our total assets?"
        ]
        
        for query in test_queries:
            total_tests += 1
            if self.test_orchestrator_query(query):
                tests_passed += 1
        
        # Individual agent tests
        total_tests += 1
        if self.test_financial_agent_query("Show me revenue data for Q1 2024"):
            tests_passed += 1
        
        total_tests += 1
        if self.test_policy_agent_query("Check our compliance status"):
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 50)
        print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            print("🎉 All tests passed! A2A Agent Network is working correctly.")
            return True
        else:
            print(f"⚠️  {total_tests - tests_passed} tests failed. Check the logs above.")
            return False


def main():
    """Main test function."""
    print("A2A Audit & Compliance Agent Network - Test Suite")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    tester = A2AAgentTester()
    
    # Wait a moment for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All tests completed successfully!")
        exit(0)
    else:
        print("\n❌ Some tests failed. Please check the server logs.")
        exit(1)


if __name__ == "__main__":
    main()
