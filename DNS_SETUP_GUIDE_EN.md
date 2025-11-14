# DNS Setup Guide for Custom Domain 🌐

## Quick Overview
This guide explains how your clients can connect their custom domain (e.g., `adamcompany.com`) to your SaaS platform.

---

## Step-by-Step Instructions 📋

### Step 1: Login to Your Domain Provider

Go to where you purchased your domain:
- **GoDaddy**: https://www.godaddy.com
- **Namecheap**: https://www.namecheap.com
- **Google Domains**: https://domains.google.com
- **Cloudflare**: https://www.cloudflare.com

---

### Step 2: Access DNS Settings

#### GoDaddy:
```
1. Login → My Products
2. Click "DNS" next to your domain
3. DNS Management page opens
```

#### Namecheap:
```
1. Login → Domain List
2. Click "Manage" next to your domain
3. Click "Advanced DNS" tab
```

#### Cloudflare:
```
1. Login → Select Domain
2. Click "DNS" from menu
3. DNS Records page opens
```

---

### Step 3: Add CNAME Record

#### CNAME Settings:
```
┌─────────────┬─────────────────┬──────────────────────┐
│ Field       │ Value           │ Example              │
├─────────────┼─────────────────┼──────────────────────┤
│ Type        │ CNAME           │ CNAME                │
│ Name/Host   │ @ or blank      │ @ (or leave blank)   │
│ Value/Target│ yourdomain.com  │ saas.myserver.com    │
│ TTL         │ Automatic       │ 3600 (or Auto)       │
└─────────────┴─────────────────┴──────────────────────┘
```

#### Field Explanation:
- **Type**: Record type = `CNAME`
- **Name**: Leave blank or use `@` (means root domain)
- **Value**: Your main server domain
- **TTL**: Leave as Automatic (or 3600 seconds)

---

### Step 4: Add WWW Subdomain (Optional)

To make `www.adamcompany.com` work too:

```
┌─────────────┬─────────────────┬──────────────────────┐
│ Field       │ Value           │ Example              │
├─────────────┼─────────────────┼──────────────────────┤
│ Type        │ CNAME           │ CNAME                │
│ Name/Host   │ www             │ www                  │
│ Value/Target│ adamcompany.com │ adamcompany.com      │
│ TTL         │ Automatic       │ 3600 (or Auto)       │
└─────────────┴─────────────────┴──────────────────────┘
```

---

## Alternative: Use A Record Instead of CNAME

If your domain provider **doesn't support CNAME for root**:

```
┌─────────────┬─────────────────┬──────────────────────┐
│ Field       │ Value           │ Example              │
├─────────────┼─────────────────┼──────────────────────┤
│ Type        │ A               │ A                    │
│ Name/Host   │ @ or blank      │ @ (or leave blank)   │
│ Value       │ Server IP       │ 123.45.67.89         │
│ TTL         │ Automatic       │ 3600 (or Auto)       │
└─────────────┴─────────────────┴──────────────────────┘
```

**Note**: Use your actual server IP address!

---

## Step 5: Save Changes

1. Click **Save** or **Add Record**
2. Wait 5-30 minutes for DNS propagation

---

## How to Verify DNS is Working? ✅

### Method 1: Terminal/CMD

```bash
# On Linux/Mac/Windows
nslookup adamcompany.com

# Expected Output:
# Server:  8.8.8.8
# Address: 8.8.8.8#53
# 
# Non-authoritative answer:
# Name:    adamcompany.com
# Address: 123.45.67.89  ← Your server IP
```

### Method 2: Online DNS Checker

Visit: https://dnschecker.org

```
1. Enter domain: adamcompany.com
2. Select Record Type: A or CNAME
3. Click Search
4. Check status across different countries
5. If most show ✅ = DNS is working
```

### Method 3: Direct Browser Test

```bash
# Open in browser
http://adamcompany.com

# If you see:
# - Your system = ✅ DNS working
# - "Site not found" = ❌ DNS not ready
# - SSL error = ✅ DNS working, need SSL setup
```

---

## Real Examples 📸

### Example 1: GoDaddy

```
┌─────────────────────────────────────────────────────┐
│  GoDaddy DNS Management                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Add] [Edit] [Delete]                             │
│                                                     │
│  Type    Name    Value              TTL            │
│  ─────   ────    ─────              ───            │
│  CNAME   @       saas.myserver.com  1 Hour         │
│  CNAME   www     adamcompany.com    1 Hour         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Example 2: Namecheap

```
┌─────────────────────────────────────────────────────┐
│  Namecheap Advanced DNS                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Host Records (A + AAAA + CNAME + NS + TXT...)     │
│                                                     │
│  [Add New Record]                                  │
│                                                     │
│  Type: [CNAME ▼]                                   │
│  Host: [@      ]                                   │
│  Value: [saas.myserver.com]                        │
│  TTL:  [Automatic ▼]                               │
│                                                     │
│  [✓ Save All Changes]                              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Example 3: Cloudflare

