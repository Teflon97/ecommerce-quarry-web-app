import { supabase } from './config';
import type { Order, Transaction, DBOrderStatus, DisplayOrderStatus } from '../types';
import { mapStatusToDisplay } from '../types';

// Helper function to determine payment type
const getPaymentType = (paymentMethod: string): string => {
  switch(paymentMethod) {
    case 'card':
      return 'visa';
    case 'mobile_money':
      return 'orange';
    case 'eft':
      return 'eft';
    default:
      return 'unknown';
  }
};

// Create a new order
export const createOrder = async (order: Order) => {
  try {
    console.log('📝 Creating order:', { id: order.id, total: order.total, customer: order.customer });
    
    const orderData: any = {
      id: order.id,
      customer: order.customer,
      total: order.total,
      status: order.orderStatus,
      payment_status: order.paymentStatus,
      payment_method: order.paymentMethod,
      items: order.items || []
    };
    
    if (order.subtotal !== undefined && order.subtotal !== null) {
      orderData.subtotal = order.subtotal;
    }
    if (order.deliveryFee !== undefined && order.deliveryFee !== null) {
      orderData.delivery_fee = order.deliveryFee;
    }
    if (order.distanceFromOrigin !== undefined && order.distanceFromOrigin !== null) {
      orderData.distance_from_origin = order.distanceFromOrigin;
    }
    if (order.deliveryLocation !== undefined && order.deliveryLocation !== null) {
      orderData.delivery_location = order.deliveryLocation;
    }
    
    const { data: orderResult, error: orderError } = await supabase
      .from('orders')
      .insert(orderData)
      .select()
      .single();

    if (orderError) {
      console.error('Order insert error:', orderError);
      throw orderError;
    }
    
    console.log('✅ Order created successfully:', orderResult);

    // Create initial pending transaction
    const transactionData = {
      order_id: order.id,
      amount: order.total,
      payment_method: order.paymentMethod,
      payment_type: getPaymentType(order.paymentMethod),
      status: 'pending',
      reference: null
    };
    
    const { data: transactionResult, error: transactionError } = await supabase
      .from('transactions')
      .insert(transactionData)
      .select()
      .single();

    if (transactionError) {
      console.error('Transaction insert error:', transactionError);
      console.log('⚠️ Transaction creation failed but order was created');
    } else {
      console.log('✅ Initial pending transaction created:', transactionResult);
    }
    
    // Update customer with order ID
    const { error: updateCustomerError } = await supabase
      .from('customers')
      .update({ order_id: order.id })
      .eq('phone', order.customer);
    
    if (updateCustomerError) {
      console.error('Error updating customer with order ID:', updateCustomerError);
    } else {
      console.log('✅ Customer updated with order ID:', order.id);
    }
    
    return { 
      ...orderResult, 
      status: mapStatusToDisplay(orderResult.status),
      transactions: transactionResult ? [transactionResult] : []
    };
  } catch (error) {
    console.error('❌ Error in createOrder:', error);
    throw error;
  }
};

