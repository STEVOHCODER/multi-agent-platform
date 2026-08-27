# Multi-Agent AI Communication & Business Operations Platform

A full-stack platform for building, deploying, and managing AI agents that communicate across WhatsApp, Email, and more — with audit trails, knowledge bases, and settlement tracking.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

### Step 1: Clone & Install

```bash
# Backend
cd saas/backend
pip install -r requirements.txt

# Frontend
cd saas/frontend
npm install
```

### Step 2: Configure Environment

```bash
cd saas/backend
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required for AI agents
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Your WhatsApp number (already configured for testing)
WHATSAPP_PHONE_NUMBER=+250786508880

# For WhatsApp Cloud API (get from Meta Developer Console)
WHATSAPP_ACCESS_TOKEN=your-meta-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_BUSINESS_ACCOUNT_ID=your-business-account-id
```

### Step 3: Start the Platform

```bash
# Terminal 1 — Backend (port 8000)
cd saas/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend (port 5173)
cd saas/frontend
npm run dev
```

### Step 4: Open the Platform

🌐 **Open in your browser:** [http://localhost:5173](http://localhost:5173)

---

## 📱 Testing Your WhatsApp Agent

### Your Configured Number
- **Phone:** `+250786508880` (already set in `.env`)

### Setup Steps for WhatsApp Cloud API

1. **Go to Meta Developer Console**
   - Visit: https://developers.facebook.com/apps/
   - Create a new app or use existing
   - Add WhatsApp product

2. **Get Your Credentials**
   - Copy `App ID` → put in `.env` as `META_APP_ID`
   - Copy `App Secret` → put in `.env` as `META_APP_SECRET`
   - Copy `Phone Number ID` → put in `.env` as `WHATSAPP_PHONE_NUMBER_ID`
   - Copy `WhatsApp Business Account ID` → put in `.env` as `WHATSAPP_BUSINESS_ACCOUNT_ID`
   - Generate a temporary access token → put in `.env` as `WHATSAPP_ACCESS_TOKEN`

3. **Configure Webhook**
   - In Meta Developer Console → WhatsApp → Configuration → Webhook
   - **Callback URL:** `http://YOUR_SERVER:8000/api/webhooks/whatsapp/YOUR_WORKSPACE_ID`
   - **Verify Token:** `agent_platform_webhook_verify_2024`
   - Subscribe to `messages` field

4. **Test It**
   - Send a WhatsApp message to your number: `+250786508880`
   - The agent will process it and respond based on its configuration

---

## 🤖 Building Your First Agent

### Step 1: Register & Login
1. Open [http://localhost:5173](http://localhost:5173)
2. Click **"Get Started"** → Create an account
3. Login with your credentials

### Step 2: Create a Workspace
- On first login, you'll be prompted to create a workspace
- Name it (e.g., "My Business")

### Step 3: Create an Agent from Template
1. Go to **Agents** in the sidebar
2. Choose a template:
   - **Customer Support Agent** — Handles customer inquiries
   - **Email Monitor Agent** — Watches inbox and forwards important emails
   - **Settlement Agent** — Tracks payments and invoices
   - **Notification Agent** — Sends alerts and updates
   - **General Assistant** — Flexible all-purpose agent
3. Click a template to instantly create an agent

### Step 4: Configure Your Agent
- **Response Mode:**
  - `off` — Never auto-replies (manual only)
  - `suggest` — Drafts replies, human approves
  - `auto` — Sends replies automatically
  - `auto_escalation` — Auto-replies with escalation for complex issues
- **Model:** Choose AI model (GPT-4o, Claude, Gemini)
- **Channels:** Select WhatsApp, Email, or both

### Step 5: Connect Channels
1. Go to **Channels** in the sidebar
2. **WhatsApp:** Enter your Meta credentials
3. **Email:** Enter your email address

### Step 6: Start Talking
- Send a message to your WhatsApp number
- The agent will process it and respond!

---

## 📊 Platform Features

### Agent Builder
- 5 pre-built agent templates
- Custom agent creation with model selection
- Per-agent response modes (off/suggest/auto/auto_escalation)
- Multi-channel support (WhatsApp, Email)

### 25+ Reusable Skills
| Category | Skills |
|----------|--------|
| **Communication** | customer_reply, send_whatsapp, send_email |
| **Email** | fetch_unread, parse_email, draft_reply |
| **Finance** | create_transaction, match_transaction, reconcile |
| **Memory** | save_short_term, save_long_term, search_memory |
| **Knowledge** | search_knowledge, add_knowledge |
| **Operations** | create_reminder, escalate_to_human, generate_report |

### Conversation Memory
- Short-term memory (per conversation)
- Long-term memory (persistent facts)
- Workspace-wide memory (shared knowledge)

### Knowledge Base
- Add FAQ, policies, product info
- Agents automatically use it for context
- Categories: faq, product, policy, process, general

### Settlement Tracking
- Transaction state machine (REQUESTED → SETTLED)
- Automatic message-to-transaction matching
- Daily reconciliation reports
- Financial safety: AI never auto-settles without approval

### Audit Trail
- Every agent action logged
- Token usage tracking
- Run history with status and duration

---

## 🔧 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/register` | Create account |
| `POST /api/auth/login` | Login |
| `GET /api/workspaces/` | List workspaces |
| `POST /api/agents/workspace/{id}` | Create agent |
| `GET /api/skills/registry` | List all skills |
| `POST /api/webhooks/whatsapp/{id}` | WhatsApp webhook |
| `GET /api/conversations/workspace/{id}/messages` | Get messages |
| `POST /api/settlement/workspace/{id}/transactions` | Create transaction |

Full API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛡️ Security Notes

- AI agents **never** auto-settle financial transactions above confidence threshold
- All actions are logged in the audit trail
- JWT authentication on all protected endpoints
- Webhook verification for WhatsApp

---

## 📁 Project Structure

```
saas/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI entry point
│       └── modules/
│           ├── core/            # Database, config
│           ├── auth/            # Authentication
│           ├── workspace/       # Multi-tenant workspaces
│           ├── agent/           # Agent system + templates
│           ├── skill/           # 25+ reusable skills
│           ├── conversation/    # Messages + memory
│           ├── settlement/      # Transaction tracking
│           ├── knowledge/       # Knowledge base
│           ├── audit/           # Audit logging
│           ├── ai_engine/       # OpenAI/Anthropic/Google
│           └── events/          # Event bus
└── frontend/
    └── src/
        ├── App.jsx              # Main router
        ├── api/client.js        # API client
        ├── components/          # Auth, Layout, Workspace
        └── pages/               # Dashboard, Agents, Skills, etc.
```

---

## 🐛 Troubleshooting

**Backend won't start:**
```bash
cd saas/backend
pip install -r requirements.txt
python -c "from app.main import app; print('OK')"
```

**Frontend won't start:**
```bash
cd saas/frontend
npm install
npm run dev
```

**WhatsApp not receiving messages:**
1. Check webhook URL is correct
2. Verify `WHATSAPP_ACCESS_TOKEN` is not expired
3. Check Meta Developer Console for webhook delivery status

**AI not responding:**
1. Verify `AI_PROVIDER` and API key in `.env`
2. Check agent response mode is not `off`
3. Check agent status is `active` (not paused)

---

## 📞 Your Test Number

**WhatsApp:** `+250786508880`

Send a message to this number after configuring the webhook. The agent will process it through the AI pipeline and respond based on its configured skills and knowledge.

---

Built with FastAPI + React + SQLAlchemy
