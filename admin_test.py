import requests
import sys
import json
import uuid
from datetime import datetime, timedelta
import time

class AdminFunctionalityTester:
    def __init__(self, base_url="https://b50188aa-ef79-4083-9076-f7eb937c29b8.preview.emergentagent.com"):
        self.base_url = base_url
        self.admin_token = None
        self.admin_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, token=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            
            # Try to get JSON response, but handle cases where response is not JSON
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                self.test_results.append({
                    "name": name,
                    "status": "PASSED",
                    "expected": expected_status,
                    "actual": response.status_code
                })
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                self.test_results.append({
                    "name": name,
                    "status": "FAILED",
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response_data
                })

            return success, response_data

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "name": name,
                "status": "ERROR",
                "error": str(e)
            })
            return False, {}

    def register_admin(self, email, password, name):
        """Register a new admin user"""
        success, response = self.run_test(
            "Register Admin",
            "POST",
            "auth/register",
            200,
            data={"email": email, "password": password, "name": name, "role": "admin"}
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_data = response['user']
            return True, response
        return False, response

    def login_admin(self, email, password):
        """Login as admin"""
        success, response = self.run_test(
            "Login Admin",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_data = response['user']
            return True, response
        return False, response

    def get_admin_dashboard(self):
        """Get admin dashboard"""
        success, response = self.run_test(
            "Get Admin Dashboard",
            "GET",
            "dashboard/admin",
            200,
            token=self.admin_token
        )
        
        # Verify dashboard has all required sections
        if success:
            required_sections = ["total_users", "total_venues", "total_bookings", "platform_earnings", 
                                "users", "venues", "bookings"]
            
            missing_sections = [section for section in required_sections if section not in response]
            
            if missing_sections:
                print(f"❌ Admin dashboard missing sections: {', '.join(missing_sections)}")
                return False, response
            else:
                print(f"✅ Admin dashboard has all required sections")
                
        return success, response

    def test_admin_endpoints(self):
        """Test admin-specific endpoints"""
        # Test getting all users
        success1, response1 = self.run_test(
            "Admin - Get All Users",
            "GET",
            "users",
            200,
            token=self.admin_token
        )
        
        if success1 and 'users' in response1:
            print(f"✅ Admin can access user list with {response1.get('total', 0)} users")
        
        # Test getting all bookings
        success2, response2 = self.run_test(
            "Admin - Get All Bookings",
            "GET",
            "bookings",
            200,
            token=self.admin_token
        )
        
        if success2 and 'bookings' in response2:
            print(f"✅ Admin can access bookings list with {response2.get('total', 0)} bookings")
        
        return success1 and success2

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print(f"🧪 PARTY2GO ADMIN FUNCTIONALITY TEST SUMMARY")
        print("="*50)
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed / self.tests_run) * 100:.2f}%")
        print("="*50)
        
        # Print failed tests
        if self.tests_passed < self.tests_run:
            print("\nFailed Tests:")
            for test in self.test_results:
                if test["status"] != "PASSED":
                    print(f"- {test['name']}: {test['status']}")
        
        print("="*50)

def main():
    print("\n=== Testing Admin Functionality ===\n")
    
    # Setup
    tester = AdminFunctionalityTester()
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Register a test admin
    admin_email = f"admin_{timestamp}@example.com"
    test_password = "TestPass123!"
    register_success, _ = tester.register_admin(admin_email, test_password, "Test Admin")
    
    if not register_success:
        print("❌ Admin registration failed, aborting test")
        return 1
    
    # Get admin dashboard
    dashboard_success, _ = tester.get_admin_dashboard()
    
    if not dashboard_success:
        print("❌ Admin dashboard check failed")
    
    # Test admin-specific endpoints
    endpoints_success = tester.test_admin_endpoints()
    
    if not endpoints_success:
        print("❌ Admin endpoints test failed")
    
    # Print summary
    tester.print_summary()
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 Admin functionality test passed successfully!")
    else:
        print("\n❌ Admin functionality test failed")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())