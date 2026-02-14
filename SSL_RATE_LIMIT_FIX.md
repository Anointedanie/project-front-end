# Let's Encrypt Rate Limit - SSL Certificate Issue

## 🚫 Problem Identified

You've hit the **Let's Encrypt Rate Limit** for `shop.emchrismobility.com`:

```
429 urn:ietf:params:acme:error:rateLimited:
too many certificates (5) already issued for this exact set of identifiers
in the last 168h0m0s
```

**What this means:**
- You've requested **5 certificates** for `shop.emchrismobility.com` in the last 7 days
- Let's Encrypt limits you to **5 certificates per exact domain per week**
- You must wait **until Feb 15, 2026 at 15:54:21 UTC** to request another certificate

---

## ✅ Solutions

### **Option 1: Use Let's Encrypt Staging (Recommended for Testing)** 🔧

For development and testing, use the **staging environment** which has **unlimited rate limits**.

**Step 1: Apply the staging ClusterIssuer**
```bash
kubectl apply -f deployment/clusterissuer-staging.yaml
```

**Step 2: Update your certificate to use staging**
```bash
# Delete the failed certificate
kubectl delete certificate frontend-tls-cert -n ecommerce-frontend-ns

# Apply the staging certificate
kubectl apply -f deployment/certificate-staging.yaml
```

**Step 3: Wait for certificate to be issued (1-2 minutes)**
```bash
kubectl get certificate -n ecommerce-frontend-ns
# Should show READY = True
```

**Note:** Staging certificates will show a browser warning (not trusted), but they work for testing. Once you're ready for production, switch to production issuer.

---

### **Option 2: Wait Until Tomorrow** ⏰

**When:** After **Feb 15, 2026 at 15:54:21 UTC**

**What to do:**
```bash
# Delete the failed certificate
kubectl delete certificate frontend-tls-cert -n ecommerce-frontend-ns

# Reapply the production certificate
kubectl apply -f deployment/certificate.yaml

# Wait for it to be issued
kubectl get certificate -n ecommerce-frontend-ns -w
```

---

### **Option 3: Use a Different Subdomain** 🌐

If you need a valid certificate now, use a different subdomain:

**Example:** Change from `shop.emchrismobility.com` to `frontend.emchrismobility.com`

**Steps:**
1. Update DNS to point new subdomain to your load balancer
2. Update certificate.yaml:
   ```yaml
   dnsNames:
     - frontend.emchrismobility.com  # Different subdomain
   ```
3. Update ingress.yaml:
   ```yaml
   spec:
     rules:
       - host: frontend.emchrismobility.com  # Match certificate
   ```
4. Apply changes:
   ```bash
   kubectl delete certificate frontend-tls-cert -n ecommerce-frontend-ns
   kubectl apply -f deployment/certificate.yaml
   kubectl apply -f deployment/frontend-ingress.yaml
   ```

---

### **Option 4: Use an Existing Valid Certificate** 📜

