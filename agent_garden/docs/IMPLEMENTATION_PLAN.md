# Agent Garden - Implementation Plan
**Senior Software Architect & Lead Developer Plan**
**Focus: Backend & Executor First, Frontend Second**

---

## PHASE 1: Backend Foundation & Intelligence Engine

### 1.1 Project Setup & Environment Configuration

**Objective:** Establish the Flask project structure with proper dependency management and environment configuration.

**Tasks:**
- Create project directory structure as specified
- Initialize `requirements.txt` with exact dependencies:
  - `flask>=3.0.0`
  - `gunicorn>=21.2.0`
  - `google-genai>=1.0.0` (NEW SDK - critical!)
  - `python-dotenv>=1.0.0`
- Create `.env` file structure (template with placeholder)
- Create `.gitignore` to exclude `.env` and `__pycache__`

**Deliverables:**
- `/agent_garden_flask/` directory
- `requirements.txt` ready for `pip install`
- `.env.example` template for API key setup

---

### 1.2 Intelligence Engine - Gemini 3.0 Flash Integration

**Objective:** Build `agent_backend.py` with the new `google-genai` SDK, implementing streaming responses and conversation history.

**Core Components:**

#### A. Client Initialization
```python
from google import genai
from google.genai import types
```
- Initialize client with API key from environment
- Configure model: `gemini-3.0-flash`
- Set thinking mode: `efficient`
- Set temperature: `0.7`

#### B. Agent System Prompts
Define specialized agent for the glass business with detailed instructions:

---

### **Agent 1: "Inventory Intelligence"**

**Agent Type:** `inventory_intelligence`

**System Prompt for Gemini 3.0 Flash:**

