"""
Agent Garden - Intelligence Engine (Backend)
Gemini 3.0 Flash Integration with Streaming & Conversation History

Uses the NEW google-genai SDK (v1.0+)
"""

import os
import logging
from typing import Generator, Dict, List
from dotenv import load_dotenv
from google import genai
from google.genai import types
from src.core.database import (
    init_db,
    save_message,
    get_session_history,
    clear_session_history,
    USE_DATABASE
)
from src.connectors.tidb_connector import tidb
# Use optimized version with caching and parallel queries
from src.connectors.agent_database_context_optimized import get_agent_database_context_optimized as get_agent_database_context

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini client
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

client = genai.Client(api_key=API_KEY)

# Initialize database tables
init_db()

# In-memory fallback if database not configured
conversation_sessions: Dict[str, List[Dict[str, str]]] = {}

# ============================================================================
# AGENT SYSTEM PROMPTS
# ============================================================================

AGENT_PROMPTS = {
    "inventory_intelligence": """You are the Inventory Intelligence Agent for ArtGlassSupplies.com, specializing in Bullseye COE90 art glass and Tekta glass inventory management.

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

CONSTRAINTS & LIMITATIONS:
- You CANNOT place orders - only recommend and draft communications
- You cannot predict future sales - use historical patterns only
- You DO have direct access to live inventory databases (automatically injected into your context)

LIVE DATA ACCESS:
- You receive REAL-TIME database intelligence automatically with every request
- Current inventory levels, zero-stock alerts, and low-stock warnings are provided
- Sales velocity data (units/day per product) is calculated from actual order history
- Recent order activity and bestseller data is available
- You can reference specific data points from the database context provided

IMPORTANT: The database context is auto-generated and injected into every conversation. Always check the "LIVE DATABASE CONTEXT" section at the end of your system prompt for the most current business intelligence.

When making recommendations, ALWAYS reference the specific data from the database context (e.g., "Based on the zero inventory alert showing Product X at 0 units..."). This demonstrates you're using real data, not assumptions.

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

You are trusted to make judgment calls within these rules. Be confident in your recommendations but transparent about reasoning and trade-offs."""
}


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def get_or_create_session(session_id: str, agent_type: str = "inventory_intelligence") -> List[Dict[str, str]]:
    """
    Retrieve or initialize conversation history for a session.

    Args:
        session_id: Unique identifier for the conversation session
        agent_type: Type of agent (used for database storage)

    Returns:
        List of message dictionaries with 'role' and 'content' keys
    """
    if USE_DATABASE:
        # Use database storage
        history = get_session_history(session_id)
        if not history:
            logger.info(f"Created new database session: {session_id}")
        return history
    else:
        # Fallback to in-memory storage
        if session_id not in conversation_sessions:
            conversation_sessions[session_id] = []
            logger.info(f"Created new in-memory session: {session_id}")
        return conversation_sessions[session_id]


def add_message_to_session(session_id: str, agent_type: str, role: str, content: str) -> None:
    """
    Add a message to the session history.

    Args:
        session_id: Unique identifier for the conversation session
        agent_type: Type of agent (for database storage)
        role: Either 'user' or 'model'
        content: Message content
    """
    if USE_DATABASE:
        # Save to database
        success = save_message(session_id, agent_type, role, content)
        if success:
            logger.info(f"Saved {role} message to database for session {session_id}")
        else:
            logger.warning(f"Failed to save {role} message to database, using in-memory fallback")
            # Fallback to in-memory
            history = get_or_create_session(session_id, agent_type)
            history.append({"role": role, "content": content})
    else:
        # Use in-memory storage
        history = get_or_create_session(session_id, agent_type)
        history.append({"role": role, "content": content})
        logger.info(f"Added {role} message to in-memory session {session_id}")


# ============================================================================
# CORE EXECUTION FUNCTION
# ============================================================================

def execute_agent(agent_type: str, user_message: str, session_id: str) -> Generator[str, None, None]:
    """
    Execute an agent with streaming response.

    Args:
        agent_type: Type of agent (e.g., 'inventory_intelligence')
        user_message: User's input message
        session_id: Unique session identifier

    Yields:
        Response chunks from Gemini API

    Raises:
        ValueError: If agent_type is invalid
        Exception: For API errors (authentication, rate limits, network)
    """
    # Validate agent type
    if agent_type not in AGENT_PROMPTS:
        available = ", ".join(AGENT_PROMPTS.keys())
        raise ValueError(f"Invalid agent type: {agent_type}. Available: {available}")

    try:
        # Get conversation history
        history = get_or_create_session(session_id, agent_type)

        # Add user message to history
        add_message_to_session(session_id, agent_type, "user", user_message)

        # Get system prompt for this agent
        base_system_prompt = AGENT_PROMPTS[agent_type]

        # 🔥 AUTO-INJECT DATABASE CONTEXT 🔥
        # This makes EVERY agent database-aware automatically!
        database_context = get_agent_database_context(agent_type)

        # Combine base prompt with live database intelligence
        system_prompt = base_system_prompt + "\n\n" + database_context

        # Build conversation for Gemini API
        # Format: system instruction + conversation history
        messages = []

        # Add conversation history (excluding the message we just added)
        for msg in history[:-1]:
            messages.append(types.Content(
                role=msg["role"],
                parts=[types.Part(text=msg["content"])]
            ))

        # Add current user message
        messages.append(types.Content(
            role="user",
            parts=[types.Part(text=user_message)]
        ))

        logger.info(f"Executing {agent_type} for session {session_id}")

        # Call Gemini API with streaming (gemini-2.5-flash is Gemini 3.0 Flash)
        response = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7
            )
        )

        # Stream response chunks
        full_response = ""
        for chunk in response:
            if chunk.text:
                full_response += chunk.text
                yield chunk.text

        # Add assistant response to history
        add_message_to_session(session_id, agent_type, "model", full_response)

        logger.info(f"Completed {agent_type} execution for session {session_id}")

    except Exception as e:
        error_msg = f"Error executing agent: {str(e)}"
        logger.error(error_msg)

        # Determine error type and provide user-friendly message
        if "API key" in str(e).lower() or "authentication" in str(e).lower():
            yield "⚠️ Authentication Error: Invalid API key. Please check your GOOGLE_API_KEY configuration."
        elif "429" in str(e) or "rate limit" in str(e).lower():
            yield "⚠️ Rate Limit: Too many requests. Please wait a moment and try again."
        elif "timeout" in str(e).lower() or "network" in str(e).lower():
            yield "⚠️ Network Error: Connection timeout. Please check your internet connection and try again."
        else:
            yield f"⚠️ Error: {str(e)}"

        raise


# ============================================================================
# SESSION CLEANUP (OPTIONAL)
# ============================================================================

def clear_session(session_id: str) -> bool:
    """
    Clear conversation history for a session.

    Args:
        session_id: Session to clear

    Returns:
        True if session was cleared, False if it didn't exist
    """
    if USE_DATABASE:
        # Clear from database
        success = clear_session_history(session_id)
        if success:
            logger.info(f"Cleared database session: {session_id}")
        return success
    else:
        # Clear from in-memory storage
        if session_id in conversation_sessions:
            del conversation_sessions[session_id]
            logger.info(f"Cleared in-memory session: {session_id}")
            return True
        return False


def get_active_sessions() -> List[str]:
    """
    Get list of active session IDs.

    Returns:
        List of session IDs
    """
    if USE_DATABASE:
        from src.core.database import get_all_sessions
        return get_all_sessions()
    else:
        return list(conversation_sessions.keys())
