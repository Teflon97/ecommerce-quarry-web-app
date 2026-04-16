import React, { useState, useContext } from 'react';
import type { Product } from '../types';
import { AppContext } from '../context/AppContext';
import { PlusIcon, MinusIcon } from './icons';

interface ProductCardProps {
  product: Product;
}

const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  const [quantity, setQuantity] = useState(1);
  const context = useContext(AppContext);

  const handleAddToCart = () => {
    if (quantity > 0) {
      context?.addToCart(product, quantity);
      setQuantity(1);
    }
  };

  const handleQuantityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    if (isNaN(val)) {
        setQuantity(1);
    } else {
        setQuantity(Math.max(1, Math.min(100, val)));
    }
  };
  
  const increment = () => setQuantity(q => Math.min(100, q + 1));
  const decrement = () => setQuantity(q => Math.max(1, q - 1));

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden flex flex-col transition-transform hover:scale-105 duration-300 border border-gray-200">
      <img src={product.imageUrl} alt={product.name} className="w-full h-48 object-cover" />
      <div className="p-4 flex flex-col flex-grow">
        <h3 className="text-lg font-bold text-black">{product.name}</h3>
        <p className="text-sm text-gray-700 mb-2">{product.category}</p>
        <p className="text-sm text-gray-800 flex-grow mb-4">{product.description}</p>
        <p className="text-xl font-bold text-orange-600 mb-4">
          P{product.price.toFixed(2)}
          <span className="text-sm font-normal text-gray-700"> / {product.unit}</span>
        </p>
        <div className="flex items-center justify-between mb-4">
          <span className="font-semibold text-black">Quantity:</span>
          <div className="flex items-center border border-gray-300 rounded-md bg-white">
            <button 
              onClick={decrement} 
              className="p-2 text-black hover:bg-orange-600 hover:text-white rounded-l-md transition-colors"
            >
                <MinusIcon className="w-4 h-4" />
            </button>
            <input
                type="number"
                value={quantity}
                onChange={handleQuantityChange}
                className="w-16 text-center font-bold outline-none text-black bg-transparent [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                min="1"
                max="100"
            />
            <button 
              onClick={increment} 
              className="p-2 text-black hover:bg-orange-600 hover:text-white rounded-r-md transition-colors"
            >
                <PlusIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
        <button
          onClick={handleAddToCart}
          className="w-full bg-orange-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-orange-700 transition-colors"
        >
          Add to Cart
        </button>
      </div>
    </div>
  );
};

export default ProductCard;