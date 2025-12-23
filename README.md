# TiDB Sync Worker

Automated daily sync from IDrive e2 backups to TiDB Cloud.

## What It Does

- Runs **twice daily** (6 AM and 6 PM UTC)
- Syncs **Categories/Products** (~5.5 MB, ~2-3 min)
- Syncs **Orders/Customers** (~112 MB, ~15-20 min)
- Auto-detects latest backup file
- Applies all MySQL→TiDB compatibility fixes

## Deployment to Render

### Option 1: Blueprint (Recommended)

1. Push this folder to a GitHub repository
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New** → **Blueprint**
4. Connect your GitHub repo
5. Render will read `render.yaml` and create the cron job
6. Set the secret environment variables (see below)

### Option 2: Manual Setup

1. Push this folder to a GitHub repository
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New** → **Cron Job**
4. Connect your GitHub repo
5. Configure:
   - **Name:** tidb-sync-worker
   - **Runtime:** Docker
   - **Dockerfile Path:** ./Dockerfile
   - **Schedule:** `0 6,18 * * *`
6. Add environment variables (see below)
7. Click **Create Cron Job**

## Environment Variables

Set these in the Render dashboard:

| Variable | Value |
|----------|-------|
| `TIDB_HOST` | gateway01.ap-southeast-1.prod.aws.tidbcloud.com |
| `TIDB_PORT` | 4000 |
| `TIDB_USER` | 3oTjjLfAngfGpch.root |
| `TIDB_PASSWORD` | (your TiDB password) |
| `TIDB_DATABASE` | test |
| `IDRIVE_ACCESS_KEY` | (your IDrive access key) |
| `IDRIVE_SECRET_KEY` | (your IDrive secret key) |
| `IDRIVE_ENDPOINT` | k8j8.or4.idrivee2-57.com |

## Testing

1. In Render dashboard, go to your cron job
2. Click **Trigger Run** to test manually
3. Watch the logs in real-time

## Logs

View logs in the Render dashboard under your cron job → **Logs** tab.

Example output:
```
2025-12-23 06:00:01 [INFO] TiDB Sync Worker Starting
2025-12-23 06:00:01 [INFO] Connecting to TiDB Cloud...
2025-12-23 06:00:02 [INFO] Connected successfully!
2025-12-23 06:00:02 [INFO] Finding latest backup in dbdaily/db/categories-products/...
2025-12-23 06:00:03 [INFO] Latest backup: 2025-12-23-05-00-01_suppliesart1_maindb_categories-products.sql.gz
...
2025-12-23 06:25:00 [INFO] SYNC COMPLETE
2025-12-23 06:25:00 [INFO] Duration: 1499.2 seconds (25.0 minutes)
```

## Cost

- ~25 min/run × 2 runs/day × 30 days = **25 hours/month**
- Render Starter tier: **~$1-2/month**
