const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5252/api';

export const stripeService = {
  // Create a payment intent for card payments
  createPaymentIntent: async (orderId: string, amount: number, customerEmail?: string) => {
    try {
      console.log('Creating payment intent for order:', orderId, 'using API URL:', API_BASE_URL);
      
      const response = await fetch(`${API_BASE_URL}/create-payment-intent`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          orderId,
          amount: Math.round(amount * 100), // Convert to thebe/cents
          currency: 'bwp',
          customerEmail
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create payment intent');
      }
      
      const data = await response.json();
      console.log('Payment intent created:', data);
      return data;
    } catch (error) {
      console.error('Error creating payment intent:', error);
      throw error;
    }
  },

  // Confirm payment and update order status
  confirmPayment: async (orderId: string, paymentIntentId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/confirm-payment`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          orderId,
          paymentIntentId
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to confirm payment');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error confirming payment:', error);
      throw error;
    }
  }
};