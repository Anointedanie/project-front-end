import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import './Cart.css';

const Cart = () => {
  const { cart, loading, updateQuantity, removeFromCart, getCartTotal } = useCart();
  const navigate = useNavigate();
  
  const handleQuantityChange = async (itemId, newQuantity) => {
    if (newQuantity < 1) return;
    await updateQuantity(itemId, newQuantity);
  };
  
  const handleRemove = async (itemId) => {
    const result = await removeFromCart(itemId);
    if (result.success) {
      showToast('Item removed from cart', 'success');
    }
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
  
  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }
  
  if (cart.length === 0) {
    return (
      <div className="cart-empty fade-in">
        <h2>Your Cart is Empty</h2>
        <p>Add some items to get started</p>
        <button 
          onClick={() => navigate('/products')} 
          className="btn btn-primary"
        >
          Continue Shopping
        </button>
      </div>
    );
  }
  
  return (
    <div className="cart-container fade-in">
      <div className="cart-header">
        <h1>Shopping Cart</h1>
        <p>{cart.length} {cart.length === 1 ? 'item' : 'items'}</p>
      </div>
      
      <div className="cart-content">
        <div className="cart-items">
          {cart.map((item) => (
            <div key={item.id} className="cart-item">
              <div className="cart-item-image">
                <img 
                  src={item.product.image || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=200'} 
                  alt={item.product.name}
                />
              </div>
              
              <div className="cart-item-details">
                <h3>{item.product.name}</h3>
                <p className="cart-item-price">
                  ${parseFloat(item.product.price).toFixed(2)}
                </p>
              </div>
              
              <div className="cart-item-actions">
                <div className="quantity-control">
                  <button
                    onClick={() => handleQuantityChange(item.id, item.quantity - 1)}
                    className="quantity-btn"
                    disabled={item.quantity <= 1}
                  >
                    −
                  </button>
                  <span className="quantity-display">{item.quantity}</span>
                  <button
                    onClick={() => handleQuantityChange(item.id, item.quantity + 1)}
                    className="quantity-btn"
                  >
                    +
                  </button>
                </div>
                
                <div className="cart-item-total">
                  ${(parseFloat(item.product.price) * item.quantity).toFixed(2)}
                </div>
                
                <button
                  onClick={() => handleRemove(item.id)}
                  className="btn-remove"
                  title="Remove item"
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>
        
        <div className="cart-summary">
          <h2>Order Summary</h2>
          
          <div className="summary-row">
            <span>Subtotal</span>
            <span>${getCartTotal().toFixed(2)}</span>
          </div>
          
          <div className="summary-row">
            <span>Shipping</span>
            <span>Calculated at checkout</span>
          </div>
          
          <div className="summary-divider"></div>
          
          <div className="summary-row summary-total">
            <span>Total</span>
            <span>${getCartTotal().toFixed(2)}</span>
          </div>
          
          <button 
            onClick={() => navigate('/checkout')}
            className="btn btn-primary btn-block"
          >
            Proceed to Checkout
          </button>
          
          <button 
            onClick={() => navigate('/products')}
            className="btn btn-secondary btn-block mt-2"
          >
            Continue Shopping
          </button>
        </div>
      </div>
    </div>
  );
};

export default Cart;
