# AI Usage Limit Feature - Implementation Summary

## Overview
Fitur limit penggunaan AI per hari untuk mengontrol biaya dan usage API. Admin Meta dapat mengatur limit per user, dan Admin RS dapat melihat sisa limit mereka.

## Database Changes

### Migration File: `001_add_ai_usage_limit.sql`

**New Columns in `users` table:**
- `daily_ai_limit` (INTEGER, default: 100) - Maximum requests per day
- `ai_usage_count` (INTEGER, default: 0) - Current day usage count
- `ai_usage_date` (DATE) - Date of current count (auto-resets daily)

**New Table: `ai_usage_history`**
- Tracks historical usage per user per day
- Columns: user_id, usage_date, request_count, last_request_at

## Backend Changes

### 1. Auth Service (`authService.ts`)
**New Methods:**
- `checkAIUsageLimit(userId)` - Check limit WITHOUT incrementing
  - Auto-resets count if date changed
  - Returns: `{ allowed, remaining, limit, current }`
  - Used BEFORE calling core_engine

- `incrementAIUsage(userId)` - Increment count AFTER successful analysis
  - Updates `users.ai_usage_count + 1`
  - Updates `ai_usage_history` table
  - Returns: `{ used, remaining, limit }`
  - Called ONLY when core_engine returns success

- `checkAndIncrementAIUsage(userId)` - Legacy method (deprecated)
  - Kept for backward compatibility
  - Not recommended for new code

- `getAIUsageStatus(userId)` - Get current usage without changing anything
  - Returns: `{ used, remaining, limit }`
  - Used for GET /api/ai/usage endpoint

**Updated Methods:**
- `register()` - Now accepts `daily_ai_limit` parameter (default: 100)

### 2. Admin Service (`adminService.ts`)
**New Methods:**
- `updateDailyAILimit(user_id, daily_ai_limit)` - Update user's limit

**Updated Methods:**
- `createAdminRS()` - Now accepts `daily_ai_limit` parameter

### 3. API Routes

#### AI Routes (`aiRoutes.ts`)
**POST `/api/ai/analyze`** - Enhanced with 2-step limit checking
```typescript
Flow:
1. checkAIUsageLimit() → Check if user has quota
2. If NO quota → Return 429 (exit early, save resources)
3. If has quota → Call core_engine API
4. If analysis SUCCESS:
   - incrementAIUsage() → DB update
   - Return result + usage info
5. If analysis FAILS:
   - Count NOT incremented
   - User keeps their quota
```

**Response Format:**
```json
{
  "success": true,
  "data": { /* analysis result */ },
  "usage": {
    "used": 15,
    "remaining": 85,
    "limit": 100
  }
}
```

**GET `/api/ai/usage`** - New endpoint
- Returns current usage status for logged-in user
- Response: `{ used, remaining, limit }`

#### Admin Routes (`adminRoutes.ts`)
**PATCH `/api/admin/users/:id/ai-limit`** - New endpoint
- Update user's daily AI limit
- Body: `{ daily_ai_limit: number }`

**POST `/api/admin/admin-rs`** - Enhanced
- Now accepts `daily_ai_limit` in request body
- Default: 100 if not provided

**GET `/api/admin/admin-rs`** - Enhanced
- Now returns AI usage fields: `daily_ai_limit`, `ai_usage_count`, `ai_usage_date`

## Frontend Changes

### 1. Admin RS Dashboard (`AdminRSDashboard.tsx`)

**New State:**
- `aiUsage: { used, remaining, limit }` - Current usage status

**New Features:**
- **Usage Indicator Card** - Shows daily usage progress bar
  - Green: >30% remaining
  - Yellow: 10-30% remaining
  - Red: <10% or 0 remaining
- **Real-time updates** - Updates immediately after analysis from response
- Shows alert when limit exceeded (429 error)

**Update Flow:**
```typescript
1. Initial load: loadAIUsage() → GET /api/ai/usage
2. User clicks Generate
3. Response received with usage data
4. setAiUsage(response.usage) → UI updates instantly
5. No extra API call needed!
```

**UI Elements:**
```tsx
<div>AI Usage Today: {remaining}/{limit}</div>
<ProgressBar percentage={(used/limit)*100} />
<p>{remaining} requests remaining</p>
```

### 2. User Management Component (`UserManagement.tsx`) - NEW

**Features:**
- Table view of all Admin RS users
- Shows for each user:
  - Name & Email
  - Active status
  - Daily AI limit
  - Today's usage (count & progress bar)
- **Edit Limit** - Inline editing
  - Click edit icon → input field appears
  - Enter new limit → click save
  - Calls PATCH `/api/admin/users/:id/ai-limit`

