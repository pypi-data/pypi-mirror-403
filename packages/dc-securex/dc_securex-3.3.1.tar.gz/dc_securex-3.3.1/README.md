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
- 💾 **Database Backends** - Native support for SQLite (default) and PostgreSQL
- 👥 **Flexible Whitelisting** - Per-guild trusted user management
- ⚖️ **Customizable Punishments** - Configure responses (ban/kick/none) per action type
- 📊 **Event Callbacks** - Hook into threat detection, backups, and restorations

---

## 📦 Installation

### Basic Installation (SQLite)

```bash
pip install dc-securex
```

### With PostgreSQL Support

```bash
pip install dc-securex[postgres]
```

---

## 🚀 Quick Start

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
        auto_backup=True,
        punishments={
            "channel_delete": "ban",
            "role_delete": "kick"
        }
    )
    print(f"✅ SecureX enabled for {bot.guilds[0].name}")

bot.run("YOUR_BOT_TOKEN")
```

---

## 📚 Documentation & Tutorials

**Full documentation, detailed tutorials, and endpoint references are available on our official website:**

👉 **[Documentation Website Coming Soon]**

For now, you can explore the examples in the `examples/` directory or check the source code for type hints and docstrings.

---

## 🔧 Requirements

- Python 3.8+
- `discord.py` 2.0.0+
- `aiofiles`
- `aiosqlite` (for SQLite)
- `asyncpg` (optional, for PostgreSQL)

---

## ⚖️ License

MIT License
