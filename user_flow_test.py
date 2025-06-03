import requests
import sys
import uuid
from datetime import datetime, timedelta
import json

class Party2GoUserFlowTester:
    def __init__(self, base_url="https://b50188aa-ef79-4083-9076-f7eb937c29b8.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}
        self.test_users = {}
        self.test_venues = {}
        self.test_bookings = {}
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

    def register_user(self, role="user"):
        """Register a test user"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"test_{role}_{unique_id}@example.com",
            "password": "TestPass123!",
            "name": f"Test {role.capitalize()} {unique_id}",
            "role": role
        }
        
        success, response = self.run_test(
            f"Register {role}",
            "POST",
            "auth/register",
            201,
            data=user_data
        )
        
        if success and "token" in response:
            self.tokens[role] = response["token"]
            self.test_users[role] = user_data
            self.test_users[role]["id"] = response.get("user_id")
            return True
        return False

    def login_user(self, role="user"):
        """Login a test user"""
        if role not in self.test_users:
            print(f"No test {role} registered yet")
            return False
            
        login_data = {
            "email": self.test_users[role]["email"],
            "password": self.test_users[role]["password"]
        }
        
        success, response = self.run_test(
            f"Login {role}",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and "token" in response:
            self.tokens[role] = response["token"]
            return True
        return False

    def search_venues(self, params=None):
        """Search venues with filters"""
        if not params:
            params = {
                "location": "Test",
                "event_type": "wedding",
                "min_price": 100,
                "max_price": 5000
            }
            
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        
        success, response = self.run_test(
            "Search Venues",
            "GET",
            f"venues?{query_string}",
            200
        )
        
        if success and "venues" in response and len(response["venues"]) > 0:
            # Store the first venue ID for future tests
            self.test_venues["venue_id"] = response["venues"][0]["id"]
            return response["venues"]
        return []

    def get_venue_details(self, venue_id=None):
        """Get details of a specific venue"""
        if not venue_id and "venue_id" in self.test_venues:
            venue_id = self.test_venues["venue_id"]
        
        if not venue_id:
            print("No venue ID available")
            return None
            
        success, response = self.run_test(
            "Get Venue Details",
            "GET",
            f"venues/{venue_id}",
            200
        )
        
        return response if success else None

    def create_booking(self, venue_id=None):
        """Create a test booking"""
        if "user" not in self.tokens:
            print("No user token available")
            return None
            
        if not venue_id and "venue_id" in self.test_venues:
            venue_id = self.test_venues["venue_id"]
        
        if not venue_id:
            print("No venue ID available")
            return None
            
        # Get venue details to use in booking
        venue_details = self.get_venue_details(venue_id)
        if not venue_details:
            print("Failed to get venue details")
            return None
            
        # Create booking data
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        booking_data = {
            "name": "Test Booker",
            "email": self.test_users["user"]["email"],
            "event_date": tomorrow,
            "event_type": "birthday",
            "guests": 50,
            "message": "This is a test booking",
            "venue_id": venue_id,
            "venue_name": venue_details.get("name", "Test Venue"),
            "price_per_hour": venue_details.get("price_per_day", 1000) / 8,  # Assuming 8 hours per day
            "total_amount": venue_details.get("price_per_day", 1000) / 2,    # Assuming 4 hours booking
            "service_fee": venue_details.get("price_per_day", 1000) / 2 * 0.025,
            "owner_payout": venue_details.get("price_per_day", 1000) / 2 * 0.975
        }
        
        success, response = self.run_test(
            "Create Booking",
            "POST",
            "bookings",
            201,
            data=booking_data,
            role="user"
        )
        
        if success and "id" in response:
            booking_id = response["id"]
            self.test_bookings["booking_id"] = booking_id
            return booking_id
        return None

    def get_user_dashboard(self):
        """Get user dashboard data"""
        if "user" not in self.tokens:
            print("No user token available")
            return None
            
        success, response = self.run_test(
            "Get User Dashboard",
            "GET",
            "dashboard/user",
            200,
            role="user"
        )
        
        if success:
            # Verify booking appears in dashboard
            if "bookings" in response and len(response["bookings"]) > 0:
                if "booking_id" in self.test_bookings:
                    booking_found = any(b["id"] == self.test_bookings["booking_id"] for b in response["bookings"])
                    if booking_found:
                        print("✅ Booking found in user dashboard")
                    else:
                        print("❌ Booking not found in user dashboard")
            return response
        return None

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print(f"🧪 USER FLOW TESTS SUMMARY: {self.tests_passed}/{self.tests_run} passed")
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
    print("\n=== Testing User Booking Flow ===\n")
    
    # Setup
    tester = Party2GoUserFlowTester()
    
    # Test user registration and login
    tester.register_user(role="user")
    tester.login_user(role="user")
    
    # Test venue search
    venues = tester.search_venues()
    if not venues:
        print("❌ No venues found, cannot continue with booking flow")
        return 1
    
    # Test venue details
    venue_details = tester.get_venue_details()
    if not venue_details:
        print("❌ Failed to get venue details, cannot continue with booking flow")
        return 1
    
    # Test booking creation
    booking_id = tester.create_booking()
    if not booking_id:
        print("❌ Failed to create booking")
        return 1
    
    # Test user dashboard
    dashboard_data = tester.get_user_dashboard()
    if not dashboard_data:
        print("❌ Failed to get user dashboard")
        return 1
    
    # Print summary
    success = tester.print_summary()
    
    if success:
        print("\n🎉 User booking flow test passed successfully!")
    else:
        print("\n❌ User booking flow test failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())