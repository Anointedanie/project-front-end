import React, { useState, useEffect } from 'react';
import './AdminDashboard.css';

// STATIC PRODUCTS FOR DEMO
const INITIAL_PRODUCTS = [
  { id: 1, name: 'Premium Wireless Headphones', description: 'High-fidelity audio with active noise cancellation', price: 299.99, stock_quantity: 15, category: 'Electronics' },
  { id: 2, name: 'Luxury Leather Watch', description: 'Elegant timepiece with Italian leather strap', price: 549.99, stock_quantity: 8, category: 'Accessories' },
  { id: 3, name: 'Designer Sunglasses', description: 'UV protection with polarized lenses', price: 189.99, stock_quantity: 22, category: 'Accessories' },
  { id: 4, name: 'Minimalist Backpack', description: 'Water-resistant with laptop compartment', price: 129.99, stock_quantity: 5, category: 'Bags' },
  { id: 5, name: 'Smart Fitness Tracker', description: 'Track your health and fitness goals', price: 199.99, stock_quantity: 30, category: 'Electronics' },
  { id: 6, name: 'Premium Running Shoes', description: 'Lightweight with superior cushioning', price: 159.99, stock_quantity: 12, category: 'Footwear' },
];

const AdminDashboard = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    stock_quantity: '',
    category: '',
    image_url: ''
  });
  
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  useEffect(() => {
    // Load products from localStorage or use initial data
    const savedProducts = localStorage.getItem('admin_products');
    if (savedProducts) {
      setProducts(JSON.parse(savedProducts));
    } else {
      setProducts(INITIAL_PRODUCTS);
      localStorage.setItem('admin_products', JSON.stringify(INITIAL_PRODUCTS));
    }
    setLoading(false);
  }, []);
  
  const saveProducts = (newProducts) => {
    setProducts(newProducts);
    localStorage.setItem('admin_products', JSON.stringify(newProducts));
  };
  
  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };
  
  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      price: '',
      stock_quantity: '',
      category: '',
      image_url: ''
    });
    setEditingProduct(null);
    setShowForm(false);
    setError('');
  };
  
  const handleEdit = (product) => {
    setEditingProduct(product);
    setFormData({
      name: product.name,
      description: product.description,
      price: product.price,
      stock_quantity: product.stock_quantity,
      category: product.category || '',
      image_url: product.image || ''
    });
    setShowForm(true);
    setError('');
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    
    // Simulate API delay
    setTimeout(() => {
      try {
        const productData = {
          name: formData.name,
          description: formData.description,
          price: parseFloat(formData.price),
          stock_quantity: parseInt(formData.stock_quantity),
          category: formData.category,
          image: formData.image_url
        };
        
        if (editingProduct) {
          // Update existing product
          const newProducts = products.map(p =>
            p.id === editingProduct.id ? { ...productData, id: p.id } : p
          );
          saveProducts(newProducts);
          showToast('Product updated successfully', 'success');
        } else {
          // Add new product
          const newProduct = {
            ...productData,
            id: Date.now() // Generate temporary ID
          };
          saveProducts([...products, newProduct]);
          showToast('Product added successfully', 'success');
        }
        
        resetForm();
      } catch (err) {
        setError('Failed to save product');
      } finally {
        setSubmitting(false);
      }
    }, 500);
  };
  
  const handleDelete = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) {
      return;
    }
    
    try {
      const newProducts = products.filter(p => p.id !== productId);
      saveProducts(newProducts);
      showToast('Product deleted successfully', 'success');
    } catch (err) {
      showToast('Failed to delete product', 'error');
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
  
  return (
    <div className="admin-container fade-in">
      <div className="admin-header">
        <div>
          <h1>Product Management</h1>
          <p>Manage your store inventory</p>
        </div>
        
        {!showForm && (
          <button 
            onClick={() => setShowForm(true)}
            className="btn btn-gold"
          >
            + Add New Product
          </button>
        )}
      </div>
      
      {showForm && (
        <div className="product-form-container">
          <div className="form-header">
            <h2>{editingProduct ? 'Edit Product' : 'Add New Product'}</h2>
            <button 
              onClick={resetForm}
              className="btn-close"
            >
              ×
            </button>
          </div>
          
          <form onSubmit={handleSubmit} className="product-form">
            {error && (
              <div className="alert alert-error">
                {error}
              </div>
            )}
            
            <div className="form-group">
              <label htmlFor="name" className="form-label">Product Name</label>
              <input
                id="name"
                name="name"
                type="text"
                className="form-input"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="Enter product name"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="description" className="form-label">Description</label>
              <textarea
                id="description"
                name="description"
                className="form-textarea"
                value={formData.description}
                onChange={handleChange}
                required
                placeholder="Enter product description"
              />
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="price" className="form-label">Price ($)</label>
                <input
                  id="price"
                  name="price"
                  type="number"
                  step="0.01"
                  min="0"
                  className="form-input"
                  value={formData.price}
                  onChange={handleChange}
                  required
                  placeholder="0.00"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="stock_quantity" className="form-label">Stock Quantity</label>
                <input
                  id="stock_quantity"
                  name="stock_quantity"
                  type="number"
                  min="0"
                  className="form-input"
                  value={formData.stock_quantity}
                  onChange={handleChange}
                  required
                  placeholder="0"
                />
              </div>
            </div>
            
            <div className="form-group">
              <label htmlFor="category" className="form-label">Category (Optional)</label>
              <input
                id="category"
                name="category"
                type="text"
                className="form-input"
                value={formData.category}
                onChange={handleChange}
                placeholder="e.g., Electronics, Fashion, Home"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="image_url" className="form-label">Image URL (Optional)</label>
              <input
                id="image_url"
                name="image_url"
                type="url"
                className="form-input"
                value={formData.image_url}
                onChange={handleChange}
                placeholder="https://example.com/image.jpg"
              />
              <small className="form-help">
                Leave empty to use placeholder images
              </small>
            </div>
            
            <div className="form-actions">
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={submitting}
              >
                {submitting 
                  ? 'Saving...' 
                  : editingProduct 
                  ? 'Update Product' 
                  : 'Add Product'
                }
              </button>
              
              <button 
                type="button"
                onClick={resetForm}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
      
      <div className="products-table-container">
        <h2>All Products ({products.length})</h2>
        
        {products.length === 0 ? (
          <div className="empty-state">
            <p>No products available. Add your first product to get started.</p>
          </div>
        ) : (
          <div className="products-table">
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Price</th>
                  <th>Stock</th>
                  <th>Category</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.id}>
                    <td>
                      <div className="product-cell">
                        <div className="product-name-cell">
                          <strong>{product.name}</strong>
                          <span className="product-description-cell">
                            {product.description}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="price-cell">${parseFloat(product.price).toFixed(2)}</td>
                    <td>
                      <span className={`stock-badge ${product.stock_quantity < 10 ? 'low-stock' : ''}`}>
                        {product.stock_quantity}
                      </span>
                    </td>
                    <td>{product.category || '-'}</td>
                    <td>
                      <div className="action-buttons">
                        <button
                          onClick={() => handleEdit(product)}
                          className="btn-action btn-edit"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(product.id)}
                          className="btn-action btn-delete"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
