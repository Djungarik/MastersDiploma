# 🔑 Adaptive OST - Setup Guide

## API Keys You Need

### 1. Groq API Key (FREE - RECOMMENDED)

Groq provides **FREE** AI inference with Llama 3 models. This is the default and recommended option.

**How to get it:**
1. Go to [console.groq.com](https://console.groq.com/)
2. Sign up (free, no credit card needed)
3. Go to **API Keys** section
4. Click **"Create API Key"**
5. Copy the key (starts with `gsk_`)

**Cost:** 
- **Completely FREE** for reasonable usage
- Very fast inference

**Setup:**
```bash
# In backend/.env file:
AI_PROVIDER=groq
GROQ_API_KEY=gsk_your-key-here
```

---

### 1b. OpenAI API Key (ALTERNATIVE - paid)

If you prefer OpenAI's GPT-4o mini, you can use it instead.

**How to get it:**
1. Go to [platform.openai.com](https://platform.openai.com/)
2. Sign up or log in
3. Go to **API Keys** section
4. Click **"Create new secret key"**
5. Copy the key (starts with `sk-`)

**Cost:** 
- New accounts get **$5-$18 free credits**
- GPT-4o mini costs ~$0.15 per 1M input tokens
- **Estimated cost: < $1/month** for typical use

**Setup:**
```bash
# In backend/.env file:
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

---

### 2. Mubert API Key (OPTIONAL - for AI-generated music)

Mubert generates unique AI music in real-time. Without it, the app uses free fallback tracks from Pixabay.

**How to get it:**
1. Go to [b2b.mubert.com](https://b2b.mubert.com/)
2. Sign up for a developer account
3. Apply for API access (free tier available for non-commercial)
4. Get your API key from the dashboard

**Cost:**
- Free tier available for non-commercial/educational use
- Commercial plans start at $9/month

**Setup:**
```bash
# Add to your backend/.env file:
MUBERT_API_KEY=your-mubert-key-here
```

---

## Quick Setup Steps

### Step 1: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
# Copy the contents below and save as .env
```

**backend/.env file:**
```env
# Required
OPENAI_API_KEY=sk-your-openai-key-here

# Optional (for AI-generated music)
MUBERT_API_KEY=

# Optional settings
OPENAI_MODEL=gpt-4o-mini
DEBUG=false
```

### Step 2: Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### Step 3: Run Both Servers

**Terminal 1 (Backend):**
```bash
cd backend
venv\Scripts\activate  # Windows
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

### Step 4: Open the App

1. Go to `http://localhost:3000`
2. Click **"Initialize Whisper AI"** (first time downloads ~150MB model)
3. Click **"Start Listening"**
4. Speak your narration!

---

## Testing Without API Keys

The app works in a limited way without API keys:

| Feature | Without Keys | With OpenAI Key |
|---------|--------------|-----------------|
| Audio Capture | ✅ Works | ✅ Works |
| Local Transcription | ✅ Works (Whisper.js) | ✅ Works |
| Mood Analysis | ⚠️ Uses mock endpoint | ✅ Full GPT-4o mini |
| Music Playback | ✅ Fallback tracks | ✅ Fallback tracks |
| AI Music Generation | ❌ Not available | ⚠️ Needs Mubert key |

**To test without OpenAI:**
1. Start the backend server
2. The app will automatically fall back to `/api/analyze-mood/mock`
3. This uses simple keyword matching instead of AI

---

## Troubleshooting

### "Failed to initialize Whisper"
- Make sure you have a stable internet connection
- The first load downloads ~150MB model
- Try refreshing the page

### "Microphone access denied"
- Click the 🔒 icon in your browser's address bar
- Allow microphone access for localhost

### "Mood analysis failed"
- Check if backend is running on port 8000
- Verify your OpenAI API key is correct
- Check backend terminal for error messages

### No sound playing
- Click somewhere on the page first (browser autoplay policy)
- Check that volume slider isn't at 0
- Use the Developer Tools panel to test music manually

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR BROWSER                          │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐             │
│  │ Capture │───▶│ Whisper │───▶│  Send   │             │
│  │  Audio  │    │ (Local) │    │  Text   │             │
│  └─────────┘    └─────────┘    └────┬────┘             │
│                                      │                  │
│  ┌─────────┐    ┌─────────┐    ┌────▼────┐             │
│  │Crossfade│◀───│  Music  │◀───│ Receive │             │
│  │ & Play  │    │ Buffer  │    │  Mood   │             │
│  └─────────┘    └─────────┘    └─────────┘             │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (localhost:8000)                │
│  ┌─────────────────────────────────────────────────┐    │
│  │              GPT-4o mini Analysis                │    │
│  │   "You are a DJ for D&D. Analyze this text..."  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   EXTERNAL APIS                          │
│  ┌───────────────┐          ┌───────────────┐          │
│  │    OpenAI     │          │    Mubert     │          │
│  │  (Required)   │          │  (Optional)   │          │
│  └───────────────┘          └───────────────┘          │
└─────────────────────────────────────────────────────────┘
```

---

## Cost Summary

| Service | Free Tier | Estimated Monthly Cost |
|---------|-----------|------------------------|
| OpenAI GPT-4o mini | $5-18 credit | < $1 |
| Mubert | Non-commercial free | $0 |
| Whisper (local) | Runs in browser | $0 |
| Hosting (Render) | Free tier | $0 |

**Total estimated cost: < $1/month** 🎉

