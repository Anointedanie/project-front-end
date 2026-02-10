import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';

const CartContext = createContext(null);

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState([]);
  const { isAuthenticated } = useAuth();

  // Load cart from localStorage when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const savedCart = localStorage.getItem('cart');
      if (savedCart) {
        setCart(JSON.parse(savedCart));
      }
    } else {
      setCart([]);
    }
  }, [isAuthenticated]);

  // Save cart to localStorage whenever it changes
  useEffect(() => {
    if (isAuthenticated && cart.length >= 0) {
      localStorage.setItem('cart', JSON.stringify(cart));
    }
  }, [cart, isAuthenticated]);

  const addToCart = async (product, quantity = 1) => {
    try {
      // Check if product already in cart
      const existingItemIndex = cart.findIndex(item => item.product.id === product.id);
      
      if (existingItemIndex >= 0) {
        // Update quantity
        const newCart = [...cart];
        newCart[existingItemIndex].quantity += quantity;
        setCart(newCart);
      } else {
        // Add new item
        const newItem = {
          id: Date.now(), // Generate temporary ID
          product: product,
          quantity: quantity
        };
        setCart([...cart, newItem]);
      }
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: 'Failed to add to cart' 
      };
    }
  };

  const updateQuantity = async (itemId, quantity) => {
    try {
      if (quantity < 1) return { success: false, error: 'Quantity must be at least 1' };
      
      const newCart = cart.map(item =>
        item.id === itemId ? { ...item, quantity } : item
      );
      setCart(newCart);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: 'Failed to update quantity' 
      };
    }
  };

  const removeFromCart = async (itemId) => {
    try {
      const newCart = cart.filter(item => item.id !== itemId);
      setCart(newCart);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: 'Failed to remove item' 
      };
    }
  };

  const clearCart = async () => {
    try {
      setCart([]);
      localStorage.removeItem('cart');
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: 'Failed to clear cart' 
      };
    }
  };

  const getCartTotal = () => {
    return cart.reduce((total, item) => {
      return total + (item.product.price * item.quantity);
    }, 0);
  };

  const getCartCount = () => {
    return cart.reduce((count, item) => count + item.quantity, 0);
  };

  const value = {
    cart,
    loading: false,
    addToCart,
    updateQuantity,
    removeFromCart,
    clearCart,
    getCartTotal,
    getCartCount,
    refreshCart: () => {}, // No-op for compatibility
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};
