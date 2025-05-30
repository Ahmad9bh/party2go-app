
import requests
import sys
import time
import uuid
from datetime import datetime, timedelta

class PartyVenueAPITester:
    def __init__(self, base_url="https://b50188aa-ef79-4083-9076-f7eb937c29b8.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_data = {}

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
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
                    error_detail = response.json()
                    print(f"Error details: {error_detail}")
                except:
                    print(f"Response text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test the health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        return success

    def test_register_user(self, role="user"):
        """Test user registration"""
        # Generate unique email to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_{role}_{unique_id}@example.com"
        password = "Test123!"
        name = f"Test {role.capitalize()} {unique_id}"
        
        success, response = self.run_test(
            f"Register {role}",
            "POST",
            "auth/register",
            200,
            data={
                "email": email,
                "name": name,
                "password": password,
                "role": role
            }
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user = response['user']
            self.test_data['user'] = {
                'email': email,
                'password': password,
                'name': name,
                'role': role,
                'id': response['user']['id']
            }
            return True
        return False

    def test_login(self, email=None, password=None):
        """Test login functionality"""
        if not email and not password and 'user' in self.test_data:
            email = self.test_data['user']['email']
            password = self.test_data['user']['password']
        
        success, response = self.run_test(
            "Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user = response['user']
            return True
        return False

    def test_get_current_user(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_create_venue(self):
        """Test venue creation"""
        if self.user['role'] not in ['venue_owner', 'admin']:
            print("⚠️ Skipping venue creation - user is not a venue owner or admin")
            return False
        
        venue_data = {
            "name": f"Test Venue {str(uuid.uuid4())[:8]}",
            "description": "A beautiful venue for testing purposes",
            "location": "123 Test Street, New York, NY",
            "price_per_day": 1000.0,
            "capacity": 100,
            "event_types": ["wedding", "birthday", "corporate"],
            "amenities": ["parking", "wifi", "catering"],
            "availability": [
                (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(1, 30)
            ]
        }
        
        success, response = self.run_test(
            "Create Venue",
            "POST",
            "venues",
            200,
            data=venue_data
        )
        
        if success:
            self.test_data['venue'] = response
            return True
        return False

    def test_get_venues(self):
        """Test getting venues list"""
        success, response = self.run_test(
            "Get Venues",
            "GET",
            "venues",
            200
        )
        
        if success and isinstance(response, list):
            print(f"Found {len(response)} venues")
            return True
        return False

    def test_get_venue_by_id(self):
        """Test getting a venue by ID"""
        if 'venue' not in self.test_data:
            print("⚠️ Skipping get venue by ID - no venue created yet")
            return False
        
        venue_id = self.test_data['venue']['id']
        success, response = self.run_test(
            "Get Venue by ID",
            "GET",
            f"venues/{venue_id}",
            200
        )
        return success

    def test_create_booking(self):
        """Test booking creation"""
        if 'venue' not in self.test_data:
            print("⚠️ Skipping booking creation - no venue created yet")
            return False
        
        venue = self.test_data['venue']
        booking_data = {
            "venue_id": venue['id'],
            "user_name": self.user['name'],
            "user_email": self.user['email'],
            "event_date": venue['availability'][0],
            "event_type": venue['event_types'][0],
            "message": "This is a test booking"
        }
        
        success, response = self.run_test(
            "Create Booking",
            "POST",
            "bookings",
            200,
            data=booking_data
        )
        
        if success and 'booking' in response:
            self.test_data['booking'] = response['booking']
            return True
        return False

    def test_create_payment_session(self):
        """Test creating a payment session"""
        if 'booking' not in self.test_data:
            print("⚠️ Skipping payment session creation - no booking created yet")
            return False
        
        booking_id = self.test_data['booking']['id']
        success, response = self.run_test(
            "Create Payment Session",
            "POST",
            f"bookings/{booking_id}/payment",
            200
        )
        
        if success and 'checkout_url' in response:
            self.test_data['payment'] = response
            return True
        return False

    def test_get_payment_status(self):
        """Test getting payment status"""
        if 'payment' not in self.test_data:
            print("⚠️ Skipping payment status check - no payment session created yet")
            return False
        
        session_id = self.test_data['payment']['session_id']
        success, response = self.run_test(
            "Get Payment Status",
            "GET",
            f"payments/status/{session_id}",
            200
        )
        return success

    def test_user_dashboard(self):
        """Test user dashboard"""
        if self.user['role'] != 'user' and self.user['role'] != 'admin':
            print("⚠️ Skipping user dashboard - user is not a regular user")
            return True  # Not a failure
        
        success, response = self.run_test(
            "User Dashboard",
            "GET",
            "dashboard/user",
            200
        )
        return success

    def test_owner_dashboard(self):
        """Test venue owner dashboard"""
        if self.user['role'] != 'venue_owner' and self.user['role'] != 'admin':
            print("⚠️ Skipping owner dashboard - user is not a venue owner")
            return True  # Not a failure
        
        success, response = self.run_test(
            "Owner Dashboard",
            "GET",
            "dashboard/owner",
            200
        )
        return success

    def test_admin_dashboard(self):
        """Test admin dashboard"""
        if self.user['role'] != 'admin':
            print("⚠️ Skipping admin dashboard - user is not an admin")
            return True  # Not a failure
        
        success, response = self.run_test(
            "Admin Dashboard",
            "GET",
            "dashboard/admin",
            200
        )
        return success

    def test_geocode(self):
        """Test geocoding endpoint"""
        success, response = self.run_test(
            "Geocode Address",
            "POST",
            "geocode",
            200,
            data="New York, NY"
        )
        return success

def main():
    # Setup
    tester = PartyVenueAPITester()
    
    # Test health check
    if not tester.test_health_check():
        print("❌ Health check failed, stopping tests")
        return 1

    # Test user registration and authentication
    print("\n=== Testing Authentication ===")
    if not tester.test_register_user(role="user"):
        print("❌ User registration failed, stopping tests")
        return 1
    
    if not tester.test_get_current_user():
        print("❌ Get current user failed")
    
    if not tester.test_login():
        print("❌ Login failed")

    # Test user dashboard
    print("\n=== Testing User Dashboard ===")
    tester.test_user_dashboard()
    
    # Test venue owner functionality
    print("\n=== Testing Venue Owner Functionality ===")
    # Register a venue owner
    venue_owner_tester = PartyVenueAPITester()
    if not venue_owner_tester.test_register_user(role="venue_owner"):
        print("❌ Venue owner registration failed")
    else:
        # Create a venue
        if not venue_owner_tester.test_create_venue():
            print("❌ Venue creation failed")
        else:
            # Test venue retrieval
            venue_owner_tester.test_get_venues()
            venue_owner_tester.test_get_venue_by_id()
            
            # Test owner dashboard
            venue_owner_tester.test_owner_dashboard()
            
            # Test booking flow as a user
            if not tester.test_login():
                print("❌ User login failed")
            else:
                # Use the venue created by the venue owner
                tester.test_data['venue'] = venue_owner_tester.test_data['venue']
                
                # Create a booking
                if not tester.test_create_booking():
                    print("❌ Booking creation failed")
                else:
                    # Create a payment session
                    if not tester.test_create_payment_session():
                        print("❌ Payment session creation failed")
                    else:
                        # Check payment status
                        tester.test_get_payment_status()
    
    # Test admin functionality
    print("\n=== Testing Admin Functionality ===")
    admin_tester = PartyVenueAPITester()
    if not admin_tester.test_register_user(role="admin"):
        print("❌ Admin registration failed")
    else:
        admin_tester.test_admin_dashboard()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"📊 Venue owner tests passed: {venue_owner_tester.tests_passed}/{venue_owner_tester.tests_run}")
    print(f"📊 Admin tests passed: {admin_tester.tests_passed}/{admin_tester.tests_run}")
    
    total_passed = tester.tests_passed + venue_owner_tester.tests_passed + admin_tester.tests_passed
    total_run = tester.tests_run + venue_owner_tester.tests_run + admin_tester.tests_run
    
    print(f"\n📊 Total tests passed: {total_passed}/{total_run} ({(total_passed/total_run)*100:.2f}%)")
    
    return 0 if total_passed == total_run else 1

if __name__ == "__main__":
    sys.exit(main())
