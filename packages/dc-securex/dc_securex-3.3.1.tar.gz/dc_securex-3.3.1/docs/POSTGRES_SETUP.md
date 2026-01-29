# PostgreSQL Installation Guide

## Prerequisites

Install PostgreSQL on your system:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download from https://www.postgresql.org/download/windows/

## Database Setup

1. **Create database and user:**
```bash
sudo -u postgres psql

CREATE DATABASE securex_db;
CREATE USER securex_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE securex_db TO securex_user;
\q
```

2. **Configure PostgreSQL for optimal performance (optional):**

Edit `/etc/postgresql/[version]/main/postgresql.conf`:

```conf
# WAL settings for concurrent read/write
wal_level = replica
max_wal_size = 1GB
checkpoint_completion_target = 0.9

# Connection settings
max_connections = 100

# Performance tuning
shared_buffers = 256MB
effective_cache_size = 1GB
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

## Install SDK with PostgreSQL Support

```bash
pip install dc-securex[postgres]
```

## Usage

```python
import discord
from securex import SecureX

bot = discord.Bot(intents=discord.Intents.all())

sdk = SecureX(
    bot=bot,
    storage_backend="postgres",
    postgres_url="postgresql://securex_user:your_secure_password@localhost:5432/securex_db",
    postgres_pool_size=10
)

@bot.event
async def on_ready():
    await sdk.enable(guild_id=YOUR_GUILD_ID)

bot.run("TOKEN")
```

## Connection URL Format

```
postgresql://username:password@hostname:port/database
```

**Examples:**

- Local: `postgresql://securex_user:pass@localhost:5432/securex_db`
- Remote: `postgresql://user:pass@db.example.com:5432/production`
- SSL: `postgresql://user:pass@host:5432/db?sslmode=require`

## Environment Variables (Recommended)

Store credentials securely:

`.env`:
```env
DATABASE_URL=postgresql://securex_user:your_password@localhost:5432/securex_db
```

Python:
```python
import os
from dotenv import load_dotenv

load_dotenv()

sdk = SecureX(
    bot=bot,
    storage_backend="postgres",
    postgres_url=os.getenv("DATABASE_URL")
)
```

## Verify Connection

```python
@bot.event
async def on_ready():
    await sdk.enable()
    # Check pool stats
    print(f"Pool size: {sdk.storage.pool.get_size()}")
    print(f"Free connections: {sdk.storage.pool.get_idle_size()}")
```

## Migration from JSON

To migrate existing JSON data to PostgreSQL, use the migration utility:

```python
from securex.utils.migrate_storage import migrate_json_to_postgres

await migrate_json_to_postgres(
    json_backup_dir="./data/backups",
    postgres_url="postgresql://user:pass@localhost/securex_db"
)
```
