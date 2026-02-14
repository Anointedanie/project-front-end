# Staging vs Production SSL Certificates

## 🔧 Current Configuration: STAGING (Default)

All automation files are now configured to use **Let's Encrypt STAGING** by default to avoid rate limits during development and testing.

---

## 📝 What Changed

### 1. **deploy_frontend.py** (automation_script/)
```python
# NOW USING STAGING (default)
CLUSTERISSUER_NAME = "letsencrypt-staging"
CLUSTERISSUER_YAML = "../deployment/clusterissuer-staging.yaml"
CERTIFICATE_YAML = "../deployment/certificate-staging.yaml"

# PRODUCTION (commented out)
# CLUSTERISSUER_NAME = "letsencrypt-prod"
# CLUSTERISSUER_YAML = "../deployment/clusterissuer.yaml"
# CERTIFICATE_YAML = "../deployment/certificate.yaml"
```

### 2. **certificate.yaml** (deployment/)
```yaml
# NOW USING STAGING (default)
issuerRef:
  name: letsencrypt-staging
  # For production: letsencrypt-prod
```

### 3. **clusterissuer.yaml** (deployment/)
```yaml
# NOW USING STAGING (default)
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    # For production: https://acme-v02.api.letsencrypt.org/directory
```

---

## 🚀 When to Use Each

### **Use STAGING When:**
- ✅ Testing the deployment process
- ✅ Making changes to certificates/ingress
- ✅ Running CI/CD pipeline multiple times
- ✅ Developing and debugging
- ✅ You hit the rate limit (5 certs/week)

**Result:** Unlimited requests, but browsers show "Not Secure" warning

### **Use PRODUCTION When:**
- ✅ Ready to deploy to real users
- ✅ Need trusted SSL certificate
- ✅ Everything tested and working
- ✅ Rate limit has reset (wait period over)

**Result:** Trusted certificate, no browser warnings, but limited to 5 certs/week

---

## 🔄 How to Switch to Production

### **Option A: Update Default Files (Recommended for CI/CD)**

**When:** After rate limit expires (Feb 15, 2026 at 15:54:21 UTC)

**Step 1:** Update `automation_script/deploy_frontend.py`:
```python
# Change from:
CLUSTERISSUER_NAME = "letsencrypt-staging"
CLUSTERISSUER_YAML = "../deployment/clusterissuer-staging.yaml"
CERTIFICATE_YAML = "../deployment/certificate-staging.yaml"

# To:
CLUSTERISSUER_NAME = "letsencrypt-prod"
CLUSTERISSUER_YAML = "../deployment/clusterissuer.yaml"
CERTIFICATE_YAML = "../deployment/certificate.yaml"
```

**Step 2:** Update `deployment/certificate.yaml`:
```yaml
# Change from:
issuerRef:
  name: letsencrypt-staging

# To:
issuerRef:
  name: letsencrypt-prod
```

**Step 3:** Update `deployment/clusterissuer.yaml`:
```yaml
# Change from:
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: letsencrypt-staging

# To:
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: letsencrypt-prod
```

**Step 4:** Redeploy:
```bash
# Clean up staging deployment
./destroy_frontend.py

# Deploy with production certificates
./deploy_frontend.py
```

---

### **Option B: Use Existing Production Files (Quick Switch)**

**When:** Need production cert right now (after rate limit expires)

Simply use the separate production files that already exist:

**Step 1:** Deploy with production files manually:
```bash
cd automation_script

# Delete staging resources
./destroy_frontend.py

# Apply production clusterissuer
kubectl apply -f ../deployment/clusterissuer-prod.yaml  # Create this file

# Deploy (temporarily override in script or apply manually)
kubectl apply -f ../deployment/namespace.yaml
kubectl apply -f ../deployment/clusterissuer-prod.yaml
kubectl apply -f ../deployment/certificate-prod.yaml
kubectl apply -f ../deployment/deployment.yaml
kubectl apply -f ../deployment/service.yaml
kubectl apply -f ../deployment/frontend-ingress.yaml
```