```
┌─────────────────────────────────────────────────────┐
│  Cloudflare DNS Records                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [+ Add record]                                    │
│                                                     │
│  Type         Name   Content           Proxy  TTL  │
│  ──────────   ────   ───────           ─────  ───  │
│  CNAME        @      saas.myserver.com  🟧    Auto │
│  CNAME        www    adamcompany.com    🟧    Auto │
│                                                     │
│  🟧 = Proxied (Orange Cloud)                       │
│  ⚪ = DNS only (Grey Cloud)                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Important for Cloudflare**:  
Keep Proxy **enabled** (🟧 Orange Cloud) for protection.

---

## Timeline ⏱️

```
┌──────────────────┬──────────────────────────────┐
│ Time             │ Status                       │
├──────────────────┼──────────────────────────────┤
│ 0-5 minutes      │ Changes uploading            │
│ 5-15 minutes     │ DNS propagating              │
│ 15-30 minutes    │ DNS working in most regions  │
│ 30-60 minutes    │ DNS fully propagated         │
│ 1-24 hours       │ Rare cases (old DNS cache)   │
└──────────────────┴──────────────────────────────┘
```

**Tip**: Use short TTL (300-3600 seconds) for faster propagation.

---

## Common Issues & Solutions 🔧

### Issue 1: DNS Not Propagated Yet
```
Symptoms:
- Website doesn't open
- nslookup returns no IP

Solution:
✅ Wait 15-30 minutes
✅ Clear DNS cache:
   # Windows
   ipconfig /flushdns
   
   # Mac
   sudo dscacheutil -flushcache
   
   # Linux
   sudo systemd-resolve --flush-caches
```

### Issue 2: Wrong DNS Configuration
```
Symptoms:
- nslookup returns wrong IP
- Website opens different site

Solution:
✅ Check Value in CNAME record
✅ Ensure Name = @ (not www)
✅ Ensure Type = CNAME (not A)
```

### Issue 3: WWW Not Working
```
Symptoms:
- adamcompany.com works ✅
- www.adamcompany.com doesn't work ❌

Solution:
✅ Add CNAME record for www:
   Type: CNAME
   Name: www
   Value: adamcompany.com
```

### Issue 4: SSL Certificate Error
```
Symptoms:
- Website opens with http:// ✅
- Website doesn't open with https:// ❌
- Error "Your connection is not private"

Solution:
✅ DNS is correct! Just need SSL
✅ See CUSTOM_DOMAIN_SETUP.md
✅ Use certbot for free SSL
```

---

## Client Email Template 📧

Send this email to your client:

```
Subject: Custom Domain Setup Instructions

Hello,

Congratulations! Your account has been successfully created 🎉

To use your custom domain (adamcompany.com), we need to 
configure DNS settings.

📋 Required Steps:

1. Login to your domain provider (GoDaddy/Namecheap/etc.)
2. Go to DNS Settings
3. Add CNAME Record:
   - Type: CNAME
   - Name: @ (or leave blank)
   - Value: saas.myserver.com
   - TTL: Automatic

4. Save changes
5. Wait 15-30 minutes

✅ Then you can access the system at:
   https://adamcompany.com

🔑 Login Credentials:
   Username: adamadmin
   Password: [sent in separate email]

📞 Need help? Contact us:
   Email: support@yourcompany.com
   Phone: +1 234 567 8900

Best regards,
Support Team
```

---

## Client Checklist ✅

Print and send this checklist:

```
□ Logged into domain provider
□ Opened DNS Management page
□ Added CNAME record for @ (root)
□ Added CNAME record for www (optional)
□ Saved changes
□ Waited 15-30 minutes
□ Tested domain with nslookup
□ Tested website in browser
□ Verified https:// works (after SSL setup)
```

---

## Tutorial Videos 📹

### GoDaddy DNS Setup:
https://www.youtube.com/results?search_query=godaddy+dns+cname+setup

### Namecheap DNS Setup:
https://www.youtube.com/results?search_query=namecheap+dns+cname+setup

### Cloudflare DNS Setup:
https://www.youtube.com/results?search_query=cloudflare+dns+setup

---

## Quick Summary 🎯

```
1. Login to Domain Provider
   ↓
2. Open DNS Settings
   ↓
3. Add CNAME Record:
   Type: CNAME
   Name: @
   Value: saas.myserver.com
   ↓
4. Save Changes
   ↓
5. Wait 15-30 minutes
   ↓
6. Test with nslookup
   ↓
7. Open in Browser
   ↓
8. ✅ Done!
```

---

## Support 📞

If the client faces any issues:

- **Email**: support@yourcompany.com
- **Phone**: +1 234 567 8900
- **Hours**: Mon-Fri, 9 AM - 6 PM

---

**Final Note**: This guide is for the client. For SSL and Nginx setup on your server, see `CUSTOM_DOMAIN_SETUP.md` 🚀
