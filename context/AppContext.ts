import { createContext } from 'react';
import type { CartItem, Product, Order, View, Customer } from '../types';

interface AppContextType {
  view: View;
  setView: (view: View) => void;
  products: Product[];
  cart: CartItem[];
  addToCart: (product: Product, quantity: number) => void;
  updateCartQuantity: (productId: string, quantity: number) => void;
  removeFromCart: (productId: string) => void;
  clearCart: () => void;
  orders: Order[];
  createOrder: (order: Order) => void;
  activeOrder: Order | null;
  setActiveOrder: (order: Order | null) => void;
  updateOrderStatus: (orderId: string, status: Order['status']) => void;
  customer: Customer;
  updateCustomer: (customer: Customer) => void;
}

export const AppContext = createContext<AppContextType | undefined>(undefined);