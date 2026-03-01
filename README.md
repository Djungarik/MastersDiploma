# 🎵 Adaptive OST

**AI-Powered Soundtrack System for Tabletop RPGs**

An intelligent soundtrack companion that listens to your Game Master and automatically generates mood-appropriate music. No more fumbling with playlists mid-session!

![Architecture](docs/architecture.png)

## ✨ Features

- **Zero UI Interaction**: The GM narrates naturally; music follows the story
- **Local Transcription**: Whisper AI runs in-browser (no audio leaves your computer)
- **Semantic Understanding**: Distinguishes "sneaky heist" from "epic battle" from "tragic loss"
- **Smooth Transitions**: Professional crossfades between tracks
- **Gap Filling**: Ambient bridges while new music generates

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (Client)                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Capture   │───▶│  Whisper.js │───▶│  Send Text  │     │
│  │   Audio     │    │  (Local AI) │    │  to Server  │     │
│  └─────────────┘    └─────────────┘    └──────┬──────┘     │
│                                               │             │
│  ┌─────────────┐    ┌─────────────┐    ┌──────▼──────┐     │
│  │  Crossfade  │◀───│  Download   │◀───│  Receive    │     │
│  │  Tracks     │    │  New Track  │    │  Mood+Track │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│        │                                                    │
│        ▼                                                    │
│  ┌─────────────┐                                           │
│  │ Web Audio   │                                           │
│  │ API Output  │                                           │
│  └─────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Receive    │───▶│ GPT-4o mini │───▶│   Mubert    │     │
│  │  Text       │    │ Mood+Intent │    │  Generate   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ (for frontend)
- Python 3.11+ (for backend)
- OpenAI API key (free credits available for new accounts)

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/adaptive-ost.git
cd adaptive-ost

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your OpenAI API key

# Setup frontend
cd ../frontend
npm install
```

### 2. Run Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 3. Open the App

Navigate to `http://localhost:3000` in your browser.

## 🎮 How to Use

1. **Initialize**: Click "Initialize Whisper AI" to load the transcription model (~150MB, cached after first load)
2. **Start Listening**: Click the green "Start Listening" button
3. **Narrate**: Speak your GM narration naturally
4. **Watch the Magic**: The mood orb changes color, and music transitions automatically

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Transcription | [Transformers.js](https://huggingface.co/docs/transformers.js) + Whisper | In-browser speech-to-text |
| Intent | GPT-4o mini | Semantic mood analysis |
| Music | Mubert API / Fallback tracks | AI-generated loops |
| Audio | Web Audio API | Crossfading & mixing |
| Frontend | React + Vite + Tailwind | UI |
| Backend | FastAPI | API orchestration |

## 📁 Project Structure

```
adaptive-ost/
├── frontend/
│   ├── src/
│   │   ├── components/       # React UI components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── services/        # Audio engine, Whisper, API
│   │   └── store/           # Zustand state management
│   └── public/
│       └── audio/           # Fallback music tracks
├── backend/
│   └── app/
│       ├── routers/         # FastAPI route handlers
│       ├── config.py        # Environment configuration
│       └── main.py          # Application entry point
└── docs/                    # Documentation & diagrams
```

## 🔧 Configuration

### Environment Variables

**Backend (`.env`):**
```bash
OPENAI_API_KEY=sk-...      # Required: Your OpenAI API key
OPENAI_MODEL=gpt-4o-mini   # Optional: Model for mood analysis
MUBERT_API_KEY=...         # Optional: For AI music generation
DEBUG=false                # Optional: Enable debug logging
```

### Mood Categories

| Mood | Description | Example Triggers |
|------|-------------|------------------|
| 🌿 Calm | Peaceful, restful | Tavern, travel, shopping |
| ⚡ Tense | Suspenseful | Sneaking, negotiations, traps |
| ⚔️ Epic | Heroic action | Combat, boss fights, victories |
| 👁️ Spooky | Horror elements | Undead, haunted, rituals |
| 🔮 Mystery | Investigation | Puzzles, secrets, magic |

## 📈 Roadmap

### Week 1-2 (Current)
- [x] React frontend with audio capture
- [x] Vibe Status display
- [x] FastAPI backend scaffold

### Week 3-4
- [ ] Connect GPT-4o mini mood detection
- [ ] Add analysis loop (every 15-30 seconds)

### Week 5-6
- [ ] Integrate Mubert API
- [ ] Add fallback track library

### Week 7-8
- [ ] Polish crossfade transitions
- [ ] Add ambient bridge sounds
- [ ] Performance optimization

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines first.

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- [Hugging Face](https://huggingface.co/) for Transformers.js
- [OpenAI](https://openai.com/) for Whisper and GPT-4o mini
- [Mubert](https://mubert.com/) for AI music generation
- All the amazing D&D communities for inspiration

---

*Built as a Master's Diploma Project*

