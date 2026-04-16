import React, { useContext, useState, useMemo, useEffect } from 'react';
import { Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { AppContext } from '../context/AppContext';
import type { DeliveryLocation, Customer, Order } from '../types';
import { LocationMarkerIcon } from './icons';
import MapModal from './MapModal';
import StripePayment from './StripePayment';
//import { MMAMASHIA_COORDS } from '../constants';
import { api } from '../services/api';

// Load Stripe with your publishable key
const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '');
const MMAMASHIA_COORDS = { lat: -24.6581, lng: 25.9087 };

// Haversine formula to calculate distance between two points in km
const haversineDistance = (coords1: { lat: number; lng: number }, coords2: { lat: number; lng: number }): number => {
  const R = 6371;
  const dLat = (coords2.lat - coords1.lat) * Math.PI / 180;
  const dLng = (coords2.lng - coords1.lng) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(coords1.lat * Math.PI / 180) * Math.cos(coords2.lat * Math.PI / 180) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

const CheckoutView: React.FC = () => {
  const context = useContext(AppContext);
  
  const [customerInfo, setCustomerInfo] = useState<Customer>(() => {
    return { name: '', email: '', phone: '' };
  });
  
  const [location, setLocation] = useState<DeliveryLocation | null>(null);
  const [distance, setDistance] = useState<number | null>(null);
  const [isLocating, setIsLocating] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<Order['paymentMethod']>('eft');
  const [isMapOpen, setIsMapOpen] = useState(false);
  const [formErrors, setFormErrors] = useState<Partial<Record<keyof Customer, string>>>({});
  
  const [showPasteCoordinates, setShowPasteCoordinates] = useState(false);
  const [pasteInput, setPasteInput] = useState('');
  const [pasteError, setPasteError] = useState('');

  const [showStripePayment, setShowStripePayment] = useState(false);
  const [currentOrder, setCurrentOrder] = useState<Order | null>(null);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const subtotal = useMemo(
    () => context?.cart.reduce((sum, item) => sum + item.product.price * item.quantity, 0) ?? 0,
    [context?.cart]
  );

  useEffect(() => {
    if (location) {
      const dist = haversineDistance(MMAMASHIA_COORDS, { lat: location.lat, lng: location.lng });
      setDistance(dist);
    } else {
      setDistance(null);
    }
  }, [location]);

  const deliveryFee = useMemo(() => {
    if (distance === null) return 0;
    if (distance <= 15) return 0;
    return (distance - 15) * 10;
  }, [distance]);

  const total = subtotal + deliveryFee;
  
  const handleUseCurrentLocation = () => {
    setIsLocating(true);
    setLocationError(null);
    setShowPasteCoordinates(false);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        const newLocation = {
          type: 'gps' as const,
          address: `Current Location: ${latitude.toFixed(6)}, ${longitude.toFixed(6)}`,
          lat: latitude,
          lng: longitude,
        };
        setLocation(newLocation);
        setIsLocating(false);
      },
      (error) => {
        setLocationError(`Error: ${error.message}. Please pin location manually.`);
        setIsLocating(false);
      },
      { timeout: 10000 }
    );
  };

  const handleOpenMap = () => {
    setIsMapOpen(true);
    setShowPasteCoordinates(false);
  };

  const handlePasteCoordinates = () => {
    setShowPasteCoordinates(true);
    setLocationError(null);
    setPasteError('');
    setPasteInput('');
  };

  const handlePasteSubmit = () => {
    let lat: number, lng: number;
    
    const commaSeparated = pasteInput.split(',').map(s => s.trim());
    if (commaSeparated.length === 2) {
      lat = parseFloat(commaSeparated[0]);
      lng = parseFloat(commaSeparated[1]);
      if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        const newLocation = {
          type: 'manual' as const,
          address: `Pinned Location: ${lat.toFixed(6)}, ${lng.toFixed(6)}`,
          lat,
          lng,
        };
        setLocation(newLocation);
        setShowPasteCoordinates(false);
        setPasteError('');
        return;
      }
    }
    
    const googleMapsMatch = pasteInput.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
    if (googleMapsMatch) {
      lat = parseFloat(googleMapsMatch[1]);
      lng = parseFloat(googleMapsMatch[2]);
      if (!isNaN(lat) && !isNaN(lng)) {
        const newLocation = {
          type: 'manual' as const,
          address: `Google Maps Location: ${lat.toFixed(6)}, ${lng.toFixed(6)}`,
          lat,
          lng,
        };
        setLocation(newLocation);
        setShowPasteCoordinates(false);
        setPasteError('');
        return;
      }
    }
    
    setPasteError('Invalid coordinates. Please use format: "lat, lng" or paste a Google Maps URL');
  };

  const handleLocationSelect = (selectedLocation: DeliveryLocation) => {
    setLocation(selectedLocation);
    setLocationError(null);
    setIsMapOpen(false);
  };

  const validateForm = (): boolean => {
    const errors: Partial<Record<keyof Customer, string>> = {};
    
    if (!customerInfo.name.trim()) {
      errors.name = 'Name is required';
    }
    
    if (!customerInfo.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(customerInfo.email)) {
      errors.email = 'Email is invalid';
    }
    
    if (!customerInfo.phone.trim()) {
      errors.phone = 'Phone number is required';
    } else if (!/^(\+267)?[7-9]\d{7}$/.test(customerInfo.phone.replace(/\s/g, ''))) {
      errors.phone = 'Please enter a valid Botswana phone number';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const resetFormData = () => {
    setCustomerInfo({ name: '', email: '', phone: '' });
    setLocation(null);
    setDistance(null);
    setFormErrors({});
    setPaymentMethod('eft');
    setPaymentError(null);
    setShowPasteCoordinates(false);
    setPasteInput('');
    setPasteError('');
    setLocationError(null);
  };

  const handlePlaceOrder = async () => {
    if (!context || !location || distance === null) return;
    
    if (!validateForm()) {
      return;
    }

    // CRITICAL FIX: Update context with customer info BEFORE creating order
    context.updateCustomer(customerInfo);

    const orderId = `ORD-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const newOrder: Order = {
      id: orderId,
      date: new Date().toISOString(),
      items: context.cart,
      subtotal: subtotal,
      deliveryFee: deliveryFee,
      distanceFromOrigin: distance,
      total: total,
      deliveryLocation: location,
      customer: customerInfo.phone,
      paymentMethod,
      paymentStatus: 'pending',
      orderStatus: 'pending',
      status: paymentMethod === 'eft' ? 'Pending Payment' : 'Processing'
    };
    
    if (paymentMethod === 'card') {
      setIsProcessing(true);
      try {
        const createdOrder = await api.createOrder(newOrder, customerInfo);
        console.log('Order created successfully:', createdOrder);
        setCurrentOrder(newOrder);
        setShowStripePayment(true);
      } catch (error) {
        console.error('Failed to create order:', error);
        setPaymentError('Failed to create order. Please try again.');
      } finally {
        setIsProcessing(false);
      }
    } else {
      try {
        const createdOrder = await api.createOrder(newOrder, customerInfo);
        console.log('Order created successfully:', createdOrder);
        context.createOrder(createdOrder);
        context.clearCart();
        context.setView('confirmation');
        resetFormData();
      } catch (error) {
        console.error('Failed to create order:', error);
        setPaymentError('Failed to create order. Please try again.');
      }
    }
  };

  const handlePaymentSuccess = async (paymentIntentId: string) => {
    if (currentOrder) {
      console.log('Payment success for order:', currentOrder.id);
      
      try {
        // Record successful payment result
        await api.recordPaymentResult(currentOrder.id, {
          success: true,
          reference: paymentIntentId, // Use actual payment intent ID instead of 'successful'
          amount: total,
          paymentMethod: 'card'
        });
        console.log('✅ Payment result recorded successfully');
      } catch (error) {
        console.error('Failed to record payment result:', error);
      }
      
      resetFormData();
      
      if (context) {
        // CRITICAL FIX: Use customer from context, not customerInfo
        // customerInfo might be stale, but context.customer is always current
        const currentCustomer = context.customer;
        
        const updatedOrder = {
          ...currentOrder,
          paymentStatus: 'paid' as const,
          paymentMethod: 'card' as const,
          status: 'Processing' as const,
          transactionId: paymentIntentId,
          customer: currentCustomer?.phone || currentOrder.customer, // Use context customer phone
          customerName: currentCustomer?.name || '', // Use context customer name
          customerEmail: currentCustomer?.email || '' // Use context customer email
        };
        
        // Also update the order with the correct customer info
        // This ensures the confirmation page shows the right person
        console.log('Updated order with customer:', {
          name: currentCustomer?.name,
          phone: currentCustomer?.phone,
          email: currentCustomer?.email
        });
        
        context.setActiveOrder(updatedOrder);
        context.clearCart();
        context.setView('confirmation');
      }
    }
    
    setShowStripePayment(false);
    setCurrentOrder(null);
  };
  
  const handlePaymentError = (errorMessage: string) => {
    setPaymentError(errorMessage);
    
    if (currentOrder) {
      // Record failed payment result
      api.recordPaymentResult(currentOrder.id, {
        success: false,
        error: errorMessage,
        reference: 'unsuccessful',
        amount: total,
        paymentMethod: 'card'
      }).catch(err => console.error('Failed to record payment failure:', err));
    }
    
    setShowStripePayment(false);
    setCurrentOrder(null);
  };
  
  const handlePaymentCancel = () => {
    setShowStripePayment(false);
    setCurrentOrder(null);
    setPaymentError(null);
  };
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCustomerInfo(prev => ({ ...prev, [name]: value }));
    if (formErrors[name as keyof Customer]) {
      setFormErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length <= 8) {
      setCustomerInfo(prev => ({ ...prev, phone: value }));
      if (formErrors.phone) {
        setFormErrors(prev => ({ ...prev, phone: '' }));
      }
    }
  };

  useEffect(() => {
    return () => {
      if (showStripePayment) {
        setShowStripePayment(false);
        setCurrentOrder(null);
      }
    };
  }, []);

  if (!context || context.cart.length === 0) {
    return <div className="text-center p-8">Your cart is empty.</div>;
  }

  const canPlaceOrder = location && customerInfo.name && customerInfo.email && customerInfo.phone;

  const getButtonText = () => {
    if (!location) return '📍 Set Delivery Location';
    if (!customerInfo.name || !customerInfo.email || !customerInfo.phone) return '✏️ Complete Your Information';
    if (isProcessing) return '⏳ Processing...';
    
    switch(paymentMethod) {
      case 'card':
        return `💳 Pay Now P${total.toFixed(2)}`;
      case 'mobile_money':
        return `📱 Pay with Mobile Money`;
      case 'eft':
      default:
        return '📝 Place Order';
    }
  };

  if (showStripePayment && currentOrder) {
    return (
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Complete Payment</h1>
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
          <StripePayment
            orderId={currentOrder.id}
            amount={total}
            customerEmail={customerInfo.email}
            onSuccess={handlePaymentSuccess}
            onError={handlePaymentError}
            onCancel={handlePaymentCancel}
          />
        </div>
      </div>
    );
  }
  
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Checkout</h1>
      
      {paymentError && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {paymentError}
        </div>
      )}
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          {/* Customer Information */}
          <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
            <h2 className="text-2xl font-bold mb-4 text-black">1. Your Information</h2>
            <div className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={customerInfo.name}
                  onChange={handleInputChange}
                  placeholder="John Doe"
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none transition text-black ${
                    formErrors.name ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {formErrors.name && (
                  <p className="mt-1 text-sm text-red-500">{formErrors.name}</p>
                )}
              </div>
              
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={customerInfo.email}
                  onChange={handleInputChange}
                  placeholder="john@example.com"
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none transition text-black ${
                    formErrors.email ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {formErrors.email && (
                  <p className="mt-1 text-sm text-red-500">{formErrors.email}</p>
                )}
              </div>
              
              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                  Phone Number <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                    <span className="text-gray-500 font-medium border-r border-gray-300 pr-2">+267</span>
                  </div>
                  <input
                    type="tel"
                    id="phone"
                    name="phone"
                    value={customerInfo.phone}
                    onChange={handlePhoneChange}
                    placeholder="72123456"
                    className={`w-full pl-20 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none transition text-black ${
                      formErrors.phone ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                </div>
                {formErrors.phone && (
                  <p className="mt-1 text-sm text-red-500">{formErrors.phone}</p>
                )}
              </div>
            </div>
          </div>

          {/* Delivery Section */}
          <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
            <h2 className="text-2xl font-bold mb-4 text-black">2. Delivery Location <span className="text-red-500">*</span></h2>
            <div className="space-y-4">
              <div className="flex gap-4 flex-wrap">
                <button 
                  onClick={handleUseCurrentLocation} 
                  disabled={isLocating} 
                  className="flex items-center gap-2 bg-blue-500 text-white font-semibold py-2 px-4 rounded-lg hover:bg-blue-600 transition disabled:bg-blue-300"
                >
                  {isLocating ? 'Locating...' : '📍 Use Current Location'}
                </button>
                <button 
                  onClick={handleOpenMap} 
                  className="flex items-center gap-2 bg-gray-700 text-white font-semibold py-2 px-4 rounded-lg hover:bg-gray-800 transition"
                >
                  🗺️ Pin Location on Map
                </button>
                <button 
                  onClick={handlePasteCoordinates} 
                  className="flex items-center gap-2 bg-purple-500 text-white font-semibold py-2 px-4 rounded-lg hover:bg-purple-600 transition"
                >
                  📋 Paste Coordinates
                </button>
              </div>

              {showPasteCoordinates && (
                <div className="mt-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                  <label className="block text-sm font-medium text-purple-800 mb-2">
                    Paste coordinates (e.g., "-24.6581, 25.9087") or Google Maps URL
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={pasteInput}
                      onChange={(e) => setPasteInput(e.target.value)}
                      placeholder="-24.6581, 25.9087"
                      className="flex-1 px-4 py-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none text-black"
                    />
                    <button
                      onClick={handlePasteSubmit}
                      className="bg-purple-500 text-white px-6 py-2 rounded-lg hover:bg-purple-600 transition font-semibold"
                    >
                      Apply
                    </button>
                  </div>
                  {pasteError && (
                    <p className="mt-2 text-sm text-red-500">{pasteError}</p>
                  )}
                  <p className="mt-2 text-xs text-purple-600">
                    💡 Tip: From Google Maps, click on a location and copy the URL.
                  </p>
                </div>
              )}

              {locationError && <p className="text-red-500 text-sm mt-2">{locationError}</p>}
              
              {location && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-start gap-3">
                  <LocationMarkerIcon className="w-6 h-6 text-blue-500 mt-1 flex-shrink-0" />
                  <div>
                    <p className="font-semibold text-blue-800">Delivering to:</p>
                    <p className="text-blue-700">{location.address}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Payment Section */}
          <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
            <h2 className="text-2xl font-bold mb-4 text-black">3. Payment Method</h2>
            <div className="space-y-3">
              <label className={`flex items-start p-4 border rounded-lg cursor-pointer transition ${paymentMethod === 'eft' ? 'border-orange-500 bg-orange-50' : 'border-gray-300'}`}>
                <input 
                  type="radio" 
                  name="payment" 
                  value="eft" 
                  checked={paymentMethod === 'eft'} 
                  onChange={() => setPaymentMethod('eft')} 
                  className="form-radio text-orange-500 focus:ring-orange-500 mt-1"
                />
                <div className="ml-3">
                  <span className="font-semibold text-black">🏦 EFT / Bank Transfer</span>
                  <p className="text-sm text-gray-600">Place order now and pay via your banking app.</p>
                </div>
              </label>
              
              <label className={`flex items-start p-4 border rounded-lg cursor-pointer transition ${paymentMethod === 'card' ? 'border-orange-500 bg-orange-50' : 'border-gray-300'}`}>
                <input 
                  type="radio" 
                  name="payment" 
                  value="card" 
                  checked={paymentMethod === 'card'} 
                  onChange={() => setPaymentMethod('card')} 
                  className="form-radio text-orange-500 focus:ring-orange-500 mt-1"
                />
                <div className="ml-3">
                  <span className="font-semibold text-black">💳 Credit/Debit Card</span>
                  <p className="text-sm text-gray-600">Pay securely with your card.</p>
                </div>
              </label>
              
              <label className={`flex items-start p-4 border rounded-lg cursor-pointer transition ${paymentMethod === 'mobile_money' ? 'border-orange-500 bg-orange-50' : 'border-gray-300'}`}>
                <input 
                  type="radio" 
                  name="payment" 
                  value="mobile_money" 
                  checked={paymentMethod === 'mobile_money'} 
                  onChange={() => setPaymentMethod('mobile_money')} 
                  className="form-radio text-orange-500 focus:ring-orange-500 mt-1"
                />
                <div className="ml-3">
                  <span className="font-semibold text-black">📱 Mobile Money</span>
                  <p className="text-sm text-gray-600">Pay with Orange Money or MyZaka.</p>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* Order Summary */}
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200 h-fit sticky top-24">
          <h2 className="text-2xl font-bold mb-4 border-b pb-3 text-black">Order Summary</h2>
          <div className="space-y-2">
            <div className="flex justify-between text-black">
              <span>Subtotal</span>
              <span className="font-semibold">P{subtotal.toFixed(2)}</span>
            </div>
            {distance !== null && (
              <div className="flex justify-between text-sm text-gray-600">
                <span>Distance</span>
                <span className="font-semibold">{distance.toFixed(1)} km</span>
              </div>
            )}
            <div className="flex justify-between text-black">
              <span>Delivery</span>
              {location ? (
                deliveryFee === 0 ? (
                  <span className="font-semibold text-green-600">Free</span>
                ) : (
                  <span className="font-semibold">P{deliveryFee.toFixed(2)}</span>
                )
              ) : (
                <span className="text-gray-500">TBD</span>
              )}
            </div>
            <div className="flex justify-between text-xl font-bold border-t pt-3 mt-3">
              <span>Total</span>
              <span>P{total.toFixed(2)}</span>
            </div>
          </div>
          
          <button 
            onClick={handlePlaceOrder} 
            disabled={!canPlaceOrder || isProcessing} 
            className="w-full mt-6 bg-green-600 text-white font-bold py-3 rounded-lg hover:bg-green-700 transition disabled:bg-gray-400 text-lg"
          >
            {getButtonText()}
          </button>
        </div>
      </div>
      
      <MapModal 
        isOpen={isMapOpen} 
        onClose={() => setIsMapOpen(false)} 
        onLocationSelect={handleLocationSelect} 
      />
    </div>
  );
};

export default CheckoutView;