import React, { useState, useEffect } from 'react';
import { PaymentElement, useStripe, useElements, Elements } from '@stripe/react-stripe-js';
import { loadStripe } from '@stripe/stripe-js';
import { stripeService } from '../services/stripe';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '');

interface StripePaymentProps {
  orderId: string;
  amount: number;
  customerEmail: string;
  onSuccess: (paymentIntentId: string) => void;
  onError: (errorMessage: string) => void;
  onCancel: () => void;
}

const StripePaymentForm: React.FC<{
  clientSecret: string;
  orderId: string;
  amount: number;
  onSuccess: (paymentIntentId: string) => void;
  onError: (errorMessage: string) => void;
  onCancel: () => void;
}> = ({ clientSecret, orderId, amount, onSuccess, onError, onCancel }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setIsProcessing(true);
    setPaymentError(null);

    try {
      const { error: submitError } = await elements.submit();
      
      if (submitError) {
        setPaymentError(submitError.message || 'Payment information is invalid');
        onError(submitError.message || 'Payment information is invalid');
        setIsProcessing(false);
        return;
      }

      const { error: confirmError, paymentIntent } = await stripe.confirmPayment({
        elements,
        clientSecret,
        confirmParams: {
          return_url: `${window.location.origin}/confirmation?order_id=${orderId}`,
        },
        redirect: 'if_required',
      });

      if (confirmError) {
        setPaymentError(confirmError.message || 'Payment failed');
        onError(confirmError.message || 'Payment failed');
        
        if (paymentIntent?.id) {
          await stripeService.confirmPayment(orderId, paymentIntent.id);
        }
      } else if (paymentIntent && paymentIntent.status === 'succeeded') {
        await stripeService.confirmPayment(orderId, paymentIntent.id);
        onSuccess(paymentIntent.id);
      }
    } catch (error: any) {
      setPaymentError(error.message || 'An unexpected error occurred');
      onError(error.message || 'An unexpected error occurred');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4 text-black">Card Payment Details</h3>
        <PaymentElement />
      </div>

      {paymentError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <p className="font-bold">Error:</p>
          <p>{paymentError}</p>
        </div>
      )}

      <div className="flex gap-4">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 bg-gray-500 text-white font-bold py-3 px-4 rounded-lg hover:bg-gray-600 transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!stripe || isProcessing}
          className="flex-1 bg-green-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400"
        >
          {isProcessing ? 'Processing...' : `Pay P${amount.toFixed(2)}`}
        </button>
      </div>
    </form>
  );
};

const StripePayment: React.FC<StripePaymentProps> = (props) => {
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let isMounted = true;
    
    const createPaymentIntent = async () => {
      try {
        const response = await stripeService.createPaymentIntent(
          props.orderId,
          props.amount,
          props.customerEmail
        );
        
        if (isMounted) {
          setClientSecret(response.clientSecret);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to initialize payment');
          props.onError(err.message || 'Failed to initialize payment');
        }
      }
    };

    createPaymentIntent();

    return () => {
      isMounted = false;
    };
  }, [props.orderId, props.amount, props.customerEmail, retryCount]);

  const handleRetry = () => {
    setError(null);
    setClientSecret(null);
    setRetryCount(prev => prev + 1);
  };

  if (error) {
    return (
      <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-6 rounded-lg text-center">
          <p className="mb-4 font-bold">Initialization Error:</p>
          <p className="mb-4">{error}</p>
          <button
            onClick={handleRetry}
            className="bg-orange-600 text-white font-bold py-2 px-6 rounded-lg hover:bg-orange-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!clientSecret) {
    return (
      <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-orange-500 border-t-transparent"></div>
          <p className="mt-2 text-gray-600">Initializing payment...</p>
        </div>
      </div>
    );
  }

  return (
    <Elements stripe={stripePromise} options={{ clientSecret }}>
      <StripePaymentForm 
        {...props} 
        clientSecret={clientSecret} 
      />
    </Elements>
  );
};

export default StripePayment;