---

## 📊 File Reference

### **Staging Files (Current Default):**
```
deployment/
├── clusterissuer.yaml              # Points to staging
├── clusterissuer-staging.yaml      # Explicit staging
├── certificate.yaml                # Points to staging
└── certificate-staging.yaml        # Explicit staging
```

### **Production Files (Available):**
```
# To switch to production, create:
deployment/
├── clusterissuer-prod.yaml         # Copy from clusterissuer-staging.yaml
└── certificate-prod.yaml           # Copy from certificate-staging.yaml

# And update server URLs to production
```

---

## 🧪 Testing Staging Certificates

### **Access Site with Staging Cert:**
1. Open https://shop.emchrismobility.com
2. You'll see: **"Your connection is not private"**
3. Click **"Advanced"** → **"Proceed to shop.emchrismobility.com (unsafe)"**
4. Site loads normally (just with browser warning)

### **Verify Certificate:**
```bash
# Check certificate status
kubectl get certificate -n ecommerce-frontend-ns

# Should show:
# NAME                READY   SECRET
# frontend-tls-cert   True    ecommerce-frontend-tls-secret

# Check certificate details
kubectl describe certificate frontend-tls-cert -n ecommerce-frontend-ns

# Should show no errors
```

---

## 🎯 Best Practices

### **1. Always Use Staging First**
```bash
# Development/Testing
./deploy_frontend.py  # Uses staging by default

# Once everything works...
# Switch to production
# Redeploy
```

### **2. Don't Mix Staging and Production**
If you have staging deployed, switch completely to production:
```bash
# Delete staging deployment
./destroy_frontend.py

# Switch files to production
# Edit deploy_frontend.py, certificate.yaml, clusterissuer.yaml

# Deploy production
./deploy_frontend.py
```

### **3. Track Your Rate Limit**
Check how many certs you've requested:
- Visit: https://crt.sh/?q=shop.emchrismobility.com
- Shows all certificates issued for your domain
- Count recent ones (last 7 days)

### **4. CI/CD Strategy**
```yaml
# .github/workflows/ci-cd.yaml

# For feature branches (use staging)
if: github.ref != 'refs/heads/main'
  run: ./deploy_frontend.py  # Uses staging

# For main branch (use production - after rate limit)
if: github.ref == 'refs/heads/main'
  run: |
    # Override to use production
    sed -i 's/letsencrypt-staging/letsencrypt-prod/g' deployment/certificate.yaml
    ./deploy_frontend.py
```

---

## 📅 Rate Limit Information

### **Your Current Status:**
- **Rate Limit Hit:** Yes (5 certificates issued)
- **Can Request Again:** Feb 15, 2026 at 15:54:21 UTC
- **Time Until Reset:** Check: https://www.timeanddate.com/countdown/

### **Limits:**
- **Production:** 5 certificates per exact domain per week
- **Staging:** Unlimited (no rate limits)

---

## ✅ Quick Reference

### **Currently Using:**
- ✅ Staging certificates (unlimited)
- ✅ Browser will show warning (expected)
- ✅ Works for development/testing

### **To Switch to Production:**
1. ⏰ Wait for rate limit to reset (Feb 15, 2026)
2. 🔧 Update 3 files: deploy_frontend.py, certificate.yaml, clusterissuer.yaml
3. 🗑️ Delete staging deployment: `./destroy_frontend.py`
4. 🚀 Deploy production: `./deploy_frontend.py`

---

## 🆘 Need Help?

**Issue: Staging cert not working**
```bash
kubectl describe certificate frontend-tls-cert -n ecommerce-frontend-ns
kubectl logs -n cert-manager deployment/cert-manager
```

**Issue: Want production but hit rate limit**
```bash
# Wait until Feb 15, 2026 at 15:54:21 UTC
# Check time remaining at: https://www.timeanddate.com/countdown/
```

---

**Remember:** Always use staging for testing, production only when ready for real users! 🚀