// Update transaction with payment result
export const updateTransactionWithPaymentResult = async (
  orderId: string,
  paymentResult: {
    success: boolean;
    reference?: string;
    error?: string;
  }
) => {
  try {
    console.log(`📝 Updating transaction for order ${orderId} with payment result:`, paymentResult);
    
    // Get the latest transaction for this order
    const { data: transactions, error: fetchError } = await supabase
      .from('transactions')
      .select('*')
      .eq('order_id', orderId)
      .order('created_at', { ascending: false })
      .limit(1);
    
    if (fetchError) {
      console.error('Error fetching transaction:', fetchError);
      throw fetchError;
    }
    
    if (!transactions || transactions.length === 0) {
      console.error('No transaction found for order:', orderId);
      // Create a new transaction if none exists
      const { data: order, error: orderError } = await supabase
        .from('orders')
        .select('total, payment_method')
        .eq('id', orderId)
        .single();
      
      if (orderError) {
        console.error('Error fetching order for new transaction:', orderError);
        throw orderError;
      }
      
      // Set simple reference values
      const referenceValue = paymentResult.success ? 'successful' : 'unsuccessful';
      
      const newTransaction = {
        order_id: orderId,
        amount: order.total,
        payment_method: order.payment_method,
        payment_type: getPaymentType(order.payment_method),
        status: paymentResult.success ? 'completed' : 'failed',
        reference: referenceValue
      };
      
      const { data: newTrans, error: insertError } = await supabase
        .from('transactions')
        .insert(newTransaction)
        .select()
        .single();
      
      if (insertError) throw insertError;
      console.log('✅ New transaction created with payment result:', newTrans);
      return newTrans;
    }
    
    const transaction = transactions[0];
    
    // Set simple reference values
    let referenceValue: string;
    if (paymentResult.success) {
      referenceValue = 'successful';
    } else {
      referenceValue = 'unsuccessful';
    }
    
    const updateData = {
      status: paymentResult.success ? 'completed' : 'failed',
      reference: referenceValue,
      updated_at: new Date().toISOString()
    };
    
    const { data: updatedTransaction, error: updateError } = await supabase
      .from('transactions')
      .update(updateData)
      .eq('id', transaction.id)
      .select()
      .single();
    
    if (updateError) {
      console.error('Error updating transaction:', updateError);
      throw updateError;
    }
    
    console.log('✅ Transaction updated with payment result:', updatedTransaction);
    return updatedTransaction;
  } catch (error) {
    console.error('❌ Error updating transaction with payment result:', error);
    throw error;
  }
};

// Get all orders
export const getAllOrders = async () => {
  try {
    const { data: orders, error } = await supabase
      .from('orders')
      .select(`
        *,
        transactions (*)
      `)
      .order('created_at', { ascending: false });

    if (error) throw error;
    
    return orders.map(order => ({
      ...order,
      id: order.id,
      createdAt: order.created_at,
      updatedAt: order.updated_at,
      paymentStatus: order.payment_status,
      status: mapStatusToDisplay(order.status),
      orderStatus: order.status,
      transactions: order.transactions?.map((t: any) => ({
        ...t,
        id: t.id,
        createdAt: t.created_at,
        updatedAt: t.updated_at,
        orderId: t.order_id
      })) || []
    }));
  } catch (error) {
    console.error('Error getting orders: ', error);
    throw error;
  }
};

// Get orders by user phone
export const getOrdersByPhone = async (phone: string) => {
  try {
    const { data: orders, error } = await supabase
      .from('orders')
      .select(`
        *,
        transactions (*)
      `)
      .eq('customer', phone)
      .order('created_at', { ascending: false });

    if (error) throw error;
    
    return orders.map(order => ({
      ...order,
      id: order.id,
      createdAt: order.created_at,
      updatedAt: order.updated_at,
      paymentStatus: order.payment_status,
      status: mapStatusToDisplay(order.status),
      orderStatus: order.status,
      transactions: order.transactions?.map((t: any) => ({
        ...t,
        id: t.id,
        createdAt: t.created_at,
        updatedAt: t.updated_at,
        orderId: t.order_id
      })) || []
    }));
  } catch (error) {
    console.error('Error getting user orders: ', error);
    throw error;
  }
};

// Get single order by ID
export const getOrderById = async (orderId: string) => {
  try {
    const { data: order, error } = await supabase
      .from('orders')
      .select(`
        *,
        transactions (*)
      `)
      .eq('id', orderId)
      .single();

    if (error) {
      if (error.code === 'PGRST116') return null;
      throw error;
    }
    
    return {
      ...order,
      id: order.id,
      createdAt: order.created_at,
      updatedAt: order.updated_at,
      paymentStatus: order.payment_status,
      status: mapStatusToDisplay(order.status),
      orderStatus: order.status,
      transactions: order.transactions?.map((t: any) => ({
        ...t,
        id: t.id,
        createdAt: t.created_at,
        updatedAt: t.updated_at,
        orderId: t.order_id
      })) || []
    };
  } catch (error) {
    console.error('Error getting order: ', error);
    throw error;
  }
};

