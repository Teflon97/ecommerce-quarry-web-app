import React, { useContext } from 'react';
import { AppContext } from '../context/AppContext';
import { CartIcon } from './icons';

const Header: React.FC = () => {
  const context = useContext(AppContext);

  if (!context) {
    return null;
  }

  const { setView, cart } = context;
  const cartItemCount = cart.length;

  return (
    <header className="bg-orange-600 shadow-md sticky top-0 z-50">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <button onClick={() => setView('products')} className="flex-shrink-0">
              <span className="text-xl font-bold text-white">Belabela Quarries Online Shop</span>
            </button>
          </div>
          <div className="flex items-center">
            <button onClick={() => setView('cart')} className="relative text-white hover:text-gray-200 transition-colors p-2 rounded-full" title="Cart">
              <CartIcon className="h-6 w-6" />
              {cartItemCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
                  {cartItemCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </nav>
    </header>
  );
};

export default Header;