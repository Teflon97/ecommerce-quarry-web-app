export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  unit: string;
  category: string;
  imageUrl: string;
}

export interface CartItem {
  product: Product;
  quantity: number;
}

export interface DeliveryLocation {
  type: 'gps' | 'manual';
  address: string;
  lat: number;
  lng: number;
}

export interface Customer {
  name: string;
  email: string;
  phone: string;
  orderId?: string;
}

// Database status types
export type DBOrderStatus = 'pending' | 'processing' | 'completed' | 'cancelled';
export type DBPaymentStatus = 'pending' | 'paid' | 'failed';
export type DisplayOrderStatus = 'Pending Payment' | 'Processing' | 'Out for Delivery' | 'Delivered' | 'Cancelled';
export type PaymentMethod = 'card' | 'mobile_money' | 'eft';

export interface Order {
  id: string;
  date: string;
  items: CartItem[];
  subtotal: number;
  deliveryFee: number;
  total: number;
  distanceFromOrigin?: number;
  deliveryLocation: DeliveryLocation;
  customer: string;
  paymentMethod: PaymentMethod;
  paymentStatus: DBPaymentStatus;
  orderStatus: DBOrderStatus;
  status: DisplayOrderStatus;
  userId?: string;
  transactionId?: string;
  createdAt?: Date | string;
  updatedAt?: Date | string;
  transactions?: Transaction[];
}

export interface Transaction {
  id: string;
  orderId: string;
  amount: number;
  paymentMethod: string;
  paymentType: string;
  status: 'pending' | 'completed' | 'failed';
  reference?: string;
  createdAt: Date | string;
  updatedAt: Date | string;
}

export type View = 'products' | 'cart' | 'checkout' | 'confirmation';

// Helper functions
export const mapStatusToDB = (displayStatus: DisplayOrderStatus): DBOrderStatus => {
  const statusMap: Record<DisplayOrderStatus, DBOrderStatus> = {
    'Pending Payment': 'pending',
    'Processing': 'processing',
    'Out for Delivery': 'processing',
    'Delivered': 'completed',
    'Cancelled': 'cancelled'
  };
  return statusMap[displayStatus] || 'pending';
};

export const mapStatusToDisplay = (dbStatus: DBOrderStatus): DisplayOrderStatus => {
  const statusMap: Record<DBOrderStatus, DisplayOrderStatus> = {
    'pending': 'Pending Payment',
    'processing': 'Processing',
    'completed': 'Delivered',
    'cancelled': 'Cancelled'
  };
  return statusMap[dbStatus];
};