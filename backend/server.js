const express = require('express');
const cors = require('cors');
const Stripe = require('stripe');
require('dotenv').config();

const app = express();

// Validate Stripe key
if (!process.env.STRIPE_SECRET_KEY) {
    console.error('❌ STRIPE_SECRET_KEY is not set in environment variables');
    console.error('Please add STRIPE_SECRET_KEY to your Render environment variables');
} else {
    console.log('✅ Stripe secret key found (length:', process.env.STRIPE_SECRET_KEY.length, 'chars)');
}

const stripe = Stripe(process.env.STRIPE_SECRET_KEY);

// Middleware - Updated CORS for Render
app.use(cors({
    origin: [
        'http://localhost:3000',
        'http://localhost:5173',
        'http://localhost:5174',
        'https://quarry-frontend-bpgs.onrender.com',
        'https://quarry-frontend.onrender.com',
        'https://*.onrender.com'
    ],
    credentials: true
}));
app.use(express.json());

// Root route
app.get('/', (req, res) => {
    res.json({
        message: 'Quarry Market Backend API is running',
        status: 'ok',
        endpoints: [
            '/api/health',
            '/api/create-payment-intent',
            '/api/confirm-payment'
        ]
    });
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Create Payment Intent endpoint
app.post('/api/create-payment-intent', async(req, res) => {
    try {
        const { orderId, amount, currency, customerEmail } = req.body;

        console.log('Creating payment intent for order:', orderId, 'amount:', amount);

        // Validate amount
        if (!amount || amount <= 0) {
            return res.status(400).json({ error: 'Invalid amount' });
        }

        const paymentIntent = await stripe.paymentIntents.create({
            amount: Math.round(amount), // Amount is in thebe/cents
            currency: currency || 'bwp',
            automatic_payment_methods: {
                enabled: true,
            },
            metadata: {
                orderId: orderId,
            },
            receipt_email: customerEmail,
        });

        console.log('Payment intent created:', paymentIntent.id);
        console.log('Client secret:', paymentIntent.client_secret);

        res.json({
            clientSecret: paymentIntent.client_secret,
            paymentIntentId: paymentIntent.id
        });
    } catch (error) {
        console.error('Error creating payment intent:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// Confirm Payment endpoint
app.post('/api/confirm-payment', async(req, res) => {
    try {
        const { orderId, paymentIntentId } = req.body;

        if (!paymentIntentId) {
            return res.status(400).json({ error: 'Payment intent ID is required' });
        }

        const paymentIntent = await stripe.paymentIntents.retrieve(paymentIntentId);

        res.json({
            success: paymentIntent.status === 'succeeded',
            paymentIntent: {
                id: paymentIntent.id,
                status: paymentIntent.status,
            }
        });
    } catch (error) {
        console.error('Error confirming payment:', error.message);
        res.status(500).json({ error: error.message });
    }
});

const PORT = process.env.PORT || 5252;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});