import requests
import sys
import json
from datetime import datetime, timedelta

class Party2GoAPITester:
    def __init__(self, base_url="https://b50188aa-ef79-4083-9076-f7eb937c29b8.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
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
                    print(f"Response: {response.text}")
                    return False, response.json()
                except:
                    return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self, email, password):
        """Test login and get token"""
        success, response = self.run_test(
            "Login",
            "POST",
            "api/auth/login",
            200,
            data={"email": email, "password": password}
        )
        if success and 'token' in response:
            self.token = response['token']
            return True
        return False

    def test_register(self, email, password, name, role="user"):
        """Test user registration"""
        success, response = self.run_test(
            "Register User",
            "POST",
            "api/auth/register",
            201,
            data={"email": email, "password": password, "name": name, "role": role}
        )
        return success

    def test_get_venues(self):
        """Test getting all venues"""
        success, response = self.run_test(
            "Get All Venues",
            "GET",
            "api/venues",
            200
        )
        if success and len(response) > 0:
            self.venue_id = response[0]['id']
            return True
        return False

    def test_get_venue_details(self):
        """Test getting venue details"""
        if not self.venue_id:
            print("❌ No venue ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get Venue Details",
            "GET",
            f"api/venues/{self.venue_id}",
            200
        )
        
        # Check if price is a valid number (not NaN)
        if success:
            price = response.get('price_per_hour') or response.get('price_per_day')
            if price is not None:
                try:
                    float_price = float(price)
                    print(f"✅ Price validation passed: ${float_price}")
                    return True
                except ValueError:
                    print(f"❌ Price validation failed: {price} is not a valid number")
                    return False
        return success

    def test_create_booking(self):
        """Test creating a booking"""
        if not self.venue_id:
            print("❌ No venue ID available for testing")
            return False
            
        # Get venue details first to use in booking
        _, venue = self.run_test(
            "Get Venue for Booking",
            "GET",
            f"api/venues/{self.venue_id}",
            200
        )
        
        if not venue:
            return False
            
        # Create booking data
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        price_per_hour = venue.get('price_per_hour') or venue.get('price_per_day') or 100
        
        booking_data = {
            "name": "Test User",
            "email": "test@example.com",
            "event_date": tomorrow,
            "event_type": "birthday",
            "guests": "50",
            "message": "Test booking",
            "venue_id": self.venue_id,
            "venue_name": venue.get('name', 'Test Venue'),
            "price_per_hour": price_per_hour,
            "total_amount": price_per_hour * 4,  # 4 hours
            "service_fee": price_per_hour * 4 * 0.025,
            "owner_payout": price_per_hour * 4 * 0.975
        }
        
        success, response = self.run_test(
            "Create Booking",
            "POST",
            "api/bookings",
            201,
            data=booking_data
        )
        
        return success

def main():
    # Setup
    tester = Party2GoAPITester()
    
    # Run tests
    print("\n🚀 Starting Party2Go API Tests...\n")
    
    # Test venue listing and details (pricing display fix)
    if not tester.test_get_venues():
        print("❌ Failed to get venues, stopping tests")
        return 1
        
    if not tester.test_get_venue_details():
        print("❌ Failed to get venue details or price validation failed")
        return 1
    
    # Test booking creation
    if not tester.test_create_booking():
        print("❌ Booking creation failed")
        return 1
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())