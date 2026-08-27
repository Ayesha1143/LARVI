# Larvi — Autonomous Email & Calendar AI Agent

> **Larvi** is an autonomous AI assistant that understands natural-language requests and performs real Email and Calendar operations through Gmail API and Google Calendar API.

---

## 📸 Project Screenshots

Screenshots will be added here to demonstrate Larvi's interface and functionality.

### Main Chat Interface

![Larvi Chat Interface](screenshots/larvi-main.png)

### Gmail & Calendar Connection

![Google Authentication](screenshots/google-auth.png)

### Email Search & Reading

![Email Management](screenshots/email-search.png)

### Calendar Management

![Calendar Management](screenshots/calendar.png)

### Multi-Agent Workflow

![Multi-Agent Workflow](screenshots/multi-agent-workflow.png)

### Email Confirmation

![Email Confirmation](screenshots/email-confirmation.png)

> **Note:** Add your screenshots inside the `screenshots/` folder using the filenames shown above.

---

# 🎯 Objective

The objective of Larvi is to build an autonomous AI agent capable of managing Email and Calendar tasks using natural-language instructions.

Unlike a normal chatbot, Larvi can understand a user's objective, select the appropriate agent, call real tools, interact with external APIs, coordinate multiple agents, maintain conversation context, and return the actual result.

---

# 🤖 What is Larvi?

Larvi works as a central AI controller between the user and specialized Email and Calendar agents.

```text
User
  │
  ▼
Larvi Master Agent
  │
  ├───────────────┐
  ▼               ▼
Email Agent    Calendar Agent
  │               │
  ▼               ▼
Email Tools    Calendar Tools
  │               │
  ▼               ▼
Gmail API     Google Calendar API
  │               │
  └───────┬───────┘
          ▼
       Result
          │
          ▼
   Larvi Master Agent
          │
          ▼
         User
```

---

# ✨ Core Features

## 📧 Email Management

Larvi can:

* Search emails
* Read emails
* Retrieve recent emails
* Search by sender
* Search by subject
* Search using keywords
* Summarize emails
* Extract useful information
* Create email drafts
* Send emails
* Reply to emails

### Example Requests

```text
Show me my latest emails
```

```text
Find emails from Ahmed
```

```text
Find the email about tomorrow's meeting
```

```text
Summarize my unread emails
```

```text
Draft a reply to this email
```

```text
Send Ali an email about the project update
```

---

# 📅 Calendar Management

Larvi can:

* View upcoming events
* Search calendar events
* Check availability
* Detect scheduling conflicts
* Create events
* Update events
* Reschedule events
* Cancel events
* Delete events
* Retrieve event details

### Example Requests

```text
What meetings do I have tomorrow?
```

```text
Am I free tomorrow at 4 PM?
```

```text
Schedule a meeting tomorrow at 3 PM
```

```text
Move my meeting to 5 PM
```

```text
Cancel tomorrow's project meeting
```

---

# 🧠 Master Agent

The **Master Agent** acts as Larvi's central controller.

It is responsible for:

* Understanding natural-language instructions
* Identifying user intent
* Extracting relevant information
* Selecting the appropriate specialized agent
* Coordinating Email and Calendar agents
* Managing workflow state
* Maintaining conversation context
* Handling failures
* Generating the final response

The Master Agent can route requests to:

```text
email_agent
calendar_agent
multi_agent
```

---

# 📧 Email Agent

The Email Agent specializes in Gmail operations.

```text
User Request
     ↓
Master Agent
     ↓
Email Agent
     ↓
Email Tool
     ↓
Gmail API
     ↓
Result
```

Available tools:

```text
search_emails
read_email
get_recent_emails
create_draft
send_email
reply_email
```

---

# 📅 Calendar Agent

The Calendar Agent specializes in Google Calendar operations.

```text
User Request
     ↓
Master Agent
     ↓
Calendar Agent
     ↓
Calendar Tool
     ↓
Google Calendar API
     ↓
Result
```

Available tools:

```text
get_events
search_events
check_availability
create_event
update_event
delete_event
```

---

# 🔄 Multi-Agent Workflows

Larvi supports workflows where multiple specialized agents work together.

## Workflow 1 — Email → Calendar

### User

```text
Find the email from Ahmed about the project meeting
and add that meeting to my calendar.
```

### Workflow

```text
Master Agent
     ↓
Email Agent
     ↓
Search Email
     ↓
Read Email
     ↓
Extract Meeting Information
     ↓
Calendar Agent
     ↓
Check Availability
     ↓
Create Event
     ↓
Final Response
```

---

## Workflow 2 — Email → Availability → Calendar

### User

```text
Check whether I received an email from Ali about
tomorrow's project meeting. If you find the meeting
time, check whether I am free and add it to my calendar.
```

### Workflow

```text
Master Agent
     ↓
Email Agent
     ↓
Search Email
     ↓
Read Email
     ↓
Extract Date & Time
     ↓
Calendar Agent
     ↓
Check Availability
     ↓
Create Event
     ↓
Final Response
```

