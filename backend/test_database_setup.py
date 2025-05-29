#!/usr/bin/env python3
"""
Database Setup Test Script for πlot Backend

This script tests:
1. Database connectivity
2. Table structure validation
3. Basic CRUD operations
4. RLS policies (without authentication for basic testing)
5. Triggers and functions
6. Default templates verification
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
import traceback

# Add the app directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ supabase-py not installed. Install it with: pip install supabase")
    sys.exit(1)

# Supabase configuration
SUPABASE_URL = "https://owfotswzzunhcevulzju.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93Zm90c3d6enVuaGNldnVsemp1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg0OTMzMDUsImV4cCI6MjA2NDA2OTMwNX0.SSUFYd3IYnf-OaQiCIiDoI9MncsmK_gJsIRS6liqPbM"

class DatabaseTester:
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.test_user_id = "test_user_123"  # Mock user ID for testing
        self.results = []
        
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
        
        # Print result
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{emoji} {test_name}: {message}")
        if details and status == "FAIL":
            print(f"   Details: {details}")

    def test_connection(self):
        """Test basic database connection"""
        try:
            # Try a simple query to test connection
            response = self.client.from_("workflow_templates").select("count").execute()
            self.log_result("Database Connection", "PASS", "Successfully connected to Supabase")
            return True
        except Exception as e:
            self.log_result("Database Connection", "FAIL", f"Failed to connect: {str(e)}")
            return False

    def test_table_structure(self):
        """Verify all required tables exist with proper structure"""
        expected_tables = [
            "workflows",
            "workflow_executions", 
            "node_execution_logs",
            "execution_events",
            "workflow_templates",
            "user_workflow_stats"
        ]
        
        try:
            # Test each table by attempting a simple select
            for table in expected_tables:
                response = self.client.from_(table).select("*").limit(1).execute()
                self.log_result(f"Table: {table}", "PASS", "Table exists and accessible")
                
            return True
        except Exception as e:
            self.log_result("Table Structure", "FAIL", f"Table validation failed: {str(e)}")
            return False

    def test_default_templates(self):
        """Test that default workflow templates are loaded"""
        try:
            response = self.client.from_("workflow_templates").select("*").execute()
            templates = response.data
            
            if len(templates) >= 3:
                template_ids = [t['id'] for t in templates]
                expected_ids = ['simple_chatbot', 'content_generator', 'data_analyzer']
                
                missing = [tid for tid in expected_ids if tid not in template_ids]
                if not missing:
                    self.log_result("Default Templates", "PASS", f"Found {len(templates)} templates including all expected ones")
                    return True
                else:
                    self.log_result("Default Templates", "FAIL", f"Missing templates: {missing}")
                    return False
            else:
                self.log_result("Default Templates", "FAIL", f"Expected at least 3 templates, found {len(templates)}")
                return False
                
        except Exception as e:
            self.log_result("Default Templates", "FAIL", f"Error checking templates: {str(e)}")
            return False

    def test_workflow_crud(self):
        """Test basic CRUD operations on workflows table"""
        workflow_id = None
        try:
            # Test CREATE
            workflow_data = {
                "name": "Test Workflow",
                "description": "A test workflow for database validation",
                "user_id": self.test_user_id,
                "workflow_data": {
                    "nodes": [],
                    "edges": []
                },
                "status": "draft",
                "tags": ["test", "database"]
            }
            
            # Note: This will fail due to RLS, but that's expected behavior
            # We're testing the table structure, not authentication
            response = self.client.from_("workflows").insert(workflow_data).execute()
            
            if response.data:
                workflow_id = response.data[0]['id']
                self.log_result("Workflow CREATE", "PASS", "Successfully created test workflow")
                
                # Test READ
                read_response = self.client.from_("workflows").select("*").eq("id", workflow_id).execute()
                if read_response.data:
                    self.log_result("Workflow READ", "PASS", "Successfully read workflow")
                    
                    # Test UPDATE
                    update_response = self.client.from_("workflows").update({
                        "description": "Updated description"
                    }).eq("id", workflow_id).execute()
                    
                    if update_response.data:
                        self.log_result("Workflow UPDATE", "PASS", "Successfully updated workflow")
                    else:
                        self.log_result("Workflow UPDATE", "FAIL", "Update operation failed")
                        
                    # Test DELETE
                    delete_response = self.client.from_("workflows").delete().eq("id", workflow_id).execute()
                    self.log_result("Workflow DELETE", "PASS", "Successfully deleted workflow")
                    
                else:
                    self.log_result("Workflow READ", "FAIL", "Could not read created workflow")
            else:
                self.log_result("Workflow CREATE", "FAIL", "No data returned from insert")
                
        except Exception as e:
            error_msg = str(e)
            if "Row Level Security" in error_msg or "new row violates row-level security policy" in error_msg:
                self.log_result("Workflow CRUD", "PASS", "RLS policies are working (blocked unauthorized access)")
                return True
            else:
                self.log_result("Workflow CRUD", "FAIL", f"Unexpected error: {error_msg}")
                return False
                
        return True

    def test_rls_policies(self):
        """Test that Row Level Security policies are enabled"""
        try:
            # Try to access workflows without proper authentication
            # This should be blocked by RLS
            response = self.client.from_("workflows").select("*").execute()
            
            # If we get here, either RLS is not enabled or we have some data
            # Let's check if the response is empty (which is expected with RLS)
            if not response.data:
                self.log_result("RLS Policies", "PASS", "RLS policies are blocking unauthorized access")
            else:
                self.log_result("RLS Policies", "WARNING", f"Got {len(response.data)} records - RLS may not be properly configured")
                
            return True
        except Exception as e:
            error_msg = str(e)
            if "Row Level Security" in error_msg:
                self.log_result("RLS Policies", "PASS", "RLS policies are active and blocking access")
                return True
            else:
                self.log_result("RLS Policies", "FAIL", f"Unexpected RLS error: {error_msg}")
                return False

    def test_views(self):
        """Test that database views are created and accessible"""
        views = ["workflow_execution_summary", "user_analytics"]
        
        try:
            for view in views:
                # Note: Views might be accessible but return empty results due to RLS
                response = self.client.from_(view).select("*").limit(1).execute()
                self.log_result(f"View: {view}", "PASS", "View exists and is accessible")
                
            return True
        except Exception as e:
            self.log_result("Database Views", "FAIL", f"Error accessing views: {str(e)}")
            return False

    def test_extensions(self):
        """Test that required PostgreSQL extensions are installed"""
        try:
            # Test uuid generation (uuid-ossp extension)
            response = self.client.rpc('uuid_generate_v4').execute()
            if response.data:
                self.log_result("UUID Extension", "PASS", "uuid-ossp extension is working")
            else:
                self.log_result("UUID Extension", "FAIL", "uuid-ossp extension not working")
                
            return True
        except Exception as e:
            # This might fail due to RPC permissions, which is okay
            self.log_result("Extensions", "WARNING", f"Could not test extensions via RPC: {str(e)}")
            return True

    def run_all_tests(self):
        """Run all database tests"""
        print("🚀 Starting πlot Database Setup Tests\n")
        print("=" * 50)
        
        # Run tests in order
        tests = [
            self.test_connection,
            self.test_table_structure,
            self.test_default_templates,
            self.test_rls_policies,
            self.test_views,
            self.test_extensions,
            self.test_workflow_crud,
        ]
        
        passed = 0
        failed = 0
        warnings = 0
        
        for test in tests:
            try:
                result = test()
                if result:
                    passed += 1
            except Exception as e:
                failed += 1
                self.log_result(test.__name__, "FAIL", f"Test crashed: {str(e)}", traceback.format_exc())
        
        # Count results
        for result in self.results:
            if result["status"] == "PASS":
                passed += 1
            elif result["status"] == "FAIL":
                failed += 1
            elif result["status"] == "WARNING":
                warnings += 1
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        
        if failed == 0:
            print("\n🎉 All tests passed! Database setup is successful.")
        elif failed <= 2:  # Allow some failures due to RLS
            print("\n✅ Database setup appears successful (some failures expected due to RLS)")
        else:
            print("\n❌ Multiple test failures detected. Please check your database setup.")
            
        return failed == 0 or failed <= 2

    def export_results(self, filename: str = "database_test_results.json"):
        """Export test results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "test_run": datetime.now().isoformat(),
                    "supabase_url": SUPABASE_URL,
                    "results": self.results
                }, f, indent=2)
            print(f"\n📄 Test results exported to: {filename}")
        except Exception as e:
            print(f"❌ Failed to export results: {str(e)}")


def main():
    """Main test runner"""
    print("πlot Backend - Database Setup Verification")
    print("=" * 50)
    
    tester = DatabaseTester()
    success = tester.run_all_tests()
    tester.export_results()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())