**Usage Visualization:**
- Color-coded progress bars
- Red: ≥90% used
- Yellow: ≥70% used
- Green: <70% used

### 3. Admin Meta Dashboard (`AdminMetaDashboard.tsx`)

**New Tab:** "AI Limit Management"
- Renders `<UserManagement />` component

**Create Form Enhanced:**
- New field: "Daily AI Limit" (default: 100)
- Helper text: "Maximum AI analysis requests per day"

## API Flow Examples

### Example 1: Admin RS Makes Analysis Request (UPDATED FLOW)

```
1. User clicks "Generate AI Insight"
2. Frontend → POST /api/ai/analyze
3. Backend:
   a. checkAIUsageLimit(userId) → Check if under limit (NO INCREMENT YET)
   b. If count >= limit → Return 429 immediately
   c. If allowed → Call core_engine API
   d. If core_engine SUCCESS:
      - incrementAIUsage(userId) → Update DB: ai_usage_count + 1
      - Update ai_usage_history table
      - Return response WITH usage data
   e. If core_engine FAILS:
      - Count NOT incremented (user doesn't lose quota)
      - Return error
4. Frontend receives response:
   - Extract usage from response.usage
   - Update UI state: setAiUsage({ used, remaining, limit })
   - Progress bar updates instantly
5. User sees updated count immediately
```

**Key Changes:**
- ✅ Count incremented ONLY after successful analysis
- ✅ Failed requests don't consume quota
- ✅ Frontend updates from response (no extra API call needed)
- ✅ Real-time UI update

### Example 2: Admin Meta Updates Limit

```
1. Admin Meta clicks edit icon for user
2. Enters new limit (e.g., 200)
3. Clicks save
4. Frontend → PATCH /api/admin/users/{id}/ai-limit
   Body: { daily_ai_limit: 200 }
5. Backend updates database
6. Frontend refreshes user list
```

### Example 3: Daily Reset

```
Automatic (handled in checkAndIncrementAIUsage):
1. User makes request on new day
2. Backend checks: ai_usage_date != today
3. If different:
   - Set ai_usage_count = 0
   - Set ai_usage_date = today
4. Proceed with request
```

## Error Handling

### 429 Too Many Requests
```json
{
  "success": false,
  "message": "Daily AI usage limit exceeded",
  "data": {
    "remaining": 0,
    "limit": 100
  }
}
```

**Frontend Response:**
```
Alert: "Limit penggunaan AI harian Anda sudah habis!
Silakan coba lagi besok atau hubungi admin untuk menambah limit."
```

## Testing Checklist

### Backend
- [ ] Create user with custom limit (e.g., 50)
- [ ] Make 50 requests → 51st should fail with 429
- [ ] Check next day → count should reset to 0
- [ ] Update limit via admin endpoint → verify increased
- [ ] Check ai_usage_history table → verify records

### Frontend - Admin RS
- [ ] Login → verify usage indicator shows
- [ ] Make analysis → verify count increments
- [ ] Reach limit → verify error message
- [ ] Check progress bar colors (green/yellow/red)

### Frontend - Admin Meta
- [ ] Open "AI Limit Management" tab
- [ ] Verify all users listed with usage stats
- [ ] Edit a user's limit → verify saved
- [ ] Create new user with custom limit → verify default 100

## Configuration

### Default Limit
Change in:
1. Migration SQL: `daily_ai_limit INTEGER DEFAULT 100`
2. authService.ts: `daily_ai_limit = 100`
3. adminService.ts: `daily_ai_limit = 100`
4. Frontend form: `daily_ai_limit: 100`

### Disable Limit
Set very high value (e.g., 999999) for specific users.

## Database Queries

### Check User's Current Usage
```sql
SELECT daily_ai_limit, ai_usage_count, ai_usage_date 
FROM users 
WHERE id = ?;
```

### Get Usage History
```sql
SELECT * FROM ai_usage_history 
WHERE user_id = ? 
ORDER BY usage_date DESC 
LIMIT 30;
```

### Reset All Counts (manual)
```sql
UPDATE users 
SET ai_usage_count = 0, ai_usage_date = CURRENT_DATE;
```

## Future Enhancements

1. **Analytics Dashboard**
   - Daily/weekly/monthly usage trends
   - Top users by usage
   - Average usage per user

2. **Alerts**
   - Email when user reaches 80% limit
   - Admin notification for high usage

3. **Tiered Limits**
   - Basic: 50/day
   - Pro: 200/day
   - Enterprise: Unlimited

4. **Usage Reports**
   - Export CSV of usage history
   - Billing integration

## Notes

- Limit check happens BEFORE calling core_engine (saves costs)
- History table allows audit & analytics
- Auto-reset ensures no manual intervention needed
- Progress bars provide clear visual feedback
- Inline editing in management UI improves UX
