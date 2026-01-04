I am building a project called "Agent Garden". Act as the Senior Software Architect and Lead Developer. I need you to understand the full context, tech stack, and constraints before we write any code.

PROJECT OVERVIEW:
We are building a web-based AI Dashboard where users can select specialized "Autonomous Agents" (Deep Research, Creative Muse, System Architect) to execute tasks.

THE TECH STACK (Strict Constraints):
1. Frontend: HTML5, CSS3, JavaScript (Vanilla).
   - Design System: Dark Mode, Glassmorphism, Neon Accents (#00ff9d).
   - Framework: None (Raw HTML/CSS injected via Flask templates).
2. Backend: Python (Flask).
   - Server: Flask (dev) / Gunicorn (production).
   - Hosting: Render Web Service.
3. Intelligence Engine (The "Executor"):
   - Model: Google Gemini 3.0 Flash (`gemini-3.0-flash`).
   - SDK: `google-genai` (The new v1.0+ Unified Client).
   - **CRITICAL:** Do NOT use the old `google-generativeai` library.
   - Configuration: Must use `thinking_mode="efficient"` and `temperature=0.7`.

FILE STRUCTURE:
/agent_garden_flask
  ├── app.py                # Flask Server (Routes: /, /execute_agent)
  ├── agent_backend.py      # Gemini 3.0 Logic (Client setup, System Prompts)
  ├── requirements.txt      # Dependencies (flask, gunicorn, google-genai, python-dotenv)
  ├── .env                  # Secrets (GOOGLE_API_KEY)
  └── templates/
      └── index.html        # The UI (Cards, Chat Interface, CSS, JS)

YOUR INSTRUCTIONS:
1. When writing code, always prioritize the "New SDK" syntax (`from google import genai`).
2. Ensure `requirements.txt` is ready for Render deployment (must include `gunicorn`).
3. The UI must match the "Agent Garden" aesthetic: Dark #0e1117 background, semi-transparent cards.
4. Error handling in `agent_backend.py` is mandatory (Gemini API calls can fail).

Acknowledged? Please confirm you understand the stack and are ready to build the Flask version.