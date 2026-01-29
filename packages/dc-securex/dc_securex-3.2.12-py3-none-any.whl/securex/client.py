"""
SecureX SDK - Main Client
Backend-only anti-nuke protection system
"""
import discord
import asyncio
from pathlib import Path
from typing import Dict, List, Callable, Optional
from .backup.manager import BackupManager
from .handlers.channel import ChannelHandler
from .handlers.role import RoleHandler
from .handlers.member import MemberHandler
from .utils.whitelist import WhitelistManager
from .utils.punishment import PunishmentExecutor
from .models import ThreatEvent, BackupInfo
from .workers import ActionWorker, CleanupWorker, LogWorker, GuildWorker
from .storage import create_storage_backend


class SecureX:
    """
    Main SecureX SDK class for anti-nuke protection.
    Backend-only - no UI, no commands, just pure protection logic.
    """
    
    def __init__(
        self,
        bot: discord.Client,
        backup_dir: str = "./data/backups",
        storage_backend: str = "sqlite",
        postgres_url: Optional[str] = None,
        postgres_pool_size: int = 10,
        punishments: Optional[Dict[str, str]] = None,
        timeout_duration: int = 600,
        notify_user: bool = True
    ):
        """
        Initialize SecureX SDK.
        
        Args:
            bot: Your discord.Client or commands.Bot instance
            backup_dir: Directory to store backups (default: ./data/backups)
            storage_backend: "sqlite" or "postgres" (default: "sqlite")
            postgres_url: PostgreSQL connection URL (required if storage_backend="postgres")
            postgres_pool_size: Connection pool size for PostgreSQL (default: 10)
            punishments: Dict mapping violation types to punishment actions
            timeout_duration: Duration in seconds for timeout punishment (default: 600)
            notify_user: Whether to DM violators about punishment (default: True)
        """
        self.bot = bot
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.storage_backend_type = storage_backend
        
        # Create storage backend (connection pool initialized later in enable())
        if storage_backend == "postgres":
            if not postgres_url:
                raise ValueError("postgres_url required when storage_backend='postgres'")
            self.storage = create_storage_backend(
                "postgres",
                url=postgres_url,
                pool_size=postgres_pool_size
            )
        else:
            self.storage = create_storage_backend(
                "sqlite",
                db_path=str(self.backup_dir / "securex.db")
            )
        
        # Managers now use storage abstraction
        self.backup_manager = BackupManager(self, self.storage)
        self.whitelist = WhitelistManager(self, self.storage)
        
        
        self._callbacks: Dict[str, List[Callable]] = {
            'threat_detected': [],
            'backup_completed': [],
            'restore_completed': [],
            'whitelist_changed': [],
        }
        
        
        self.punishments = {
            
            "bot_add": "none",
            
            
            "channel_create": "none",
            "channel_delete": "none",
            "channel_update": "none",
            
            
            "role_create": "none",
            "role_delete": "none",
            "role_update": "none",
            
            
            "member_ban": "none",
            "member_kick": "none",
            "member_unban": "none",
            "member_update": "none",
            
            
            "webhook_create": "none",
            "webhook_delete": "none",
            "webhook_update": "none",
            
            "guild_update": "none"
        }
        
        
        self.punisher = PunishmentExecutor(bot)
        self.timeout_duration = timeout_duration
        self.notify_punished_user = notify_user
        
        
        self.action_queue = asyncio.Queue(maxsize=1000)
        self.log_queue = asyncio.Queue(maxsize=1000)
        self.cleanup_queue = asyncio.Queue(maxsize=1000)
        self.guild_queue = asyncio.Queue(maxsize=1000)
        
        
        self.whitelist_cache = {}  
        self.punishment_cache = {}  
        
        
        self._worker_tasks = []
        
        
        # Initialize handlers
        self.channel_handler = ChannelHandler(self)
        self.role_handler = RoleHandler(self)
        self.member_handler = MemberHandler(self)
        
        # Initialize workers
        self.action_worker = ActionWorker(self)
        self.cleanup_worker = CleanupWorker(self)
        self.log_worker = LogWorker(self)
        self.guild_worker = GuildWorker(self)
        
        self._register_audit_log_listener()
        
        
        self._register_events()
    
    def _register_audit_log_listener(self):
        """Register INSTANT audit log event listener (v2.0 - 5-10ms response)"""
        @self.bot.event
        async def on_audit_log_entry_create(entry: discord.AuditLogEntry):
            try:
                await self.action_queue.put(entry)
                await self.log_queue.put(entry)
                await self.cleanup_queue.put(entry)
                await self.guild_queue.put(entry)
            except asyncio.QueueFull as e:
                print(f"⚠️ Queue full: {e}")

    def _register_events(self):
        """Register Discord event listeners for restorations"""
        # NOTE: These handlers are for RESTORATION (restoring deletions/reverting updates)
        # The audit log listener handles DETECTION (detecting unauthorized creations)
        # Both are needed!
        
        @self.bot.event
        async def on_guild_channel_delete(channel):
            await self.channel_handler.on_channel_delete(channel)
        
        @self.bot.event
        async def on_guild_channel_update(before, after):
            await self.channel_handler.on_channel_update(before, after)
        
        @self.bot.event
        async def on_guild_role_delete(role):
            await self.role_handler.on_role_delete(role)
        
        @self.bot.event
        async def on_guild_role_update(before, after):
            await self.role_handler.on_role_update(before, after)
        
        @self.bot.event
        async def on_member_ban(guild, user):
            await self.member_handler.on_member_ban(guild, user)
        
        @self.bot.event
        async def on_member_update(before, after):
            await self.member_handler.on_member_update(before, after)

    
    def on(self, event_name: str):
        """
        Decorator to register callbacks for SDK events.
        
        Usage:
            @sx.on('threat_detected')
            async def handle_threat(event: ThreatEvent):
                print(f"Threat: {event.type}")
        """
        def decorator(func: Callable):
            if event_name in self._callbacks:
                self._callbacks[event_name].append(func)
            return func
        return decorator
    
    @property
    def on_threat_detected(self):
        """Convenience decorator for threat_detected events"""
        return self.on('threat_detected')
    
    @property
    def on_backup_completed(self):
        """Convenience decorator for backup_completed events"""
        return self.on('backup_completed')
    
    @property
    def on_restore_completed(self):
        """Convenience decorator for restore_completed events"""
        return self.on('restore_completed')
    
    @property
    def on_whitelist_changed(self):
        """Convenience decorator for whitelist_changed events"""
        return self.on('whitelist_changed')
    
    async def _trigger_callbacks(self, event_name: str, *args, **kwargs):
        """Trigger all registered callbacks for an event"""
        if event_name in self._callbacks:
            for callback in self._callbacks[event_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(*args, **kwargs)
                    else:
                        callback(*args, **kwargs)
                except Exception as e:
                    print(f"Error in callback for {event_name}: {e}")
    
    async def enable(
        self,
        guild_id: Optional[int] = None,
        whitelist: Optional[List[int]] = None,
        auto_backup: bool = True,
        punishments: Optional[Dict[str, str]] = None,
        timeout_duration: int = 600,
        notify_user: bool = True
    ):
        """
        Enable SecureX protection.
        
        Args:
            guild_id: Guild ID to enable protection for (required if using whitelist)
            whitelist: List of user IDs to whitelist (default: [])
            auto_backup: Enable automatic backups every 30 minutes (default: True)
            role_position_monitoring: Enable role position monitoring (default: True)
            punishments: Dict mapping violation types to punishment actions
                Example: {"channel_delete": "ban", "role_create": "kick"}
                Available actions: "none", "warn", "timeout", "kick", "ban"
            timeout_duration: Duration in seconds for timeout punishment (default: 600)
            notify_user: Whether to DM violators about punishment (default: True)
        """
        
        # Initialize storage backend (connection pool for PostgreSQL)
        if hasattr(self.storage, 'initialize'):
            await self.storage.initialize()
        
        await self.whitelist.preload_all()
        await self.backup_manager.preload_all()
        
        
        if guild_id:
            whitelist_data = await self.whitelist.get_all(guild_id)
            self.whitelist_cache[guild_id] = set(whitelist_data)
        
        if whitelist and guild_id:
            for user_id in whitelist:
                await self.whitelist.add(guild_id, user_id)
            
            self.whitelist_cache[guild_id] = self.whitelist_cache.get(guild_id, set()) | set(whitelist)
        
        
        if punishments:
            self.punishments.update(punishments)
        
        if guild_id:
            self.punishment_cache[guild_id] = self.punishments.copy()
        
        
        await self.action_worker.start()
        await self.cleanup_worker.start()
        await self.log_worker.start()
        await self.guild_worker.start()
        
        if auto_backup:
            # Enable automatic backups
            self.backup_manager.start_auto_backup()
            # Enable cache auto-refresh
            self.backup_manager.start_auto_refresh()
            
        self.timeout_duration = timeout_duration
        self.notify_punished_user = notify_user
        
        
        if punishments:
            enabled_punishments = {k: v for k, v in self.punishments.items() if v != "none"}
            if enabled_punishments:
                print(f"⚠️  Punishments configured for {len(enabled_punishments)} violation types")
        
        if guild_id:
            await self.backup_manager.create_backup(guild_id)
            
        print("""
 ######  ########  ######  ##     ## ########  ######## ##     ##          ######  ########  ##    ## 
##    ## ##       ##    ## ##     ## ##     ## ##        ##   ##          ##    ## ##     ## ##   ##  
##       ##       ##       ##     ## ##     ## ##         ## ##           ##       ##     ## ##  ##   
 ######  ######   ##       ##     ## ########  ######      ###    #######  ######  ##     ## #####    
      ## ##       ##       ##     ## ##   ##   ##         ## ##                 ## ##     ## ##  ##   
##    ## ##       ##    ## ##     ## ##    ##  ##        ##   ##          ##    ## ##     ## ##   ##  
 ######  ########  ######   #######  ##     ## ######## ##     ##          ######  ########  ##    ##  
""")
    
    
    async def create_backup(self, guild_id: int) -> BackupInfo:
        """
        Create a backup for the specified guild.
        
        Args:
            guild_id: The guild ID to backup
            
        Returns:
            BackupInfo object with backup results
        """
        return await self.backup_manager.create_backup(guild_id)
    
    async def restore_channel(self, guild: discord.Guild, channel: discord.abc.GuildChannel):
        """
        Restore a deleted channel from backup.
        
        Args:
            guild: The guild object
            channel: The deleted channel object
            
        Returns:
            The newly created channel or None if restoration failed
        """
        return await self.backup_manager.restore_channel(guild, channel)
    
    async def restore_role(self, guild: discord.Guild, role_id: int) -> bool:
        """
        Restore a deleted role from backup.
        
        Args:
            guild: The guild object
            role_id: The ID of the deleted role
            
        Returns:
            True if successful, False otherwise
        """
        return await self.backup_manager.restore_role(guild, role_id)
