import { create } from "zustand";
import { getStoredUser, getToken } from "../services/authService";

/**
 * Central state management for Adaptive OST
 *
 * State Flow:
 * 1. isListening → audio capture active
 * 2. transcribedText → latest GM speech
 * 3. currentMood → analyzed mood from backend
 * 4. isTransitioning → crossfade in progress
 */

export const MOODS = {
  CALM: "calm",
  TENSE: "tense",
  EPIC: "epic",
  SPOOKY: "spooky",
  MYSTERY: "mystery",
};

export const ENVIRONMENTS = {
  TAVERN: "tavern",
  DUNGEON: "dungeon",
  FOREST: "forest",
  CASTLE: "castle",
  WILDERNESS: "wilderness",
  CITY: "city",
  UNDERWATER: "underwater",
  VOID: "void",
};

const initialState = {
  // Authentication
  user: getStoredUser(),
  isAuthenticated: !!getToken(),
  isAuthLoading: false,

  // Audio capture
  isListening: false,
  audioLevel: 0,

  // Transcription
  isTranscribing: false,
  transcribedText: "",
  transcriptionHistory: [],

  // Mood analysis
  currentMood: MOODS.CALM,
  previousMood: null,
  intensity: 5,
  environment: ENVIRONMENTS.TAVERN,
  lastAnalysis: null,

  // Music playback
  isPlaying: false,
  currentTrackUrl: null,
  nextTrackUrl: null,
  isTransitioning: false,
  volume: 0.7,

  // System
  isInitialized: false,
  error: null,
  whisperReady: false,
  analysisInterval: 20000, // 20 seconds default
};

export const useAppStore = create((set, get) => ({
  ...initialState,

  // === Authentication Actions ===
  setUser: (user) => set({ user, isAuthenticated: !!user }),

  setAuthLoading: (isAuthLoading) => set({ isAuthLoading }),

  logout: () => set({ user: null, isAuthenticated: false }),

  // === Audio Capture Actions ===
  setListening: (isListening) => set({ isListening }),

  setAudioLevel: (audioLevel) => set({ audioLevel }),

  // === Transcription Actions ===
  setTranscribing: (isTranscribing) => set({ isTranscribing }),

  setTranscribedText: (text) =>
    set((state) => ({
      transcribedText: text,
      transcriptionHistory: [
        ...state.transcriptionHistory.slice(-9), // Keep last 10
        { text, timestamp: Date.now() },
      ],
    })),

  clearTranscription: () => set({ transcribedText: "" }),

  // === Mood Analysis Actions ===
  setMoodAnalysis: ({ mood, intensity, environment }) =>
    set((state) => ({
      previousMood: state.currentMood,
      currentMood: mood,
      intensity,
      environment,
      lastAnalysis: Date.now(),
    })),

  // === Music Playback Actions ===
  setPlaying: (isPlaying) => set({ isPlaying }),

  setCurrentTrack: (url) => set({ currentTrackUrl: url }),

  setNextTrack: (url) => set({ nextTrackUrl: url }),

  startTransition: () => set({ isTransitioning: true }),

  completeTransition: () =>
    set((state) => ({
      isTransitioning: false,
      currentTrackUrl: state.nextTrackUrl,
      nextTrackUrl: null,
    })),

  setVolume: (volume) => set({ volume: Math.max(0, Math.min(1, volume)) }),

  // === System Actions ===
  initialize: () => set({ isInitialized: true }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),

  setWhisperReady: (ready) => set({ whisperReady: ready }),

  setAnalysisInterval: (interval) => set({ analysisInterval: interval }),

  // === Computed / Helpers ===
  getMoodChanged: () => {
    const { currentMood, previousMood } = get();
    return previousMood !== null && currentMood !== previousMood;
  },

  reset: () => set(initialState),
}));

export default useAppStore;
