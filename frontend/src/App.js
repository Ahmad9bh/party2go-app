import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route, Link, Navigate, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { Search, MapPin, Calendar, Users, Star, Heart, Menu, X, Upload, DollarSign, User, LogOut, Settings, Plus } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserInfo();
    }
  }, [token]);

  const fetchUserInfo = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      logout();
    }
  };

  const login = (tokenData) => {
    localStorage.setItem('token', tokenData.access_token);
    setToken(tokenData.access_token);
    setUser(tokenData.user);
    axios.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access_token}`;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => React.useContext(AuthContext);

// Components
const Header = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <header className="bg-gradient-to-r from-pink-500 via-purple-500 to-teal-500 text-white shadow-lg">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link to="/" className="text-3xl font-bold flex items-center">
          🎉 Party2go
        </Link>
        
        <nav className="hidden md:flex space-x-6">
          <Link to="/" className="hover:text-yellow-300 transition">Home</Link>
          <Link to="/venues" className="hover:text-yellow-300 transition">Venues</Link>
          {isAuthenticated && (
            <Link to="/dashboard" className="hover:text-yellow-300 transition">Dashboard</Link>
          )}
        </nav>

        <div className="flex items-center space-x-4">
          {isAuthenticated ? (
            <div className="relative">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="flex items-center space-x-2 bg-white/20 px-3 py-2 rounded-lg hover:bg-white/30 transition"
              >
                <User size={20} />
                <span>{user?.name}</span>
              </button>
              
              {isMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 z-50">
                  <button
                    onClick={() => { navigate('/dashboard'); setIsMenuOpen(false); }}
                    className="w-full text-left px-4 py-2 text-gray-800 hover:bg-gray-100 flex items-center space-x-2"
                  >
                    <Settings size={16} />
                    <span>Dashboard</span>
                  </button>
                  <button
                    onClick={() => { logout(); setIsMenuOpen(false); }}
                    className="w-full text-left px-4 py-2 text-gray-800 hover:bg-gray-100 flex items-center space-x-2"
                  >
                    <LogOut size={16} />
                    <span>Logout</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="space-x-2">
              <Link to="/login" className="bg-white text-purple-600 px-4 py-2 rounded-lg font-semibold hover:bg-yellow-300 transition">
                Login
              </Link>
              <Link to="/register" className="bg-yellow-400 text-purple-800 px-4 py-2 rounded-lg font-semibold hover:bg-yellow-300 transition">
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

const HomePage = () => {
  const [searchLocation, setSearchLocation] = useState('');
  const [eventType, setEventType] = useState('');
  const [featuredVenues, setFeaturedVenues] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchFeaturedVenues();
  }, []);

  const fetchFeaturedVenues = async () => {
    try {
      const response = await axios.get(`${API}/venues`);
      setFeaturedVenues(response.data.slice(0, 6));
    } catch (error) {
      console.error('Error fetching venues:', error);
    }
  };

  const handleSearch = () => {
    const params = new URLSearchParams();
    if (searchLocation) params.append('location', searchLocation);
    if (eventType) params.append('event_type', eventType);
    navigate(`/venues?${params.toString()}`);
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative h-96 bg-gradient-to-r from-pink-400 via-purple-500 to-teal-400 flex items-center justify-center text-white">
        <div className="absolute inset-0 bg-black/30"></div>
        <img 
          src="https://images.pexels.com/photos/11282246/pexels-photo-11282246.jpeg" 
          alt="Party2go venue" 
          className="absolute inset-0 w-full h-full object-cover mix-blend-overlay"
        />
        <div className="relative z-10 text-center max-w-4xl mx-auto px-4">
          <h1 className="text-5xl font-bold mb-4">Find the Perfect Venue for Your Celebration! 🎉</h1>
          <p className="text-xl mb-8">Book amazing venues for weddings, birthdays, graduations, and more!</p>
          
          <div className="bg-white p-6 rounded-xl shadow-lg max-w-2xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="relative">
                <MapPin className="absolute left-3 top-3 text-purple-500" size={20} />
                <input
                  type="text"
                  placeholder="Enter location..."
                  value={searchLocation}
                  onChange={(e) => setSearchLocation(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border rounded-lg text-gray-800 focus:ring-2 focus:ring-purple-500"
                />
              </div>
              
              <select
                value={eventType}
                onChange={(e) => setEventType(e.target.value)}
                className="w-full px-4 py-2 border rounded-lg text-gray-800 focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Event Type</option>
                <option value="wedding">Wedding</option>
                <option value="birthday">Birthday</option>
                <option value="graduation">Graduation</option>
                <option value="corporate">Corporate</option>
                <option value="anniversary">Anniversary</option>
              </select>
              
              <button
                onClick={handleSearch}
                className="bg-gradient-to-r from-pink-500 to-purple-600 text-white px-6 py-2 rounded-lg font-semibold hover:from-pink-600 hover:to-purple-700 transition flex items-center justify-center space-x-2"
              >
                <Search size={20} />
                <span>Search</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Venues */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-12 text-gray-800">Featured Venues ✨</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {featuredVenues.map((venue) => (
              <div key={venue.id} className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition transform hover:-translate-y-2">
                <div className="relative h-48">
                  <img
                    src={venue.images?.[0]?.url || "https://images.unsplash.com/photo-1513151233558-d860c5398176"}
                    alt={venue.name}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-4 right-4 bg-white/90 px-2 py-1 rounded-lg">
                    <span className="text-purple-600 font-bold">${venue.price_per_day}/day</span>
                  </div>
                </div>
                
                <div className="p-6">
                  <h3 className="text-xl font-bold mb-2 text-gray-800">{venue.name}</h3>
                  <p className="text-gray-600 mb-3 flex items-center">
                    <MapPin size={16} className="mr-1 text-purple-500" />
                    {venue.location}
                  </p>
                  <p className="text-gray-600 mb-3 flex items-center">
                    <Users size={16} className="mr-1 text-purple-500" />
                    Capacity: {venue.capacity} guests
                  </p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Star className="text-yellow-400" size={16} />
                      <span className="ml-1 text-gray-600">{venue.rating || 4.5} ({venue.total_reviews || 12} reviews)</span>
                    </div>
                    <Link
                      to={`/venues/${venue.id}`}
                      className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition"
                    >
                      View Details
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-teal-400 to-pink-500 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-6">Ready to Host Your Dream Event? 🌟</h2>
          <p className="text-xl mb-8">Join thousands of happy customers who found their perfect venue with Party2go!</p>
          <div className="space-x-4">
            <Link to="/venues" className="bg-white text-purple-600 px-8 py-3 rounded-lg font-semibold hover:bg-yellow-300 transition">
              Browse Venues
            </Link>
            <Link to="/register?role=venue_owner" className="bg-yellow-400 text-purple-800 px-8 py-3 rounded-lg font-semibold hover:bg-yellow-300 transition">
              List Your Venue
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};

const VenueList = () => {
  const [venues, setVenues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    location: '',
    event_type: '',
    min_price: '',
    max_price: '',
    min_capacity: ''
  });

  useEffect(() => {
    fetchVenues();
  }, []);

  const fetchVenues = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      const response = await axios.get(`${API}/venues?${params.toString()}`);
      setVenues(response.data);
    } catch (error) {
      console.error('Error fetching venues:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    fetchVenues();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading amazing venues...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <h1 className="text-4xl font-bold text-center mb-8 text-gray-800">Find Your Perfect Venue 🎪</h1>
        
        {/* Filters */}
        <div className="bg-white p-6 rounded-xl shadow-lg mb-8">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Filter Venues</h2>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <input
              type="text"
              placeholder="Location"
              value={filters.location}
              onChange={(e) => handleFilterChange('location', e.target.value)}
              className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
            />
            
            <select
              value={filters.event_type}
              onChange={(e) => handleFilterChange('event_type', e.target.value)}
              className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
            >
              <option value="">All Event Types</option>
              <option value="wedding">Wedding</option>
              <option value="birthday">Birthday</option>
              <option value="graduation">Graduation</option>
              <option value="corporate">Corporate</option>
            </select>
            
            <input
              type="number"
              placeholder="Min Price"
              value={filters.min_price}
              onChange={(e) => handleFilterChange('min_price', e.target.value)}
              className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
            />
            
            <input
              type="number"
              placeholder="Max Price"
              value={filters.max_price}
              onChange={(e) => handleFilterChange('max_price', e.target.value)}
              className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
            />
            
            <button
              onClick={applyFilters}
              className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition flex items-center justify-center space-x-2"
            >
              <Search size={20} />
              <span>Apply Filters</span>
            </button>
          </div>
        </div>

        {/* Venue Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {venues.map((venue) => (
            <div key={venue.id} className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition transform hover:-translate-y-2">
              <div className="relative h-48">
                <img
                  src={venue.images?.[0]?.url || "https://images.pexels.com/photos/9543812/pexels-photo-9543812.jpeg"}
                  alt={venue.name}
                  className="w-full h-full object-cover"
                />
                <div className="absolute top-4 right-4 bg-white/90 px-2 py-1 rounded-lg">
                  <span className="text-purple-600 font-bold">${venue.price_per_day}/day</span>
                </div>
              </div>
              
              <div className="p-6">
                <h3 className="text-xl font-bold mb-2 text-gray-800">{venue.name}</h3>
                <p className="text-gray-600 mb-3 line-clamp-2">{venue.description}</p>
                <p className="text-gray-600 mb-3 flex items-center">
                  <MapPin size={16} className="mr-1 text-purple-500" />
                  {venue.location}
                </p>
                <p className="text-gray-600 mb-3 flex items-center">
                  <Users size={16} className="mr-1 text-purple-500" />
                  Capacity: {venue.capacity} guests
                </p>
                
                <div className="flex flex-wrap gap-1 mb-4">
                  {venue.event_types?.slice(0, 3).map((type) => (
                    <span key={type} className="bg-purple-100 text-purple-600 px-2 py-1 rounded-full text-xs">
                      {type}
                    </span>
                  ))}
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Star className="text-yellow-400" size={16} />
                    <span className="ml-1 text-gray-600">{venue.rating || 4.5}</span>
                  </div>
                  <Link
                    to={`/venues/${venue.id}`}
                    className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition"
                  >
                    View Details
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {venues.length === 0 && (
          <div className="text-center py-16">
            <h3 className="text-2xl font-semibold text-gray-600 mb-4">No venues found</h3>
            <p className="text-gray-500">Try adjusting your search filters</p>
          </div>
        )}
      </div>
    </div>
  );
};

const VenueDetail = () => {
  const { id } = useParams();
  const [venue, setVenue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showBookingForm, setShowBookingForm] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchVenue();
  }, [id]);

  const fetchVenue = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/venues/${id}`);
      setVenue(response.data);
    } catch (error) {
      setError('Venue not found');
      console.error('Error fetching venue:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-50 to-teal-100 flex items-center justify-center">
        <div className="text-2xl text-gray-600">Loading venue details...</div>
      </div>
    );
  }

  if (error || !venue) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-50 to-teal-100 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-800 mb-4">Venue Not Found</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => navigate('/venues')}
            className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition"
          >
            Back to Venues
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-50 to-teal-100 py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/venues')}
            className="text-purple-600 hover:text-purple-800 mb-4 flex items-center"
          >
            ← Back to Venues
          </button>
        </div>

        {/* Venue Details */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          {/* Image */}
          {venue.image_url && (
            <div className="h-96 bg-gray-200">
              <img
                src={venue.image_url}
                alt={venue.name}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          <div className="p-8">
            {/* Title and Price */}
            <div className="flex justify-between items-start mb-6">
              <div>
                <h1 className="text-4xl font-bold text-gray-800 mb-2">{venue.name}</h1>
                <p className="text-xl text-gray-600 flex items-center">
                  📍 {venue.location}
                </p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-purple-600">${venue.price_per_hour || venue.price_per_day || 100}/hour</div>
                <div className="text-sm text-gray-500">Starting price</div>
              </div>
            </div>

            {/* Description */}
            <div className="mb-8">
              <h3 className="text-2xl font-semibold text-gray-800 mb-4">About This Venue</h3>
              <p className="text-gray-700 leading-relaxed">{venue.description}</p>
            </div>

            {/* Amenities */}
            {venue.amenities && venue.amenities.length > 0 && (
              <div className="mb-8">
                <h3 className="text-2xl font-semibold text-gray-800 mb-4">Amenities</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {venue.amenities.map((amenity, index) => (
                    <div key={index} className="flex items-center text-gray-700">
                      <span className="text-green-500 mr-2">✓</span>
                      {amenity}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Details */}
            <div className="grid md:grid-cols-2 gap-8 mb-8">
              <div>
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Venue Details</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Event Types:</span>
                    <span className="text-gray-800">{venue.event_types?.join(', ') || 'All events'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Capacity:</span>
                    <span className="text-gray-800">{venue.capacity || 'Contact for details'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Rating:</span>
                    <span className="text-gray-800">⭐ {venue.rating || 4.5}/5</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Contact & Booking</h3>
                <div className="space-y-4">
                  <button
                    onClick={() => setShowBookingForm(true)}
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-4 px-6 rounded-lg font-semibold text-lg hover:from-purple-700 hover:to-pink-700 transition"
                  >
                    Book This Venue 🎉
                  </button>
                  <p className="text-sm text-gray-500 text-center">
                    No payment required now. Owner will contact you with details.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Booking Form Modal */}
        {showBookingForm && (
          <BookingForm
            venue={venue}
            onClose={() => setShowBookingForm(false)}
          />
        )}
      </div>
    </div>
  );
};

const BookingForm = ({ venue, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    event_date: '',
    event_type: '',
    guests: '',
    message: ''
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const pricePerHour = venue.price_per_hour || venue.price_per_day || 100;
      const bookingData = {
        ...formData,
        venue_id: venue.id,
        venue_name: venue.name,
        price_per_hour: pricePerHour,
        total_amount: pricePerHour * 4, // Assuming 4 hours default
        service_fee: pricePerHour * 4 * 0.025,
        owner_payout: pricePerHour * 4 * 0.975
      };

      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/bookings`, bookingData);
      setSuccess(true);
    } catch (error) {
      console.error('Booking error:', error);
      alert('Failed to submit booking request. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h3 className="text-2xl font-bold text-gray-800 mb-4">Booking Request Sent!</h3>
            <p className="text-gray-600 mb-6">
              We've sent your booking request to the venue owner. They'll contact you within 24 hours with confirmation and payment details.
            </p>
            <button
              onClick={onClose}
              className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-8 max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-800">Book {venue.name}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-700 mb-2">Full Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Email *</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-700 mb-2">Event Date *</label>
              <input
                type="date"
                required
                value={formData.event_date}
                onChange={(e) => setFormData({...formData, event_date: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Event Type *</label>
              <select
                required
                value={formData.event_type}
                onChange={(e) => setFormData({...formData, event_type: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="">Select event type</option>
                <option value="wedding">Wedding</option>
                <option value="birthday">Birthday Party</option>
                <option value="graduation">Graduation</option>
                <option value="corporate">Corporate Event</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-gray-700 mb-2">Expected Guests</label>
            <input
              type="number"
              value={formData.guests}
              onChange={(e) => setFormData({...formData, guests: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Number of guests"
            />
          </div>

          <div>
            <label className="block text-gray-700 mb-2">Special Message</label>
            <textarea
              value={formData.message}
              onChange={(e) => setFormData({...formData, message: e.target.value})}
              rows="4"
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Any special requirements or questions..."
            />
          </div>

          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-800 mb-2">Pricing Estimate</h4>
            <div className="text-sm text-gray-600">
              <div className="flex justify-between">
                <span>Base rate (4 hours):</span>
                <span>${((venue.price_per_hour || venue.price_per_day || 100) * 4).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span>Service fee (2.5%):</span>
                <span>${((venue.price_per_hour || venue.price_per_day || 100) * 4 * 0.025).toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-semibold border-t pt-2 mt-2">
                <span>Total estimate:</span>
                <span>${((venue.price_per_hour || venue.price_per_day || 100) * 4 * 1.025).toFixed(2)}</span>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Final pricing will be confirmed by venue owner based on your specific requirements.
            </p>
          </div>

          <div className="flex gap-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-300 text-gray-700 py-3 px-6 rounded-lg hover:bg-gray-400 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 px-6 rounded-lg hover:from-purple-700 hover:to-pink-700 transition disabled:opacity-50"
            >
              {loading ? 'Sending...' : 'Send Booking Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const RegisterPage = () => {
  const [formData, setFormData] = useState({ email: '', password: '', name: '', role: 'user' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/auth/register`, formData);
      login(response.data);
      navigate('/dashboard');
    } catch (error) {
      setError(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-400 via-purple-500 to-teal-400 flex items-center justify-center px-4">
      <div className="bg-white p-8 rounded-xl shadow-2xl max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Join the Party2go! 🎉</h1>
          <p className="text-gray-600">Create your Party2go account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter your name"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter your email"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">Password</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter your password"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">Role</label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="user">User</option>
              <option value="venue_owner">Venue Owner</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 transition disabled:opacity-50"
          >
            {loading ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600">
          Already have an account?{' '}
          <Link to="/login" className="text-purple-600 hover:text-purple-800 font-semibold">
            Sign in here
          </Link>
        </p>
      </div>
    </div>
  );
};
const LoginPage = () => {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API}/auth/login`, formData);
      login(response.data);
      navigate('/dashboard');
    } catch (error) {
      setError(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-400 via-purple-500 to-teal-400 flex items-center justify-center px-4">
      <div className="bg-white p-8 rounded-xl shadow-2xl max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Welcome Back! 🎉</h1>
          <p className="text-gray-600">Sign in to your Party2go account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">Email</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter your email"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2">Password</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Enter your password"
              required
            />
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 transition disabled:opacity-50"
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600">
          Don't have an account?{' '}
          <Link to="/register" className="text-purple-600 hover:text-purple-800 font-semibold">
            Sign up here
          </Link>
        </p>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user } = useAuth();
  
  if (!user) return <Navigate to="/login" />;
  
  if (user.role === 'venue_owner') return <OwnerDashboard />;
  if (user.role === 'admin') return <AdminDashboard />;
  return <UserDashboard />;
};

const UserDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/user`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <h1 className="text-4xl font-bold mb-8 text-gray-800">My Dashboard 🎪</h1>
        
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Bookings</h3>
            <p className="text-3xl font-bold text-purple-600">{dashboardData?.total_bookings || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Spent</h3>
            <p className="text-3xl font-bold text-green-600">${dashboardData?.total_spent || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Upcoming Events</h3>
            <p className="text-3xl font-bold text-teal-600">
              {dashboardData?.bookings?.filter(b => new Date(b.event_date) > new Date()).length || 0}
            </p>
          </div>
        </div>

        {/* Bookings List */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="p-6 border-b">
            <h2 className="text-2xl font-semibold text-gray-800">My Bookings</h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Venue</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {dashboardData?.bookings?.map((booking) => (
                  <tr key={booking.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{booking.venue_details?.name}</div>
                        <div className="text-sm text-gray-500">{booking.venue_details?.location}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(booking.event_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${booking.total_amount}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        booking.payment_status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {booking.payment_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

const OwnerDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/owner`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800">Venue Owner Dashboard 🏛️</h1>
          <Link 
            to="/venues/new" 
            className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition flex items-center space-x-2"
          >
            <Plus size={20} />
            <span>Add New Venue</span>
          </Link>
        </div>
        
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Venues</h3>
            <p className="text-3xl font-bold text-purple-600">{dashboardData?.total_venues || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Bookings</h3>
            <p className="text-3xl font-bold text-blue-600">{dashboardData?.total_bookings || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Earnings</h3>
            <p className="text-3xl font-bold text-green-600">${dashboardData?.total_earnings || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Service Fees Paid</h3>
            <p className="text-3xl font-bold text-red-600">${dashboardData?.total_fees_paid || 0}</p>
          </div>
        </div>

        {/* Recent Bookings */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="p-6 border-b">
            <h2 className="text-2xl font-semibold text-gray-800">Recent Bookings</h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Guest</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Venue</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Your Earnings</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {dashboardData?.bookings?.slice(0, 10).map((booking) => (
                  <tr key={booking.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{booking.user_name}</div>
                      <div className="text-sm text-gray-500">{booking.user_email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {dashboardData.venues.find(v => v.id === booking.venue_id)?.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(booking.event_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${booking.total_amount}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                      ${booking.owner_payout}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        booking.payment_status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {booking.payment_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

const AdminDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/admin`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <h1 className="text-4xl font-bold mb-8 text-gray-800">Admin Dashboard 👑</h1>
        
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Users</h3>
            <p className="text-3xl font-bold text-blue-600">{dashboardData?.total_users || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Venues</h3>
            <p className="text-3xl font-bold text-purple-600">{dashboardData?.total_venues || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Total Bookings</h3>
            <p className="text-3xl font-bold text-teal-600">{dashboardData?.total_bookings || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-lg">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Platform Earnings</h3>
            <p className="text-3xl font-bold text-green-600">${dashboardData?.platform_earnings || 0}</p>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="p-6 border-b">
            <h2 className="text-2xl font-semibold text-gray-800">Recent Transactions</h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Transaction ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Service Fee</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {dashboardData?.recent_transactions?.map((transaction) => (
                  <tr key={transaction.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      {transaction.session_id.substring(0, 20)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${transaction.amount}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                      ${transaction.service_fee}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        transaction.payment_status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {transaction.payment_status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(transaction.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <Elements stripe={stripePromise}>
      <AuthProvider>
        <div className="App">
          <BrowserRouter>
            <Header />
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/venues" element={<VenueList />} />
              <Route path="/venues/:id" element={<VenueDetail />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
          </BrowserRouter>
        </div>
      </AuthProvider>
    </Elements>
  );
}

export default App;