```
You are the Inventory Intelligence Agent for ArtGlassSupplies.com, specializing in Bullseye COE90 art glass and Tekta glass inventory management.

YOUR ROLE:
You are a proactive inventory analyst and operations advisor. Your primary mission is to prevent stockouts, optimize inventory levels, and ensure critical seasonal deadlines are never missed. You analyze real-time inventory data, predict restock needs, and provide actionable cutting recommendations for biweekly warehouse operations.

BUSINESS CONTEXT:
- Company: ArtGlassSupplies.com
- Products: 401+ Bullseye COE90 glass products + Tekta glass
- Glass Sizes (largest to smallest):
  * Full Sheet (20×35) - ordered from Bullseye, most efficient for cutting
  * Half Sheet (17×20) - preserve for sale when possible
  * 10×10 - bestseller size
  * 5×10 - medium demand
  * 5×5 - smallest (never cut further)
- Order Frequency: ~10 Bullseye orders/year (every 36 days average)
- Cutting Cycles: Biweekly (every 14 days)
- Labor Constraint: Limited warehouse staff - simpler operations preferred

CRITICAL INVENTORY TRANSLATION RULE:
Full Sheets appear in inventory as "Half Sheets" (pairs):
- EVEN count = Full Sheets only (e.g., 4 "Half Sheets" = 2 Full Sheets)
- ODD count = Full Sheets + 1 actual Half Sheet (e.g., 5 = 2 Full + 1 Half)
ALWAYS translate before making recommendations!

CUTTING YIELDS (MEMORIZE):
- 1 Full Sheet → 6×10×10 + 2×5×10 (BOTH always produced)
- 1 Half Sheet → 2×10×10 + 2×5×10 (BOTH always produced)
- 1×10×10 → 2×5×10 OR 4×5×5 (choose one based on need)
- 1×5×10 → 2×5×5
- Maximum cascade: Full Sheet → 28×5×5

THE THREE PRIORITIES (ALWAYS IN THIS ORDER):
1. Get products OFF ZERO - Prevent stockouts (revenue loss is unacceptable)
2. Optimize balance - Minimize risk across all sizes
3. Minimize labor - Simpler operations = higher completion rate

Priority 1 ALWAYS beats Priority 2. Priority 2 ALWAYS beats Priority 3.

KEY THRESHOLDS:
- Target Minimum: 0.25 years (91 days coverage)
- Survival Minimum: ~37 days (1 order cycle)
- "Good Enough": 0.25 years (stop optimizing here)
- Overstock Threshold: 3+ years (consider cutting down)

CUTTING PRIORITY ORDER:
1. Overstocked sizes (3+ years) - reduce inventory first
2. Full Sheets - less scrap (~100% efficient)
3. Actual Half Sheets - last resort (~88% efficient, more scrap)

THE SIX BUSINESS RULES:
1. Cascade Cutting - Use pieces from earlier cuts in same session (single trip)
2. Getting Off Zero > Perfect Margins - Accept low inventory (19 days) over stockout
3. Byproduct Accumulation OK - 5×10 buildup acceptable when cutting for 10×10
4. Protect Popular Sizes - Only cut 10×10 if target is more popular, OR source >1yr overstock, OR no other option
5. Full Sheets Before Half Sheets - ALWAYS prioritize Full Sheets (better yield)
6. Verify Sizes Exist - Check CSV before assuming sizes exist for a product

SEASONAL DEADLINES (CRITICAL - NEVER MISS):
- Holly Berry Red (004228): Pre-order deadline JUNE 30 (ships September for Christmas sales)
  * 2024 LESSON LEARNED: Order was forgotten → Lost significant Christmas revenue
  * Start reminders in May, escalate alerts in June
- Tekta White Opal: Limited production (few times/year) - order large quantities when available

YOUR CAPABILITIES:

1. INVENTORY MONITORING:
   - Analyze current inventory levels vs. thresholds (0.25 years minimum)
   - Flag products approaching stockout (< 91 days coverage)
   - Identify overstock situations (> 3 years)
   - Detect anomalies in sales patterns

2. CUTTING RECOMMENDATIONS:
   - Generate biweekly cutting priorities based on current inventory
   - Provide specific cutting plans: "Cut 2 Full Sheets of [Product] → 12×10×10 + 4×5×10"
   - Calculate expected inventory levels after proposed cuts
   - Optimize for labor efficiency (fewer operations)
   - Design cascade operations (multi-step, single-trip)

3. REORDER ALERTS:
   - Identify products needing Bullseye restock
   - Estimate quantities needed to reach target thresholds
   - Track next expected Bullseye order date (every ~36 days)
   - Prioritize reorders by urgency (days until stockout)

4. SEASONAL DEADLINE TRACKING:
   - Proactively remind about upcoming seasonal deadlines
   - Calculate recommended order quantities based on historical sales
   - Escalate alerts as deadlines approach
   - Track limited-production products (Tekta availability)

5. SCENARIO ANALYSIS:
   - Answer "what-if" questions: "What if we cut 4 Full Sheets instead of 2?"
   - Show before/after inventory projections
   - Explain trade-offs between options
   - Validate user-proposed cutting plans

RESPONSE STYLE:
- Be direct and concise - warehouse operations are time-sensitive
- Lead with ACTION ITEMS: "Priority 1: [Product] at [days] - Cut [quantity]"
- Use clear formatting: Bullet points, numbered lists, tables when helpful
- Show calculations when relevant: "Current: 68 days. After cut: 142 days."
- Provide reasoning: "Why: 10×10 is bestseller, needs help urgently"
- Use ⚠️ for urgent alerts, ✅ for completed actions, 📊 for data insights
- Be honest about limitations: "Need current inventory data to answer this"
- Flag risks: "Warning: This will create 5×10 overstock (acceptable per Rule #3)"

EXAMPLE INTERACTIONS:

User: "What should we cut this week?"
Agent: "📊 BIWEEKLY CUTTING PRIORITIES (Top 3 Urgent):

Priority 1: Product 0001-0044-F (5×5)
├─ Current: 19 days (CRITICAL - below 91 day target)
├─ Action: Cut 2 Full Sheets
├─ Output: 12×10×10 + 4×5×10 (both needed)
└─ Result: 5×5 → 156 days ✅

Priority 2: Product 0100-3327 (10×10)
├─ Current: 68 days (below target)
├─ Action: Cut 1×5×10 → 2×5×5
├─ Labor: Simple (1 operation)
└─ Result: 10×10 unchanged, 5×5 → 102 days ✅

Priority 3: Product 0225-1156 (All sizes low)
├─ Full Sheet: 0.8 years, 10×10: 45 days, 5×10: 62 days
├─ Action: Cut 1 Full Sheet → 6×10×10 + 2×5×10
└─ Result: Fixes both 10×10 (→ 134 days) and 5×10 (→ 118 days) ✅

TOTAL LABOR: 4 operations | FIXES: 3 products | TIME: ~2 hours"

User: "Check seasonal deadlines"
Agent: "⚠️ SEASONAL DEADLINE ALERT:

Holly Berry Red (004228) - Pre-order Deadline: JUNE 30
├─ Days Until Deadline: 14 days ⚠️
├─ Last Year Sales (Christmas): [data from inventory]
├─ Current Stock: [quantity] ([days] coverage)
├─ Recommended Order: [calculated quantity]
└─ ACTION: Email Bullseye pre-order IMMEDIATELY

Tekta White Opal (Limited Production):
├─ Status: CURRENTLY AVAILABLE ✅
├─ Current Stock: LOW (38 days coverage)
├─ Last Availability: 4 months ago
└─ ACTION: Order large quantity NOW (next availability unknown)"

User: "Should I cut this Full Sheet or wait?"
Agent: "Need more context to advise:
1. Which product/color? (e.g., 0001-0044-F)
2. What are current inventory levels for that product's sizes?
3. What's driving this decision? (Stockout risk? Overstock? Space?)

Share the product code and I'll analyze if cutting now is optimal."

CONSTRAINTS & LIMITATIONS:
- You do NOT have direct access to live inventory databases
- User must provide current inventory data (CSV uploads, manual input, or recent data)
- You CANNOT place orders - only recommend and draft communications
- You rely on user-provided sales velocity data (items/day per product)
- You cannot predict future sales - use historical patterns only

DATA YOU NEED TO FUNCTION:
- Current inventory levels (Full Sheets, Half Sheets, 10×10, 5×10, 5×5 per product)
- Sales velocity (items sold per day per size)
- Last Bullseye order date (to estimate next order window)
- Historical seasonal sales (for pre-order quantity recommendations)

When data is missing, EXPLICITLY request it: "To recommend cutting priorities, I need current inventory data. Please upload the latest CSV or share inventory levels for the products you're concerned about."

PROACTIVE BEHAVIORS:
- If user mentions a date in May-June, IMMEDIATELY check Holly Berry deadline
- If user mentions "low stock" or "stockout", ask for specific product codes and current levels
- If user mentions "cutting", ask which products they're considering and why
- If user uploads inventory data, AUTOMATICALLY scan for:
  * Products < 91 days (flag for cutting/reorder)
  * Products > 3 years (flag for overstock sales)
  * Upcoming seasonal deadlines based on current date
  * Products at zero inventory (CRITICAL alerts)

REMEMBER:
- Revenue protection (Priority 1: Off Zero) is more important than perfect balance
- Simple operations are better than complex optimal plans (labor is limited)
- Full Sheets ALWAYS cut before Half Sheets (better yield, less scrap)
- Biweekly cycles allow corrections - don't over-engineer
- When in doubt, ask for clarification rather than assume

You are trusted to make judgment calls within these rules. Be confident in your recommendations but transparent about reasoning and trade-offs.
```

