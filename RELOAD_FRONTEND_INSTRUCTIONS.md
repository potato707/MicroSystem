# Frontend Reload Required

## Issue
The custom status management section is not appearing for users with complaint admin permissions because the frontend needs to be reloaded/rebuilt to apply the recent code changes.

## What Changed
Updated `v0-micro-system/components/complaints/complaints-dashboard.tsx`:
- Changed condition from `userRole === 'admin'` 
- To: `userRole === 'admin' || complaintAdminPermissions?.can_manage_categories`

## Required Actions

### Option 1: Hard Refresh Browser (Quick Fix)
1. Open the browser with the complaints page
2. Press **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (Mac)
3. This will clear the cache and reload the page

### Option 2: Restart Next.js Development Server (Recommended)
```bash
cd /home/ahmedyasser/lab/MicroSystem/v0-micro-system

# Stop the current dev server (Ctrl+C if running)

# Start it again
npm run dev
```

### Option 3: Clear Browser Cache Completely
1. Open browser DevTools (F12)
2. Go to Network tab
3. Check "Disable cache"
4. Reload the page (F5)

## What Should Appear

After reloading, users with `can_manage_categories` permission should see:

```
┌─────────────────────────────────────────────────────┐
│ Custom Status Management          [Add Custom Status]│
├─────────────────────────────────────────────────────┤
│ ● Hello                            [Edit] [Delete]   │
│ ● Responded                        [Edit] [Delete]   │
│ ● Waiting for Client Responses    [Edit] [Delete]   │
│ ● Escalated                        [Edit] [Delete]   │
│ ● Partially Resolved               [Edit] [Delete]   │
└─────────────────────────────────────────────────────┘
```

This card should appear **at the very top** of the complaints dashboard page, just like it does for admins.

## Verification Steps

1. Log in with account that has complaint admin permissions
2. Navigate to complaints dashboard
3. Look at the top of the page (above the stats cards)
4. You should see "Custom Status Management" card
5. Click "Add Custom Status" button to test functionality

## If Still Not Appearing

Check the following:

### 1. Verify Permission is Granted
```bash
curl 'http://localhost:8000/hr/complaint-admin-permissions/user/' \
  -H 'Authorization: Bearer YOUR_TOKEN' | python3 -m json.tool
```

Should show:
```json
{
  "has_permission": true,
  "can_manage_categories": true,  // ← This must be true
  "can_assign": true,
  "can_change_status": true,
  "can_delete": false
}
```

### 2. Check Browser Console for Errors
1. Open DevTools (F12)
2. Go to Console tab
3. Look for any red errors
4. Share screenshot if errors appear

### 3. Verify TypeScript Compilation
```bash
cd /home/ahmedyasser/lab/MicroSystem/v0-micro-system
npx tsc --noEmit
```

Should complete with no errors.

## Technical Details

**File Modified:** `v0-micro-system/components/complaints/complaints-dashboard.tsx`

**Before:**
```typescript
{userRole === 'admin' && (
  <StatusManagement userRole={userRole} />
)}
```

**After:**
```typescript
{(userRole === 'admin' || complaintAdminPermissions?.can_manage_categories) && (
  <StatusManagement userRole={userRole} />
)}
```

The change is live in the code, but Next.js needs to:
1. Detect the file change
2. Rebuild the component
3. Send the updated JavaScript to the browser
4. Browser needs to clear old cached version

This is why a hard refresh or dev server restart is required.
