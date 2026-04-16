import React, { useContext, useEffect } from 'react';
import { AppContext } from '../context/AppContext';
import { DownloadIcon } from './icons';
import { generatePdf } from '../services/pdfService';

const OrderConfirmation: React.FC = () => {
  const context = useContext(AppContext);
  const urlParams = new URLSearchParams(window.location.search);
  const paymentIntentId = urlParams.get('payment_intent');
  const paymentStatus = urlParams.get('payment_intent_client_secret') ? 'succeeded' : null;

  useEffect(() => {
    // If we have a payment intent in URL, payment was successful
    if (paymentIntentId && context?.activeOrder) {
      console.log('Payment successful with ID:', paymentIntentId);
    }
  }, [paymentIntentId, context]);

  if (!context || !context.activeOrder) {
    return (
      <div className="text-center p-10">
        <h2 className="text-2xl font-bold">No active order found.</h2>
        <button 
          onClick={() => context?.setView('products')} 
          className="mt-4 bg-orange-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-orange-700"
        >
          Back to Shopping
        </button>
      </div>
    );
  }

  const { activeOrder: order, setView, customer } = context;

  // CRITICAL: Use customer from context, not from order
  // The customer object in context is the one who just placed the order
  const currentCustomer = customer;
  
  // Format phone number helper
  const formatPhoneNumber = (phone: string) => {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 8) {
      return `+267 ${cleaned}`;
    }
    return phone;
  };

  const getPaymentStatusMessage = () => {
    if (order.paymentStatus === 'paid' || paymentStatus === 'succeeded') {
      return {
        icon: '✅',
        title: 'Payment Successful!',
        message: 'Thank you for your payment. Your order is confirmed and being processed.',
        color: 'green'
      };
    } else if (order.paymentMethod === 'eft') {
      return {
        icon: '⏳',
        title: 'Order Received - Awaiting Payment',
        message: 'Please complete your EFT payment to start processing.',
        color: 'blue'
      };
    } else if (order.paymentStatus === 'failed') {
      return {
        icon: '❌',
        title: 'Payment Failed',
        message: 'Your payment could not be processed. Please try again.',
        color: 'red'
      };
    } else {
      return {
        icon: '⏳',
        title: 'Processing Payment',
        message: 'We are processing your payment. You will receive a confirmation shortly.',
        color: 'yellow'
      };
    }
  };

  const status = getPaymentStatusMessage();

  // If payment failed, show error and button to retry
  if (status.color === 'red') {
    return (
      <div className="max-w-4xl mx-auto bg-white p-6 sm:p-8 rounded-xl shadow-lg border border-gray-200">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-20 w-20 rounded-full bg-red-100 mb-4 text-4xl">
            ❌
          </div>
          <h1 className="text-3xl font-bold text-gray-800">Payment Failed</h1>
          <p className="text-gray-600 mt-2">{status.message}</p>
        </div>
        
        <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
          <button 
            onClick={() => setView('checkout')} 
            className="bg-orange-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-orange-700"
          >
            Try Again
          </button>
          <button 
            onClick={() => setView('products')} 
            className="bg-gray-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-gray-700"
          >
            Continue Shopping
          </button>
        </div>
      </div>
    );
  }

  // Use current customer from context
  const customerName = currentCustomer?.name || 'N/A';
  const customerPhone = formatPhoneNumber(currentCustomer?.phone || order.customer || '');
  const numberOfItems = order.items.length;

  return (
    <div className="max-w-4xl mx-auto bg-white p-6 sm:p-8 rounded-xl shadow-lg border border-gray-200">
      <div className="text-center">
        <div className={`mx-auto flex items-center justify-center h-20 w-20 rounded-full bg-${status.color === 'green' ? 'green' : status.color === 'blue' ? 'blue' : 'yellow'}-100 mb-4 text-4xl`}>
          {status.icon}
        </div>
        <h1 className="text-3xl font-bold text-gray-800">{status.title}</h1>
        <p className="text-gray-600 mt-2">{status.message}</p>
        <p className="text-sm text-gray-500 mt-1">
          Order ID: <span className="font-mono bg-gray-100 px-2 py-1 rounded">{order.id}</span>
        </p>
        {paymentIntentId && (
          <p className="text-xs text-gray-400 mt-1">
            Transaction ID: {paymentIntentId}
          </p>
        )}
      </div>

      {/* Payment Success Info */}
      {(order.paymentStatus === 'paid' || paymentIntentId) && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-800">
            <span className="font-bold">✅ Payment Method:</span> {order.paymentMethod === 'card' ? 'Credit/Debit Card' : order.paymentMethod === 'eft' ? 'EFT / Bank Transfer' : 'Mobile Money'}
          </p>
          <p className="text-sm text-green-800">
            <span className="font-bold">💰 Status:</span> Paid ✓
          </p>
          {(order.transactionId || paymentIntentId) && (
            <p className="text-sm text-green-800">
              <span className="font-bold">🔑 Transaction ID:</span>{' '}
              <span className="font-mono text-xs">{order.transactionId || paymentIntentId}</span>
            </p>
          )}
        </div>
      )}

      {/* Customer Info - Using current customer from context */}
      <div className="mt-4 bg-gray-50 p-3 rounded-lg">
        <h3 className="font-bold mb-1 text-black text-sm">👤 Customer Information</h3>
        <p className="text-gray-700 text-sm"><span className="font-semibold">Name:</span> {customerName}</p>
        <p className="text-gray-700 text-sm"><span className="font-semibold">Contact:</span> {customerPhone}</p>
      </div>

      {/* Order Items with Count */}
      <div className="mt-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-bold text-black text-sm">📦 Order Items ({numberOfItems})</h3>
        </div>
        <div className="border-t border-b border-gray-200 divide-y divide-gray-200 max-h-64 overflow-y-auto">
          {order.items.map(({ product, quantity }) => (
            <div key={product.id} className="flex justify-between items-center py-3">
              <div>
                <p className="font-semibold text-black">{product.name}</p>
                <p className="text-xs text-gray-500">{quantity} {product.unit} × P{product.price.toFixed(2)} each</p>
              </div>
              <p className="font-semibold text-black">P{(product.price * quantity).toFixed(2)}</p>
            </div>
          ))}
        </div>
      </div>
      
      <div className="mt-4 space-y-1 text-right">
        <p className="text-sm text-black">Subtotal: <span className="font-semibold">P{order.subtotal.toFixed(2)}</span></p>
        <p className="text-sm text-black">Delivery Fee: <span className="font-semibold">{order.deliveryFee === 0 ? 'Free' : 'P' + order.deliveryFee.toFixed(2)}</span></p>
        <p className="text-xl font-bold text-black">Total: <span className="text-orange-600">P{order.total.toFixed(2)}</span></p>
      </div>

      <div className="mt-4 bg-gray-50 p-3 rounded-lg">
        <h3 className="font-bold mb-1 text-black text-sm">📦 Delivery Details</h3>
        <p className="text-gray-700 text-sm"><span className="font-semibold">To:</span> {customerName}</p>
        <p className="text-gray-700 text-sm"><span className="font-semibold">Address:</span> {order.deliveryLocation.address}</p>
        <p className="text-gray-500 text-xs mt-1">
          <span className="font-semibold">📍 Coordinates:</span> {order.deliveryLocation.lat.toFixed(6)}, {order.deliveryLocation.lng.toFixed(6)}
        </p>
        {order.distanceFromOrigin && (
          <p className="text-gray-500 text-xs">📏 {order.distanceFromOrigin.toFixed(1)} km from Mmamashia</p>
        )}
      </div>
      
      <div className="mt-6 flex flex-col sm:flex-row gap-4">
        <button 
          onClick={() => generatePdf(order, currentCustomer)} 
          className="flex-1 flex items-center justify-center gap-2 bg-gray-700 text-white font-bold py-3 px-4 rounded-lg hover:bg-gray-800"
        >
          <DownloadIcon className="w-5 h-5" /> Download Receipt (PDF)
        </button>
        <button 
          onClick={() => setView('products')} 
          className="flex-1 bg-orange-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-orange-700"
        >
          Continue Shopping
        </button>
      </div>
    </div>
  );
};

export default OrderConfirmation;