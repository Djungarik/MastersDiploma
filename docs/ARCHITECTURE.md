# Adaptive OST Architecture

## System Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                              USER (Game Master)                             │
│                                     🎙️                                      │
└────────────────────────────────────────┬───────────────────────────────────┘
                                         │ Speech
                                         ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           BROWSER (React Frontend)                          │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────┐  │
│  │   Audio Capture │         │  Transformers.js │         │  State      │  │
│  │   (MediaRecorder)│───────▶│  (Whisper Tiny) │───────▶│  Management │  │
│  │                 │         │                 │         │  (Zustand)  │  │
│  │  navigator.     │         │  LOCAL AI       │         │             │  │
│  │  mediaDevices   │         │  No server cost │         │  mood,      │  │
│  └─────────────────┘         └─────────────────┘         │  intensity, │  │
│                                      │                    │  environment│  │
│                                      │ text               └──────┬──────┘  │
│                                      ▼                           │         │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        Agentic Loop (15-30s)                         │  │
│  │  Every N seconds: capture → transcribe → analyze → decide → play    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                      │                                     │
│                                      │ POST /api/analyze-mood              │
│                                      ▼                                     │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────┐  │
│  │   Audio Engine  │◀────────│  Music Buffer   │◀────────│  API Client │  │
│  │   (Web Audio)   │         │  (Preload)      │         │             │  │
│  │                 │         │                 │         │  Fetch new  │  │
│  │  GainNode A ────│───┐     │  Next track     │         │  tracks     │  │
│  │  GainNode B ────│───┤     │  ready to play  │         │             │  │
│  │                 │   │     └─────────────────┘         └─────────────┘  │
│  └─────────────────┘   │                                                   │
│                        ▼                                                   │
│                    🔊 Output                                               │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         │ HTTP/REST
                                         ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI BACKEND                                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────┐  │
│  │  /analyze-mood  │───────▶│   GPT-4o mini   │         │  /generate- │  │
│  │                 │         │                 │         │  music      │  │
│  │  Receives text  │         │  System Prompt: │         │             │  │
│  │  from frontend  │         │  "You are a DJ  │         │  Calls      │  │
│  │                 │         │  for D&D..."    │         │  Mubert API │  │
│  └─────────────────┘         └────────┬────────┘         └─────────────┘  │
│                                       │                                    │
│                                       ▼                                    │
│                              ┌─────────────────┐                          │
│                              │  JSON Response  │                          │
│                              │                 │                          │
│                              │  {              │                          │
│                              │    mood: "epic" │                          │
│                              │    intensity: 8 │                          │
│                              │    environment: │                          │
│                              │      "dungeon"  │                          │
│                              │  }              │                          │
│                              └─────────────────┘                          │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         │ API Calls
                                         ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SERVICES                                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐                              ┌─────────────────┐      │
│  │    OpenAI API   │                              │   Mubert API    │      │
│  │                 │                              │                 │      │
│  │  GPT-4o mini    │                              │  AI-generated   │      │
│  │  for mood       │                              │  royalty-free   │      │
│  │  analysis       │                              │  music loops    │      │
│  │                 │                              │                 │      │
│  │  ~$0.15/1M      │                              │  Free tier for  │      │
│  │  input tokens   │                              │  non-commercial │      │
│  └─────────────────┘                              └─────────────────┘      │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### The Agentic Loop

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Every 15-30 Seconds                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   1. CAPTURE                                                              │
│   ┌───────────────────────────────────────────────────────────────────┐  │
│   │  MediaRecorder.getAudioChunk() → Blob (webm)                      │  │
│   └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│   2. TRANSCRIBE (Local)                                                   │
│   ┌───────────────────────────────────────────────────────────────────┐  │
│   │  Whisper Tiny (Transformers.js) → "The dragon breathes fire..."   │  │
│   └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│   3. ANALYZE (Server)                                                     │
│   ┌───────────────────────────────────────────────────────────────────┐  │
│   │  POST /api/analyze-mood → { mood: "epic", intensity: 9 }          │  │
│   └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│   4. DECIDE                                                               │
│   ┌───────────────────────────────────────────────────────────────────┐  │
│   │  shouldChangeMusic(oldMood, newMood) → true/false                 │  │
│   │                                                                    │  │
│   │  Rules:                                                            │  │
│   │  - Mood changed? → Change music                                    │  │
│   │  - Intensity shifted by 3+? → Change music                         │  │
│   │  - Otherwise → Keep playing                                        │  │
│   └───────────────────────────────────────────────────────────────────┘  │
│                                    │                                      │
│                                    ▼                                      │
│   5. TRANSITION (if needed)                                               │
│   ┌───────────────────────────────────────────────────────────────────┐  │
│   │  a) Start bridge sound (ambient fill)                              │  │
│   │  b) Fetch new track from Mubert/cache                              │  │
│   │  c) Buffer new track                                               │  │
│   │  d) Crossfade: Track A → Track B (3 seconds)                       │  │
│   │  e) Stop bridge sound                                              │  │
│   └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## Audio Crossfade Detail

```
Volume
  │
1 │  ████████████████▓▓▓▓░░░░░░░░░░░░░░░░░░  Track A
  │                  ▓▓▓▓████████████████████  Track B  
  │
0 └──────────────────────────────────────────────────────▶ Time
                     │    │
                     └────┘
                   Crossfade
                   (3 seconds)
```

## State Management (Zustand)

```typescript
interface AppState {
  // Audio Capture
  isListening: boolean
  audioLevel: number (0-1)
  
  // Transcription
  isTranscribing: boolean
  transcribedText: string
  transcriptionHistory: Array<{text, timestamp}>
  
  // Mood Analysis
  currentMood: 'calm' | 'tense' | 'epic' | 'spooky' | 'mystery'
  previousMood: string | null
  intensity: number (1-10)
  environment: 'tavern' | 'dungeon' | 'forest' | ...
  
  // Music Playback
  isPlaying: boolean
  currentTrackUrl: string | null
  nextTrackUrl: string | null
  isTransitioning: boolean
  volume: number (0-1)
  
  // System
  whisperReady: boolean
  error: string | null
}
```

## Cost Analysis

| Component | Service | Cost |
|-----------|---------|------|
| Transcription | Transformers.js (local) | **$0** |
| Mood Analysis | GPT-4o mini | ~$0.15/1M tokens |
| Music Generation | Mubert Free Tier | **$0** (non-commercial) |
| Hosting Backend | Render/Railway | **$0** (free tier) |
| Hosting Frontend | Vercel/Netlify | **$0** (free tier) |

**Estimated Monthly Cost for Active Use**: < $1

