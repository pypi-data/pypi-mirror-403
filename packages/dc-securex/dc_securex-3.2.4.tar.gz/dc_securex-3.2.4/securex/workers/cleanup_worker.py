"""
Cleanup Worker - Deletes unauthorized creations instantly
"""
import discord
import asyncio


class CleanupWorker:
    """Worker that deletes unauthorized creations (channels, roles, webhooks)"""
    
    def __init__(self, sdk):
        self.sdk = sdk
        self.bot = sdk.bot
        self.cleanup_queue = sdk.cleanup_queue  # Use SDK's shared queue
        self._worker_task = None
     
    
    async def start(self):
        """Start the cleanup worker"""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker_loop())
            print("🧹 Cleanup Worker started")
    
    async def stop(self):
        """Stop the worker"""
        if self._worker_task:
            self._worker_task.cancel()
            self._worker_task = None
    
    async def _worker_loop(self):
        """Main worker loop"""
        while True:
            try:
                entry = await self.cleanup_queue.get()
                await self._process_entry(entry)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup worker: {e}")
    
    async def _process_entry(self, entry):
        """Process deletion of unauthorized creations"""
        print(f"🧹 [CLEANUP] Processing entry: {entry.action}")
        try:
            guild = entry.guild
            executor = entry.user
            
            print(f"   Executor: {executor.name} (ID: {executor.id})")
            print(f"   Bot ID: {self.bot.user.id}")
            print(f"   Owner ID: {guild.owner_id}")
            
            # Skip if bot
            if executor.id == self.bot.user.id:
                print(f"   ⏭️  Skipping - executor is bot")
                return
            
            # Skip if owner
            if executor.id == guild.owner_id:
                print(f"   ⏭️  Skipping - executor is owner")
                return
            
            # Check whitelist
            is_whitelisted = await self.sdk.whitelist.is_whitelisted(guild.id, executor.id)
            print(f"   Whitelisted: {is_whitelisted}")
            if is_whitelisted:
                print(f"   ⏭️  Skipping - executor is whitelisted")
                return
            
            # Only handle creation actions
            if entry.action not in [
                discord.AuditLogAction.channel_create,
                discord.AuditLogAction.role_create,
                discord.AuditLogAction.webhook_create
            ]:
                print(f"   ⏭️  Skipping - action type not handled: {entry.action}")
                return

            print(f"   ⚠️  UNAUTHORIZED ACTION DETECTED!")
            try:
                target = entry.target
                if not target:
                    print(f"   ❌ No target found")
                    return

                if entry.action == discord.AuditLogAction.role_create:
                    role = guild.get_role(target.id)
                    if role:
                        await role.delete(reason="SecureX: Unauthorized role creation")
                        print(f"🗑️  DELETED unauthorized role: {role.name}")
                    else:
                        print(f"   ⚠️  Role already deleted")
                
                elif entry.action == discord.AuditLogAction.channel_create:
                    channel = guild.get_channel(target.id)
                    if channel:
                        await channel.delete(reason="SecureX: Unauthorized channel creation")
                        print(f"🗑️  DELETED unauthorized channel: {channel.name}")
                    else:
                        print(f"   ⚠️  Channel already deleted")
                
                elif entry.action == discord.AuditLogAction.webhook_create:
                    webhooks = await guild.webhooks()
                    for webhook in webhooks:
                        if webhook.id == target.id:
                            await webhook.delete(reason="SecureX: Unauthorized webhook creation")
                            print(f"🗑️  DELETED unauthorized webhook: {webhook.name}")
                            break

            except (discord.Forbidden, discord.NotFound) as e:
                print(f"   ❌ Permission error: {e}")
            except Exception as e:
                print(f"   ❌ Cleanup error: {e}")

        except Exception as e:
            print(f"❌ Error processing cleanup entry: {e}")
