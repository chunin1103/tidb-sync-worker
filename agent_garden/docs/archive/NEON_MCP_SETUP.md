# Neon MCP Configuration Guide

This guide explains how to configure the Neon Model Context Protocol (MCP) server for Agent Garden, enabling Claude to directly interact with your Neon PostgreSQL database.

## What is Neon MCP?

The Neon MCP server allows Claude Code to:
- Query your Neon database directly
- Inspect database schema and tables
- Run SQL queries interactively
- Debug database issues in real-time
- Manage chat history data

## Prerequisites

1. **Neon Account**: Sign up at https://console.neon.tech
2. **Database Created**: Set up a PostgreSQL database in Neon
3. **Connection String**: Get your connection string from Neon console
4. **MCP Support**: Ensure you're using Claude Code with MCP support

## Step 1: Install Neon MCP Server

The Neon MCP server is typically installed through Claude Code's MCP server management.

### Option A: Using Claude Code MCP Manager (Recommended)

1. Open Claude Code settings
2. Navigate to MCP Servers section
3. Add new MCP server:
   - **Server Type**: `@modelcontextprotocol/server-postgres`
   - **Name**: `neon-agent-garden`
   - **Configuration**: See below

### Option B: Manual Installation via npm

```bash
npm install -g @modelcontextprotocol/server-postgres
```

## Step 2: Configure MCP Server

Add the following configuration to your Claude Code MCP settings (typically in `.claude/mcp.json` or via settings UI):

```json
{
  "mcpServers": {
    "neon-agent-garden": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://[username]:[password]@[host]/[database]?sslmode=require"
      ],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

**Replace the connection string** with your actual Neon connection string from `.env`.

### Example Configuration

```json
{
  "mcpServers": {
    "neon-agent-garden": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://myuser:mypassword@ep-xxx-xxx.us-east-1.aws.neon.tech/agent_garden?sslmode=require"
      ],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

## Step 3: Verify MCP Connection

After configuration, Claude Code should automatically connect to the MCP server. You can verify by:

1. **Check MCP Server Status**: In Claude Code, look for the Neon MCP server in available tools
2. **Test Query**: Ask Claude to query the database:
   ```
   "Can you show me the chat_sessions table schema?"
   ```
3. **Check Tables**: Ask Claude to list all tables:
   ```
   "What tables exist in the agent_garden database?"
   ```

## Step 4: Initialize Database Tables

If you haven't already created the tables, run the initialization script:

```bash
cd agent_garden_flask
python init_db.py
```

Expected output:
```
✅ Database tables created successfully!

Tables created:
  - chat_sessions (session metadata)
  - chat_messages (conversation history)
```

## Common MCP Commands

Once configured, you can ask Claude to:

### Inspect Schema
```
"Show me the structure of the chat_messages table"
"What indexes exist on chat_sessions?"
```

### Query Data
```
"How many chat sessions are in the database?"
"Show me the last 10 messages from session abc123"
```

### Debug Issues
```
"Are there any sessions without messages?"
"Show sessions older than 30 days"
```

### Manage Data
```
"Delete all sessions older than 90 days"
"Clear test sessions from the database"
```

## Security Best Practices

1. **Read-Only Access** (Recommended for MCP):
   - Create a separate Neon user with read-only permissions
   - Grant SELECT access only
   - Use this read-only connection string in MCP config

   ```sql
   CREATE USER mcp_reader WITH PASSWORD 'secure_password';
   GRANT CONNECT ON DATABASE agent_garden TO mcp_reader;
   GRANT USAGE ON SCHEMA public TO mcp_reader;
   GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_reader;
   ```

2. **Environment Variables**: Never commit connection strings to git
3. **SSL Mode**: Always use `sslmode=require` for Neon connections

## Troubleshooting

### MCP Server Not Connecting

1. **Check Connection String**: Verify format and credentials
2. **Test Direct Connection**: Use `psql` to test connection:
   ```bash
   psql "postgresql://user:pass@host/db?sslmode=require"
   ```
3. **Firewall**: Ensure Neon IP ranges are not blocked
4. **MCP Logs**: Check Claude Code logs for MCP server errors

### Tables Not Found

Run the initialization script:
```bash
python init_db.py
```

### Permission Errors

Ensure the database user has proper permissions:
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
```

## Alternative: Direct Database Access (Without MCP)

If you prefer not to use MCP, you can still:

1. **Use psql**: Connect directly via command line
2. **Use Neon Console**: Web-based SQL editor at console.neon.tech
3. **Use Database GUI**: Tools like DBeaver, TablePlus, pgAdmin

## Next Steps

After MCP configuration:

1. ✅ Test MCP connection with simple queries
2. ✅ Verify tables are accessible
3. ✅ Set up read-only user for security
4. ✅ Run Agent Garden with DATABASE_URL configured
5. ✅ Monitor database usage in Neon console

## Resources

- **Neon Documentation**: https://neon.tech/docs
- **Neon Console**: https://console.neon.tech
- **MCP Protocol**: https://modelcontextprotocol.io
- **PostgreSQL Docs**: https://www.postgresql.org/docs

---

**Need Help?**

If you encounter issues:
1. Check Neon status page: https://neonstatus.com
2. Review Neon logs in console
3. Verify connection string format
4. Ensure database is not paused (Neon auto-pauses after inactivity)
