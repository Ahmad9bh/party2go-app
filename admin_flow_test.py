import requests
import sys
import uuid
from datetime import datetime, timedelta
import json

class Party2GoAdminFlowTester:
    def __init__(self, base_url="https://b50188aa-ef79-4083-9076-f7eb937c29b8.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.test_users = {}
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = {}

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, role=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        elif role and role in self.tokens:
            headers['Authorization'] = f'Bearer {self.tokens[role]}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            
            # Try to parse response as JSON
            response_data = {}
            try:
                if response.text:
                    response_data = response.json()
            except:
                response_data = {"text": response.text}
                
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                self.test_results[name] = {"status": "PASS", "response": response_data}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                self.test_results[name] = {"status": "FAIL", "expected": expected_status, "actual": response.status_code, "response": response_data}

            return success, response_data

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results[name] = {"status": "ERROR", "error": str(e)}
            return False, {}

    def register_admin(self):
        """Register a test admin"""
        unique_id = str(uuid.uuid4())[:8]
        admin_data = {
            "email": f"test_admin_{unique_id}@example.com",
            "password": "AdminPass123!",
            "name": f"Test Admin {unique_id}",
            "role": "admin"
        }
        
        success, response = self.run_test(
            "Register Admin",
            "POST",
            "auth/register",
            200,  # API returns 200 instead of 201
            data=admin_data
        )
        
        if success and "access_token" in response:
            self.tokens["admin"] = response["access_token"]
            self.test_users["admin"] = admin_data
            self.test_users["admin"]["id"] = response.get("user", {}).get("id")
            return True
        return False

    def login_admin(self):
        """Login a test admin"""
        if "admin" not in self.test_users:
            print("No test admin registered yet")
            return False
            
        login_data = {
            "email": self.test_users["admin"]["email"],
            "password": self.test_users["admin"]["password"]
        }
        
        success, response = self.run_test(
            "Login Admin",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and "access_token" in response:
            self.tokens["admin"] = response["access_token"]
            return True
        return False

    def get_admin_dashboard(self):
        """Get admin dashboard data"""
        if "admin" not in self.tokens:
            print("No admin token available")
            return None
            
        success, response = self.run_test(
            "Get Admin Dashboard",
            "GET",
            "dashboard/admin",
            200,
            role="admin"
        )
        
        if success:
            # Verify dashboard data
            required_fields = ["total_users", "total_venues", "total_bookings", "platform_earnings"]
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"❌ Missing fields in admin dashboard: {', '.join(missing_fields)}")
            else:
                print("✅ Admin dashboard contains all required fields")
                
            return response
        return None

    def get_all_users(self):
        """Get all users (admin only)"""
        if "admin" not in self.tokens:
            print("No admin token available")
            return None
            
        success, response = self.run_test(
            "Get All Users",
            "GET",
            "users",
            200,
            role="admin"
        )
        
        if success:
            if isinstance(response, list):
                return response
            return response.get("users", [])
        return []

    def get_all_venues(self):
        """Get all venues"""
        success, response = self.run_test(
            "Get All Venues",
            "GET",
            "venues",
            200,
            role="admin"
        )
        
        if success:
            if isinstance(response, list):
                return response
            return response.get("venues", [])
        return []

    def get_all_bookings(self):
        """Get all bookings (admin only)"""
        if "admin" not in self.tokens:
            print("No admin token available")
            return None
            
        success, response = self.run_test(
            "Get All Bookings",
            "GET",
            "bookings",
            200,
            role="admin"
        )
        
        return response.get("bookings", []) if success else []

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print(f"🧪 ADMIN FLOW TESTS SUMMARY: {self.tests_passed}/{self.tests_run} passed")
        print("="*50)
        
        # Group results by status
        passed = {k: v for k, v in self.test_results.items() if v["status"] == "PASS"}
        failed = {k: v for k, v in self.test_results.items() if v["status"] == "FAIL"}
        errors = {k: v for k, v in self.test_results.items() if v["status"] == "ERROR"}
        
        print(f"\n✅ PASSED TESTS ({len(passed)}): {', '.join(passed.keys())}")
        
        if failed:
            print(f"\n❌ FAILED TESTS ({len(failed)}):")
            for name, result in failed.items():
                print(f"  - {name}: Expected {result['expected']}, got {result['actual']}")
                
        if errors:
            print(f"\n⚠️ ERRORS ({len(errors)}):")
            for name, result in errors.items():
                print(f"  - {name}: {result['error']}")
                
        return self.tests_passed == self.tests_run

def main():
    print("\n=== Testing Admin Flow ===\n")
    
    # Setup
    tester = Party2GoAdminFlowTester()
    
    # Test admin registration and login
    tester.register_admin()
    tester.login_admin()
    
    # Test admin dashboard
    dashboard_data = tester.get_admin_dashboard()
    if not dashboard_data:
        print("❌ Failed to get admin dashboard")
        return 1
    
    # Test getting all users
    users = tester.get_all_users()
    if users is None:
        print("❌ Failed to get all users")
        return 1
    
    # Test getting all venues
    venues = tester.get_all_venues()
    if venues is None:
        print("❌ Failed to get all venues")
        return 1
    
    # Test getting all bookings
    bookings = tester.get_all_bookings()
    if bookings is None:
        print("❌ Failed to get all bookings")
        return 1
    
    # Print summary
    success = tester.print_summary()
    
    if success:
        print("\n🎉 Admin flow test passed successfully!")
    else:
        print("\n❌ Admin flow test failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())