If you have a certificate that was issued earlier in the week and is still valid (Let's Encrypt certs are valid for 90 days), you can reuse it.

**Check if you have an existing secret:**
```bash
# List secrets in all namespaces
kubectl get secrets --all-namespaces | grep tls

# If you find one, copy it:
kubectl get secret <old-secret-name> -n <old-namespace> -o yaml > old-cert.yaml

# Edit the YAML to change namespace and apply
kubectl apply -f old-cert.yaml
```

---

## 🔄 Quick Fix: Switch to Staging NOW

**For immediate testing, run these commands:**

```bash
# 1. Create staging ClusterIssuer
kubectl apply -f deployment/clusterissuer-staging.yaml

# 2. Delete failed certificate
kubectl delete certificate frontend-tls-cert -n ecommerce-frontend-ns

# 3. Apply staging certificate
kubectl apply -f deployment/certificate-staging.yaml

# 4. Wait for it to be ready (1-2 minutes)
kubectl get certificate -n ecommerce-frontend-ns -w

# 5. Once READY = True, check the site
# You'll see a browser warning (expected for staging certs)
# Click "Advanced" → "Proceed" to test
```

---

## 📊 Understanding Let's Encrypt Rate Limits

### **Production Limits:**
- **5 certificates** per exact domain per week (168 hours)
- **50 certificates** per registered domain per week
- **300 new orders** per account per 3 hours

### **Staging Limits:**
- **Unlimited** requests (for testing)
- Issues **fake certificates** (browsers will warn)
- Perfect for development/testing

### **Rate Limit Reset:**
Your rate limit for `shop.emchrismobility.com` resets on:
**Feb 15, 2026 at 15:54:21 UTC**

---

## 🔐 Best Practices to Avoid Rate Limits

### **1. Use Staging for Development**
Always use staging issuer during development:
```yaml
issuerRef:
  name: letsencrypt-staging  # For testing
  kind: ClusterIssuer
```

Switch to production only when ready to go live:
```yaml
issuerRef:
  name: letsencrypt-prod  # For production
  kind: ClusterIssuer
```

### **2. Don't Delete and Recreate Certificates Frequently**
Each recreation counts against your rate limit. Instead:
- Keep certificates and only update if needed
- Use staging for testing changes
- Only request production certs once everything works

### **3. Use One Certificate for Multiple Subdomains**
Instead of separate certs for each subdomain:
```yaml
dnsNames:
  - shop.emchrismobility.com
  - api.emchrismobility.com
  - admin.emchrismobility.com
```

This counts as **1 certificate** request instead of 3.

### **4. Let cert-manager Auto-Renew**
Don't manually delete and recreate certificates. cert-manager will automatically renew them 30 days before expiry.

---

## 🧪 Testing the Fix

### **After applying staging certificate:**

```bash
# Check certificate status
kubectl get certificate -n ecommerce-frontend-ns

# Should show:
# NAME                READY   SECRET                          AGE
# frontend-tls-cert   True    ecommerce-frontend-tls-secret   2m

# Check certificate details
kubectl describe certificate frontend-tls-cert -n ecommerce-frontend-ns

# Should show no errors in Events section

# Access your site
curl -k https://shop.emchrismobility.com
# -k flag accepts self-signed certs
```

### **Browser Testing:**
1. Open https://shop.emchrismobility.com
2. You'll see: "Your connection is not private" (expected for staging)
3. Click "Advanced" → "Proceed to shop.emchrismobility.com"
4. Your application should load correctly

---

## 📚 Resources

- **Let's Encrypt Rate Limits:** https://letsencrypt.org/docs/rate-limits/
- **cert-manager Troubleshooting:** https://cert-manager.io/docs/troubleshooting/
- **Check Rate Limit Status:** https://crt.sh/?q=shop.emchrismobility.com

---

## 🎯 Recommended Action Plan

**For Right Now (Testing):**
1. ✅ Use staging certificates (unlimited)
2. ✅ Test your application
3. ✅ Fix any issues

**For Tomorrow (Production):**
1. ⏰ Wait until Feb 15, 2026 at 15:54:21 UTC
2. ⏰ Switch to production issuer
3. ⏰ Get trusted SSL certificate

**For Future Deployments:**
1. 🔧 Always use staging for testing
2. 🔧 Only use production when deploying to users
3. 🔧 Don't delete/recreate certificates unnecessarily

---

## ✅ Files Created

I've created two new files for you:

1. **`deployment/clusterissuer-staging.yaml`**
   - Let's Encrypt staging issuer (unlimited rate limits)

2. **`deployment/certificate-staging.yaml`**
   - Certificate using staging issuer

Use these for testing to avoid hitting rate limits!

---

## 🆘 Need Help?

If you're still having issues:

1. **Check cert-manager logs:**
   ```bash
   kubectl logs -n cert-manager deployment/cert-manager --tail=100
   ```

2. **Check certificate order:**
   ```bash
   kubectl get order -n ecommerce-frontend-ns
   kubectl describe order <order-name> -n ecommerce-frontend-ns
   ```

3. **Check challenge:**
   ```bash
   kubectl get challenge -n ecommerce-frontend-ns
   kubectl describe challenge <challenge-name> -n ecommerce-frontend-ns
   ```

---

**TL;DR:** You hit Let's Encrypt rate limit (5 certs/week). Use staging for testing now, or wait until tomorrow for production cert. 🚀