// Add transaction
export const addTransaction = async (
  orderId: string, 
  transactionData: {
    amount: number;
    paymentMethod: string;
    paymentType: string;
    status: 'pending' | 'completed' | 'failed';
    reference?: string;
  }
) => {
  try {
    console.log(`📝 Adding transaction for order ${orderId}:`, transactionData);
    
    const { data, error } = await supabase
      .from('transactions')
      .insert({
        order_id: orderId,
        amount: transactionData.amount,
        payment_method: transactionData.paymentMethod,
        payment_type: transactionData.paymentType,
        status: transactionData.status,
        reference: transactionData.reference || null
      })
      .select()
      .single();

    if (error) throw error;
    
    console.log('✅ Transaction added:', data);
    return {
      id: data.id,
      ...transactionData,
      createdAt: data.created_at,
      updatedAt: data.updated_at
    };
  } catch (error) {
    console.error('❌ Error adding transaction: ', error);
    throw error;
  }
};

// Get transactions by order ID
export const getTransactionsByOrderId = async (orderId: string) => {
  try {
    const { data, error } = await supabase
      .from('transactions')
      .select('*')
      .eq('order_id', orderId)
      .order('created_at', { ascending: false });

    if (error) throw error;
    
    return data.map(t => ({
      id: t.id,
      orderId: t.order_id,
      amount: t.amount,
      paymentMethod: t.payment_method,
      paymentType: t.payment_type,
      status: t.status,
      reference: t.reference,
      createdAt: t.created_at,
      updatedAt: t.updated_at
    }));
  } catch (error) {
    console.error('Error getting transactions: ', error);
    throw error;
  }
};

// Update transaction status
export const updateTransactionStatus = async (
  orderId: string, 
  transactionId: string, 
  status: 'pending' | 'completed' | 'failed',
  reference?: string
) => {
  try {
    const updateData: any = { status };
    if (reference) updateData.reference = reference;
    
    const { error } = await supabase
      .from('transactions')
      .update(updateData)
      .eq('id', transactionId)
      .eq('order_id', orderId);

    if (error) throw error;
    console.log('✅ Transaction status updated');
  } catch (error) {
    console.error('❌ Error updating transaction: ', error);
    throw error;
  }
};

// Update order status
export const updateOrderStatus = async (orderId: string, displayStatus: DisplayOrderStatus) => {
  try {
    const statusMap: Record<DisplayOrderStatus, DBOrderStatus> = {
      'Pending Payment': 'pending',
      'Processing': 'processing',
      'Out for Delivery': 'processing',
      'Delivered': 'completed',
      'Cancelled': 'cancelled'
    };
    
    const dbStatus = statusMap[displayStatus] || 'pending';
    console.log(`📝 Updating order status for ${orderId} to ${dbStatus} (from ${displayStatus})`);
    
    const { error } = await supabase
      .from('orders')
      .update({ status: dbStatus })
      .eq('id', orderId);

    if (error) throw error;
    console.log('✅ Order status updated');
  } catch (error) {
    console.error('❌ Error updating order: ', error);
    throw error;
  }
};

// Update payment status
export const updatePaymentStatus = async (orderId: string, paymentStatus: 'pending' | 'paid' | 'failed') => {
  try {
    console.log(`📝 Updating payment status for order ${orderId} to ${paymentStatus}`);
    
    const { error } = await supabase
      .from('orders')
      .update({ payment_status: paymentStatus })
      .eq('id', orderId);

    if (error) throw error;
    console.log('✅ Payment status updated');
  } catch (error) {
    console.error('❌ Error updating payment: ', error);
    throw error;
  }
};