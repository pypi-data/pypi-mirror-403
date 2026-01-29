"""
Guild Restoration Worker - Restores server name and vanity URL only
Triggered by GuildHandler when unauthorized changes are detected
Supports per-guild user tokens with file storage and memory caching
"""
import asyncio
import discord
import aiohttp
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class GuildWorker:
    """Background worker for guild settings restoration"""
    
    def __init__(self, sdk):
        self.sdk = sdk
        self.bot = sdk.bot
        self._worker_task = None
        
        # Per-guild user tokens
        self._user_tokens: Dict[int, str] = {}  # guild_id -> user_token (cache)
        self._tokens_file = sdk.backup_dir / "user_tokens.json"
    
    async def _load_tokens(self):
        """Load user tokens from file into cache"""
        try:
            if self._tokens_file.exists():
                with open(self._tokens_file, 'r') as f:
                    data = json.load(f)
                    # Convert string keys back to int
                    self._user_tokens = {int(k): v for k, v in data.items()}
                    print(f"✅ Loaded user tokens for {len(self._user_tokens)} guild(s)")
        except Exception as e:
            print(f"Error loading user tokens: {e}")
    
    async def _save_tokens(self):
        """Save user tokens to file"""
        try:
            # Convert int keys to string for JSON
            data = {str(k): v for k, v in self._user_tokens.items()}
            with open(self._tokens_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving user tokens: {e}")
    
    async def set_user_token(self, guild_id: int, token: str):
        """Set user token for a specific guild"""
        self._user_tokens[guild_id] = token
        await self._save_tokens()
        print(f"✅ User token set for guild {guild_id}")
    
    def get_user_token(self, guild_id: int) -> Optional[str]:
        """Get user token for a guild (from cache)"""
        return self._user_tokens.get(guild_id)
    
    async def remove_user_token(self, guild_id: int):
        """Remove user token for a guild"""
        if guild_id in self._user_tokens:
            del self._user_tokens[guild_id]
            await self._save_tokens()
            print(f"❌ User token removed for guild {guild_id}")
    
    async def start(self):
        """Start the guild restoration worker"""
        # Load tokens first
        await self._load_tokens()
        
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._restoration_loop())
            print("⚡ Guild Restoration Worker started")
    
    async def stop(self):
        """Stop the worker"""
        if self._worker_task:
            self._worker_task.cancel()
            self._worker_task = None
    
    async def _restoration_loop(self):
        """Main worker loop - processes guild_update entries from queue"""
        while True:
            try:
                entry = await self.sdk.guild_queue.get()
                
                # Only process guild_update actions
                if entry.action != discord.AuditLogAction.guild_update:
                    continue
                
                # Extract changes from entry
                guild = entry.guild
                executor = entry.user
                
                # Skip if bot did it
                if executor.id == self.bot.user.id:
                    continue
                
                # Check authorization
                if executor.id == guild.owner_id:
                    continue
                
                whitelist_set = self.sdk.whitelist_cache.get(guild.id, set())
                if executor.id in whitelist_set:
                    continue
                
                # Unauthorized change - restore from backup
                print(f"🔍 Unauthorized guild update by {executor.name}")
                await self._restore_guild_settings(guild)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in guild restoration worker: {e}")
    
    async def _restore_vanity_via_api(self, guild_id: int, vanity_code: str) -> bool:
        """Restore vanity URL using user token and Discord API"""
        user_token = self.get_user_token(guild_id)
        
        if not user_token:
            print(f"⚠️ No user token set for guild {guild_id}! Cannot restore vanity URL.")
            print(f"   Use: await sx.guild_worker.set_user_token({guild_id}, 'USER_TOKEN')")
            return False
        
        try:
            url = f"https://discord.com/api/v9/guilds/{guild_id}/vanity-url"
            headers = {
                "authorization": user_token,
                "content-type": "application/json"
            }
            payload = {"code": vanity_code}
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        return True
                    else:
                        error_text = await response.text()
                        print(f"⚠️ Failed to restore vanity: {response.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"Error restoring vanity via API: {e}")
            return False
    
    async def _restore_guild_settings(self, guild):
        """Restore guild settings (name and vanity) from backup"""
        try:
            print(f"🔧 [DEBUG] Starting restoration for guild: {guild.name}")
            start_time = datetime.now()
            
            backup_data = await self.sdk.backup_manager.get_guild_settings(guild.id)
            print(f"📦 [DEBUG] Backup data retrieved: {backup_data}")
            if not backup_data:
                print(f"⚠️ No backup found for guild {guild.name}")
                return
            
            restore_params = {}
            restored_items = []
            
            # Restore vanity URL if we have it in backup
            if backup_data.get("vanity_url_code"):
                old_vanity = backup_data["vanity_url_code"]
                vanity_success = await self._restore_vanity_via_api(guild.id, old_vanity)
                if vanity_success:
                    restored_items.append(f"vanity (discord.gg/{old_vanity})")
            
            # Restore server name if different from backup
            if backup_data.get("name") and backup_data["name"] != guild.name:
                restore_params["name"] = backup_data["name"]
                restored_items.append(f"name ({backup_data['name']})")
            
            if restore_params:
                await guild.edit(**restore_params, reason="SecureX: Restoring unauthorized guild changes")
            
            if restored_items:
                elapsed = (datetime.now() - start_time).total_seconds() * 1000
                items_str = ", ".join(restored_items)
                print(f"⚡ Restored guild settings in {elapsed:.0f}ms: {items_str}")
            
        except discord.errors.HTTPException as e:
            if e.code == 50035:
                print(f"⚠️ Some settings could not be restored: {e}")
            else:
                print(f"Error restoring guild settings: {e}")
        except Exception as e:
            import traceback
            print(f"❌ Error in guild restoration: {e}")
            print(f"Traceback: {traceback.format_exc()}")
