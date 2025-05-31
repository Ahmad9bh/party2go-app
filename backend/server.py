from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import cloudinary
import cloudinary.uploader
import googlemaps
import stripe

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Configuration
cloudinary.config(
    cloud_name=os.environ['CLOUDINARY_CLOUD_NAME'],
    api_key=os.environ['CLOUDINARY_API_KEY'],
    api_secret=os.environ['CLOUDINARY_API_SECRET']
)

gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])
stripe.api_key = os.environ['STRIPE_SECRET_KEY']

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI(title="Party Venue Booking API")
api_router = APIRouter(prefix="/api")

# Models
class UserRole(str):
    USER = "user"
    VENUE_OWNER = "venue_owner"
    ADMIN = "admin"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    role: str = UserRole.USER
    password_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = UserRole.USER

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class Venue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price_per_day: float
    capacity: int
    event_types: List[str]
    amenities: List[str]
    images: List[Dict[str, Any]] = []
    availability: List[str] = []  # Available dates in YYYY-MM-DD format
    owner_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    rating: float = 0.0
    total_reviews: int = 0

class VenueCreate(BaseModel):
    name: str
    description: str
    location: str
    price_per_day: float
    capacity: int
    event_types: List[str]
    amenities: List[str]
    availability: List[str] = []

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    venue_id: str
    user_id: str
    user_name: str
    user_email: EmailStr
    event_date: str  # YYYY-MM-DD format
    event_type: str
    message: Optional[str] = None
    total_amount: float
    service_fee: float
    owner_payout: float
    payment_status: str = "pending"  # pending, paid, cancelled
    booking_status: str = "pending"  # pending, confirmed, cancelled
    stripe_session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BookingCreate(BaseModel):
    venue_id: str
    user_name: str
    user_email: EmailStr
    event_date: str
    event_type: str
    message: Optional[str] = None

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    booking_id: Optional[str] = None
    amount: float
    currency: str = "usd"
    service_fee: float
    owner_payout: float
    payment_status: str = "pending"
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Helper functions
def mongo_doc_to_dict(doc):
    """Convert MongoDB document to dict, removing _id and converting ObjectId"""
    if doc is None:
        return None
    
    if isinstance(doc, list):
        return [mongo_doc_to_dict(item) for item in doc]
    
    if isinstance(doc, dict):
        # Remove MongoDB's _id field and convert any ObjectId fields
        result = {}
        for key, value in doc.items():
            if key == '_id':
                continue  # Skip MongoDB's _id field
            elif hasattr(value, '__dict__') and 'ObjectId' in str(type(value)):
                result[key] = str(value)  # Convert ObjectId to string
            elif isinstance(value, list):
                result[key] = [mongo_doc_to_dict(item) for item in value]
            elif isinstance(value, dict):
                result[key] = mongo_doc_to_dict(value)
            else:
                result[key] = value
        return result
    
    return doc

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=int(os.environ.get('JWT_EXPIRATION_HOURS', 24)))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.environ['JWT_SECRET_KEY'], algorithm=os.environ['JWT_ALGORITHM'])
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, os.environ['JWT_SECRET_KEY'], algorithms=[os.environ['JWT_ALGORITHM']])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = await db.users.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def calculate_fees(amount: float):
    service_fee = round(amount * 0.025, 2)  # 2.5% service fee
    owner_payout = round(amount - service_fee, 2)
    return service_fee, owner_payout

# Auth endpoints
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        password_hash=hashed_password
    )
    
    await db.users.insert_one(user.dict())
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    
    user_dict = user.dict()
    user_dict.pop('password_hash', None)
    
    return Token(access_token=access_token, token_type="bearer", user=user_dict)

