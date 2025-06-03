
import requests
import sys
import uuid
from datetime import datetime

class VenueCreationTester:
    def __init__(self, base_url="https://b50188aa-ef79-4083-9076-f7eb937c29b8.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.venue_owner_data = None
        self.venue_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None):
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

    def test_register_venue_owner(self):
        """Test venue owner registration"""
        # Generate unique username to avoid conflicts
        username = f"test_venue_owner_{uuid.uuid4().hex[:8]}"
        email = f"{username}@test.com"
        
        data = {
            "name": "Test Venue Owner",
            "email": email,
            "password": "Test123!",
            "role": "venue_owner"
        }
        
        success, response = self.run_test(
            "Register Venue Owner",
            "POST",
            "auth/register",
            200,
            data=data
        )
        
        if success:
            self.venue_owner_data = {"email": email, "password": "Test123!", "name": "Test Venue Owner"}
        
        return success, response

    def test_login_venue_owner(self):
        """Test venue owner login"""
        if not self.venue_owner_data:
            print("❌ No venue owner data available for login")
            return False, {}
            
        success, response = self.run_test(
            "Login as Venue Owner",
            "POST",
            "auth/login",
            200,
            data={"email": self.venue_owner_data["email"], "password": self.venue_owner_data["password"]}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True, response
        return False, response

    def test_create_venue(self):
        """Test venue creation"""
        data = {
            "name": f"Test Venue {uuid.uuid4().hex[:6]}",
            "description": "A beautiful venue for testing the venue creation functionality",
            "location": "123 Test Street, Test City",
            "price_per_day": 1000.0,
            "capacity": 100,
            "event_types": ["wedding", "birthday", "corporate"],
            "amenities": ["parking", "wifi", "catering"]
        }
        
        success, response = self.run_test(
            "Create Venue",
            "POST",
            "venues",
            200,
            data=data
        )
        
        if success and 'id' in response:
            self.venue_id = response['id']
            print(f"Created venue with ID: {self.venue_id}")
        
        return success, response

    def test_get_venue(self):
        """Test getting a specific venue"""
        if not self.venue_id:
            print("❌ No venue ID available for testing")
            return False, {}
        
        return self.run_test("Get Venue", "GET", f"venues/{self.venue_id}", 200)

def main():
    # Setup
    tester = VenueCreationTester()
    
    # Test venue owner registration and login
    print("\n=== Testing Venue Owner Authentication ===")
    success_owner, _ = tester.test_register_venue_owner()
    
    if success_owner:
        login_success, _ = tester.test_login_venue_owner()
        
        if login_success:
            # Test venue creation
            print("\n=== Testing Venue Creation ===")
            venue_success, venue_data = tester.test_create_venue()
            
            if venue_success:
                # Test venue retrieval
                tester.test_get_venue()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run} ({tester.tests_passed/tester.tests_run*100:.1f}%)")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
