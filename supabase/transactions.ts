import { supabase } from './config';

export interface Transaction {
  id?: string;
  orderId: string;
  amount: number;
  currency: string;
  paymentMethod: string;
  status: 'pending' | 'completed' | 'failed';
  stripePaymentIntentId?: string;
  customerEmail?: string;
  customerPhone?: string;
  createdAt: Date;
  updatedAt: Date;
}

// Create a new transaction record
export const createTransaction = async (transactionData: Omit<Transaction, 'id' | 'createdAt' | 'updatedAt'>) => {
  try {
    const { data, error } = await supabase
      .from('transactions')
      .insert({
        order_id: transactionData.orderId,
        amount: transactionData.amount,
        payment_method: transactionData.paymentMethod,
        payment_type: getPaymentType(transactionData.paymentMethod),
        status: transactionData.status,
        reference: transactionData.stripePaymentIntentId
      })
      .select()
      .single();

    if (error) throw error;
    
    console.log('Transaction created with ID: ', data.id);
    return {
      id: data.id,
      ...transactionData,
      createdAt: data.created_at,
      updatedAt: data.updated_at
    };
  } catch (error) {
    console.error('Error creating transaction: ', error);
    throw error;
  }
};

// Helper function
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

// Update transaction status
export const updateTransactionStatus = async (transactionId: string, status: Transaction['status']) => {
  try {
    const { error } = await supabase
      .from('transactions')
      .update({ status })
      .eq('id', transactionId);

    if (error) throw error;
    console.log('Transaction status updated');
  } catch (error) {
    console.error('Error updating transaction: ', error);
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
      status: t.status,
      createdAt: t.created_at,
      updatedAt: t.updated_at
    }));
  } catch (error) {
    console.error('Error getting transactions: ', error);
    throw error;
  }
};

// Get all transactions (for admin)
export const getAllTransactions = async () => {
  try {
    const { data, error } = await supabase
      .from('transactions')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) throw error;
    
    return data.map(t => ({
      id: t.id,
      orderId: t.order_id,
      amount: t.amount,
      paymentMethod: t.payment_method,
      status: t.status,
      createdAt: t.created_at,
      updatedAt: t.updated_at
    }));
  } catch (error) {
    console.error('Error getting transactions: ', error);
    throw error;
  }
};