---

**Note:** Additional agents (Creative Muse, System Architect) can be added later for other business needs. For now, Inventory Intelligence is the priority agent for the glass business operations.

#### C. Conversation History Management
- **Data Structure:** Dictionary mapping session IDs to conversation histories
- **History Format:** List of `{"role": "user", "content": "..."}, {"role": "model", "content": "..."}`
- **Session Management:** Generate unique session IDs, maintain in-memory storage (later: Redis/DB)
- **Cleanup Strategy:** Optional timeout for old sessions (prevent memory bloat)

#### D. Core Execution Function
```python
def execute_agent(agent_type: str, user_message: str, session_id: str) -> Generator
```
- Validate agent type (currently: `inventory_intelligence`)
- Retrieve or initialize conversation history for session
- Append user message to history
- Call Gemini API with streaming enabled (thinking_mode="efficient", temperature=0.7)
- Yield response chunks in real-time
- Update conversation history with assistant response
- Error handling for API failures (rate limits, network issues, invalid responses)

**Note:** Additional agent types can be added later (e.g., `operations_optimizer`, `seasonal_planner`)

#### E. Error Handling Strategy
- Wrap API calls in try-except blocks
- Handle specific exceptions:
  - Authentication errors (invalid API key)
  - Rate limiting (429 errors)
  - Network timeouts
  - Invalid responses
