import React, { useState, useMemo, useCallback, useEffect } from 'react';
import type { CartItem, Product, Order, View, Customer } from './types';
import { AppContext } from './context/AppContext';
import Header from './components/Header';
import ProductList from './components/ProductList';
import CartView from './components/CartView';
import CheckoutView from './components/CheckoutView';
import OrderConfirmation from './components/OrderConfirmation';
import BackButton from './components/BackButton';
import { api } from './services/api';

// Fallback products in case API fails
const FALLBACK_PRODUCTS: Product[] = [];

const App: React.FC = () => {
  const [view, setView] = useState<View>('products');
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  
  const [customer, setCustomer] = useState<Customer>(() => {
    try {
        const savedCustomer = localStorage.getItem('quarryCustomer');
        return savedCustomer ? JSON.parse(savedCustomer) : { name: '', email: '', phone: '' };
    } catch {
        return { name: '', email: '', phone: '' };
    }
  });
  
  const [activeOrder, setActiveOrder] = useState<Order | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  const showNotification = (message: string) => {
    setNotification(message);
    setTimeout(() => setNotification(null), 3000);
  };

  // Fetch Products on Mount
  useEffect(() => {
    api.getProducts().then(data => {
        if (data.length > 0) {
            setProducts(data);
        } else {
            setProducts(FALLBACK_PRODUCTS);
        }
    });
  }, []);

  // Save customer to localStorage when it changes
  useEffect(() => {
    try {
        localStorage.setItem('quarryCustomer', JSON.stringify(customer));
    } catch (error) {
        console.error("Failed to save customer to localStorage", error);
    }
  }, [customer]);

  const addToCart = useCallback((product: Product, quantity: number) => {
    setCart(prevCart => {
      const existingItem = prevCart.find(item => item.product.id === product.id);
      if (existingItem) {
        return prevCart.map(item =>
          item.product.id === product.id
            ? { ...item, quantity: Math.min(100, item.quantity + quantity) }
            : item
        );
      }
      return [...prevCart, { product, quantity }];
    });
    showNotification(`${product.name} added to cart!`);
  }, []);

  const updateCartQuantity = useCallback((productId: string, quantity: number) => {
    setCart(prevCart => {
      if (quantity === 0) {
        return prevCart.filter(item => item.product.id !== productId);
      }
      return prevCart.map(item =>
        item.product.id === productId ? { ...item, quantity: Math.min(100, Math.max(1, quantity)) } : item
      );
    });
  }, []);

  const removeFromCart = useCallback((productId: string) => {
    setCart(prevCart => prevCart.filter(item => item.product.id !== productId));
    showNotification('Item removed from cart');
  }, []);

  const clearCart = useCallback(() => {
    setCart([]);
  }, []);

  const createOrder = useCallback(async (order: Order) => {
    if (!customer.phone) {
        showNotification("Please provide your contact details.");
        return;
    }
    
    setOrders(prevOrders => [order, ...prevOrders]);
    setActiveOrder(order);
    clearCart();
    setView('confirmation');
    
    try {
        await api.createOrder(order, customer);
        showNotification('Order placed successfully!');
    } catch (e) {
        showNotification('Order saved locally but failed to sync. Check connection.');
        console.error(e);
    }
  }, [clearCart, customer]);
  
  const updateOrderStatus = useCallback(async (orderId: string, status: Order['status']) => {
    setOrders(prevOrders => 
      prevOrders.map(o => o.id === orderId ? {...o, status} : o)
    );
    try {
      await api.updateOrderStatus(orderId, status);
    } catch (e) {
      console.error('Error updating order status:', e);
    }
  }, []);

  const updateCustomer = useCallback(async (newCustomer: Customer) => {
    setCustomer(newCustomer);
    try {
        await api.saveUser(newCustomer);
        showNotification('Information saved successfully!');
    } catch (e) {
        console.error(e);
        showNotification('Error saving information.');
    }
  }, []);

  const appContextValue = useMemo(() => ({
    view,
    setView,
    products,
    cart,
    addToCart,
    updateCartQuantity,
    removeFromCart,
    clearCart,
    orders,
    createOrder,
    activeOrder,
    setActiveOrder,
    updateOrderStatus,
    customer,
    updateCustomer
  }), [view, products, cart, orders, activeOrder, addToCart, updateCartQuantity, removeFromCart, clearCart, createOrder, updateOrderStatus, customer, updateCustomer]);

  const renderView = () => {
    switch (view) {
      case 'cart':
        return <CartView />;
      case 'checkout':
        return <CheckoutView />;
      case 'confirmation':
        return <OrderConfirmation />;
      case 'products':
      default:
        return <ProductList />;
    }
  };

  return (
    <AppContext.Provider value={appContextValue}>
      <div className="min-h-screen bg-gray-100">
        <Header />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-20">
          {renderView()}
        </main>
        <BackButton />
      </div>
    </AppContext.Provider>
  );
};

export default App;