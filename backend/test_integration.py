#!/usr/bin/env python3
"""
πlot Backend Integration Tests

This script tests the main functionality of the backend:
1. Database connection
2. AI service integration
3. Workflow creation and execution
4. WebSocket connectivity

Run this after setting up your environment variables.
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, Any
import time


class PilotBackendTester:
    """Integration test suite for πlot backend"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.auth_token = None  # In real tests, get this from Clerk

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_health_check(self) -> bool:
        """Test basic health endpoint"""
        print("🔍 Testing health check...")

        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data.get('status')}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

    async def test_ai_connection(self) -> bool:
        """Test AI service connection"""
        print("🤖 Testing AI service connection...")

        try:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"

            # Test without auth first (if endpoint allows)
            async with self.session.post(
                f"{self.base_url}/api/v1/ai/test-connection",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ AI connection successful: {data.get('message')}")
                    return True
                elif response.status == 401:
                    print("⚠️ AI connection test requires authentication")
                    return True  # Expected without auth
                else:
                    text = await response.text()
                    print(f"❌ AI connection failed: {response.status} - {text}")
                    return False
        except Exception as e:
            print(f"❌ AI connection error: {e}")
            return False

    async def test_workflow_templates(self) -> bool:
        """Test workflow templates endpoint"""
        print("📋 Testing workflow templates...")

        try:
            async with self.session.get(f"{self.base_url}/api/v1/workflows/templates") as response:
                if response.status == 200:
                    data = await response.json()
                    templates = data.get("templates", [])
                    print(f"✅ Found {len(templates)} workflow templates")

                    for template in templates[:2]:  # Show first 2
                        print(f"   - {template.get('name')}: {template.get('description')}")

                    return len(templates) > 0
                else:
                    text = await response.text()
                    print(f"❌ Templates test failed: {response.status} - {text}")
                    return False
        except Exception as e:
            print(f"❌ Templates test error: {e}")
            return False

    async def test_ai_models(self) -> bool:
        """Test available AI models endpoint"""
        print("🎯 Testing AI models endpoint...")

        try:
            async with self.session.get(f"{self.base_url}/api/v1/ai/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    print(f"✅ Found {len(models)} available AI models")

                    for model in models[:3]:  # Show first 3
                        print(f"   - {model.get('name')} ({model.get('provider')})")

                    return len(models) > 0
                else:
                    text = await response.text()
                    print(f"❌ Models test failed: {response.status} - {text}")
                    return False
        except Exception as e:
            print(f"❌ Models test error: {e}")
            return False

    async def test_prompt_analysis(self) -> bool:
        """Test prompt analysis (requires auth)"""
        print("🧠 Testing prompt analysis...")

        if not self.auth_token:
            print("⚠️ Skipping prompt analysis (requires authentication)")
            return True

        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {
                "prompt": "Create a chatbot that helps customers with product support",
                "context": {}
            }

            async with self.session.post(
                f"{self.base_url}/api/v1/ai/analyze-prompt",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    analysis = data.get("analysis", {})
                    print(f"✅ Prompt analysis successful")
                    print(f"   Intent: {analysis.get('intent')}")
                    print(f"   Complexity: {analysis.get('complexity')}")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Prompt analysis failed: {response.status} - {text}")
                    return False
        except Exception as e:
            print(f"❌ Prompt analysis error: {e}")
            return False

    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection"""
        print("🌐 Testing WebSocket connection...")

        try:
            import websockets

            ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
            ws_url += "/ws/test-user"

            # Try to connect with a short timeout
            try:
                async with websockets.connect(ws_url, timeout=5) as websocket:
                    # Send a test message
                    await websocket.send("ping")

                    # Wait for response
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    print(f"✅ WebSocket connection successful: {response}")
                    return True
            except asyncio.TimeoutError:
                print("⚠️ WebSocket connection timeout (server may not be running)")
                return False
            except Exception as ws_error:
                print(f"❌ WebSocket connection failed: {ws_error}")
                return False

        except ImportError:
            print("⚠️ Skipping WebSocket test (websockets package not installed)")
            print("   Install with: pip install websockets")
            return True
        except Exception as e:
            print(f"❌ WebSocket test error: {e}")
            return False

    async def test_database_setup(self) -> bool:
        """Test if database is properly set up"""
        print("🗄️ Testing database setup...")

        # This is indirect - we test templates which require database
        return await self.test_workflow_templates()

    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        print("🚀 Starting πlot Backend Integration Tests\n")

        tests = [
            ("Health Check", self.test_health_check),
            ("Database Setup", self.test_database_setup),
            ("AI Connection", self.test_ai_connection),
            ("AI Models", self.test_ai_models),
            ("Workflow Templates", self.test_workflow_templates),
            ("Prompt Analysis", self.test_prompt_analysis),
            ("WebSocket Connection", self.test_websocket_connection),
        ]

        results = {}
        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
                if result:
                    passed += 1
                print()  # Add spacing between tests
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}\n")
                results[test_name] = False

        # Summary
        print("=" * 50)
        print(f"📊 Test Results: {passed}/{total} passed")
        print("=" * 50)

        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")

        print("\n" + "=" * 50)

        if passed == total:
            print("🎉 All tests passed! Backend is ready to go!")
        elif passed >= total * 0.8:
            print("⚠️ Most tests passed. Check failed tests above.")
        else:
            print("❌ Multiple tests failed. Please check your configuration.")

        return results


async def main():
    """Run the integration tests"""
    print("πlot Backend Integration Test Suite")
    print("=" * 50)

    # Check if server is likely running
    base_url = os.getenv("BACKEND_URL", "http://localhost:8000")

    async with PilotBackendTester(base_url) as tester:
        # You can set auth token here if available
        # tester.auth_token = "your-clerk-jwt-token"

        results = await tester.run_all_tests()

        # Exit with appropriate code
        if all(results.values()):
            exit(0)
        else:
            exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⛔ Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n💥 Test runner crashed: {e}")
        exit(1)
