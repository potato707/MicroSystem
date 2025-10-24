# Category Display Fix - "7" Issue Resolved

## Issue
The category was showing as a number (e.g., "7") instead of the category name (e.g., "Account Issues") throughout the client portal.

## Root Cause
The backend serializer (`ClientComplaintSerializer`) returns both:
- `category` - the ID (number like 7)
- `category_name` - the actual name (string like "Account Issues")

But the frontend was displaying `complaint.category` (the ID) instead of `complaint.category_name` (the name).

## Example
**Before Fix:**
```
Priority: MEDIUM | 7  ← showing category ID
```

**After Fix:**
```
Priority: MEDIUM | Account Issues  ← showing category name
```

## Files Fixed

### 1. TypeScript Types (`types/client.ts`)
Updated the `Complaint` interface to include both fields:
```typescript
export interface Complaint {
  id: string;
  title: string;
  description: string;
  category: number;  // Category ID (for form submission)
  category_name: string;  // Category name (for display)
  // ... other fields
}
```

### 2. Complaint Detail Page (`app/client/complaints/[id]/page.tsx`)
Changed from:
```typescript
<span className="text-sm text-gray-500">{complaint.category}</span>
```

To:
```typescript
<span className="text-sm text-gray-500">{complaint.category_name}</span>
```

### 3. Complaints List Page (`app/client/complaints/page.tsx`)
Changed from:
```typescript
<span>Category: {complaint.category}</span>
```

To:
```typescript
<span>Category: {complaint.category_name}</span>
```

### 4. Dashboard Page (`app/client/dashboard/page.tsx`)
Changed from:
```typescript
<p className="mt-1 text-sm text-gray-500">{complaint.category}</p>
```

To:
```typescript
<p className="mt-1 text-sm text-gray-500">{complaint.category_name}</p>
```

## Testing

After restarting the Next.js dev server, you should now see:

✅ **Dashboard**: Category names displayed properly in recent complaints  
✅ **Complaints List**: "Category: Account Issues" instead of "Category: 7"  
✅ **Complaint Detail**: Category name shown next to priority  

## Why Keep Both Fields?

- `category` (number) - Used when submitting new complaints (backend expects category ID)
- `category_name` (string) - Used for displaying the category to users

## Next Steps

1. **Restart Next.js dev server**:
   ```bash
   cd v0-micro-system
   npm run dev
   ```

2. **Test in browser**:
   - Login at http://localhost:3000/client/login
   - View dashboard - categories should show names
   - View complaints list - categories should show names
   - View complaint details - category name should appear instead of "7"

## Summary

✅ Fixed category display in all 3 locations  
✅ Updated TypeScript interface to include category_name  
✅ Category names now display properly throughout the client portal  

**The "7" is now replaced with the actual category name like "Account Issues"!**
