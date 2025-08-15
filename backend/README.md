# Backend Database Monitoring Guide

This guide provides comprehensive instructions for monitoring database queries and managing database connections using both command-line tools and DBeaver.

## 📋 Table of Contents
- [Database Connection Setup](#database-connection-setup)
- [Command-Line Monitoring](#command-line-monitoring)
- [DBeaver Monitoring Setup](#dbeaver-monitoring-setup)
- [Monitoring Queries](#monitoring-queries)
- [Database Agent Tools](#database-agent-tools)
- [Troubleshooting](#troubleshooting)

## 🔌 Database Connection Setup

### Environment Variables
The backend uses the following environment variables for database connection:
```bash
DB_HOST=localhost
DB_PORT=5433
DB_NAME=testdb
DB_USER=testuser
DB_PASSWORD=testpass
```

### Docker Compose Configuration
The database runs in Docker with the following configuration:
- **Host Port**: 5433 (mapped to container port 5432)
- **Database**: testdb
- **User**: testuser
- **Password**: testpass

## 💻 Command-Line Monitoring

### 1. Check All Active Queries
```bash
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost', 
    port='5433', 
    database='testdb', 
    user='testuser', 
    password='testpass'
)
cur = conn.cursor()
cur.execute('SELECT pid, state, query, query_start, backend_start FROM pg_stat_activity WHERE state = %s', ('active',))
results = cur.fetchall()
for row in results:
    print(f'PID: {row[0]}, State: {row[1]}, Started: {row[3]}, Query: {row[2][:100]}...')
cur.close()
conn.close()
"
```

### 2. Check Long-Running Queries
```bash
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost', 
    port='5433', 
    database='testdb', 
    user='testuser', 
    password='testpass'
)
cur = conn.cursor()
cur.execute('SELECT pid, state, query, query_start, now() - query_start as duration FROM pg_stat_activity WHERE state = %s AND query_start < now() - interval %s', ('active', '1 minute'))
results = cur.fetchall()
for row in results:
    print(f'PID: {row[0]}, Duration: {row[4]}, Query: {row[2][:100]}...')
cur.close()
conn.close()
"
```

### 3. Check Specific pg_sleep Queries
```bash
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost', 
    port='5433', 
    database='testdb', 
    user='testuser', 
    password='testpass'
)
cur = conn.cursor()
cur.execute('SELECT pid, state, query, query_start FROM pg_stat_activity WHERE query ILIKE %s AND state = %s', ('%pg_sleep%', 'active'))
results = cur.fetchall()
for row in results:
    print(f'PID: {row[0]}, State: {row[1]}, Started: {row[3]}, Query: {row[2]}')
cur.close()
conn.close()
"
```

### 4. Check Connection Count
```bash
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost', 
    port='5433', 
    database='testdb', 
    user='testuser', 
    password='testpass'
)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) as active_connections, MAX(backend_start) as latest_connection FROM pg_stat_activity WHERE state = %s', ('active',))
result = cur.fetchone()
print(f'Active connections: {result[0]}, Latest: {result[1]}')
cur.close()
conn.close()
"
```

### 5. Run Database Agent Directly
```bash
cd backend
python3 -c "
from agents.database_agent import execute_database_monitoring
result = execute_database_monitoring()
print('Database Monitoring Result:')
print(result['result'])
"
```

## 🖥️ DBeaver Monitoring Setup

### Step 1: Connect to Your Database
1. Open DBeaver
2. Click **"New Database Connection"** (plug icon)
3. Select **PostgreSQL**
4. Enter connection details:
   - **Host**: `localhost`
   - **Port**: `5433`
   - **Database**: `testdb`
   - **Username**: `testuser`
   - **Password**: `testpass`
5. Click **"Test Connection"** to verify
6. Click **"Finish"**

### Step 2: Open SQL Editor
1. Right-click on your database connection
2. Select **"SQL Editor"** → **"New SQL Script"**
3. Or use the shortcut: `Ctrl+Shift+N` (Windows/Linux) or `Cmd+Shift+N` (Mac)

### Step 3: Set Up Auto-Refresh (Optional)
1. In the SQL Editor, click the **"Auto-refresh"** button (🔄 icon)
2. Set refresh interval (e.g., every 5 seconds)
3. This will automatically update the results

### Step 4: Create a Dashboard View
1. Create multiple SQL tabs
2. Run different monitoring queries in each tab
3. Arrange them side by side for comprehensive monitoring

## 📊 Monitoring Queries

### Query 1: View All Active Queries
```sql
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    backend_start,
    query,
    wait_event_type,
    wait_event
FROM pg_stat_activity 
WHERE state = 'active'
ORDER BY query_start;
```

### Query 2: View Long-Running Queries
```sql
SELECT 
    pid,
    usename,
    application_name,
    state,
    query_start,
    now() - query_start as duration,
    query
FROM pg_stat_activity 
WHERE state = 'active' 
    AND query_start < now() - interval '1 minute'
ORDER BY duration DESC;
```

### Query 3: View Specific pg_sleep Queries
```sql
SELECT 
    pid,
    usename,
    state,
    query_start,
    now() - query_start as duration,
    query
FROM pg_stat_activity 
WHERE query ILIKE '%pg_sleep%' 
    AND state = 'active';
```

### Query 4: View Connection Statistics
```sql
SELECT 
    COUNT(*) as total_connections,
    COUNT(*) FILTER (WHERE state = 'active') as active_queries,
    COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
    MAX(backend_start) as latest_connection
FROM pg_stat_activity;
```

## 🤖 Database Agent Tools

The backend includes several database monitoring tools:

### Available Tools
- **QueryStatusTool**: Check the status of running database queries
- **QueryKillerTool**: Terminate running queries using process ID
- **ConnectionInfoTool**: Get database connection information and statistics
- **WeatherTool**: Testing tool (unrelated to database monitoring)

### Tool Usage
```python
from agents.database_agent import execute_database_monitoring

# Execute database monitoring
result = execute_database_monitoring()
print(result['result'])
```

## 🧪 Testing Long-Running Queries

### Start a Long Query
```bash
python3 backend/long_query.py
```

This will:
1. Create a test table if it doesn't exist
2. Insert test data if the table is empty
3. Execute a long-running query with `pg_sleep(300)` (5 minutes)

### Monitor the Query
Use any of the monitoring methods above to watch the query execution in real-time.

## 💡 Pro Tips

### Real-time Monitoring
- Use **"Auto-refresh"** in DBeaver for live updates
- Set refresh interval to 5-10 seconds for active monitoring
- Monitor multiple aspects simultaneously using multiple SQL tabs

### Query Results Formatting
- Right-click on results → **"Format"** for better readability
- Use **"Export"** to save results as CSV/Excel
- Save frequently used monitoring queries as **"Saved Scripts"**

### Performance Monitoring
- Focus on queries with long duration
- Monitor connection counts to prevent connection pool exhaustion
- Use the database agent tools for automated monitoring

## 🔧 Troubleshooting

### Common Issues

#### Connection Refused
- Ensure Docker container is running: `docker-compose ps`
- Check port mapping: should be `5433:5432`
- Verify database credentials

#### Permission Denied
- Check user privileges in the database
- Ensure `testuser` has proper permissions on `testdb`

#### Query Not Showing
- Verify the query is actually running
- Check if the query is in a different state (e.g., 'idle')
- Use broader monitoring queries to see all connections

### Debug Commands
```bash
# Check Docker container status
docker-compose ps

# View container logs
docker-compose logs postgres

# Check if port is listening
lsof -i :5433

# Test database connection
python3 -c "import psycopg2; print('Connection successful')" 2>/dev/null && echo "✅ Connected" || echo "❌ Connection failed"
```

## 📚 Additional Resources

- [PostgreSQL pg_stat_activity Documentation](https://www.postgresql.org/docs/current/monitoring-stats.html)
- [DBeaver User Guide](https://dbeaver.io/docs/)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)

---

**Note**: This monitoring setup is designed for development and testing environments. For production use, consider implementing proper logging, alerting, and security measures.
