# Gradio App Daemon Management

## Current Status

✅ **Gradio app is running in daemon mode**
- Process ID: 32498
- URL: http://localhost:7860
- Log file: `gradio_app.log`

## Managing the Daemon

### Check if the app is running
```bash
ps aux | grep "[p]ython -m qa_chatbot.main"
```

### View logs
```bash
# View entire log
cat gradio_app.log

# Follow log in real-time
tail -f gradio_app.log

# View last 20 lines
tail -20 gradio_app.log
```

### Stop the daemon
```bash
# Using the PID
kill 32498

# Or find and kill all instances
pkill -f "python -m qa_chatbot.main"
```

### Restart the daemon
```bash
# Stop existing
kill 32498

# Start fresh
cd /Users/ondra/Documents/Projects/xm.nosync/xm-qa-chatbot
nohup python -m qa_chatbot.main > gradio_app.log 2>&1 &
echo $!  # This shows the new PID
```

### Check if the app is responding
```bash
curl -s http://localhost:7860 > /dev/null && echo "✅ App is responding" || echo "❌ App is not responding"
```

## API Submission Results

### Submission via Gradio API (2026-02-08)

**Successfully submitted:**
- Project: Client Trading (client_journey stream)
- Period: 2026-01
- Manual Total: 1000
- Manual Created: 100
- Manual Updated: 120
- Automated: 0 (all fields)

**Verification:**
```bash
sqlite3 qa_chatbot.db "SELECT project_id, month, test_coverage FROM submissions WHERE project_id = 'client_trading';"
```

**Output:**
```
client_trading|2026-01|1000|100|120
```

## Workflow Summary

1. **Initialize Database**
   ```bash
   rm -f qa_chatbot.db
   python -c "from qa_chatbot.adapters.output import SQLiteAdapter; adapter = SQLiteAdapter('sqlite:///./qa_chatbot.db', echo=False); adapter.initialize_schema()"
   ```

2. **Start Daemon**
   ```bash
   nohup python -m qa_chatbot.main > gradio_app.log 2>&1 &
   echo $!
   ```

3. **Wait for Startup**
   ```bash
   sleep 6
   curl -s http://localhost:7860 > /dev/null && echo "Ready"
   ```

4. **Submit Data via API**
   ```bash
   python scripts/submit_via_api.py
   ```

5. **Verify Submission**
   ```bash
   sqlite3 qa_chatbot.db "SELECT * FROM submissions;"
   ```

## Important Notes

- The daemon continues running in the background until explicitly stopped
- Logs are written to `gradio_app.log` and will grow over time
- To rotate logs, stop the daemon, rename/archive the log file, and restart
- The database must have the correct schema (with `project_id` column, not `team_id`)
- Always verify the database schema before running API submissions

## Troubleshooting

### App won't start
```bash
# Check for errors in log
tail -50 gradio_app.log

# Check if port 7860 is already in use
lsof -i :7860
```

### API submission fails
```bash
# Check database schema
sqlite3 qa_chatbot.db ".schema submissions"

# Verify columns include: project_id, month, test_coverage
# NOT: team_id (old schema)

# If schema is wrong, recreate database
rm -f qa_chatbot.db
python -c "from qa_chatbot.adapters.output import SQLiteAdapter; adapter = SQLiteAdapter('sqlite:///./qa_chatbot.db', echo=False); adapter.initialize_schema()"
```

### Session state issues
The Gradio Client API has limitations with session state management. If you encounter issues:
- Use `scripts/submit_data_direct.py` instead (bypasses Gradio entirely)
- Restart the Gradio daemon to clear any cached state
