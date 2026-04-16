
import React, { useState, useContext, useMemo } from 'react';
import { AppContext } from '../context/AppContext';
import ProductCard from './ProductCard';

const ProductList: React.FC = () => {
  const context = useContext(AppContext);
  const [selectedCategory, setSelectedCategory] = useState('All');

  if (!context) return null;

  const { products } = context;

  const categories = useMemo(() => {
      const uniqueCategories = Array.from(new Set(products.map(p => p.category)));
      return ['All', ...uniqueCategories];
  }, [products]);

  const filteredProducts =
    selectedCategory === 'All'
      ? products
      : products.filter(p => p.category === selectedCategory);

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-2">Our Products</h1>
      <p className="text-md text-gray-600 mb-6">Select from our range of high-quality quarry materials.</p>
      
      <div className="mb-8 overflow-x-auto pb-2">
        <div className="flex space-x-2">
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 text-sm font-semibold rounded-full transition-colors whitespace-nowrap ${
                selectedCategory === category
                  ? 'bg-primary text-white shadow'
                  : 'bg-surface text-secondary hover:bg-gray-200'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {products.length === 0 ? (
          <div className="text-center py-10">
              <p>Loading products...</p>
          </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredProducts.map(product => (
            <ProductCard key={product.id} product={product} />
            ))}
        </div>
      )}
    </div>
  );
};

export default ProductList;