@api_router.post("/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc or not verify_password(login_data.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user_doc["email"], "role": user_doc["role"]})
    
    # Convert MongoDB document to clean dict
    user_dict = mongo_doc_to_dict(user_doc)
    user_dict.pop('password_hash', None)
    
    return Token(access_token=access_token, token_type="bearer", user=user_dict)

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# Venue endpoints
@api_router.post("/venues", response_model=Venue)
async def create_venue(venue_data: VenueCreate, current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.VENUE_OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only venue owners can create venues")
    
    # Geocode the location
    try:
        geocode_result = gmaps.geocode(venue_data.location)
        if geocode_result:
            location = geocode_result[0]["geometry"]["location"]
            latitude = location["lat"]
            longitude = location["lng"]
        else:
            latitude = longitude = None
    except Exception:
        latitude = longitude = None
    
    venue = Venue(
        **venue_data.dict(),
        owner_id=current_user.id,
        latitude=latitude,
        longitude=longitude
    )
    
    await db.venues.insert_one(venue.dict())
    return venue

@api_router.get("/venues", response_model=List[Venue])
async def get_venues(
    location: Optional[str] = None,
    event_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_capacity: Optional[int] = None
):
    query = {}
    
    if event_type:
        query["event_types"] = {"$in": [event_type]}
    if min_price is not None:
        query["price_per_day"] = {"$gte": min_price}
    if max_price is not None:
        query.setdefault("price_per_day", {})["$lte"] = max_price
    if min_capacity is not None:
        query["capacity"] = {"$gte": min_capacity}
    
    venues = await db.venues.find(query).to_list(100)
    return [Venue(**venue) for venue in venues]

@api_router.get("/venues/{venue_id}", response_model=Venue)
async def get_venue(venue_id: str):
    venue = await db.venues.find_one({"id": venue_id})
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return Venue(**venue)

@api_router.post("/venues/{venue_id}/upload-images")
async def upload_venue_images(
    venue_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    venue = await db.venues.find_one({"id": venue_id})
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    if venue["owner_id"] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to upload images for this venue")
    
    uploaded_urls = []
    
    for file in files:
        try:
            result = cloudinary.uploader.upload(
                file.file,
                folder=f"venues/{venue_id}",
                transformation=[
                    {"width": 1920, "height": 1080, "crop": "limit"},
                    {"quality": "auto"},
                    {"fetch_format": "auto"}
                ]
            )
            
            uploaded_urls.append({
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "width": result.get("width"),
                "height": result.get("height")
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload {file.filename}: {str(e)}")
    
    await db.venues.update_one(
        {"id": venue_id},
        {"$push": {"images": {"$each": uploaded_urls}}}
    )
    
    return {"message": f"Successfully uploaded {len(uploaded_urls)} images", "images": uploaded_urls}

# Booking endpoints
@api_router.post("/bookings")
async def create_booking(booking_data: BookingCreate):
    venue = await db.venues.find_one({"id": booking_data.venue_id})
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Check if date is available
    if booking_data.event_date not in venue.get("availability", []):
        raise HTTPException(status_code=400, detail="Venue not available on selected date")
    
    # Calculate fees
    total_amount = venue["price_per_day"]
    service_fee, owner_payout = calculate_fees(total_amount)
    
    booking = Booking(
        **booking_data.dict(),
        total_amount=total_amount,
        service_fee=service_fee,
        owner_payout=owner_payout
    )
    
    await db.bookings.insert_one(booking.dict())
    return {"booking": booking.dict(), "message": "Booking created successfully"}

@api_router.post("/bookings/{booking_id}/payment")
async def create_payment_session(booking_id: str, request: Request):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["payment_status"] == "paid":
        raise HTTPException(status_code=400, detail="Booking already paid")
    
    # Get origin URL from request headers
    origin_url = str(request.base_url).rstrip('/')
    success_url = f"{origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/payment-cancel"
    
    # Create checkout session using standard Stripe API
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Venue Booking',
                        'description': f'Booking for venue {booking["venue_id"]}'
                    },
                    'unit_amount': int(booking["total_amount"] * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "booking_id": booking_id,
                "venue_id": booking["venue_id"],
                "user_email": booking["user_email"]
            }
        )
        
        # Create payment transaction record
        service_fee, owner_payout = calculate_fees(booking["total_amount"])
        payment_transaction = PaymentTransaction(
            session_id=session.id,
            booking_id=booking_id,
            amount=booking["total_amount"],
            service_fee=service_fee,
            owner_payout=owner_payout,
            metadata={
                "booking_id": booking_id,
                "venue_id": booking["venue_id"],
                "user_email": booking["user_email"]
            }
        )
        
        await db.payment_transactions.insert_one(payment_transaction.dict())
        await db.bookings.update_one(
            {"id": booking_id},
            {"$set": {"stripe_session_id": session.id}}
        )
        
        return {"checkout_url": session.url, "session_id": session.id}
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str):
    try:
        # Get checkout status from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Update payment transaction
        payment_transaction = await db.payment_transactions.find_one({"session_id": session_id})
        if payment_transaction:
            payment_status = "paid" if session.payment_status == "paid" else "pending"
            update_data = {
                "payment_status": payment_status
            }
            
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            # Update booking if payment successful
            if payment_status == "paid" and payment_transaction.get("booking_id"):
                await db.bookings.update_one(
                    {"id": payment_transaction["booking_id"]},
                    {"$set": {"payment_status": "paid", "booking_status": "confirmed"}}
                )
        
        return {
            "session_id": session_id,
            "payment_status": session.payment_status,
            "status": session.status,
            "amount_total": session.amount_total,
            "currency": session.currency
        }
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

# Dashboard endpoints
@api_router.get("/dashboard/owner")
async def get_owner_dashboard(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.VENUE_OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get venues
    venues = await db.venues.find({"owner_id": current_user.id}).to_list(100)
    
    # Get bookings for owner's venues
    venue_ids = [venue["id"] for venue in venues]
    bookings = await db.bookings.find({"venue_id": {"$in": venue_ids}}).to_list(1000)
    
    # Calculate earnings
    total_earnings = sum(booking["owner_payout"] for booking in bookings if booking["payment_status"] == "paid")
    total_fees_paid = sum(booking["service_fee"] for booking in bookings if booking["payment_status"] == "paid")
    
    return {
        "venues": venues,
        "bookings": bookings,
        "total_venues": len(venues),
        "total_bookings": len(bookings),
        "total_earnings": total_earnings,
        "total_fees_paid": total_fees_paid,
        "pending_bookings": len([b for b in bookings if b["booking_status"] == "pending"])
    }

@api_router.get("/dashboard/user")
async def get_user_dashboard(current_user: User = Depends(get_current_user)):
    bookings = await db.bookings.find({"user_email": current_user.email}).to_list(1000)
    
    # Get venue details for each booking
    for booking in bookings:
        venue = await db.venues.find_one({"id": booking["venue_id"]})
        booking["venue_details"] = venue
    
    return {
        "bookings": bookings,
        "total_bookings": len(bookings),
        "total_spent": sum(booking["total_amount"] for booking in bookings if booking["payment_status"] == "paid")
    }

@api_router.get("/dashboard/admin")
async def get_admin_dashboard(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all data
    users = await db.users.find().to_list(1000)
    venues = await db.venues.find().to_list(1000)
    bookings = await db.bookings.find().to_list(1000)
    transactions = await db.payment_transactions.find().to_list(1000)
    
    # Calculate platform earnings
    platform_earnings = sum(t["service_fee"] for t in transactions if t["payment_status"] == "paid")
    
    return {
        "total_users": len(users),
        "total_venues": len(venues),
        "total_bookings": len(bookings),
        "platform_earnings": platform_earnings,
        "users": users,
        "venues": venues,
        "bookings": bookings,
        "recent_transactions": transactions[-10:]  # Last 10 transactions
    }

# Geocoding endpoint
@api_router.post("/geocode")
async def geocode_address(address: str):
    try:
        result = gmaps.geocode(address)
        if not result:
            raise HTTPException(status_code=404, detail="Address not found")
        
        location = result[0]["geometry"]["location"]
        return {
            "lat": location["lat"],
            "lng": location["lng"],
            "formatted_address": result[0]["formatted_address"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Party Venue Booking API is running"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