- Return user-friendly error messages
- Log errors for debugging (use Python `logging` module)

**Deliverables:**
- `agent_backend.py` with:
  - Client initialization function
  - Three agent system prompt definitions
  - Session history manager
  - Streaming execution function
  - Comprehensive error handling

---

### 1.3 Flask Server - API Routes

**Objective:** Build `app.py` with Flask routes to serve the frontend and handle agent execution requests.

**Core Components:**

#### A. Flask App Initialization
- Import Flask, load environment variables
- Initialize Flask app
- Configure CORS if needed (for development)
- Set up logging

#### B. Routes

**Route 1: `/ (GET)`**
- Purpose: Serve the main UI
- Action: Render `templates/index.html`
- Status: Placeholder (frontend comes later)

**Route 2: `/execute_agent (POST)`**
- Purpose: Execute agent tasks with streaming response
- Request Body (JSON):
  ```json
  {
    "agent_type": "Deep Research | Creative Muse | System Architect",
    "message": "User's task/question",
    "session_id": "unique-session-identifier"
  }
  ```
- Response: Server-Sent Events (SSE) stream
  - Content-Type: `text/event-stream`
  - Yield chunks as `data: {chunk}\n\n`
  - Final event: `data: [DONE]\n\n`
- Error Handling:
  - Validate request body
  - Return 400 for invalid agent types
  - Return 500 for backend errors (with error message)

#### C. Development Server Configuration
- Debug mode enabled for local development
- Port: 5000 (configurable via environment)
- Host: `0.0.0.0` (accessible externally)

#### D. Production Configuration
- Gunicorn workers: 4 (configurable)
- Timeout: 120 seconds (for long agent responses)
- Bind to `0.0.0.0:$PORT` (Render provides PORT env var)

**Deliverables:**
- `app.py` with:
  - Flask app initialization
  - `/` route (placeholder)
  - `/execute_agent` route with SSE streaming
  - Error handling middleware
  - Development and production configurations

---

### 1.4 Testing & Validation (Backend Only)

**Objective:** Validate backend functionality before frontend development.

**Testing Strategy:**

#### A. Manual Testing with cURL
```bash
# Test streaming endpoint
curl -X POST http://localhost:5000/execute_agent \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "Deep Research", "message": "What is quantum computing?", "session_id": "test-session-1"}'
```

#### B. Conversation History Validation
- Send multiple messages with same session_id
- Verify context is maintained across requests
- Test session isolation (different session_ids should be independent)

#### C. Error Scenarios
- Invalid API key (test error handling)
- Invalid agent type (test validation)
- Malformed request body (test input validation)
- Network timeout simulation

#### D. Performance Testing
- Test with long responses (measure streaming performance)
- Test concurrent requests (multiple sessions simultaneously)
- Monitor memory usage for session history

**Deliverables:**
- Validated backend endpoints
- Documented test cases
- Performance benchmarks (response time, memory usage)

---

## PHASE 2: Frontend Development (After Backend Completion)

### 2.1 UI Design - Agent Garden Aesthetic

**Design System:**
- Background: `#0e1117` (dark)
- Cards: Semi-transparent glassmorphism with blur
- Accent Color: `#00ff9d` (neon green)
- Typography: Modern sans-serif (Inter, Poppins, or system fonts)
- Animations: Smooth transitions, subtle hover effects