---

## Workflow 3 — Context-Based Follow-Up

### User

```text
Find my meeting with Ali tomorrow.
```

### Larvi

```text
I found the Project Review meeting at 3 PM.
```

### User

```text
Move it to 5 PM.
```

Larvi uses the maintained conversation context to understand that **"it"** refers to the previously identified Project Review meeting.

---

# 🛠️ Tool Calling

Larvi uses actual functions/tools to perform operations.

The system follows the principle:

```text
User Request
     ↓
LLM Reasoning
     ↓
Tool Selection
     ↓
Tool Execution
     ↓
API Result
     ↓
Final Response
```

Larvi must **never claim an operation succeeded unless the corresponding tool/API confirms success**.

---

# 🔐 Authentication

Larvi uses **Google OAuth 2.0** for Gmail and Google Calendar.

```text
User
  ↓
Connect Google
  ↓
Google OAuth
  ↓
Permission Granted
  ↓
Authorization Code
  ↓
Larvi
  ↓
Google Credentials
  ↓
Gmail / Calendar APIs
```

Required Google APIs:

* Gmail API
* Google Calendar API

Sensitive credentials are stored through environment variables and are not hard-coded into the source code.

---

# 🛡️ Safety & Confirmation

Larvi handles important actions carefully.

Confirmation can be required before:

* Sending important emails
* Deleting emails
* Cancelling meetings
* Rescheduling important meetings
* Performing destructive actions

For example:

```text
User:
Send Ali an email about the project update.
```

Larvi can prepare the draft first:

```text
Draft ready — confirm before sending.

To: ali@example.com
Subject: Project Update

[Email content]

[ Confirm Send ]   [ Edit Draft ]
```

---

# 🧩 Context Management

Larvi maintains relevant conversation state so users can give follow-up instructions naturally.

Example:

```text
User:
Find my Project Review meeting.

Larvi:
I found the Project Review meeting at 3 PM.

User:
Move it to 5 PM.
```

Larvi can use the previous state to identify the correct event.

---

# ⚠️ Error Handling

Larvi handles errors such as:

* Email not found
* Calendar event not found
* Invalid email recipient
* Missing date
* Missing time
* Authentication failure
* Expired authentication
* API failure
* Scheduling conflict
* Tool execution failure

Instead of crashing, Larvi returns a meaningful response.

Example:

```text
No meeting found at 5 PM tomorrow.
Did you mean the 3:00 PM Project Review?
```

---

# 🏗️ Technology Stack

| Component           | Technology                   |
| ------------------- | ---------------------------- |
| Language            | Python                       |
| IDE                 | PyCharm                      |
| Backend             | FastAPI                      |
| Agent Orchestration | LangGraph                    |
| Agent Framework     | LangChain                    |
| LLM                 | Ollama Cloud                 |
| Email               | Gmail API                    |
| Calendar            | Google Calendar API          |
| Authentication      | OAuth 2.0                    |
| State               | In-memory conversation state |
| Frontend            | HTML, CSS, JavaScript        |
| Version Control     | Git + GitHub                 |
| Deployment          | Railway                      |

> No database is used in the current Larvi implementation.

---

# 📁 Project Structure

```text
LARVI/
│
├── app/
│   ├── main.py
│   │
│   ├── config/
│   │   ├── settings.py
│   │   └── constants.py
│   │
│   ├── agents/
│   │   ├── master_agent.py
│   │   ├── email_agent.py
│   │   └── calendar_agent.py
│   │
│   ├── graph/
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── workflow.py
│   │
│   ├── tools/
│   │   ├── email_tools.py
│   │   └── calendar_tools.py
│   │
│   ├── services/
│   │   ├── gmail_service.py
│   │   ├── calendar_service.py
│   │   └── oauth_service.py
│   │
│   ├── schemas/
│   │   ├── chat_schema.py
│   │   ├── email.py
│   │   └── calendar.py
│   │
│   ├── api/
│   │   ├── chat.py
│   │   └── auth.py
│   │
│   └── utils/
│       ├── error_handler.py
│       └── helpers.py
│
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── screenshots/
│   ├── larvi-main.png
│   ├── google-auth.png
│   ├── email-search.png
│   ├── calendar.png
│   ├── multi-agent-workflow.png
│   └── email-confirmation.png
│
├── tests/
│   ├── test_email_tools.py
│   ├── test_calendar_tools.py
│   ├── test_agents.py
│   └── test_workflows.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── Procfile
├── railway.json
└── README.md
```

---

# ⚙️ Installation

Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Go into the project:

```bash
cd LARVI
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file in the project root.

```env
OLLAMA_API_KEY=your_ollama_api_key
OLLAMA_MODEL=your_ollama_model

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

APP_NAME=Larvi
APP_ENV=development
DEBUG=True

BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:8000
```

**Never commit `.env` to GitHub.**

Use `.env.example` as the public template.

---

# ☁️ Google Cloud Configuration

Before using Gmail and Calendar functionality:

1. Create a Google Cloud project.
2. Enable Gmail API.
3. Enable Google Calendar API.
4. Configure the OAuth consent screen.
5. Create OAuth 2.0 credentials.
6. Add the required redirect URI.
7. Add credentials to `.env`.

For local development:

```text
http://localhost:8000/auth/callback
```

For Railway:

```text
https://YOUR-RAILWAY-DOMAIN/auth/callback
```

---

# ▶️ Run Locally

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Open Larvi:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 🔌 API Endpoints

### Health Check

```text
GET /health
```

### Google Login

```text
GET /auth/login
```

### Google OAuth Callback

```text
GET /auth/callback
```

### Larvi Chat

```text
POST /chat
```

Example:

```json
{
    "message": "Show me my latest emails",
    "conversation_id": null
}
```

---

# 🧪 Testing

Run all tests:

```bash
pytest
```

Email tools:

```bash
pytest tests/test_email_tools.py
```

Calendar tools:

```bash
pytest tests/test_calendar_tools.py
```

Agents:

```bash
pytest tests/test_agents.py
```

Workflows:

```bash
pytest tests/test_workflows.py
```

---

# 🚀 Deployment

Larvi is configured for deployment on **Railway**.

The project includes:

```text
Procfile
railway.json
```

Railway start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Required Railway environment variables:

```text
OLLAMA_API_KEY
OLLAMA_MODEL
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI
APP_NAME
APP_ENV
DEBUG
BACKEND_URL
FRONTEND_URL
```

After deployment, update the Google OAuth redirect URI to the Railway deployment URL.

---

# 📸 Demonstration Evidence

The final project demonstration should include screenshots showing:

### 1. Larvi Interface

The main AI chat interface and Larvi's overall UI.

### 2. Google Authentication

Successful Google OAuth authentication.

### 3. Email Search

Larvi searching and retrieving emails through Gmail API.

### 4. Email Reading & Summarization

Larvi reading an email and extracting useful information.

### 5. Email Draft

Larvi preparing an email draft before sending.

### 6. Email Confirmation

Confirmation before performing an external email action.

### 7. Calendar Events

Larvi retrieving upcoming calendar events.

### 8. Availability Check

Larvi checking for scheduling conflicts.

### 9. Event Creation

Larvi creating an actual Google Calendar event.

### 10. Multi-Agent Workflow

Email Agent → Calendar Agent coordination.

### 11. Context-Based Follow-Up

Larvi understanding a follow-up request based on previous conversation context.

### 12. Error Handling

Larvi returning a meaningful response when an email/event is not found or another operation fails.

---

# 🎥 Project Demonstration Video

A short demonstration video should show the complete working system, including:

```text
Google Authentication
        ↓
Email Operation
        ↓
Calendar Operation
        ↓
Multi-Agent Workflow
        ↓
Context-Based Follow-Up
        ↓
Confirmation
        ↓
Error Handling
```

**Demo Video:** `ADD_YOUR_VIDEO_LINK_HERE`

---

# 🐙 GitHub

Repository:

**GitHub:** `ADD_YOUR_GITHUB_REPOSITORY_LINK_HERE`

---

# 🌐 Live Deployment

**Railway:** `ADD_YOUR_RAILWAY_DEPLOYMENT_LINK_HERE`

---

# 🎓 Final Demonstration Checklist

* [ ] Gmail authentication
* [ ] Google Calendar authentication
* [ ] Email searching
* [ ] Email reading
* [ ] Email summarization
* [ ] Email drafting
* [ ] Email sending
* [ ] Email replying
* [ ] Calendar event viewing
* [ ] Availability checking
* [ ] Calendar event creation
* [ ] Calendar event updating
* [ ] Calendar event deletion
* [ ] Context-based follow-up
* [ ] Multi-agent workflow 1
* [ ] Multi-agent workflow 2
* [ ] Multi-agent workflow 3
* [ ] Confirmation handling
* [ ] Error handling
* [ ] Real API execution
* [ ] GitHub repository
* [ ] Railway deployment
* [ ] Screenshots
* [ ] Demonstration video

---

# 👩‍💻 Project

**Project Name:** Larvi
**Project Type:** Autonomous AI Agent
**Domain:** AI / Agentic AI / Automation
**Backend:** FastAPI
**Agent Orchestration:** LangGraph
**APIs:** Gmail API + Google Calendar API
**Deployment:** Railway

---

## Final Objective

Larvi demonstrates an AI system that goes beyond a traditional chatbot.

```text
Understand
    ↓
Reason
    ↓
Select Agent
    ↓
Select Tool
    ↓
Execute Real API Action
    ↓
Coordinate Agents
    ↓
Maintain Context
    ↓
Handle Errors
    ↓
Return Verified Result
```

**Larvi — Your autonomous Email & Calendar assistant.**
