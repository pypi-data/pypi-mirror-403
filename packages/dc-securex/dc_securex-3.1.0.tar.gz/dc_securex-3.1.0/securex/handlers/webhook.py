"""
Webhook protection handler for SecureX SDK.
"""
import discord
import asyncio
from datetime import datetime, timedelta, timezone


class WebhookHandler:
    """Handles webhook protection logic"""
    
    def __init__(self, sdk):
        self.sdk = sdk
        self.bot = sdk.bot
        self.whitelist = sdk.whitelist
    
    async def _is_authorized(self, guild: discord.Guild, user_id: int) -> bool:
        """Check if user is authorized"""
        if guild.owner_id == user_id:
            return True
        if user_id == self.bot.user.id:
            return True
        return await self.whitelist.is_whitelisted(guild.id, user_id)
    
    async def on_webhooks_update(self, channel: discord.TextChannel):
        """Handle webhook creation/deletion/update"""
        try:
            guild = channel.guild
            await asyncio.sleep(0.5)
            
            # Check audit log for webhook actions
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=30)
            
            async for entry in guild.audit_logs(limit=50, oldest_first=False):
                if entry.created_at < cutoff_time:
                    break
                
                # Check for webhook creation
                if entry.action == discord.AuditLogAction.webhook_create:
                    if not await self._is_authorized(guild, entry.user.id):
                        # Unauthorized webhook creation - delete it
                        webhooks = await channel.webhooks()
                        for webhook in webhooks:
                            if webhook.id == entry.target.id:
                                await webhook.delete(reason="SecureX: Unauthorized webhook creation")
                                print(f"🗑️ Deleted unauthorized webhook: {webhook.name} in {channel.name}")
                                
                                # Trigger threat callback
                                from ..models import ThreatEvent
                                threat = ThreatEvent(
                                    guild_id=guild.id,
                                    user_id=entry.user.id,
                                    action_type="webhook_create",
                                    target_id=webhook.id,
                                    target_name=webhook.name,
                                    timestamp=datetime.now(timezone.utc)
                                )
                                await self.sdk._trigger_callbacks('threat_detected', threat)
                                await self.sdk._queue_punishment(threat)
                                break
                    break
                    
        except Exception as e:
            print(f"Error in on_webhooks_update: {e}")
