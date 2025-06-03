import requests
import sys
import json
import uuid
from datetime import datetime, timedelta
import random

class Party2goVenueAPITester:
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
        self.venue_availability = []

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                if files:
                    # For file uploads, don't use JSON
                    headers.pop('Content-Type', None)
                    response = requests.post(url, data=data, files=files, headers=headers, params=params)
                else:
                    response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)

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
            200,
            data=data
        )
        
        if success:
            if role == "user":
                self.user_data = {"email": email, "password": "Test123!", "name": f"Test {role.capitalize()}"}
            elif role == "venue_owner":
                self.venue_owner_data = {"email": email, "password": "Test123!", "name": f"Test {role.capitalize()}"}
            elif role == "admin":
                self.admin_data = {"email": email, "password": "Test123!", "name": f"Test {role.capitalize()}"}
        
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

    def test_create_venue(self, venue_data=None):
        """Test venue creation"""
        # Generate availability for the next 30 days
        today = datetime.now()
        availability = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 31)]
        self.venue_availability = availability
        
        if venue_data is None:
            venue_data = {
                "name": f"Test Venue {uuid.uuid4().hex[:6]}",
                "description": "A beautiful venue for testing",
                "location": "Los Angeles, CA",
                "price_per_day": 1500.0,
                "capacity": 100,
                "event_types": ["wedding", "birthday"],
                "amenities": ["Parking", "WiFi", "Sound System"],
                "availability": availability
            }
        
        success, response = self.run_test(
            "Create Venue",
            "POST",
            "venues",
            200,
            data=venue_data
        )
        
        if success and 'id' in response:
            self.venue_id = response['id']
            print(f"Created venue with ID: {self.venue_id}")
        
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
        if not self.venue_id or not self.venue_availability:
            print("❌ No venue ID or availability available for testing")
            return False, {}
        
        # Use a date from the venue's availability
        event_date = self.venue_availability[0]
        
        data = {
            "venue_id": self.venue_id,
            "user_name": self.user_data["name"],
            "user_email": self.user_data["email"],
            "event_date": event_date,
            "event_type": "birthday",
            "message": "Test booking"
        }
        
        success, response = self.run_test(
            "Create Booking",
            "POST",
            "bookings",
            200,
            data=data
        )
        
        if success and 'booking' in response and 'id' in response['booking']:
            self.booking_id = response['booking']['id']
        
        return success, response

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
            data={"address": "123 Main St, New York, NY"}  # Using JSON data
        )

def test_venue_creation_flow():
    """Test the complete venue creation flow"""
    tester = Party2goVenueAPITester()
    
    print("\n=== Testing Venue Creation Flow ===")
    
    # 1. Register as a venue owner
    success_owner, _ = tester.test_register_user("venue_owner")
    if not success_owner:
        print("❌ Failed to register venue owner")
        return False
    
    # 2. Login as venue owner
    login_success, _ = tester.test_login(tester.venue_owner_data["email"], tester.venue_owner_data["password"])
    if not login_success:
        print("❌ Failed to login as venue owner")
        return False
    
    # 3. Create a venue with specific test data
    venue_data = {
        "name": "Test Venue",
        "description": "Beautiful venue for events",
        "location": "Los Angeles, CA",
        "price_per_day": 1500.0,
        "capacity": 100,
        "event_types": ["wedding", "birthday"],
        "amenities": ["Parking", "WiFi", "Sound System"],
        "availability": []
    }
    
    venue_success, venue_response = tester.test_create_venue(venue_data)
    if not venue_success:
        print("❌ Failed to create venue")
        return False
    
    # 4. Verify venue was created correctly
    get_success, venue_details = tester.test_get_venue()
    if not get_success:
        print("❌ Failed to retrieve venue")
        return False
    
    # 5. Verify venue data matches what we submitted
    data_correct = True
    for key, value in venue_data.items():
        if key in venue_details and venue_details[key] != value:
            print(f"❌ Venue data mismatch for {key}: expected {value}, got {venue_details[key]}")
            data_correct = False
    
    if data_correct:
        print("✅ Venue data verified correctly")
    
    # 6. Check venue appears in venue list
    list_success, venues_list = tester.test_get_venues()
    if not list_success:
        print("❌ Failed to retrieve venues list")
        return False
    
    venue_found = False
    for venue in venues_list:
        if venue.get('id') == tester.venue_id:
            venue_found = True
            break
    
    if venue_found:
        print("✅ Venue found in venues list")
    else:
        print("❌ Venue not found in venues list")
        return False
    
    # 7. Check owner dashboard shows the venue
    dashboard_success, dashboard_data = tester.test_owner_dashboard()
    if not dashboard_success:
        print("❌ Failed to retrieve owner dashboard")
        return False
    
    venue_in_dashboard = False
    if 'venues' in dashboard_data:
        for venue in dashboard_data['venues']:
            if venue.get('id') == tester.venue_id:
                venue_in_dashboard = True
                break
    
    if venue_in_dashboard:
        print("✅ Venue found in owner dashboard")
    else:
        print("❌ Venue not found in owner dashboard")
        return False
    
    print("\n✅ Complete venue creation flow tested successfully")
    return True

def main():
    # Run the venue creation flow test
    venue_creation_success = test_venue_creation_flow()
    
    if venue_creation_success:
        print("\n🎉 Venue creation flow test passed successfully!")
        return 0
    else:
        print("\n❌ Venue creation flow test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
