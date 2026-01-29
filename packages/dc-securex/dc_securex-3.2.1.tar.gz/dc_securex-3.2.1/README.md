# 🛡️ SecureX SDK - Discord Server Protection Made Easy

**Protect your Discord server from attacks in just 5 lines of code!**

[![PyPI version](https://badge.fury.io/py/dc-securex.svg)](https://pypi.org/project/dc-securex/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🤔 What is this?

SecureX is a **Python library** that protects your Discord server from people who try to destroy it. 

Imagine someone gets admin powers and starts:
- 🗑️ Deleting all channels
- 👥 Kicking everyone
- 🚫 Banning members
- 🤖 Adding spam bots

**SecureX stops them in milliseconds** (0.005 seconds!) and fixes everything automatically!

---

## ✨ Features

- ⚡ **Instant Threat Response** - Triple-worker architecture for microsecond-level detection
- 🛡️ **Comprehensive Protection** - Guards channels, roles, members, bots, webhooks, and guild settings
- 🔄 **Smart Backup & Restore** - Automatic structural backups with intelligent restoration
- 💾 **SQLite Storage with WAL** - Fast, reliable storage with Write-Ahead Logging for concurrent access
- 🗄️ **Multiple Storage Backends** - Choose between SQLite (default) or PostgreSQL
- 👥 **Flexible Whitelisting** - Per-guild trusted user management
- ⚖️ **Customizable Punishments** - Configure responses (ban/kick/none) per action type
- 📊 **Event Callbacks** - Hook into threat detection, backups, and restorations
- ✅ **90% Test Coverage** - Comprehensive test suite with 100% coverage on critical paths
- 🔌 **Production Ready** - Built with asyncio, type hints, and comprehensive error handling

---

## 📋 Requirements

### Python & Dependencies

**Required:**
- ✅ Python 3.8 or higher
- ✅ discord.py 2.0.0 or higher (auto-installed)
- ✅ aiofiles 23.0.0 or higher (auto-installed)

## Installation

### Basic Installation (SQLite)

```bash
pip install dc-securex
```

### With PostgreSQL Support

```bash
pip install dc-securex[postgres]
```

This automatically installs all required dependencies!

### Discord Bot Permissions

**REQUIRED Permissions** (Bot won't work without these):

| Permission | Why Needed | Priority |
|------------|-----------|----------|
| `View Audit Log` | See who did what (CRITICAL!) | 🔴 MUST HAVE |
| `Manage Channels` | Restore deleted channels | 🔴 MUST HAVE |
| `Manage Roles` | Restore deleted roles | 🔴 MUST HAVE |
| `Ban Members` | Ban attackers | 🟡 For bans |
| `Kick Members` | Kick attackers | 🟡 For kicks |
| `Moderate Members` | Timeout attackers | 🟡 For timeouts |
| `Manage Webhooks` | Delete spam webhooks | 🟢 Optional |

**Easy Invite Link:**
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=8&scope=bot
```
Using `permissions=8` gives Administrator (easiest for testing).

### Discord Bot Intents

**REQUIRED Intents** (Enable in Developer Portal AND code):

**In Discord Developer Portal:**
1. Go to your app → Bot → Privileged Gateway Intents
2. Enable:
   - ✅ SERVER MEMBERS INTENT
   - ✅ MESSAGE CONTENT INTENT (if using commands)

**In Your Code:**
```python
import discord
intents = discord.Intents.all()
```

Or specific intents:
```python
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.bans = True
intents.webhooks = True
```

### Bot Role Position

⚠️ **IMPORTANT:** Your bot's role must be **higher** than roles it manages!

```
✅ CORRECT:
1. Owner
2. SecureBot ← Bot here
3. Admin
4. Moderator

❌ WRONG:
1. Owner
2. Admin
3. SecureBot ← Bot too low!
4. Moderator
```

### System Requirements

- **OS:** Windows, Linux, macOS (any OS with Python 3.8+)
- **RAM:** 512MB minimum (1GB recommended)
- **Disk:** 100MB for SDK + backups
- **Network:** Stable internet connection
- **Discord:** Bot must have access to audit logs

### Optional (Recommended)

- **Git** - For version control
- **Virtual Environment** - Keep dependencies isolated
  ```bash
  python -m venv venv
  source venv/bin/activate
  pip install dc-securex
  ```


---

## 📋 Before You Start

### Step 1: Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Give it a name (like "SecureBot")
4. Go to **"Bot"** tab → Click **"Add Bot"**
5. **Important**: Enable these switches:
   - ✅ SERVER MEMBERS INTENT
   - ✅ MESSAGE CONTENT INTENT
6. Click **"Reset Token"** → Copy your bot token (you'll need this!)

### Step 2: Invite Bot to Your Server

Use this link (replace `YOUR_BOT_ID` with your bot's ID from Developer Portal):
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=8&scope=bot
```

**Permission value `8` = Administrator** (easiest for beginners)

### Step 3: Install Python & Libraries

**Check if Python is installed:**
```bash
python --version
```

**Requirements:**
- ✅ Python 3.8 or newer (Python 3.10+ recommended)
- ✅ pip (comes with Python)

**If you don't have Python:**
- Download from [python.org](https://python.org)
- During installation, check "Add Python to PATH"

**Install SecureX SDK:**
```bash
pip install dc-securex
```

**What gets installed automatically:**
- `discord.py >= 2.0.0` - Discord API wrapper
- `aiofiles >= 23.0.0` - Async file operations

**Optional: Use Virtual Environment (Recommended)**
```bash
python -m venv venv
source venv/bin/activate
pip install dc-securex
```

**Verify installation:**
```bash
pip show dc-securex
```

You should see version 2.15.3 or higher!

---

## 🚀 Quick Start

### Using SQLite (Default)

```python
import discord
from securex import SecureX

bot = discord.Client(intents=discord.Intents.all())
sx = SecureX(bot)  # SQLite storage automatically configured

@bot.event
async def on_ready():
    await sx.enable(
        guild_id=YOUR_GUILD_ID,
        whitelist=[ADMIN_USER_ID_1, ADMIN_USER_ID_2],
        auto_backup=True
    )
    print(f"✅ SecureX enabled for {bot.guilds[0].name}")
    print(f"💾 Using SQLite storage with WAL mode")

bot.run("YOUR_BOT_TOKEN")
```

### Using PostgreSQL

```python
import discord
from securex import SecureX

bot = discord.Client(intents=discord.Intents.all())
sx = SecureX(
    bot,
    storage_backend="postgres",
    postgres_url="postgresql://user:password@localhost:5432/securex_db",
    postgres_pool_size=10
)

@bot.event
async def on_ready():
    await sx.enable(
        guild_id=YOUR_GUILD_ID,
        whitelist=[ADMIN_USER_ID],
        auto_backup=True
    )
    print(f"✅ SecureX enabled with PostgreSQL storage")

bot.run("YOUR_BOT_TOKEN")
```

### Step 3: Add Your Bot Token

Replace `"YOUR_BOT_TOKEN_HERE"` with the token you copied from Discord Developer Portal.

**⚠️ KEEP YOUR TOKEN SECRET!** Never share it or post it online!

### Step 4: Run Your Bot

```bash
python bot.py
```

You should see: `✅ YourBotName is online and protected!`

### Step 5: Test It!

Your server is now protected! If someone tries to delete a channel or kick members without permission, SecureX will:
1. **Ban them instantly** (in 0.005 seconds!)
2. **Restore what they deleted** (channels, roles, etc.)
3. **Log the attack** (so you know what happened)

---

## 🎯 Understanding the Code

Let's break down what each part does:

```python
from securex import SecureX
```
This imports the SecureX library.

```python
sx = SecureX(bot)
```
This connects SecureX to your bot.

```python
await sx.enable(punishments={...})
```
This turns on protection and sets punishments:
- `"ban"` = Ban the attacker
- `"kick"` = Kick them out
- `"timeout"` = Mute them for 10 minutes
- `"none"` = Just restore, don't punish

---

## 🔧 What Can You Protect?

Here are ALL the things you can protect:

| Type | What it stops | Available Punishments |
|------|--------------|----------------------|
| `channel_delete` | Deleting channels | `"none"`, `"warn"`, `"timeout"`, `"kick"`, `"ban"` |
| `channel_create` | Creating too many channels (spam) | `"none"`, `"warn"`, `"timeout"`, `"kick"`, `"ban"` |
| `role_delete` | Deleting roles | `"none"`, `"warn"`, `"timeout"`, `"kick"`, `"ban"` |
| `role_create` | Creating too many roles (spam) | `"none"`, `"warn"`, `"timeout"`, `"kick"`, `"ban"` |
| `member_kick` | Kicking members | `"none"`, `"warn"`, `"timeout"`, `"kick"`, `"ban"` |
| `member_ban` | Banning members | `"none"`, `"warn"`, `"timeout"`, `"kick"`, `"ban"` |
| `member_unban` | Unbanning people | `"none"`, `"warn"`, `"timeout"`, `"kick"`, `"ban"` |
| `webhook_create` | Creating spam webhooks | `"none"`, `"warn"`, `"timeout"`, `"kick"`, `"ban"` |
| `bot_add` | Adding bad bots | Always `"ban"` (automatic) |

**Punishment Options Explained:**
- `"none"` - Only restore, don't punish
- `"warn"` - Send warning message  
- `"timeout"` - Mute for 10 minutes (configurable)
- `"kick"` - Kick from server
- `"ban"` - Ban from server

---

## 🎨 Simple Examples

### Example 1: Strict Mode (Ban Everything)

```python
await sx.enable(
    punishments={
        "channel_delete": "ban",
        "channel_create": "ban",
        "role_delete": "ban",
        "role_create": "ban",
        "member_kick": "ban",
        "member_ban": "ban"
    }
)
```

### Example 2: Gentle Mode (Warn Only)

```python
await sx.enable(
    punishments={
        "channel_delete": "timeout",
        "role_delete": "timeout",
        "member_kick": "warn"
    }
)
```

### Example 3: Protection Without Punishment

```python
await sx.enable()
```
This only restores deleted stuff but doesn't punish anyone.

---

## 👥 Whitelist (Allow Trusted Users)

Want to allow some people to delete channels? Add them to the whitelist:

```python
await sx.whitelist.add(guild_id, user_id)
```

**Example:**
```python
@bot.command()
@commands.is_owner()
async def trust(ctx, member: discord.Member):
    await sx.whitelist.add(ctx.guild.id, member.id)
    await ctx.send(f"✅ {member.name} is now trusted!")

@bot.command()
@commands.is_owner()
async def untrust(ctx, member: discord.Member):
    await sx.whitelist.remove(ctx.guild.id, member.id)
    await ctx.send(f"❌ {member.name} is no longer trusted!")
```

---

## 🔔 Get Notified When Attacks Happen

Add this to your code to get alerts:

```python
@sx.on_threat_detected
async def alert(threat):
    print(f"🚨 ATTACK DETECTED!")
    print(f"   Type: {threat.type}")
    print(f"   Attacker: {threat.actor_id}")
    print(f"   Punishment: {threat.punishment_action}")
```

**Fancier Alert (Discord Embed):**

```python
@sx.on_threat_detected
async def fancy_alert(threat):
    channel = bot.get_channel(YOUR_LOG_CHANNEL_ID)
    
    embed = discord.Embed(
        title="🚨 Security Alert!",
        description=f"Someone tried to {threat.type}!",
        color=discord.Color.red()
    )
    embed.add_field(name="Attacker", value=f"<@{threat.actor_id}>")
    embed.add_field(name="What Happened", value=threat.target_name)
    embed.add_field(name="Punishment", value=threat.punishment_action.upper())
    
    await channel.send(embed=embed)
```

---

## 📝 Full Working Example

Here's a complete bot with commands:

```python
import discord
from discord.ext import commands
from securex import SecureX

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
sx = SecureX(bot)

@bot.event
async def on_ready():
    await sx.enable(punishments={"channel_delete": "ban", "member_ban": "ban"})
    print(f"✅ {bot.user.name} is protecting {len(bot.guilds)} servers!")

@sx.on_threat_detected
async def log_attack(threat):
    print(f"🚨 Stopped {threat.type} by user {threat.actor_id}")

@bot.command()
@commands.is_owner()
async def trust(ctx, member: discord.Member):
    await sx.whitelist.add(ctx.guild.id, member.id)
    await ctx.send(f"✅ {member.mention} can now manage the server!")

@bot.command()
@commands.is_owner()
async def untrust(ctx, member: discord.Member):
    await sx.whitelist.remove(ctx.guild.id, member.id)
    await ctx.send(f"❌ {member.mention} is no longer trusted!")

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Protection active!")

bot.run("YOUR_BOT_TOKEN")
```

---

## ❓ Common Questions

### Q: Will this slow down my bot?
**A:** No! SecureX is SUPER fast (5-10 milliseconds). Your bot will work normally.

### Q: What if I accidentally delete a channel?
**A:** If you're the server owner, SecureX won't stop you! Or add yourself to the whitelist.

### Q: Can I change punishments later?
**A:** Yes! Just call `await sx.enable(punishments={...})` again with new settings.

### Q: Does it work on multiple servers?
**A:** Yes! It automatically protects all servers your bot is in.

### Q: What if my bot goes offline?
**A:** When it comes back online, it automatically creates new backups. But it can't stop attacks while offline.

### Q: How do I make my own commands?
**A:** Check [discord.py documentation](https://discordpy.readthedocs.io/) to learn more about making bot commands!

---

## 🔧 Troubleshooting

### ❌ "Missing Permissions" Error

**Solution:** Make sure your bot has Administrator permission, or at least these:
- Manage Channels
- Manage Roles
- Ban Members
- Kick Members
- View Audit Log

### ❌ Bot doesn't detect attacks

**Solution:**
1. Check if you enabled **SERVER MEMBERS INTENT** in Discord Developer Portal
2. Make sure your bot is using `intents=discord.Intents.all()`
3. Check if bot role is above other roles in Server Settings → Roles

### ❌ Can't restore deleted channels

**Solution:** Bot role must be **higher** than the roles it needs to manage

---

## 🏗️ Architecture (How It Works Under the Hood)

SecureX uses a **Triple-Worker Architecture** for maximum speed and reliability. Here's how it works:

### ⚡ The Triple-Worker System

Think of SecureX like a security team with 3 specialized workers:

```
┌─────────────────────────────────────────────────────────┐
│                    DISCORD SERVER                        │
│  (Someone deletes a channel, kicks a member, etc.)      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│          DISCORD AUDIT LOG EVENT (Instant!)            │
│  Discord creates a log entry: "User X deleted #general"│
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼ (5-10 milliseconds)
┌────────────────────────────────────────────────────────┐
│              SECUREX EVENT LISTENER                     │
│         (Catches the audit log instantly)               │
└─────┬──────────┬─────────────┬────────────────────────┘
      │          │             │
      ▼          ▼             ▼
  ┌─────┐    ┌─────┐      ┌─────┐
  │ Q1  │    │ Q2  │      │ Q3  │  (3 Queues)
  └──┬──┘    └──┬──┘      └──┬──┘
     │          │            │
     ▼          ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│Worker 1 │ │Worker 2 │ │Worker 3 │
│ Action  │ │ Cleanup │ │   Log   │
└─────────┘ └─────────┘ └─────────┘
```

### 🔨 Worker 1: Action Worker (PUNISHER)
**Job:** Ban/kick bad users INSTANTLY

**What it does:**
1. Checks if user is whitelisted
2. If NOT whitelisted → BAN them immediately
3. Takes only 5-10 milliseconds!

**Example:**
```
User "Hacker123" deletes #general
  ↓ (5ms later)
Action Worker: "Hacker123 is NOT whitelisted"
  ↓
*BANS Hacker123 instantly*
```

### 🧹 Worker 2: Cleanup Worker (CLEANER)
**Job:** Delete spam creations (channels, roles, webhooks)

**What it does:**
1. If someone creates 50 spam channels
2. Deletes them all INSTANTLY
3. Prevents server from getting cluttered

**Example:**
```
User creates spam channel "#spam1"
  ↓ (10ms later)
Cleanup Worker: "Unauthorized channel!"
  ↓
*Deletes #spam1 immediately*
```

### � Worker 3: Log Worker (REPORTER)
**Job:** Alert you about attacks

**What it does:**
1. Fires your callbacks
2. Sends you alerts
3. Logs everything for review

**Example:**
```
Attack detected!
  ↓
Log Worker: Calls your @sx.on_threat_detected
  ↓
You get an alert embed in Discord!
```

---

### 🔄 Restoration System (Separate from Workers)

**Job:** Restore deleted stuff from backups

**How it works:**
```
Channel deleted
  ↓ (500ms wait for audit log)
  ↓
Restoration Handler checks: "Was this authorized?"
  ↓ NO
  ↓
Looks in backup: "Found #general backup!"
  ↓
*Recreates channel with same permissions*
```

**Automatic Backups:**
- Creates backup every 10 minutes
- Saves: Channels, roles, permissions, positions
- Stored in `./data/backups/` folder

---

### 🏰 Worker 4: Guild Worker (GUILD SETTINGS PROTECTOR)

**NEW in v2.15+!** The Guild Worker protects and restores critical guild settings.

**Job:** Restore guild name, icon, banner, vanity URL when changed unauthorized

**What it does:**
1. Monitors `guild_update` audit log events
2. Detects changes to server name, icon, banner, description, vanity URL
3. Restores from backup if unauthorized user made changes
4. Uses user tokens for vanity URL restoration (Discord API limitation)

**Protected Settings:**
- ✅ Server Name
- ✅ Server Icon
- ✅ Server Banner
- ✅ Server Description
- ✅ **Vanity URL** (requires user token)

**Example:**
```
Unauthorized user changes server name to "HACKED SERVER"
  ↓ (50ms wait for audit log)
  ↓
Guild Worker checks: "Was this authorized?"
  ↓ NO
  ↓
Looks in backup: "Found original name: Cool Community"
  ↓
*Restores server name to "Cool Community"*
```

---

### 🔑 Setting Up Guild Worker (With Vanity URL Support)

**Important:** Vanity URL restoration requires a **user token** due to Discord API limitations. Bot tokens cannot modify vanity URLs.

#### Step 1: Get Your User Token (One-Time Setup)

**⚠️ WARNING:** Your user token is VERY sensitive! Never share it publicly!

**How to get it:**
1. Open Discord in your browser (not the app!)
2. Press `F12` to open Developer Tools
3. Go to **Console** tab  
4. Type: `window.webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]);m.find(m=>m?.exports?.default?.getToken!==void 0).exports.default.getToken()`
5. Copy the long string that appears (your token)

**Alternative Method (Network Tab):**
1. Open Discord in browser → `F12` → Network tab
2. Filter by "api"
3. Click any request to `discord.com/api/`
4. Look in Headers → Request Headers → `authorization`
5. Copy the token value

#### Step 2: Set The User Token in Your Bot

```python
@bot.event
async def on_ready():
    await sx.enable(punishments={...})
    
    # Set user token for vanity URL restoration
    guild_id = 1234567890  # Your server ID
    user_token = "YOUR_USER_TOKEN_HERE"  # From step 1
    
    await sx.guild_worker.set_user_token(guild_id, user_token)
    print("✅ Guild settings protection enabled with vanity URL support!")
```

#### Step 3: Test It!

Try changing your server's vanity URL - SecureX will restore it automatically!

**Full Example:**
```python
import discord
from discord.ext import commands
from securex import SecureX

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
sx = SecureX(bot)

@bot.event
async def on_ready():
    # Enable punishments
    await sx.enable(punishments={"channel_delete": "ban"})
    
    # Set user token for each guild
    for guild in bot.guilds:
        token = get_user_token_for_guild(guild.id)  # Your token storage
        await sx.guild_worker.set_user_token(guild.id, token)
    
    print(f"✅ {bot.user.name} protecting {len(bot.guilds)} servers!")

bot.run("YOUR_BOT_TOKEN")
```

---

### 🎯 Guild Worker API

**Set User Token:**
```python
await sx.guild_worker.set_user_token(guild_id, "user_token_here")
```

**Get User Token:**
```python
token = sx.guild_worker.get_user_token(guild_id)
```

**Remove User Token:**
```python
await sx.guild_worker.remove_user_token(guild_id)
```

**Check If Token Is Set:**
```python
if sx.guild_worker.get_user_token(guild_id):
    print("Token is configured!")
else:
    print("No token set - vanity restoration won't work!")
```

---

### 💾 User Token Storage

User tokens are **automatically saved** to `./data/backups/user_tokens.json` for persistence.

**Token Data Model:**
```python
from securex.models import UserToken

# Create token metadata
token_data = UserToken(
    guild_id=123456789,
    token="user_token_here",
    set_by=999888777,  # Admin who set it
    description="Production server token"
)

# Track usage
token_data.mark_used()  # Updates last_used timestamp

# Serialize
token_dict = token_data.to_dict()
```

**Storage Format (user_tokens.json):**
```json
{
  "1234567890": "user_token_abc...",
  "9876543210": "user_token_xyz..."
}
```

---

### ⚠️ Important Notes About User Tokens

**Security:**
- ✅ Tokens are stored locally in `./data/backups/`
- ✅ Never commit `user_tokens.json` to Git!
- ✅ Add to `.gitignore`: `data/backups/user_tokens.json`
- ⚠️ User tokens are more powerful than bot tokens - keep them secure!

**Limitations:**
- User tokens can **only** restore vanity URLs
- Other guild settings (name, icon, banner) use bot permissions
- User must be a server owner or have Manage Guild permission
- User token must be from someone with vanity URL access

**What Happens Without User Token:**
```
Unauthorized user changes vanity URL
  ↓
Guild Worker tries to restore
  ↓
⚠️ No user token set!
  ↓
Prints: "No user token set for guild 123! Cannot restore vanity."
  ↓
Other settings (name, icon) still restored via bot!
```

---

### 🔄 Complete Guild Protection Flow

**Timeline of Guild Name Change:**
```
0ms    - Unauthorized user changes server name
50ms   - Discord audit log updated
75ms   - Guild Worker detects change
80ms   - Checks whitelist (user not whitelisted)
85ms   - Loads backup (finds original name)
100ms  - Calls guild.edit(name="Original Name")
300ms  - Server name restored!
```

---

## 💾 Storage Backends

SecureX v3.0+ supports **two storage backends** for maximum flexibility:

### 🗃️ SQLite (Default)

**The recommended choice for most users.** SQLite provides fast, reliable local storage with zero configuration.

**Features:**
- ✅ **Zero Configuration** - Works out of the box
- ✅ **WAL Mode** - Write-Ahead Logging for concurrent read/write
- ✅ **ACID Compliant** - Guaranteed data integrity
- ✅ **Single File** - All data in `./data/securex.db`
- ✅ **High Performance** - Indexed queries, fast I/O
- ✅ **No Dependencies** - Built into Python

**Usage:**
```python
# Automatic (default)
sx = SecureX(bot)

# Explicit
sx = SecureX(bot, storage_backend="sqlite")

# Custom database path
sx = SecureX(bot, storage_backend="sqlite", backup_dir="./custom/path")
# Database will be at: ./custom/path/securex.db
```

**What WAL Mode Means:**
Write-Ahead Logging allows multiple simultaneous readers while one writer is active. This means SecureX can read backups while creating new ones, preventing any blocking.

---

### 🐘 PostgreSQL (Optional)

**For enterprise deployments** requiring centralized database management or multi-instance setups.

**Features:**
- ✅ **Centralized Storage** - Single database for multiple bot instances
- ✅ **Connection Pooling** - Efficient resource usage
- ✅ **Advanced Queries** - Full SQL capabilities
- ✅ **Professional Tools** - pgAdmin, psql, monitoring
- ✅ **Scalable** - Handle thousands of guilds

**Installation:**
```bash
pip install dc-securex[postgres]
```

This installs the `asyncpg` driver.

**Usage:**
```python
import discord
from securex import SecureX

bot = discord.Client(intents=discord.Intents.all())

sx = SecureX(
    bot,
    storage_backend="postgres",
    postgres_url="postgresql://username:password@host:5432/database",
    postgres_pool_size=10  # Optional, default: 10
)

@bot.event
async def on_ready():
    await sx.enable(guild_id=YOUR_GUILD_ID)
    print("✅ Connected to PostgreSQL")

bot.run("YOUR_BOT_TOKEN")
```

**Connection URL Format:**
```
postgresql://username:password@hostname:port/database_name
```

**Examples:**
```python
# Local PostgreSQL
postgres_url = "postgresql://securex:mypassword@localhost:5432/securex_db"

# Remote server
postgres_url = "postgresql://user:pass@db.example.com:5432/prod_securex"

# With connection pooling
sx = SecureX(
    bot,
    storage_backend="postgres",
    postgres_url=postgres_url,
    postgres_pool_size=20  # Max connections
)
```

---

### 📊 Storage Backend Comparison

| Feature | SQLite | PostgreSQL |
|:---|:---|:---|
| **Setup Complexity** | Zero config | Requires DB server |
| **Installation** | Built-in | `pip install dc-securex[postgres]` |
| **Performance** | Excellent | Excellent |
| **Concurrency** | WAL mode (good) | Connection pooling (excellent) |
| **Scalability** | Up to ~100 guilds | Unlimited |
| **Multi-Instance** | No | Yes |
| **Maintenance** | Zero | DB administration |
| **Best For** | Most use cases | Enterprise deployments |

---

### 🔄 Migrating from JSON to SQLite

**If you're upgrading from SecureX v2.x (JSON storage):**

**Important:** JSON data is **not automatically migrated**. The new SQLite backend starts fresh.

**Migration Steps:**

1. **Backup your existing data:**
   ```bash
   cp -r ./data/backups ./data/backups_old
   cp -r ./data/whitelists ./data/whitelists_old
   ```

2. **Upgrade SecureX:**
   ```bash
   pip install --upgrade dc-securex
   ```

3. **Update your code** (no changes needed - SQLite is now default)

4. **Re-add whitelisted users:**
   ```python
   @bot.event
   async def on_ready():
       await sx.enable(guild_id=YOUR_GUILD_ID)
       
       # Re-add your whitelisted users
       await sx.whitelist.add(YOUR_GUILD_ID, USER_ID_1)
       await sx.whitelist.add(YOUR_GUILD_ID, USER_ID_2)
   ```

5. **Create fresh backups:**
   ```python
   # Automatic on first enable
   await sx.enable(guild_id=YOUR_GUILD_ID, auto_backup=True)
   
   # Or manual
   backup_info = await sx.create_backup(YOUR_GUILD_ID)
   print(f"✅ Backup created: {backup_info.channel_count} channels, {backup_info.role_count} roles")
   ```

**What You'll Lose:**
- Historical JSON backup files (new SQLite backups will be created)
- Old JSON whitelist files (re-add users)
- User tokens (re-configure if using vanity URL restoration)

**What You'll Gain:**
- 🚀 **Faster performance** with indexed queries
- 🔒 **Better data integrity** with ACID transactions
- ⚡ **Concurrent access** with WAL mode
- 📦 **Single file storage** instead of multiple JSON files

---

### 🔧 Storage Configuration

**SQLite Configuration:**
```python
sx = SecureX(
    bot,
    storage_backend="sqlite",
    backup_dir="./data/backups"  # Database location
)
# Creates: ./data/backups/securex.db
```

**PostgreSQL Configuration:**
```python
sx = SecureX(
    bot,
    storage_backend="postgres",
    postgres_url="postgresql://user:pass@host:5432/db",
    postgres_pool_size=15  # Connection pool size
)
```

**Environment Variables (Recommended for Production):**
```python
import os

sx = SecureX(
    bot,
    storage_backend=os.getenv("STORAGE_BACKEND", "sqlite"),
    postgres_url=os.getenv("DATABASE_URL")  # For PostgreSQL
)
```

**`.env` file:**
```bash
STORAGE_BACKEND=postgres
DATABASE_URL=postgresql://securex:password@localhost:5432/securex_db
DISCORD_TOKEN=your_bot_token_here
```



**Multi-Setting Attack:**
```
User changes: name + icon + banner + vanity
  ↓
Guild Worker restores ALL in one go:
  - Name: Restored via bot
  - Icon: Restored via bot  
  - Banner: Restored via bot
  - Vanity: Restored via user token (API)
  ↓
Total time: ~500ms for all 4 settings!
```

---

### 📊 Guild Worker vs Other Workers

| Worker | Speed | What It Protects | Token Needed
|--------|-------|------------------|-------------|
| Action Worker | 5-10ms | Punishes attackers | Bot token ✅ |
| Cleanup Worker | 10-20ms | Deletes spam | Bot token ✅ |
| Log Worker | 15ms | Sends alerts | Bot token ✅ |
| Guild Worker | 50-500ms | Server settings | Bot + User token ⚠️ |

**Why Guild Worker is slower:**
- Waits for audit log (50ms)
- Loads backup from disk
- Makes API calls to restore
- Vanity URL uses external API endpoint

**But still VERY fast compared to manual restoration!**



---

### 🎯 Why Triple Workers?

**Speed:**
- Workers don't wait for each other
- All process in parallel
- Punishment happens in 5-10ms!

**Reliability:**
- If one worker crashes, others keep working
- Each worker has its own queue
- No single point of failure

**Separation:**
- Punishment (fast) ≠ Restoration (slower but thorough)
- Action Worker = instant ban
- Restoration Handler = careful rebuild

---

### 📊 Data Flow Example

Let's say "BadUser" deletes 5 channels:

**Timeline:**
```
0ms    - BadUser deletes #general
5ms    - SecureX detects it (audit log)
7ms    - Broadcasts to 3 workers
10ms   - Action Worker BANS BadUser
12ms   - Cleanup Worker ready (no cleanup needed)
15ms   - Log Worker alerts you
500ms  - Restoration Handler starts
750ms  - #general recreated with permissions
```

**Result:**
- ✅ BadUser banned in 10ms
- ✅ You alerted in 15ms
- ✅ #general restored in 750ms
- ✅ Total response: Less than 1 second!

---

### 🧠 Smart Permission Detection

When someone updates a member's roles:

```
User "Sneaky" gives Admin role to "Friend"
  ↓
Member Update Handler triggered
  ↓
Checks: "Is Sneaky whitelisted?"
  ↓ NO
  ↓
Scans ALL roles of "Friend"
  ↓
Finds roles with dangerous permissions:
  - Administrator ❌
  - Manage Roles ❌
  - Ban Members ❌
  ↓
*Removes ALL dangerous roles in ONE API call*
  ↓
Friend is now safe!
```

**Dangerous Permissions Detected:**
- Administrator
- Kick Members
- Ban Members
- Manage Guild
- Manage Roles
- Manage Channels
- Manage Webhooks
- Manage Emojis
- Mention Everyone
- Manage Expressions

---

### 💾 Caching System

SecureX uses caching for maximum speed:

**Cached Data:**
1. **Whitelist** - Frozenset for O(1) lookup
2. **Dangerous Permissions** - Class-level constant
3. **Guild Backups** - Updated every 10 minutes

**Why This Matters:**
```python


OLD (v1.x):
Check whitelist → Database query (50-100ms)

NEW (v2.x):
Check whitelist → Memory lookup (0.001ms)
```

**50,000x faster!**

---

## 📊 How It Works (Simple Summary)

1. **Someone does something bad** (delete channel, ban member, etc.)
2. **Discord logs it** (in audit log)
3. **SecureX sees it instantly** (5-10 milliseconds later!)
4. **Checks if they're allowed** (whitelist check)
5. **If NOT allowed:**
   - Bans/kicks them (punishment)
   - Restores what they deleted (from backup)
   - Alerts you (via callback)

All of this happens **automatically** while you sleep! 😴


---

## 🎓 Next Steps

1. ✅ Get bot token from Discord Developer Portal
2. ✅ Install: `pip install dc-securex`
3. ✅ Copy the example code
4. ✅ Add your bot token
5. ✅ Run: `python bot.py`
6. 🎉 Your server is protected!

---

## 📚 Want to Learn More?

- [Discord.py Docs](https://discordpy.readthedocs.io/) - Learn to make Discord bots
- [Python Tutorial](https://docs.python.org/3/tutorial/) - Learn Python basics
- [Discord Developer Portal](https://discord.com/developers/docs) - Official Discord docs

---

## 📄 License

MIT License - Free to use! ❤️

---

## 🌟 Support

Having issues? Questions? Found a bug?
- Open an issue on GitHub
- Read this README carefully
- Check if your bot has all permissions

---

**Made with ❤️ for Discord bot developers**  
**Version 2.15.5** - Lightning-fast server protection!

🚀 **Start protecting your server today!**
