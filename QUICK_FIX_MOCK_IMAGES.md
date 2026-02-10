# Quick Fix for MOCK_IMAGES Error

## The Error
```
[eslint] 
src/pages/ProductList.js
  Line 129:36:  'MOCK_IMAGES' is not defined  no-undef
```

## ✅ Quick Fix

Open `src/pages/ProductList.js` and find line 129:

**Change this:**
```javascript
onError={(e) => {
  e.target.src = MOCK_IMAGES[0];
}}
```

**To this:**
```javascript
onError={(e) => {
  e.target.src = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400';
}}
```

## 🚀 Complete Fix (Copy-Paste Ready)

Replace the entire image tag (around line 124-131) with this:

```javascript
<img 
  src={product.image} 
  alt={product.name}
  className="product-image"
  onError={(e) => {
    e.target.src = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400';
  }}
/>
```

## ✅ Test the Fix

```bash
# Should now build successfully
npm run build

# Expected output: "Compiled successfully!"
```

## 🐳 Then Build Docker

Once the build works locally:

```bash
# Docker build will now work
sudo docker build -t ecommerce-frontend .
```

---

**OR** download the updated package above - it's already fixed! 🎉
