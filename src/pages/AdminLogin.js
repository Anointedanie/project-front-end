import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Auth.css';

const AdminLogin = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login, isAuthenticated, isAdmin } = useAuth();
  const navigate = useNavigate();
  
  // Redirect if already authenticated as admin
  React.useEffect(() => {
    if (isAuthenticated && isAdmin) {
      navigate('/admin');
    } else if (isAuthenticated && !isAdmin) {
      navigate('/products');
    }
  }, [isAuthenticated, isAdmin, navigate]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    const result = await login(email, password, true);
    
    if (result.success) {
      navigate('/admin');
    } else {
      setError(result.error);
      setLoading(false);
    }
  };
  
  return (
    <div className="auth-container fade-in">
      <div className="auth-card admin-card">
        <div className="auth-header">
          <h1>Admin Portal</h1>
          <p>Manage your store inventory</p>
        </div>
        
        <form onSubmit={handleSubmit} className="auth-form">
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="email" className="form-label">Admin Email</label>
            <input
              id="email"
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="admin@example.com"
              autoComplete="email"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password" className="form-label">Admin Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter admin password"
              autoComplete="current-password"
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-gold btn-block"
            disabled={loading}
          >
            {loading ? 'Verifying...' : 'Admin Sign In'}
          </button>
        </form>
        
        <div className="auth-footer">
          <p>
            <Link to="/login" className="auth-link">User Login</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;
