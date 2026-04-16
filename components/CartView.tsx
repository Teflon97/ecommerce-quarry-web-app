import React, { useContext, useMemo } from 'react';
import { AppContext } from '../context/AppContext';
import { MinusIcon, PlusIcon, TrashIcon } from './icons';

const CartView: React.FC = () => {
  const context = useContext(AppContext);

  if (!context) return null;

  const { cart, updateCartQuantity, removeFromCart, setView } = context;

  const subtotal = useMemo(
    () => cart.reduce((sum, item) => sum + item.product.price * item.quantity, 0),
    [cart]
  );

  const handleProceed = () => {
    setView('checkout');
  };

  if (cart.length === 0) {
    return (
      <div className="text-center py-20">
        <h2 className="text-2xl font-bold text-black mb-4">Your Cart is Empty</h2>
        <p className="text-gray-800 mb-6">Looks like you haven't added any materials yet.</p>
        <button onClick={() => setView('products')} className="bg-orange-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-orange-700">
          Start Shopping
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto bg-white p-4 sm:p-8 rounded-xl shadow-lg border border-gray-200">
      <h1 className="text-3xl font-bold text-black mb-6 border-b border-gray-300 pb-4">Your Cart</h1>
      <ul className="divide-y divide-gray-300">
        {cart.map(({ product, quantity }) => (
          <li key={product.id} className="flex flex-col sm:flex-row items-center justify-between py-6">
            <div className="flex items-center mb-4 sm:mb-0">
              <img src={product.imageUrl} alt={product.name} className="w-24 h-24 rounded-lg object-cover mr-6 shadow-sm" />
              <div>
                <h3 className="text-lg font-semibold text-black">{product.name}</h3>
                <p className="text-gray-800">P{product.price.toFixed(2)} / {product.unit}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center border border-gray-400 rounded-lg bg-white">
                <button 
                  onClick={() => updateCartQuantity(product.id, quantity - 1)} 
                  className="p-2 text-black hover:bg-orange-600 hover:text-white rounded-l-lg transition-colors"
                  title="Decrease quantity"
                >
                  <MinusIcon className="w-5 h-5" />
                </button>
                <span className="px-4 py-1 text-lg font-bold text-black min-w-[3rem] text-center">{quantity}</span>
                <button 
                  onClick={() => updateCartQuantity(product.id, quantity + 1)} 
                  className="p-2 text-black hover:bg-orange-600 hover:text-white rounded-r-lg transition-colors"
                  title="Increase quantity"
                >
                  <PlusIcon className="w-5 h-5" />
                </button>
              </div>
              <p className="text-lg font-bold text-black w-24 text-right">
                P{(product.price * quantity).toFixed(2)}
              </p>
              <button 
                onClick={() => removeFromCart(product.id)} 
                className="text-red-600 hover:text-red-800 p-2 rounded-full hover:bg-red-100 transition-colors"
                title="Remove from cart"
              >
                <TrashIcon className="w-6 h-6" />
              </button>
            </div>
          </li>
        ))}
      </ul>
      <div className="mt-8 pt-6 border-t border-gray-300 flex flex-col sm:flex-row items-center justify-between">
        <div className="text-left mb-4 sm:mb-0">
          <h3 className="text-2xl font-bold text-black">Subtotal: P{subtotal.toFixed(2)}</h3>
          <p className="text-gray-800">Delivery fees will be calculated at checkout.</p>
        </div>
        <button 
          onClick={handleProceed} 
          className="w-full sm:w-auto bg-green-600 text-white font-bold py-3 px-8 rounded-lg hover:bg-green-700 text-lg"
        >
          Proceed to Checkout
        </button>
      </div>
    </div>
  );
};

export default CartView;