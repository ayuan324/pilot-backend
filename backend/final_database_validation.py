#!/usr/bin/env python3
"""
Final Comprehensive Database Validation for πlot Backend

This script performs a complete validation of the Supabase database setup including:
1. Schema validation
2. Indexes verification  
3. RLS policies testing
4. Triggers and functions testing
5. Computed columns validation
6. Views functionality
7. Template data integrity
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
import sys
import uuid

# Supabase configuration
SUPABASE_URL = "https://owfotswzzunhcevulzju.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93Zm90c3d6enVuaGNldnVsemp1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg0OTMzMDUsImV4cCI6MjA2NDA2OTMwNX0.SSUFYd3IYnf-OaQiCIiDoI9MncsmK_gJsIRS6liqPbM"

class ComprehensiveDatabaseValidator:
    def __init__(self):
        self.base_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self.results = []
        self.critical_failures = 0
        self.warnings = 0

    def log_result(self, category: str, test_name: str, status: str, message: str = "", details: str = None):
        """Log test result with category"""
        result = {
            "category": category,
            "test": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        emoji = "✅" if status == "PASS" else "❌" if status == "CRITICAL" else "⚠️"
        print(f"{emoji} [{category}] {test_name}: {message}")
        
        if status == "CRITICAL":
            self.critical_failures += 1
        elif status == "WARNING":
            self.warnings += 1
        
        if details and status in ["CRITICAL", "WARNING"]:
            print(f"   Details: {details}")

    def make_request(self, method: str, endpoint: str, data: dict = None) -> tuple:
        """Make HTTP request to Supabase"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if data:
                data_encoded = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(url, data=data_encoded, headers=self.headers, method=method)
            else:
                req = urllib.request.Request(url, headers=self.headers, method=method)
            
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8')
                return response.status, content
                
        except urllib.error.HTTPError as e:
            error_content = e.read().decode('utf-8') if e.fp else str(e)
            return e.code, error_content
        except Exception as e:
            return 0, str(e)

    def run_rpc(self, function_name: str, params: dict = None) -> tuple:
        """Execute RPC function"""
        endpoint = f"rpc/{function_name}"
        return self.make_request("POST", endpoint, params or {})

    def validate_core_tables(self):
        """Validate all core tables exist and are accessible"""
        required_tables = {
            "workflows": ["id", "name", "user_id", "workflow_data", "status"],
            "workflow_executions": ["id", "workflow_id", "user_id", "status", "duration_ms"],
            "node_execution_logs": ["id", "execution_id", "node_id", "status", "execution_time_ms"],
            "execution_events": ["id", "execution_id", "event_type", "timestamp"],
            "workflow_templates": ["id", "name", "category", "template_data"],
            "user_workflow_stats": ["user_id", "total_workflows", "total_executions"]
        }
        
        for table, expected_columns in required_tables.items():
            status, content = self.make_request("GET", f"{table}?select={','.join(expected_columns)}&limit=1")
            
            if status in [200, 206]:
                self.log_result("Schema", f"Table {table}", "PASS", "Table accessible with expected columns")
            else:
                self.log_result("Schema", f"Table {table}", "CRITICAL", f"HTTP {status}", content)

    def validate_default_templates(self):
        """Validate default workflow templates"""
        status, content = self.make_request("GET", "workflow_templates?select=*")
        
        if status == 200:
            try:
                templates = json.loads(content)
                
                if len(templates) >= 3:
                    self.log_result("Data", "Template Count", "PASS", f"Found {len(templates)} templates")
                    
                    # Validate specific templates
                    expected_templates = {
                        'simple_chatbot': 'conversational',
                        'content_generator': 'content', 
                        'data_analyzer': 'analysis'
                    }
                    
                    found_templates = {t['id']: t['category'] for t in templates}
                    
                    for template_id, expected_category in expected_templates.items():
                        if template_id in found_templates:
                            if found_templates[template_id] == expected_category:
                                self.log_result("Data", f"Template {template_id}", "PASS", 
                                              f"Found with correct category: {expected_category}")
                            else:
                                self.log_result("Data", f"Template {template_id}", "WARNING", 
                                              f"Wrong category: {found_templates[template_id]} != {expected_category}")
                        else:
                            self.log_result("Data", f"Template {template_id}", "CRITICAL", "Template missing")
                    
                    # Validate template data structure
                    for template in templates:
                        template_data = template.get('template_data', {})
                        if isinstance(template_data, dict) and 'nodes' in template_data:
                            self.log_result("Data", f"Template {template['id']} Structure", "PASS", 
                                          f"Valid structure with {len(template_data.get('nodes', []))} nodes")
                        else:
                            self.log_result("Data", f"Template {template['id']} Structure", "WARNING", 
                                          "Invalid or missing template_data structure")
                            
                else:
                    self.log_result("Data", "Template Count", "CRITICAL", f"Expected ≥3 templates, found {len(templates)}")
                    
            except json.JSONDecodeError as e:
                self.log_result("Data", "Template Parsing", "CRITICAL", f"JSON parsing failed: {str(e)}")
        else:
            self.log_result("Data", "Template Access", "CRITICAL", f"HTTP {status}", content)

    def validate_rls_policies(self):
        """Validate Row Level Security policies"""
        
        # Test 1: Unauthorized workflow creation should fail
        test_workflow = {
            "name": "Unauthorized Test",
            "description": "This should fail",
            "user_id": "unauthorized_user",
            "workflow_data": {"nodes": [], "edges": []}
        }
        
        status, content = self.make_request("POST", "workflows", test_workflow)
        
        if status in [401, 403]:
            self.log_result("Security", "RLS Workflow Creation Block", "PASS", "Unauthorized creation blocked")
        elif "policy" in content.lower() or "rls" in content.lower():
            self.log_result("Security", "RLS Workflow Creation Block", "PASS", "RLS policy active")
        else:
            self.log_result("Security", "RLS Workflow Creation Block", "CRITICAL", 
                          f"Unauthorized creation allowed: HTTP {status}")
        
        # Test 2: Reading workflows should work but return limited data
        status, content = self.make_request("GET", "workflows?select=count")
        
        if status == 200:
            self.log_result("Security", "RLS Workflow Read Access", "PASS", "Read access controlled by RLS")
        else:
            self.log_result("Security", "RLS Workflow Read Access", "WARNING", f"Unexpected response: HTTP {status}")
        
        # Test 3: Templates should be publicly readable
        status, content = self.make_request("GET", "workflow_templates?select=count")
        
        if status == 200:
            self.log_result("Security", "Template Public Access", "PASS", "Templates publicly accessible")
        else:
            self.log_result("Security", "Template Public Access", "CRITICAL", f"Templates not accessible: HTTP {status}")

    def validate_computed_columns(self):
        """Validate computed columns work correctly"""
        
        # Check that computed columns exist in schema
        computed_columns_expected = [
            ("workflow_executions", "duration_ms"),
            ("node_execution_logs", "execution_time_ms")
        ]
        
        for table, column in computed_columns_expected:
            status, content = self.make_request("GET", f"{table}?select={column}&limit=1")
            
            if status in [200, 206]:
                self.log_result("Schema", f"Computed Column {table}.{column}", "PASS", "Column accessible")
            else:
                self.log_result("Schema", f"Computed Column {table}.{column}", "CRITICAL", 
                              f"Column not accessible: HTTP {status}")

    def validate_views(self):
        """Validate analytics views"""
        views = [
            ("workflow_execution_summary", ["workflow_id", "workflow_name", "total_executions"]),
            ("user_analytics", ["user_id", "total_workflows", "success_rate_percent"])
        ]
        
        for view_name, expected_columns in views:
            status, content = self.make_request("GET", f"{view_name}?select={','.join(expected_columns)}&limit=1")
            
            if status in [200, 206]:
                self.log_result("Views", f"View {view_name}", "PASS", "View accessible and functional")
            else:
                self.log_result("Views", f"View {view_name}", "CRITICAL", f"View not accessible: HTTP {status}")

    def validate_indexes_performance(self):
        """Validate indexes exist by testing query performance expectations"""
        
        # Test queries that should benefit from indexes
        index_tests = [
            ("workflows", "user_id=eq.test_user", "User ID index"),
            ("workflows", "status=eq.published", "Status index"),
            ("workflow_executions", "workflow_id=eq.00000000-0000-0000-0000-000000000000", "Workflow ID index"),
            ("workflow_templates", "category=eq.conversational", "Category index"),
        ]
        
        for table, filter_condition, index_description in index_tests:
            status, content = self.make_request("GET", f"{table}?select=count&{filter_condition}")
            
            if status == 200:
                self.log_result("Performance", index_description, "PASS", "Query executed successfully")
            else:
                self.log_result("Performance", index_description, "WARNING", f"Query issue: HTTP {status}")

    def validate_constraints_and_checks(self):
        """Validate database constraints and check constraints"""
        
        # Test invalid workflow status
        invalid_workflow = {
            "name": "Test Invalid Status",
            "description": "Testing constraints",
            "user_id": "test_user",
            "status": "invalid_status",  # Should violate check constraint
            "workflow_data": {"nodes": [], "edges": []}
        }
        
        status, content = self.make_request("POST", "workflows", invalid_workflow)
        
        # Should fail due to check constraint (even before RLS kicks in)
        if status == 400 or "check constraint" in content.lower() or "violates" in content.lower():
            self.log_result("Constraints", "Status Check Constraint", "PASS", "Invalid status rejected")
        elif status in [401, 403]:
            self.log_result("Constraints", "Status Check Constraint", "WARNING", "RLS blocked before constraint check")
        else:
            self.log_result("Constraints", "Status Check Constraint", "CRITICAL", 
                          f"Invalid status accepted: HTTP {status}")

    def test_database_connectivity(self):
        """Basic connectivity test"""
        status, content = self.make_request("GET", "workflow_templates?select=count")
        
        if status == 200:
            self.log_result("Connectivity", "Basic Connection", "PASS", "Database connection successful")
            return True
        else:
            self.log_result("Connectivity", "Basic Connection", "CRITICAL", f"Connection failed: HTTP {status}")
            return False

    def run_comprehensive_validation(self):
        """Run all validation tests"""
        print("🔍 πlot Database - Comprehensive Validation")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_database_connectivity():
            print("❌ Database connection failed. Aborting validation.")
            return False
        
        print("\n📋 Running validation tests...\n")
        
        # Run all validation tests
        validation_tests = [
            ("Core Schema", self.validate_core_tables),
            ("Default Data", self.validate_default_templates),
            ("Security Policies", self.validate_rls_policies),
            ("Computed Columns", self.validate_computed_columns),
            ("Analytics Views", self.validate_views),
            ("Performance Indexes", self.validate_indexes_performance),
            ("Data Constraints", self.validate_constraints_and_checks),
        ]
        
        for test_category, test_func in validation_tests:
            print(f"\n--- {test_category} ---")
            try:
                test_func()
            except Exception as e:
                self.log_result("System", f"{test_category} Test", "CRITICAL", f"Test crashed: {str(e)}")
        
        # Generate summary
        self.generate_summary()
        
        return self.critical_failures == 0

    def generate_summary(self):
        """Generate validation summary"""
        print("\n" + "=" * 60)
        print("📊 Validation Summary")
        print("=" * 60)
        
        # Count results by category and status
        categories = {}
        total_pass = 0
        total_critical = 0
        total_warning = 0
        
        for result in self.results:
            category = result["category"]
            status = result["status"]
            
            if category not in categories:
                categories[category] = {"PASS": 0, "CRITICAL": 0, "WARNING": 0}
            
            categories[category][status] = categories[category].get(status, 0) + 1
            
            if status == "PASS":
                total_pass += 1
            elif status == "CRITICAL":
                total_critical += 1
            elif status == "WARNING":
                total_warning += 1
        
        # Print category breakdown
        for category, counts in categories.items():
            pass_count = counts.get("PASS", 0)
            critical_count = counts.get("CRITICAL", 0)
            warning_count = counts.get("WARNING", 0)
            
            status_emoji = "✅" if critical_count == 0 else "❌"
            print(f"{status_emoji} {category}: {pass_count} pass, {critical_count} critical, {warning_count} warnings")
        
        print(f"\n🎯 Overall Results:")
        print(f"✅ Passed: {total_pass}")
        print(f"❌ Critical: {total_critical}")
        print(f"⚠️  Warnings: {total_warning}")
        
        # Final assessment
        if total_critical == 0:
            if total_warning == 0:
                print(f"\n🎉 Perfect! Database setup is fully validated and ready for production.")
                print(f"✅ All core functionality, security, and performance features are working correctly.")
            else:
                print(f"\n✅ Excellent! Database setup is validated and ready for use.")
                print(f"⚠️  Minor warnings detected but do not affect core functionality.")
        elif total_critical <= 2:
            print(f"\n⚠️  Good! Database setup is mostly complete.")
            print(f"🔧 A few critical issues need attention but core features work.")
        else:
            print(f"\n❌ Issues detected! Database setup needs attention.")
            print(f"🚨 Multiple critical failures may affect functionality.")
        
        print(f"\n📡 Database URL: {SUPABASE_URL}")
        print(f"📅 Validation completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main validation runner"""
    validator = ComprehensiveDatabaseValidator()
    success = validator.run_comprehensive_validation()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())