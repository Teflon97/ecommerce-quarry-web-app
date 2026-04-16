import React, { useContext } from 'react';
import { AppContext } from '../context/AppContext';

interface BackButtonProps {
  fallbackView?: 'products' | 'cart' | 'checkout';
}

const BackButton: React.FC<BackButtonProps> = ({ fallbackView = 'products' }) => {
  const context = useContext(AppContext);
  
  if (!context) return null;
  
  const { view, setView } = context;
  
  // Don't show back button on products page or confirmation page
  if (view === 'products' || view === 'confirmation') return null;
  
  const handleGoBack = () => {
    switch(view) {
      case 'checkout':
        setView('cart');
        break;
      case 'cart':
        setView('products');
        break;
      default:
        setView(fallbackView);
    }
  };
  
  return (
    <button
      onClick={handleGoBack}
      className="fixed bottom-6 left-6 bg-gray-800 text-white px-4 py-3 rounded-full shadow-lg hover:bg-gray-900 transition-colors z-40 flex items-center gap-2 group"
      title="Go back"
    >
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        className="h-5 w-5 transform group-hover:-translate-x-1 transition-transform" 
        fill="none" 
        viewBox="0 0 24 24" 
        stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
      </svg>
      <span className="text-sm font-medium hidden sm:inline">
        {view === 'checkout' ? 'Back to Cart' : 'Back to Products'}
      </span>
    </button>
  );
};

export default BackButton;