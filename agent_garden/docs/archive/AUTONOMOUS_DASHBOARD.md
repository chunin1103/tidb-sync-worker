# Autonomous Agents Dashboard

Complete dashboard for monitoring and managing autonomous agents in Agent Garden.

**Version:** 2.2.0
**Date:** December 22, 2025

---

## Features

### 1. **Scheduled Tasks Management**
- View all 3 scheduled autonomous agents
- See schedule for each task (Daily, Every 6 hours, Weekly)
- **Trigger tasks manually** with one click
- Real-time task status updates

### 2. **Recent Agent Runs**
- Live feed of all agent executions
- Status badges (Completed, Running, Failed)
- Execution duration and timestamps
- Trigger information (cron, manual, event)
- Output summaries

### 3. **Generated Reports**
- View all AI-generated reports
- Unread indicators (NEW badge + neon green border)
- Report previews
- Click to mark as read
- Different icons for report types:
  - 🌅 Morning Intelligence
  - 🔍 Health Check
  - 📊 Weekly Summary

### 4. **Auto-Refresh**
- Dashboard refreshes every 10 seconds
- Manual refresh buttons available
- Real-time data updates

---

## UI Design

### Glassmorphism Theme
- Frosted glass cards with blur effects
- Neon green accents (#00ff9d)
- Dark gradient background
- Smooth animations and transitions
- Responsive design (mobile-friendly)

### Layout
```
┌────────────────────────────────────────────────────────┐
│  ← BACK    🤖 Autonomous Agents                        │
│            Monitor scheduled tasks and reports         │
├─────────────────────┬──────────────────────────────────┤
│  ⏰ SCHEDULED TASKS │  📄 GENERATED REPORTS            │
│  - Morning Report   │  - Morning Intelligence Report   │
│  - Health Check     │  - Health Check - 04:31 PM       │
│  - Weekly Summary   │  - Weekly Summary - Week of...   │
│                     │                                  │
│  📈 RECENT RUNS     │  (scrollable list)              │
│  - INVENTORY...     │                                  │
│  - Status: ✅       │                                  │
│  - Duration: 5.7s   │                                  │
│  (scrollable list)  │                                  │
└─────────────────────┴──────────────────────────────────┘
```

---

## How to Access

### Method 1: From Main Page
1. Click on "Autonomous Agents" card
2. Click "OPEN DASHBOARD" button

### Method 2: Direct URL
```
http://localhost:5001/#autonomous-dashboard
```

---

## Scheduled Tasks

### 1. Morning Intelligence Report
- **Schedule:** Daily at 7:00 AM
- **Purpose:** Comprehensive morning briefing with critical alerts
- **Content:**
  - Products needing immediate attention
  - Today's priorities
  - Inventory health summary
  - Upcoming deadlines

### 2. Inventory Health Check
- **Schedule:** Every 6 hours
- **Purpose:** Quick check for critical issues
- **Content:**
  - Zero inventory alerts
  - Products below 30-day threshold
  - Unusual sales spikes

### 3. Weekly Summary Report
- **Schedule:** Monday at 8:00 AM
- **Purpose:** Week-over-week analysis and planning
- **Content:**
  - Last week recap
  - This week priorities
  - Upcoming events

---

## Manual Task Triggering

### How to Trigger
1. Open dashboard
2. Find task in "Scheduled Tasks" section
3. Click "TRIGGER NOW" button
4. Button changes to "TRIGGERING..."
5. Changes to "✓ TRIGGERED" when complete
6. View result in "Recent Runs" section

### Button States
- **Normal:** Green outline, "TRIGGER NOW"
- **Triggering:** Disabled, "TRIGGERING..."
- **Success:** Green filled, "✓ TRIGGERED"
- **Error:** Red, "ERROR"

---

## Agent Runs Display

### Information Shown
```
🤖 INVENTORY INTELLIGENCE
3m ago • 5.7s                          COMPLETED

To perform an inventory health check, I need current
inventory data...

📅 interval:6_hours
```

### Status Colors
- **COMPLETED:** Green (#00ff9d)
- **RUNNING:** Blue (#00b8ff)
- **FAILED:** Red (#ff6b9d)

---

## Reports Display

### Unread Reports
- Highlighted with neon green left border
- "NEW" badge in top right
- More prominent styling

### Reading Reports
- Click any report to mark as read
- "NEW" badge disappears
- Border color fades to normal
- Reports auto-refresh after 500ms

---

## API Integration

### Endpoints Used
```javascript
// Get recent agent runs
GET /get_agent_runs?limit=20

// Get agent reports
GET /get_agent_reports?limit=10

// Mark report as read
POST /mark_report_read/<report_id>

// Trigger task manually
POST /trigger_agent_task
{
  "task_name": "morning_intelligence_report"
}

// Check task status
GET /get_task_status/<task_id>
```

---

## Responsive Design

### Desktop (>1024px)
- Two-column layout
- Full feature visibility
- Larger cards and text

### Tablet (768px - 1024px)
- Single column layout
- Stacked cards
- Same functionality

### Mobile (<768px)
- Single column
- Compressed header
- Full-width trigger buttons
- Touch-optimized

---

## Keyboard Shortcuts

- **Esc:** Close dashboard, return to main
- **R:** Refresh agent runs
- **T:** Refresh reports

*(To be implemented)*

---

## Performance

### Loading Times
- Initial load: <500ms
- Refresh cycle: <200ms
- Manual trigger: 2-5 seconds
- Report marking: <100ms

### Auto-Refresh
- Interval: 10 seconds
- Pauses when dashboard closed
- Resumes on reopening

---

## Troubleshooting

### "No agent runs yet"
**Issue:** Empty runs list
**Solution:**
- Wait for scheduled task to run
- OR click "TRIGGER NOW" on any task
- Runs appear within 5-10 seconds

### "Failed to load agent runs"
**Issue:** API error
**Solution:**
- Check Flask server is running (port 5001)
- Check Celery worker is running
- Verify database connection
- Check browser console for errors

### Task trigger not working
**Issue:** Button says "ERROR"
**Solution:**
- Ensure Celery worker is active
- Check Celery Beat scheduler is running
- Verify Redis connection (Upstash)
- Check `/get_agent_runs` endpoint manually

### Reports not showing
**Issue:** Empty reports list
**Solution:**
- Reports only appear after tasks complete
- Trigger a task and wait 5-10 seconds
- Check database has reports table
- Verify `/get_agent_reports` endpoint

---

## Code Structure

### HTML Components
```html
<!-- Dashboard Container -->
<div class="autonomous-dashboard" id="autonomousDashboard">
  <div class="dashboard-container">
    <!-- Header with back button -->
    <div class="dashboard-header">...</div>

    <!-- Two-column grid -->
    <div class="dashboard-grid">
      <!-- Left: Tasks & Runs -->
      <div class="dashboard-column">
        <div class="dashboard-card">
          <!-- Scheduled tasks -->
        </div>
        <div class="dashboard-card">
          <!-- Recent runs -->
        </div>
      </div>

      <!-- Right: Reports -->
      <div class="dashboard-column">
        <div class="dashboard-card full-height">
          <!-- Reports list -->
        </div>
      </div>
    </div>
  </div>
</div>
```

### JavaScript Functions
```javascript
// Dashboard control
openAutonomousDashboard()
closeAutonomousDashboard()
startDashboardRefresh()
stopDashboardRefresh()

// Data loading
loadAutonomousDashboard()
loadAgentRuns()
loadAgentReports()

// User actions
triggerTask(taskName)
viewReport(reportId)

// Utilities
formatTimeAgo(timestamp)
```

---

## CSS Classes

### Container Classes
- `.autonomous-dashboard` - Main container
- `.dashboard-container` - Content wrapper
- `.dashboard-grid` - Two-column layout
- `.dashboard-card` - Glass card

### Component Classes
- `.task-card` - Scheduled task item
- `.run-item` - Agent run display
- `.report-item` - Report display
- `.task-trigger-btn` - Trigger button

### State Classes
- `.active` - Dashboard visible
- `.unread` - Unread report
- `.disabled` - Disabled button

---

## Future Enhancements

### Planned Features
- [ ] Export all reports as ZIP
- [ ] Filter runs by status/date
- [ ] Search reports by keyword
- [ ] Task execution logs viewer
- [ ] Real-time WebSocket updates
- [ ] Email notifications toggle
- [ ] Custom schedule editor
- [ ] Multi-select report actions
- [ ] Report templates
- [ ] Agent performance metrics

### UI Improvements
- [ ] Dark/Light theme toggle
- [ ] Customizable dashboard layout
- [ ] Drag-and-drop card ordering
- [ ] Collapsible sections
- [ ] Full-screen report viewer
- [ ] Keyboard shortcuts panel

---

## Testing Checklist

- [x] Dashboard opens from main page
- [x] Back button returns to main
- [x] All 3 scheduled tasks display
- [x] Trigger buttons work
- [x] Agent runs load correctly
- [x] Reports load correctly
- [x] Unread badges show
- [x] Mark as read works
- [x] Auto-refresh works
- [x] Manual refresh works
- [x] Responsive on mobile
- [x] Glassmorphism effects render
- [x] Animations smooth
- [x] Status colors correct

---

## Technical Specs

### Dependencies
- **Frontend:** Vanilla JavaScript (ES6+)
- **Backend:** Flask (Python)
- **Database:** Neon PostgreSQL
- **Task Queue:** Celery + Redis (Upstash)
- **Icons:** Unicode emoji
- **Fonts:** Inter (Google Fonts)

### Browser Support
- Chrome/Edge: ✅ (recommended)
- Firefox: ✅
- Safari: ✅
- Mobile browsers: ✅

---

## Version History

### v2.2.0 (Dec 22, 2025)
- ✨ Initial release of Autonomous Dashboard
- Added scheduled tasks display
- Added recent runs feed
- Added generated reports view
- Implemented manual task triggering
- Added auto-refresh (10s interval)
- Responsive design for all devices

---

## Support

### Need Help?
- Check `CELERY_SETUP_GUIDE.md` for Celery configuration
- Check `CELERY_TEST_RESULTS.md` for testing info
- View Flask logs for errors
- Check Celery worker logs

### Contributing
Found a bug or have a feature request?
Open an issue in the repository!

---

**Built for ArtGlassSupplies.com | Agent Garden v2.2.0**
