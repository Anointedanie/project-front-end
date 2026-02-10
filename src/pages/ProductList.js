import React, { useState } from 'react';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import './ProductList.css';

// STATIC MOCK PRODUCTS - No backend needed
const STATIC_PRODUCTS = [
  {
    id: 1,
    name: 'Premium Wireless Headphones',
    description: 'High-fidelity audio with active noise cancellation',
    price: 299.99,
    stock_quantity: 15,
    image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400',
  },
  {
    id: 2,
    name: 'Luxury Leather Watch',
    description: 'Elegant timepiece with Italian leather strap',
    price: 549.99,
    stock_quantity: 8,
    image: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400',
  },
  {
    id: 3,
    name: 'Designer Sunglasses',
    description: 'UV protection with polarized lenses',
    price: 189.99,
    stock_quantity: 22,
    image: 'https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400',
  },
  {
    id: 4,
    name: 'Minimalist Backpack',
    description: 'Water-resistant with laptop compartment',
    price: 129.99,
    stock_quantity: 5,
    image: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400',
  },
  {
    id: 5,
    name: 'Smart Fitness Tracker',
    description: 'Track your health and fitness goals',
    price: 199.99,
    stock_quantity: 30,
    image: 'https://images.unsplash.com/photo-1560343090-f0409e92791a?w=400',
  },
  {
    id: 6,
    name: 'Premium Running Shoes',
    description: 'Lightweight with superior cushioning',
    price: 159.99,
    stock_quantity: 12,
    image: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400',
  },
  {
    id: 7,
    name: 'Portable Bluetooth Speaker',
    description: 'Waterproof with 360° sound',
    price: 89.99,
    stock_quantity: 18,
    image: 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400',
  },
  {
    id: 8,
    name: 'Classic Sneakers',
    description: 'Timeless style meets comfort',
    price: 119.99,
    stock_quantity: 25,
    image: 'https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=400',
  },
];

const ProductList = () => {
  const [products] = useState(STATIC_PRODUCTS);
  const [addingToCart, setAddingToCart] = useState({});
  
  const { addToCart } = useCart();
  const { isAdmin } = useAuth();
  
  const handleAddToCart = async (product) => {
    setAddingToCart({ ...addingToCart, [product.id]: true });
    
    // Add to local cart (no backend)
    const result = await addToCart(product, 1);
    
    if (result.success) {
      showToast('Product added to cart!', 'success');
    } else {
      showToast(result.error, 'error');
    }
    
    setAddingToCart({ ...addingToCart, [product.id]: false });
  };
  
  const showToast = (message, type) => {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<p><strong>${message}</strong></p>`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.remove();
    }, 3000);
  };
  
  return (
    <div className="products-container fade-in">
      <div className="products-header">
        <h1>Curated Collection</h1>
        <p>Discover our hand-picked selection of premium products</p>
      </div>
      
      {products.length === 0 ? (
        <div className="empty-state">
          <h3>No products available</h3>
          <p>Check back soon for new arrivals</p>
        </div>
      ) : (
        <div className="products-grid">
          {products.map((product) => (
            <div key={product.id} className="product-card">
              <div className="product-image-container">
                <img 
                  src={product.image} 
                  alt={product.name}
                  className="product-image"
                  onError={(e) => {
                    e.target.src = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400';
                  }}
                />
                {product.stock_quantity < 10 && product.stock_quantity > 0 && (
                  <span className="product-badge">Limited Stock</span>
                )}
                {product.stock_quantity === 0 && (
                  <span className="product-badge out-of-stock">Out of Stock</span>
                )}
              </div>
              
              <div className="product-content">
                <h3 className="product-name">{product.name}</h3>
                <p className="product-description">{product.description}</p>
                
                <div className="product-footer">
                  <div className="product-price">
                    ${parseFloat(product.price).toFixed(2)}
                  </div>
                  
                  {!isAdmin && (
                    <button
                      onClick={() => handleAddToCart(product)}
                      disabled={addingToCart[product.id] || product.stock_quantity === 0}
                      className="btn btn-primary btn-sm"
                    >
                      {addingToCart[product.id] 
                        ? 'Adding...' 
                        : product.stock_quantity === 0 
                        ? 'Out of Stock'
                        : 'Add to Cart'
                      }
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProductList;
