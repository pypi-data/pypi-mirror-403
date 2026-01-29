# WowBits CLI

A command-line interface for managing connectors and integrations in the WowBits AI platform.

## Installation

### From PyPI (once published)

```bash
pip install wowbits-cli
```

### From source

```bash
cd src
pip install -e .
```

## Configuration

Set your database connection string:

```bash
export SUPABASE_CONNECTION_STRING="postgresql://user:password@host:5432/database"
```

## Usage

```bash
# Show help
wowbits --help

# List all connectors
wowbits list connectors

# List available providers
wowbits list providers

# Create a connector (interactive mode)
wowbits create connector --provider openai

# Create a connector with config
wowbits create connector --provider fmp --config '{"api_key": "your-key"}'

# Update a connector
wowbits update connector --id <uuid> --config '{"api_key": "new-key"}'

# Delete a connector
wowbits delete connector --id <uuid>
wowbits delete connector --name "OpenAI"
```

## Available Providers

- `openai` - OpenAI API for GPT models
- `anthropic` - Anthropic API for Claude models
- `google-ai` - Google AI Studio / Gemini API
- `fmp` - Financial Modeling Prep (stock data)
- `alpha-vantage` - Stock market data
- `polygon` - Real-time market data
- `firecrawl` - Web scraping API
- `serp` - Google Search results API
- `supabase` - Postgres database with REST API
- `discord` - Discord bot integration
- `github` - GitHub API
- `custom` - Custom connector

## Publishing to PyPI

```bash
cd src

# Build the package
pip install build
python -m build

# Upload to PyPI (requires account)
pip install twine
twine upload dist/*
python -m twine upload --repository testpypi dist/*
```

---

## How to create and run agents

### Command to push agents to db
```python scripts/create_agent_from_yaml.py agent_studio/stock-news-monitor.yaml```

### Command to create agents from db
```python create_agents_from_db.py --agent StockNewsMonitor```

### Command to start agent_runner
adk web --host 0.0.0.0 --port 8000


## How to run db migrations

Common commands (run from repo root)
- Create autogen revision:
    ``` alembic -c src/db/alembic/alembic.ini revision --autogenerate -m "short-msg" ```
- Review/edit generated file: src/db/alembic/versions/<timestamp>_*.py
- Generate SQL for review:
    ``` alembic -c src/db/alembic/alembic.ini upgrade --sql head > /tmp/migration.sql ```
- This lets you scroll up and down through the file. Press q to quit. : 
    ``` cat /tmp/migration.sql ```
- Apply migrations:
    ``` alembic -c src/db/alembic/alembic.ini upgrade head ```
- Inspect state:
-
    ```alembic -c src/db/alembic/alembic.ini current```
-
    ```alembic -c src/db/alembic/alembic.ini heads```
-
    ```alembic -c src/db/alembic/alembic.ini history --verbose```




## NEW Commands

# Step 1: create db

PYTHONPATH=src python src/db/schema.py

# OR

# 1A. Execute from wowbits-ai directory

# 1B. Run Commands in README.md of db/alembic for migration on prod db

# Step 2: YAML → DB

PYTHONPATH=src python src/agentstudio/scripts/create_agent_from_yaml.py \
 src/agentstudio/agent_studio/supermax.yaml

# Step 3: DB → agent.py files

cd src/agent_runner
PYTHONPATH=.. python create_agents_from_db.py

# Step 4: Runtime execution

ENV=production docker-compose up -d --build

ENV=production docker-compose exec wowbits-agent-runner adk web --host 0.0.0.0 --port 8000

# Step 5. Stop

docker-compose down