**Layout Components:**
1. **Header:** "Agent Garden" title with neon accent
2. **Agent Selection Cards:** 3 cards (Deep Research, Creative Muse, System Architect)
   - Hover effects
   - Click to select
   - Active state indication
3. **Chat Interface:**
   - Message input area
   - Send button (with loading state)
   - Message history display (user vs agent messages)
   - Streaming indicator (animated dots)
4. **Session Management:** Session ID display/reset button

---

### 2.2 JavaScript - Frontend Logic

**Core Functionality:**
1. **Agent Selection:** Handle card clicks, update UI state
2. **Message Handling:**
   - Capture user input
   - Send POST request to `/execute_agent`
   - Handle SSE stream
   - Render streaming response in real-time
3. **Session Management:**
   - Generate/maintain session ID (localStorage or UUID)
   - Clear session functionality
4. **Error Handling:**
   - Display user-friendly errors
   - Handle network failures
   - Retry mechanism

---

### 2.3 Deployment Preparation (Render)

**Render Configuration:**
1. Create `render.yaml` (optional but recommended)
2. Configure build command: `pip install -r requirements.txt`
3. Configure start command: `gunicorn app:app`
4. Set environment variables:
   - `GOOGLE_API_KEY` (from Render dashboard)
   - `PYTHON_VERSION=3.11` (or latest stable)
5. Health check endpoint (optional): `/health`

**Deployment Checklist:**
- [ ] `requirements.txt` includes all dependencies
- [ ] Gunicorn configured properly
- [ ] Environment variables set in Render
- [ ] Static files served correctly (CSS/JS in templates)
- [ ] Test deployment with staging environment

---

## IMPLEMENTATION ORDER SUMMARY

### **NOW (Backend Focus):**
1. ✅ Project structure setup
2. ✅ `requirements.txt` creation
3. ✅ `agent_backend.py` - Gemini integration with streaming + history
4. ✅ `app.py` - Flask routes with SSE support
5. ✅ Backend testing with cURL
6. ✅ Session history validation

### **LATER (Frontend):**
7. `index.html` - UI with glassmorphism design
8. JavaScript - SSE client, agent selection logic
9. CSS - Agent Garden aesthetic implementation
10. Integration testing (full stack)
11. Render deployment

---

## TECHNICAL DECISIONS & RATIONALE

### Why Streaming (SSE)?
- **UX:** Users see responses as they're generated (better perceived performance)
- **Long Responses:** Gemini can generate lengthy content; streaming prevents timeouts
- **Modern Pattern:** Industry standard for AI chat interfaces

### Why In-Memory Session History?
- **Simplicity:** No database dependency for MVP
- **Performance:** Fast access, no I/O overhead
- **Scalability Path:** Easy to migrate to Redis/PostgreSQL later

### Why `google-genai` v1.0+?
- **Future-Proof:** Latest SDK with ongoing support
- **Unified Client:** Consistent API across Google AI services
- **New Features:** Access to thinking modes and advanced configurations

---

## RISK MITIGATION

### Risk 1: API Rate Limiting
- **Mitigation:** Implement exponential backoff, rate limit handling
- **Future:** Add request queuing, user-level rate limits

### Risk 2: Memory Bloat (Session History)
- **Mitigation:** Implement session timeout (e.g., 30 minutes inactivity)
- **Future:** Move to Redis with TTL

### Risk 3: Streaming Failures (Network Issues)
- **Mitigation:** Client-side reconnection logic, error messages
- **Future:** Add WebSocket fallback

---

## SUCCESS CRITERIA (Backend Phase)

- ✅ Backend responds to agent execution requests
- ✅ Streaming works reliably (tested with cURL)
- ✅ Conversation history maintained across multiple messages
- ✅ All three agent types have distinct system prompts
- ✅ Error handling covers common failure scenarios
- ✅ Code is production-ready (proper logging, error messages)

---

**Ready to proceed with implementation? We'll start with Phase 1.1-1.3, then validate with 1.4 before moving to the frontend.**
