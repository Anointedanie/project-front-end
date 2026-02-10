import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { CartProvider, useCart } from './contexts/CartContext';
import './App.css';

// Import pages
import UserLogin from './pages/UserLogin';
import AdminLogin from './pages/AdminLogin';
import Register from './pages/Register';
import ProductList from './pages/ProductList';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import AdminDashboard from './pages/AdminDashboard';
import UserProfile from './pages/UserProfile';

// Protected Route Component
const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  if (adminOnly && !isAdmin) {
    return <Navigate to="/products" replace />;
  }
  
  return children;
};

// Navigation Component
const Navigation = () => {
  const { isAuthenticated, isAdmin, logout, user } = useAuth();
  const { getCartCount } = useCart();
  
  return (
    <nav className="navbar">
      <div className="navbar-content">
        <Link to="/products" className="navbar-brand">
          LUXE MARKET
        </Link>
        
        <div className="navbar-links">
          {isAuthenticated ? (
            <>
              <Link to="/products" className="nav-link">Products</Link>
              
              {!isAdmin && (
                <>
                  <Link to="/cart" className="nav-link">
                    Cart
                    {getCartCount() > 0 && (
                      <span className="cart-badge">{getCartCount()}</span>
                    )}
                  </Link>
                  
                  <Link to="/profile" className="nav-link">Profile</Link>
                </>
              )}
              
              {isAdmin && (
                <Link to="/admin" className="nav-link">Dashboard</Link>
              )}
              
              <span className="nav-link" style={{ cursor: 'default' }}>
                {user?.email || 'User'}
              </span>
              
              <button 
                onClick={logout} 
                className="nav-link" 
                style={{ background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-link">Login</Link>
              <Link to="/register" className="nav-link">Register</Link>
              <Link to="/admin/login" className="nav-link">Admin</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

// Main App Component
function AppContent() {
  return (
    <div className="app">
      <Navigation />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/products" replace />} />
          <Route path="/login" element={<UserLogin />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/register" element={<Register />} />
          
          <Route 
            path="/products" 
            element={
              <ProtectedRoute>
                <ProductList />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/cart" 
            element={
              <ProtectedRoute>
                <Cart />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/checkout" 
            element={
              <ProtectedRoute>
                <Checkout />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/profile" 
            element={
              <ProtectedRoute>
                <UserProfile />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute adminOnly>
                <AdminDashboard />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <CartProvider>
          <AppContent />
        </CartProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
