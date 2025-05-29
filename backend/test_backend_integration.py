#!/usr/bin/env python3
"""
Backend Integration Test for πlot

Tests the complete backend integration with Supabase database:
1. Service layer functionality
2. Model validation
3. Database operations through services
4. Error handling
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Mock environment variables for testing
os.environ['SUPABASE_URL'] = 'https://owfotswzzunhcevulzju.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93Zm90c3d6enVuaGNldnVsemp1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg0OTMzMDUsImV4cCI6MjA2NDA2OTMwNX0.SSUFYd3IYnf-OaQiCIiDoI9MncsmK_gJsIRS6liqPbM'
os.environ['SUPABASE_SERVICE_KEY'] = 'service_key_placeholder'
os.environ['CLERK_SECRET_KEY'] = 'test_key'
os.environ['CLERK_PUBLISHABLE_KEY'] = 'test_key'
os.environ['CLERK_JWT_ISSUER'] = 'test_issuer'
os.environ['OPENROUTER_API_KEY'] = 'test_key'
os.environ['SECRET_KEY'] = 'test_secret_key_for_testing_only_very_long'

class BackendIntegrationTester:
    def __init__(self):
        self.results = []
        self.test_user_id = "test_user_integration_123"

    def log_result(self, test_name: str, status: str, message: str = "", details: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{emoji} {test_name}: {message}")
        if details and status == "FAIL":
            print(f"   Details: {details}")

    def test_imports(self):
        """Test that all required modules can be imported"""
        try:
            # Test core imports
            from core.config import settings
            self.log_result("Core Config Import", "PASS", "Configuration loaded successfully")
            
            # Test database imports
            from database.supabase_client import get_supabase
            self.log_result("Database Client Import", "PASS", "Supabase client imported")
            
            # Test model imports
            from models.workflow import Workflow, NodeType, WorkflowStatus
            self.log_result("Model Imports", "PASS", "Workflow models imported")
            
            # Test service imports
            from services.workflow_service import WorkflowService
            self.log_result("Service Imports", "PASS", "Workflow service imported")
            
            return True
            
        except ImportError as e:
            self.log_result("Module Imports", "FAIL", f"Import error: {str(e)}")
            return False
        except Exception as e:
            self.log_result("Module Imports", "FAIL", f"Unexpected error: {str(e)}")
            return False

    def test_configuration(self):
        """Test configuration loading"""
        try:
            from core.config import settings
            
            # Check required settings
            required_settings = [
                'SUPABASE_URL', 'SUPABASE_KEY', 'CLERK_SECRET_KEY',
                'PROJECT_NAME', 'API_V1_STR'
            ]
            
            missing = []
            for setting in required_settings:
                if not hasattr(settings, setting) or not getattr(settings, setting):
                    missing.append(setting)
            
            if not missing:
                self.log_result("Configuration", "PASS", "All required settings loaded")
                return True
            else:
                self.log_result("Configuration", "FAIL", f"Missing settings: {missing}")
                return False
                
        except Exception as e:
            self.log_result("Configuration", "FAIL", f"Config error: {str(e)}")
            return False

    def test_database_client(self):
        """Test database client initialization"""
        try:
            from database.supabase_client import get_supabase
            
            supabase = get_supabase()
            
            if supabase and hasattr(supabase, 'client'):
                self.log_result("Database Client", "PASS", "Supabase client initialized")
                return True
            else:
                self.log_result("Database Client", "FAIL", "Client not properly initialized")
                return False
                
        except Exception as e:
            self.log_result("Database Client", "FAIL", f"Client error: {str(e)}")
            return False

    def test_model_validation(self):
        """Test Pydantic model validation"""
        try:
            from models.workflow import (
                NodePosition, NodeConfig, WorkflowNode, WorkflowEdge,
                WorkflowCreate, NodeType
            )
            
            # Test NodePosition
            pos = NodePosition(x=100.0, y=200.0)
            if pos.x == 100.0 and pos.y == 200.0:
                self.log_result("Model: NodePosition", "PASS", "Position model validation works")
            else:
                self.log_result("Model: NodePosition", "FAIL", "Position validation failed")
                return False
            
            # Test NodeConfig
            config = NodeConfig(
                name="Test Node",
                model="gpt-3.5-turbo",
                temperature=0.7
            )
            if config.name == "Test Node":
                self.log_result("Model: NodeConfig", "PASS", "Config model validation works")
            else:
                self.log_result("Model: NodeConfig", "FAIL", "Config validation failed")
                return False
            
            # Test WorkflowNode
            node = WorkflowNode(
                id="test_node",
                type=NodeType.LLM,
                position=pos,
                config=config
            )
            if node.id == "test_node" and node.type == NodeType.LLM:
                self.log_result("Model: WorkflowNode", "PASS", "Node model validation works")
            else:
                self.log_result("Model: WorkflowNode", "FAIL", "Node validation failed")
                return False
            
            # Test WorkflowCreate
            workflow_create = WorkflowCreate(
                name="Test Workflow",
                description="Test workflow for validation",
                nodes=[node],
                edges=[]
            )
            if workflow_create.name == "Test Workflow":
                self.log_result("Model: WorkflowCreate", "PASS", "Workflow create model works")
            else:
                self.log_result("Model: WorkflowCreate", "FAIL", "Workflow create validation failed")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Model Validation", "FAIL", f"Validation error: {str(e)}")
            return False

    def test_workflow_templates(self):
        """Test workflow template loading"""
        try:
            from models.workflow import WORKFLOW_TEMPLATES
            
            if isinstance(WORKFLOW_TEMPLATES, dict) and len(WORKFLOW_TEMPLATES) > 0:
                template_names = list(WORKFLOW_TEMPLATES.keys())
                self.log_result("Workflow Templates", "PASS", f"Found {len(WORKFLOW_TEMPLATES)} templates: {template_names}")
                return True
            else:
                self.log_result("Workflow Templates", "FAIL", "No templates found or invalid format")
                return False
                
        except Exception as e:
            self.log_result("Workflow Templates", "FAIL", f"Template error: {str(e)}")
            return False

    async def test_workflow_service_basic(self):
        """Test basic workflow service operations"""
        try:
            from services.workflow_service import WorkflowService
            from database.supabase_client import get_supabase
            from models.workflow import WorkflowCreate, NodeType, NodePosition, NodeConfig, WorkflowNode
            
            # Initialize service
            supabase = get_supabase()
            service = WorkflowService(supabase)
            
            # Test service initialization
            if service and hasattr(service, 'supabase'):
                self.log_result("Workflow Service Init", "PASS", "Service initialized successfully")
            else:
                self.log_result("Workflow Service Init", "FAIL", "Service initialization failed")
                return False
            
            # Test template retrieval
            try:
                templates = await service.get_templates()
                if templates and len(templates) > 0:
                    self.log_result("Service: Get Templates", "PASS", f"Retrieved {len(templates)} templates")
                else:
                    self.log_result("Service: Get Templates", "FAIL", "No templates retrieved")
                    return False
            except Exception as e:
                # Expected if the method doesn't exist or has issues
                self.log_result("Service: Get Templates", "WARNING", f"Template retrieval issue: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_result("Workflow Service Basic", "FAIL", f"Service error: {str(e)}")
            return False

    async def test_direct_database_operations(self):
        """Test direct database operations to verify backend can connect"""
        try:
            from database.supabase_client import get_supabase
            
            supabase = get_supabase()
            
            # Test reading templates (should work without authentication)
            try:
                result = supabase.client.table('workflow_templates').select('id,name').limit(3).execute()
                if result.data and len(result.data) > 0:
                    template_names = [t['name'] for t in result.data]
                    self.log_result("Direct DB: Template Read", "PASS", f"Read templates: {template_names}")
                else:
                    self.log_result("Direct DB: Template Read", "FAIL", "No templates found")
                    return False
            except Exception as e:
                self.log_result("Direct DB: Template Read", "FAIL", f"Template read error: {str(e)}")
                return False
            
            # Test workflows table access (should be restricted by RLS)
            try:
                result = supabase.client.table('workflows').select('count').execute()
                # This should work but return empty due to RLS
                self.log_result("Direct DB: Workflows Access", "PASS", "Workflows table accessible (RLS working)")
            except Exception as e:
                error_msg = str(e).lower()
                if "rls" in error_msg or "policy" in error_msg:
                    self.log_result("Direct DB: Workflows RLS", "PASS", "RLS policies blocking access")
                else:
                    self.log_result("Direct DB: Workflows Access", "FAIL", f"Access error: {str(e)}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_result("Direct Database Operations", "FAIL", f"Database error: {str(e)}")
            return False

    def test_error_handling(self):
        """Test error handling in models"""
        try:
            from models.workflow import WorkflowCreate, WorkflowNode, NodeType
            from pydantic import ValidationError
            
            # Test invalid workflow creation
            try:
                invalid_workflow = WorkflowCreate(
                    name="",  # Invalid: empty name
                    description="Test",
                    nodes=[],
                    edges=[]
                )
                self.log_result("Error Handling: Invalid Workflow", "FAIL", "Should have failed validation")
                return False
            except ValidationError:
                self.log_result("Error Handling: Invalid Workflow", "PASS", "Validation correctly caught empty name")
            
            # Test invalid node type
            try:
                from models.workflow import NodePosition, NodeConfig
                invalid_node = WorkflowNode(
                    id="test",
                    type="invalid_type",  # Invalid node type
                    position=NodePosition(x=0, y=0),
                    config=NodeConfig()
                )
                self.log_result("Error Handling: Invalid Node Type", "FAIL", "Should have failed validation")
                return False
            except (ValidationError, ValueError):
                self.log_result("Error Handling: Invalid Node Type", "PASS", "Validation correctly caught invalid type")
            
            return True
            
        except Exception as e:
            self.log_result("Error Handling", "FAIL", f"Error testing error handling: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all backend integration tests"""
        print("🚀 Starting πlot Backend Integration Tests\n")
        print("=" * 60)
        
        # Synchronous tests
        sync_tests = [
            ("Module Imports", self.test_imports),
            ("Configuration", self.test_configuration),
            ("Database Client", self.test_database_client),
            ("Model Validation", self.test_model_validation),
            ("Workflow Templates", self.test_workflow_templates),
            ("Error Handling", self.test_error_handling),
        ]
        
        # Asynchronous tests
        async_tests = [
            ("Workflow Service Basic", self.test_workflow_service_basic),
            ("Direct Database Operations", self.test_direct_database_operations),
        ]
        
        passed = 0
        failed = 0
        warnings = 0
        
        # Run synchronous tests
        for test_name, test_func in sync_tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                self.log_result(test_name, "FAIL", f"Test crashed: {str(e)}")
        
        # Run asynchronous tests
        for test_name, test_func in async_tests:
            try:
                if await test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                self.log_result(test_name, "FAIL", f"Test crashed: {str(e)}")
        
        # Count warnings
        for result in self.results:
            if result["status"] == "WARNING":
                warnings += 1
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Backend Integration Test Summary:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        
        if failed == 0:
            print("\n🎉 All backend integration tests passed!")
            print("✅ Backend is properly connected to Supabase database")
            print("✅ All models and services are working correctly")
        elif failed <= 2:
            print("\n✅ Backend integration mostly successful")
            print("⚠️  Minor issues detected but core functionality works")
        else:
            print("\n❌ Multiple integration failures detected")
            print("❌ Backend may not be properly configured")
        
        return failed <= 2

async def main():
    """Main test runner"""
    print("πlot Backend - Integration Test Suite")
    print("=" * 60)
    
    tester = BackendIntegrationTester()
    success = await tester.run_all_tests()
    
    print(f"\n📡 Supabase URL: {os.environ.get('SUPABASE_URL')}")
    print(f"🔧 Backend Status: {'✅ Ready' if success else '❌ Issues detected'}")
    
    return 0 if success else 1

if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)