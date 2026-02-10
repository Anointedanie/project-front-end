import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import './Checkout.css';

const Checkout = () => {
  const { cart, getCartTotal, clearCart } = useCart();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    zipCode: '',
    country: 'Nigeria',
    notes: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    // Simulate order processing
    setTimeout(async () => {
      try {
        // Clear cart after "successful" order
        await clearCart();
        
        // Show success message
        alert('Order placed successfully! (Demo - no payment processed)\n\nThank you for your purchase!');
        
        // Redirect to products page
        navigate('/products');
      } catch (err) {
        setError('Failed to place order. Please try again.');
        setLoading(false);
      }
    }, 1000);
  };
  
  if (cart.length === 0) {
    return (
      <div className="checkout-empty fade-in">
        <h2>Your cart is empty</h2>
        <p>Add items to your cart before checkout</p>
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
    <div className="checkout-container fade-in">
      <div className="checkout-header">
        <h1>Checkout</h1>
        <p>Complete your order</p>
      </div>
      
      <div className="checkout-content">
        <div className="checkout-form-section">
          <form onSubmit={handleSubmit} className="checkout-form">
            {error && (
              <div className="alert alert-error">
                {error}
              </div>
            )}
            
            <div className="form-section">
              <h2>Contact Information</h2>
              
              <div className="form-group">
                <label htmlFor="fullName" className="form-label">Full Name</label>
                <input
                  id="fullName"
                  name="fullName"
                  type="text"
                  className="form-input"
                  value={formData.fullName}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="email" className="form-label">Email Address</label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  className="form-input"
                  value={formData.email}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="phone" className="form-label">Phone Number</label>
                <input
                  id="phone"
                  name="phone"
                  type="tel"
                  className="form-input"
                  value={formData.phone}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
            
            <div className="form-section">
              <h2>Shipping Address</h2>
              
              <div className="form-group">
                <label htmlFor="address" className="form-label">Street Address</label>
                <input
                  id="address"
                  name="address"
                  type="text"
                  className="form-input"
                  value={formData.address}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="city" className="form-label">City</label>
                  <input
                    id="city"
                    name="city"
                    type="text"
                    className="form-input"
                    value={formData.city}
                    onChange={handleChange}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="state" className="form-label">State/Province</label>
                  <input
                    id="state"
                    name="state"
                    type="text"
                    className="form-input"
                    value={formData.state}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="zipCode" className="form-label">ZIP/Postal Code</label>
                  <input
                    id="zipCode"
                    name="zipCode"
                    type="text"
                    className="form-input"
                    value={formData.zipCode}
                    onChange={handleChange}
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="country" className="form-label">Country</label>
                  <input
                    id="country"
                    name="country"
                    type="text"
                    className="form-input"
                    value={formData.country}
                    onChange={handleChange}
                    required
                  />
                </div>
              </div>
            </div>
            
            <div className="form-section">
              <h2>Additional Notes (Optional)</h2>
              
              <div className="form-group">
                <label htmlFor="notes" className="form-label">Order Notes</label>
                <textarea
                  id="notes"
                  name="notes"
                  className="form-textarea"
                  value={formData.notes}
                  onChange={handleChange}
                  placeholder="Any special instructions for your order?"
                />
              </div>
            </div>
            
            <button 
              type="submit" 
              className="btn btn-primary btn-block"
              disabled={loading}
            >
              {loading ? 'Processing...' : 'Place Order'}
            </button>
          </form>
        </div>
        
        <div className="checkout-summary">
          <h2>Order Summary</h2>
          
          <div className="order-items">
            {cart.map((item) => (
              <div key={item.id} className="order-item">
                <div className="order-item-info">
                  <span className="order-item-name">{item.product.name}</span>
                  <span className="order-item-qty">× {item.quantity}</span>
                </div>
                <span className="order-item-price">
                  ${(parseFloat(item.product.price) * item.quantity).toFixed(2)}
                </span>
              </div>
            ))}
          </div>
          
          <div className="summary-divider"></div>
          
          <div className="summary-row">
            <span>Subtotal</span>
            <span>${getCartTotal().toFixed(2)}</span>
          </div>
          
          <div className="summary-row">
            <span>Shipping</span>
            <span>TBD</span>
          </div>
          
          <div className="summary-divider"></div>
          
          <div className="summary-row summary-total">
            <span>Total</span>
            <span>${getCartTotal().toFixed(2)}</span>
          </div>
          
          <div className="payment-notice">
            <p>
              <strong>Note:</strong> Payment processing is not integrated. 
              This is a demo checkout process.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Checkout;
