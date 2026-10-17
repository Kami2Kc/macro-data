# Macro Data

## About this repo

This is basically a quick learning project around macro data. I wanted to try building a small pipeline to pull macro data, store it in Postgres, and then hook it up to an MCP server so Claude (or another MCP client) can ask questions about it.

## How to run

1. Create a Postgres database locally.

2. Create a `.env` file from `.env.example` and fill in the values.

   ```bash
   cp .env.example .env
   ```

3. Install deps:

   ```bash
   uv sync
   ```

4. Create the main tables:

   ```bash
   psql "$DATABASE_URL" -f schema.sql
   ```

5. Create the read-only user (optional).

   Note: `reader.sql` currently assumes the database is called `macro`.

   ```bash
   psql "$DATABASE_URL" -f reader.sql
   ```

6. Load the macro data:

   ```bash
   ./.venv/bin/python load.py
   ```

7. Create the indicator views:

   ```bash
   psql "$DATABASE_URL" -f indicators.sql
   ```

8. Run the quick checks if you want:

   ```bash
   psql "$DATABASE_URL" -f checks.sql
   ```

## Adding MCP server to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` and add something like:

```json
"mcpServers": {
  "macro-data": {
    "command": "uv",
    "args": [
      "--directory",
      "/absolute/path/to/macro-data",
      "run",
      "server.py"
    ]
  }
}
```

If `uv` is not on your PATH in Claude Desktop, use the full path to the `uv` binary instead.

After that Claude Desktop should be able to start the MCP server and use the tools.

## Files

### `schema.sql`

Sets up the database tables in Postgres.

### `reader.sql`

Creates a read-only database user for the MCP client.

### `checks.sql`

Some quick SQL checks for basic data quality / freshness stuff.

### `indicators.sql`

Creates a couple of views for commonly used derived indicators.

### `server.py`

This is the MCP server. It runs locally and exposes a few read-only tools for listing series, pulling raw observations, and getting monthly averages from the database.

### `load.py`

Defines the initial 5 series to load, calls the FRED API, and upserts the observations into Postgres.
