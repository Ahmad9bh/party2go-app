
import requests
import sys
import json
import uuid
from datetime import datetime, timedelta
import random

class PartyVenueAPITester:
    def __init__(self, base_url="https://b50188aa-ef79-4083-9076-f7eb937c29b8.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_data = None
        self.venue_owner_data = None
        self.admin_data = None
        self.venue_id = None
        self.booking_id = None
        self.session_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    # For file uploads, don't use JSON
                    headers.pop('Content-Type', None)
                    response = requests.post(url, data=data, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'No detail provided')
                    print(f"Error: {error_detail}")
                except:
                    print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test the health check endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_register_user(self, role="user"):
        """Test user registration"""
        # Generate unique username to avoid conflicts
        username = f"test_{role}_{uuid.uuid4().hex[:8]}"
        email = f"{username}@test.com"
        
        data = {
            "name": f"Test {role.capitalize()}",
            "email": email,
            "password": "Test123!",
            "role": role
        }
        
        success, response = self.run_test(
            f"Register {role}",
            "POST",
            "auth/register",
            201,
            data=data
        )
        
        if success:
            if role == "user":
                self.user_data = {"email": email, "password": "Test123!"}
            elif role == "venue_owner":
                self.venue_owner_data = {"email": email, "password": "Test123!"}
            elif role == "admin":
                self.admin_data = {"email": email, "password": "Test123!"}
        
        return success, response

    def test_login(self, email, password):
        """Test login and get token"""
        success, response = self.run_test(
            "Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True, response
        return False, response

    def test_get_current_user(self):
        """Test getting current user info"""
        return self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_create_venue(self):
        """Test venue creation"""
        data = {
            "name": f"Test Venue {uuid.uuid4().hex[:6]}",
            "description": "A beautiful venue for testing",
            "location": "123 Test Street, Test City",
            "price_per_hour": 100.0,
            "capacity": 100,
            "event_types": ["wedding", "birthday", "corporate"],
            "amenities": ["parking", "wifi", "catering"],
            "lat": 40.7128,
            "lng": -74.0060,
            "images": []
        }
        
        success, response = self.run_test(
            "Create Venue",
            "POST",
            "venues",
            201,
            data=data
        )
        
        if success and 'id' in response:
            self.venue_id = response['id']
        
        return success, response

    def test_get_venues(self):
        """Test getting all venues"""
        return self.run_test("Get All Venues", "GET", "venues", 200)

    def test_get_venue(self):
        """Test getting a specific venue"""
        if not self.venue_id:
            print("❌ No venue ID available for testing")
            return False, {}
        
        return self.run_test("Get Venue", "GET", f"venues/{self.venue_id}", 200)

    def test_create_booking(self):
        """Test booking creation"""
        if not self.venue_id:
            print("❌ No venue ID available for testing")
            return False, {}
        
        # Book for tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        event_date = tomorrow.strftime("%Y-%m-%d")
        
        data = {
            "venue_id": self.venue_id,
            "event_date": event_date,
            "start_time": "14:00",
            "end_time": "18:00",
            "guest_count": 50,
            "event_type": "birthday",
            "special_requests": "Test booking"
        }
        
        success, response = self.run_test(
            "Create Booking",
            "POST",
            "bookings",
            201,
            data=data
        )
        
        if success and 'id' in response:
            self.booking_id = response['id']
            if 'checkout_url' in response and 'session_id' in response:
                self.session_id = response['session_id']
        
        return success, response

    def test_get_bookings(self):
        """Test getting all bookings"""
        return self.run_test("Get All Bookings", "GET", "bookings", 200)

    def test_get_booking(self):
        """Test getting a specific booking"""
        if not self.booking_id:
            print("❌ No booking ID available for testing")
            return False, {}
        
        return self.run_test("Get Booking", "GET", f"bookings/{self.booking_id}", 200)

    def test_payment_status(self):
        """Test payment status endpoint"""
        if not self.session_id:
            print("❌ No session ID available for testing")
            return False, {}
        
        return self.run_test("Get Payment Status", "GET", f"payments/status/{self.session_id}", 200)

    def test_user_dashboard(self):
        """Test user dashboard endpoint"""
        return self.run_test("Get User Dashboard", "GET", "dashboard/user", 200)

    def test_owner_dashboard(self):
        """Test venue owner dashboard endpoint"""
        return self.run_test("Get Owner Dashboard", "GET", "dashboard/owner", 200)

    def test_admin_dashboard(self):
        """Test admin dashboard endpoint"""
        return self.run_test("Get Admin Dashboard", "GET", "dashboard/admin", 200)

    def test_geocode(self):
        """Test geocoding endpoint"""
        return self.run_test(
            "Geocode Address",
            "POST",
            "geocode",
            200,
            data="123 Main St, New York, NY"
        )

def main():
    # Setup
    tester = PartyVenueAPITester()
    
    # Test health check
    tester.test_health_check()
    
    # Test user registration and login
    print("\n=== Testing Authentication ===")
    success_user, _ = tester.test_register_user("user")
    if success_user:
        tester.test_login(tester.user_data["email"], tester.user_data["password"])
        tester.test_get_current_user()
    
    # Test venue owner registration and login
    success_owner, _ = tester.test_register_user("venue_owner")
    if success_owner:
        tester.test_login(tester.venue_owner_data["email"], tester.venue_owner_data["password"])
        tester.test_get_current_user()
        
        # Test venue creation and retrieval
        print("\n=== Testing Venue Management ===")
        tester.test_create_venue()
        tester.test_get_venues()
        tester.test_get_venue()
    
    # Test user booking flow
    if success_user and tester.venue_id:
        print("\n=== Testing Booking System ===")
        tester.test_login(tester.user_data["email"], tester.user_data["password"])
        tester.test_create_booking()
        tester.test_get_bookings()
        tester.test_get_booking()
        if tester.session_id:
            tester.test_payment_status()
    
    # Test dashboards
    print("\n=== Testing Dashboards ===")
    
    # User dashboard
    if success_user:
        tester.test_login(tester.user_data["email"], tester.user_data["password"])
        tester.test_user_dashboard()
    
    # Owner dashboard
    if success_owner:
        tester.test_login(tester.venue_owner_data["email"], tester.venue_owner_data["password"])
        tester.test_owner_dashboard()
    
    # Admin dashboard - register admin if needed
    success_admin, _ = tester.test_register_user("admin")
    if success_admin:
        tester.test_login(tester.admin_data["email"], tester.admin_data["password"])
        tester.test_admin_dashboard()
    
    # Test geocoding
    print("\n=== Testing Geocoding ===")
    tester.test_geocode()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run} ({tester.tests_passed/tester.tests_run*100:.1f}%)")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
