# 🔧 Dependency Fix - pymysql Missing

## ❌ The Problem

When running Celery, you encountered:
```
ModuleNotFoundError: No module named 'pymysql'
```

## 🔍 Root Cause

Your project uses a virtual environment at `/Users/vusmac/Desktop/AGS_LAB/.venv`, but `pymysql` was only installed globally (in pyenv), not in the venv.

## ✅ The Fix

Installed `pymysql` in the correct virtual environment:

```bash
source /Users/vusmac/Desktop/AGS_LAB/.venv/bin/activate
pip install pymysql
```

Also verified all other dependencies from `requirements.txt` are installed.

## 🎯 How to Prevent This

### Always Use Virtual Environment

**Before running any commands:**
```bash
# Activate venv first
source /Users/vusmac/Desktop/AGS_LAB/.venv/bin/activate

# Then run your commands
python app.py
celery -A celery_app worker
```

### Install All Dependencies

After activating venv:
```bash
pip install -r requirements.txt
```

This ensures all dependencies (`pymysql`, `redis`, `flask`, etc.) are installed in the venv.

## 📊 Verification

Test that everything loads:
```bash
source /Users/vusmac/Desktop/AGS_LAB/.venv/bin/activate
python -c "import celery_app; print('✅ Success!')"
```

Output:
```
✅ Celery app loaded successfully!
INFO:tidb_connector:✅ TiDB Connector initialized
INFO:agent_database_context_optimized:✅ Redis cache enabled
INFO:schedule_loader:Successfully loaded 3 schedules
```

## 🚀 Now You Can Run

### Start Flask App:
```bash
source /Users/vusmac/Desktop/AGS_LAB/.venv/bin/activate
python app.py
# or with MCP
python run_with_mcp.py
```

### Start Celery Worker:
```bash
source /Users/vusmac/Desktop/AGS_LAB/.venv/bin/activate
celery -A celery_app worker -Q agent_tasks --loglevel=info
```

### Start Celery Beat:
```bash
source /Users/vusmac/Desktop/AGS_LAB/.venv/bin/activate
celery -A celery_app beat --loglevel=info
```

## 💡 Pro Tip

Add a script to activate venv automatically:

**`run.sh`:**
```bash
#!/bin/bash
source /Users/vusmac/Desktop/AGS_LAB/.venv/bin/activate
python app.py
```

Then just run:
```bash
chmod +x run.sh
./run.sh
```

---

**✅ Issue resolved! All dependencies are now properly installed in the virtual environment.**
