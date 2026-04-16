import type { Product, Order, Customer, DisplayOrderStatus, DBPaymentStatus } from '../types';
import { 
  createOrder as supabaseCreateOrder,
  getAllOrders as supabaseGetAllOrders,
  getOrdersByPhone,
  updateOrderStatus as supabaseUpdateOrderStatus,
  updatePaymentStatus as supabaseUpdatePaymentStatus,
  updateTransactionWithPaymentResult,
  getTransactionsByOrderId,
  getOrderById as supabaseGetOrderById,
  addTransaction
} from '../supabase/orders';
import { supabase } from '../supabase/config';

// Fallback products in case API fails
const FALLBACK_PRODUCTS: Product[] = [];

export const api = {
  // Products - Fetch from Supabase directly
  getProducts: async (): Promise<Product[]> => {
    try {
      console.log('Fetching products from Supabase...');
      
      const { data, error } = await supabase
        .from('products')
        .select('*')
        .order('category', { ascending: true });

      if (error) {
        console.error('Error fetching products from Supabase:', error);
        return FALLBACK_PRODUCTS;
      }

      if (data && data.length > 0) {
        const products: Product[] = data.map(item => ({
          id: item.id,
          name: item.name,
          description: item.description,
          price: item.price,
          unit: item.unit,
          category: item.category,
          imageUrl: item.image_url || 'https://via.placeholder.com/400'
        }));
        
        console.log(`✅ Loaded ${products.length} products from Supabase`);
        return products;
      }
      
      console.log('No products found in Supabase');
      return FALLBACK_PRODUCTS;
    } catch (error) {
      console.error('Failed to fetch products:', error);
      return FALLBACK_PRODUCTS;
    }
  },

  // Orders
  getUserOrders: async (phone: string): Promise<Order[]> => {
    try {
      const orders = await getOrdersByPhone(phone);
      return orders as Order[];
    } catch (error) {
      console.error('Error fetching user orders:', error);
      return [];
    }
  },

  createOrder: async (order: Order, customer?: Customer): Promise<Order> => {
    try {
      const result = await supabaseCreateOrder(order);
      console.log('Order created successfully:', result);
      
      if (customer) {
        try {
          await supabase
            .from('customers')
            .upsert({
              phone: customer.phone,
              name: customer.name,
              email: customer.email,
              order_id: result.id,
              updated_at: new Date().toISOString()
            }, {
              onConflict: 'phone'
            });
          console.log('✅ Customer saved after order creation');
        } catch (customerError) {
          console.error('Error saving customer after order:', customerError);
        }
      }
      
      return result as Order;
    } catch (error) {
      console.error('Error creating order:', error);
      throw error;
    }
  },

  recordPaymentResult: async (
    orderId: string,
    paymentResult: {
      success: boolean;
      reference?: string;
      error?: string;
      amount?: number;
      paymentMethod?: string;
    }
  ): Promise<any> => {
    try {
      console.log('Recording payment result for order:', orderId, paymentResult);
      
      const transaction = await updateTransactionWithPaymentResult(orderId, {
        success: paymentResult.success,
        error: paymentResult.error
      });
      
      const paymentStatus = paymentResult.success ? 'paid' : 'failed';
      await supabaseUpdatePaymentStatus(orderId, paymentStatus);
      
      if (paymentResult.success) {
        await supabaseUpdateOrderStatus(orderId, 'Processing');
      }
      
      console.log('✅ Payment result recorded successfully');
      return transaction;
    } catch (error) {
      console.error('Error recording payment result:', error);
      throw error;
    }
  },

  updateOrderStatus: async (orderId: string, status: DisplayOrderStatus): Promise<void> => {
    try {
      await supabaseUpdateOrderStatus(orderId, status);
      console.log('Order status updated in Supabase');
    } catch (error: any) {
      console.error('Error updating order status:', error);
      
      if (error.message?.includes('row-level security policy')) {
        console.log('⚠️ RLS policy error - you may need to add proper policies');
      }
      
      if (error.code === 'permission-denied' || error.message?.includes('policy')) {
        console.log('Permission error but payment may have succeeded!');
      } else {
        throw error;
      }
    }
  },

  updatePaymentStatus: async (orderId: string, paymentStatus: DBPaymentStatus): Promise<void> => {
    try {
      await supabaseUpdatePaymentStatus(orderId, paymentStatus);
      console.log('Payment status updated in Supabase');
    } catch (error) {
      console.error('Error updating payment status:', error);
      throw error;
    }
  },

  getAllOrders: async (): Promise<Order[]> => {
    try {
      const orders = await supabaseGetAllOrders();
      return orders as Order[];
    } catch (error) {
      console.error('Error fetching all orders:', error);
      return [];
    }
  },

  getOrderById: async (orderId: string): Promise<Order | null> => {
    try {
      const order = await supabaseGetOrderById(orderId);
      return order as Order | null;
    } catch (error) {
      console.error('Error fetching order by ID:', error);
      return null;
    }
  },

  getTransactionsByOrderId: async (orderId: string): Promise<any[]> => {
    try {
      const transactions = await getTransactionsByOrderId(orderId);
      return transactions;
    } catch (error) {
      console.error('Error fetching transactions:', error);
      return [];
    }
  },

  // Customers
  getCustomer: async (phone: string): Promise<Customer | null> => {
    try {
      const { data, error } = await supabase
        .from('customers')
        .select('*')
        .eq('phone', phone)
        .single();
      
      if (error && error.code !== 'PGRST116') {
        console.error('Error fetching customer:', error);
      }
      
      if (data) {
        return {
          name: data.name,
          email: data.email,
          phone: data.phone,
          orderId: data.order_id
        } as Customer;
      }
      
      const stored = localStorage.getItem('quarryCustomer');
      if (stored) {
        return JSON.parse(stored);
      }
      
      return null;
    } catch (error) {
      console.error('Error getting customer:', error);
      return null;
    }
  },

  saveUser: async (customer: Customer): Promise<void> => {
    try {
      localStorage.setItem('quarryCustomer', JSON.stringify(customer));
      
      const customerData: any = {
        phone: customer.phone,
        name: customer.name,
        email: customer.email,
        updated_at: new Date().toISOString()
      };
      
      if (customer.orderId) {
        customerData.order_id = customer.orderId;
      }
      
      try {
        console.log('Attempting to save customer to Supabase:', customerData);
        
        const { data, error } = await supabase
          .from('customers')
          .upsert(customerData, {
            onConflict: 'phone'
          })
          .select();
        
        if (error) {
          console.error('Supabase error saving customer:', error);
        } else {
          console.log('✅ Customer saved to Supabase:', data);
        }
      } catch (dbError) {
        console.error('Database error saving customer:', dbError);
      }
      
      console.log('Customer info saved:', customer);
    } catch (error) {
      console.error('Error saving customer:', error);
    }
  },

  // Transactions
  processPayment: async (
    orderId: string, 
    paymentMethod: string,
    paymentDetails: {
      type: 'orange' | 'myzaka' | 'smega' | 'visa' | 'mastercard' | 'eft';
      reference?: string;
      amount?: number;
    }
  ) => {
    try {
      const { data: order, error: orderError } = await supabase
        .from('orders')
        .select('total')
        .eq('id', orderId)
        .single();
      
      if (orderError) {
        console.error('Error fetching order for payment:', orderError);
        throw orderError;
      }
      
      const transaction = await addTransaction(orderId, {
        amount: paymentDetails.amount || order?.total || 0,
        paymentMethod,
        paymentType: paymentDetails.type,
        status: 'pending',
        reference: paymentDetails.reference
      });
      
      console.log('Payment transaction created in Supabase:', transaction);
      return transaction;
    } catch (error) {
      console.error('Error processing payment:', error);
      throw error;
    }
  }
};