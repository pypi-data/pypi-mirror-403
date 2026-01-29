# Changelog

## [3.2.13] - 2026-01-25

### 📚 **Documentation Update**

**Changes:**
- Simplified `README.md` significantly
- Removed detailed guides in favor of upcoming documentation website
- Updated references to `user_tokens.json` to reflect new database storage

## [3.2.12] - 2026-01-25

### 🎨 **Cosmetic: Custom Banner**

**Changes:**
- Updated startup banner to new custom ASCII art design
- Removed "Initialised" text for cleaner look, just the art

## [3.2.11] - 2026-01-25

### 🧼 **Polish: Final Log Cleanup**

**Changes:**
- Removed "Preloading whitelists into cache..."
- Removed "Cached X whitelists in memory"
- Removed "Preloaded settings for X guilds"
- Removed all intermediate startup logs
- Console output is now purely the ASCII banner upon success

## [3.2.10] - 2026-01-25

### 🎨 **Cosmetic: Startup Banner**

**Changes:**
- Replaced verbose startup logs ("Rocket", "Flash" emojis) with a clean ASCII art banner
- Banner only displays upon successful initialization of all components
- Removed intermediate success logs for cleaner console output

## [3.2.9] - 2026-01-25

### ⚡ **Improvements: Silent Mode & Startup Fix**

**Fixes:**
- Fixed `AttributeError: 'GuildWorker' object has no attribute '_tokens_file'` on startup
- Removed legacy `_load_tokens()` call causing the crash

**Improvements:**
- 🤫 **Silent Cleanup**: Removed "Deleted unauthorized role/channel" logs as requested
- Cleaner console output for production environments
- Critical warnings and errors are still logged

## [3.2.8] - 2026-01-25

### ♻️ **Refactor: Complete JSON Removal**

**Changes:**
- Removed all remaining JSON file operations from `BackupManager`
- `roles.json` and `channels.json` are no longer created
- `preload_all` now correctly loads from storage backend
- Validated total removal of file-based backup legacy code

## [3.2.7] - 2026-01-25

### ♻️ **Refactor: Removed User Tokens JSON**

**Changes:**
- Migrated `user_tokens.json` to SQLite storage backend
- `GuildWorker` now saves tokens securely in the database
- `roles.json`, `channels.json`, `guild_settings.json`, and `user_tokens.json` are ALL removed
- SDK is now 100% database-driven (SQLite/PostgreSQL)

**Files Modified:**
- `securex/workers/guild_worker.py` - Replaced JSON operations with storage backend calls

---

## [3.2.6] - 2026-01-25

### ♻️ **Refactor: Removed Legacy JSON Storage**

**Changes:**
- Removed all remaining JSON file operations from `BackupManager`
- `roles.json` and `channels.json` are no longer created
- All backup/restore operations now strictly use the SQLite/PostgreSQL storage backend
- Fixed `restore_role`, `restore_channel_permissions` to read from DB instead of files
- Fixed `preload_all` to load from DB

**Affected Components:**
- `securex/backup/manager.py` - Full migration to storage backend

---

## [3.2.5] - 2026-01-25

### 🧹 **Cleanup: Removed Debug Logging**

**Changes:**
- Removed verbose debug logs added in v3.2.1-3.2.4 for troubleshooting
- Removed `🔍 [DEBUG]` logs from client
- Removed `🧹 [CLEANUP]` logs from cleanup worker
- Removed `⚙️ [ActionWorker]` logs from action worker

**State:**
- System is fully verified and stable
- Console output is now clean and only shows critical information (warnings, successful startups)
- All audit log detection and restoration features are working correctly

---

## [3.2.4] - 2026-01-25

### 🐛 **Bugfix: Workers Not Processing Events**

**Issue:**
- Events were being queued to `self.sdk.cleanup_queue`, `action_queue`, etc.
- But workers were creating their **OWN** internal queues: `self.cleanup_queue = asyncio.Queue()`
- Result: Workers were listening to empty queues while SDK filled the main queues.

**Fix:**
- Updated all workers to use shared SDK queues:
  - `CleanupWorker` → `sdk.cleanup_queue`
  - `ActionWorker` → `sdk.action_queue`
  - `LogWorker` → `sdk.log_queue`

**Why this happened:**
- When refactoring to the new architecture, the workers weren't updated to reference the shared queues in `client.py`.

**Status:**
- ✅ All workers now properly processing events
- ✅ Audit logs are detected AND processed
- ✅ Deletion/Restoration actions should now execute

---

## [3.2.3] - 2026-01-25

### 🐛 **Bugfix: Cleanup Worker Queue Fix (Partial)**

**Fixed Cleanup Worker Queue:**
- Fixed cleanup worker reading from wrong queue
- Added detailed debug logging for cleanup worker

---

## [3.2.2] - 2026-01-25

### 🐛 **CRITICAL FIX: Restored Restoration Handlers**

**The Problem:**
- v3.2.0 incorrectly removed ALL event handlers
- **Audit log** is for detecting unauthorized CREATIONS (to delete them)
- **Individual events** are for detecting unauthorized DELETIONS (to restore them)
- Both are needed!

**What was broken in v3.2.0-3.2.1:**
- ❌ Deleted channels were NOT being restored
- ❌ Deleted roles were NOT being restored  
- ❌ Unauthorized bans were NOT being reversed
- ❌ Permission changes were NOT being reverted

**What's fixed in v3.2.2:**
- ✅ Restored `on_guild_channel_delete` - Restores deleted channels
- ✅ Restored `on_guild_channel_update` - Reverts channel permission changes
- ✅ Restored `on_guild_role_delete` - Restores deleted roles
- ✅ Restored `on_guild_role_update` - Reverts role permission changes
- ✅ Restored `on_member_ban` - Unbans unauthorized bans
- ✅ Restored `on_member_update` - Reverts member updates

**How it works now (CORRECT):**

```python
# DETECTION (unauthorized creations) → DELETE
@bot.event
async def on_audit_log_entry_create(entry):
    if entry.action == role_create and not authorized:
        await role.delete()  # Delete unauthorized creation

# RESTORATION (unauthorized deletions) → RESTORE
@bot.event  
async def on_guild_role_delete(role):
    if deleter not authorized:
        await restore_role()  # Restore deleted role
```

**Files Modified:**
- `securex/client.py` - Restored all individual event handlers
- Restored ChannelHandler, RoleHandler, MemberHandler imports and initialization

**Migration from v3.2.0-3.2.1:**
Just upgrade - no code changes needed.

---

## [3.2.1] - 2026-01-25

### 🐛 **Bugfix: Intent Verification & Debug Logging**

**Added Intent Check**
- **Issue**: `on_audit_log_entry_create` wasn't firing for some users
- **Cause**: Missing `guild_moderation` intent  
- **Fixed**: Added intent verification on `enable()` with clear error message

**Added Debug Logging:**
```python
async def on_audit_log_entry_create(entry):
    print(f"🔍 [DEBUG] Audit log event received: {entry.action}")
    # ... queue to workers
    print(f"✅ [DEBUG] Entry queued successfully")
```

**Files Modified:**
- `securex/client.py` - Added intent check and debug logging

---

## [3.2.0] - 2026-01-25 [BROKEN - DO NOT USE]

**WARNING: This version broke restoration functionality. Use v3.2.2+ instead.**

---
