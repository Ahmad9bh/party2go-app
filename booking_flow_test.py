import requests
import sys
import json
import uuid
from datetime import datetime, timedelta
import time

class BookingFlowTester:
    def __init__(self, base_url="https://b50188aa-ef79-4083-9076-f7eb937c29b8.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.test_venue_id = None
        self.test_booking_id = None
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

    def register_user(self, email, password, name, role="user"):
        """Register a new user"""
        success, response = self.run_test(
            f"Register {role}",
            "POST",
            "auth/register",
            200,
            data={"email": email, "password": password, "name": name, "role": role}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response['user']
            return True, response
        return False, response

    def login_user(self, email, password):
        """Login a user"""
        success, response = self.run_test(
            "Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response['user']
            return True, response
        return False, response

    def search_venues(self, location="Los Angeles"):
        """Search for venues"""
        success, response = self.run_test(
            "Search Venues",
            "GET",
            "venues",
            200,
            params={"location": location}
        )
        
        # Find a venue to use for booking
        if success and len(response) > 0:
            self.test_venue_id = response[0]['id']
            print(f"Found venue for testing: {response[0]['name']} (ID: {self.test_venue_id})")
            return True, response
        else:
            print("❌ No venues found for testing")
            return False, response

    def get_venue_details(self, venue_id):
        """Get venue details"""
        success, response = self.run_test(
            "Get Venue Details",
            "GET",
            f"venues/{venue_id}",
            200
        )
        return success, response

    def create_booking(self, venue_id):
        """Create a booking"""
        # Use a date 7 days in the future
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        booking_data = {
            "venue_id": venue_id,
            "user_name": "John Doe",
            "user_email": "john@example.com",
            "event_date": future_date,
            "event_type": "wedding",
            "message": "Test booking request",
            "guests": 50
        }
        
        success, response = self.run_test(
            "Create Booking",
            "POST",
            "bookings",
            200,
            data=booking_data,
            token=self.token
        )
        
        if success and 'booking' in response and 'id' in response['booking']:
            self.test_booking_id = response['booking']['id']
            print(f"Created booking with ID: {self.test_booking_id}")
            return True, response
        return False, response

    def get_user_dashboard(self):
        """Get user dashboard"""
        success, response = self.run_test(
            "Get User Dashboard",
            "GET",
            "dashboard/user",
            200,
            token=self.token
        )
        
        # Verify the booking appears in the dashboard
        if success and 'bookings' in response:
            booking_found = False
            for booking in response['bookings']:
                if booking['id'] == self.test_booking_id:
                    booking_found = True
                    print(f"✅ Booking found in user dashboard")
                    break
            
            if not booking_found and self.test_booking_id:
                print(f"❌ Booking not found in user dashboard")
                return False, response
                
        return success, response

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print(f"🧪 PARTY2GO BOOKING FLOW TEST SUMMARY")
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
    print("\n=== Testing Complete Booking Flow ===\n")
    
    # Setup
    tester = BookingFlowTester()
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Register a test user
    user_email = f"user_{timestamp}@example.com"
    test_password = "TestPass123!"
    register_success, _ = tester.register_user(user_email, test_password, "Test User")
    
    if not register_success:
        print("❌ User registration failed, aborting test")
        return 1
    
    # Search for venues
    search_success, _ = tester.search_venues()
    
    if not search_success or not tester.test_venue_id:
        print("❌ Venue search failed, aborting test")
        return 1
    
    # Get venue details
    tester.get_venue_details(tester.test_venue_id)
    
    # Create a booking
    booking_success, _ = tester.create_booking(tester.test_venue_id)
    
    if not booking_success:
        print("❌ Booking creation failed, aborting test")
        return 1
    
    # Check user dashboard
    dashboard_success, _ = tester.get_user_dashboard()
    
    if not dashboard_success:
        print("❌ Dashboard check failed")
    
    # Print summary
    tester.print_summary()
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 Complete booking flow test passed successfully!")
    else:
        print("\n❌ Booking flow test failed")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())