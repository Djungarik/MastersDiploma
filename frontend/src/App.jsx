import { useEffect } from "react";
import useAppStore from "./store/useAppStore";
import { useAgenticLoop } from "./hooks/useAgenticLoop";
import { logout as logoutService } from "./services/authService";
import MoodOrb from "./components/MoodOrb";
import ListenerStatus from "./components/ListenerStatus";
import EnvironmentDisplay from "./components/EnvironmentDisplay";
import VolumeControl from "./components/VolumeControl";
import ControlPanel from "./components/ControlPanel";
import TransitionLog from "./components/TransitionLog";
import SettingsPanel from "./components/SettingsPanel";
import AuthPage from "./components/AuthPage";

function App() {
  const { error, clearError, currentMood, isAuthenticated, user, logout } =
    useAppStore();

  // Initialize the agentic loop (runs automatically when listening starts)
  useAgenticLoop();

  // Auto-dismiss errors after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(clearError, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  // Handle logout
  const handleLogout = async () => {
    await logoutService();
    logout();
  };

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <AuthPage />;
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Decorative header with user info */}
      <header className="pt-8 pb-4">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex-1" />
            <div className="text-center">
              <div className="inline-flex items-center gap-3">
                <span className="text-gold-400 text-2xl">✧</span>
                <h1 className="font-display text-3xl md:text-4xl text-parchment-100 tracking-widest">
                  Adaptive OST
                </h1>
                <span className="text-gold-400 text-2xl">✧</span>
              </div>
              <p className="mt-2 text-parchment-400 text-sm tracking-wide">
                AI-Powered Soundtrack for Tabletop Adventures
              </p>
            </div>

            {/* User menu */}
            <div className="flex-1 flex justify-end">
              <div className="flex items-center gap-3">
                <span className="text-parchment-300 text-sm hidden sm:block">
                  {user?.username || user?.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="px-3 py-1.5 text-sm text-parchment-400 hover:text-parchment-200 
                             border border-parchment-700 hover:border-parchment-500
                             rounded-lg transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Error toast */}
      {error && (
        <div className="fixed top-4 right-4 z-50 animate-fade-in">
          <div className="glass-card bg-blood-600/20 border-blood-500/30 p-4 max-w-sm">
            <div className="flex items-start gap-3">
              <span className="text-blood-400 text-xl">⚠️</span>
              <div className="flex-1">
                <p className="text-parchment-200 text-sm">{error}</p>
              </div>
              <button
                onClick={clearError}
                className="text-parchment-500 hover:text-parchment-300 transition-colors"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="flex-1 container mx-auto px-4 py-8 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left sidebar */}
          <div className="space-y-6 order-2 lg:order-1">
            <ListenerStatus />
            <ControlPanel />
          </div>

          {/* Center - Mood Orb */}
          <div className="flex items-center justify-center py-12 order-1 lg:order-2">
            <MoodOrb />
          </div>

          {/* Right sidebar */}
          <div className="space-y-6 order-3">
            <EnvironmentDisplay />
            <VolumeControl />
            <TransitionLog />
            <SettingsPanel />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 text-center border-t border-gold-400/10">
        <p className="text-parchment-600 text-xs">
          Built with Web Audio API, Transformers.js, and GPT-4o mini
        </p>
        <p className="text-parchment-700 text-xs mt-1">
          Master's Diploma Project — Adaptive Soundtrack System
        </p>
      </footer>

      {/* Background mood ambient effect */}
      <div
        className="fixed inset-0 pointer-events-none transition-opacity duration-[3000ms] opacity-20 z-[-1]"
        style={{
          background:
            currentMood === "epic"
              ? "radial-gradient(circle at 50% 50%, rgba(196, 91, 91, 0.3) 0%, transparent 70%)"
              : currentMood === "spooky"
                ? "radial-gradient(circle at 50% 50%, rgba(123, 104, 201, 0.3) 0%, transparent 70%)"
                : currentMood === "tense"
                  ? "radial-gradient(circle at 50% 50%, rgba(212, 175, 55, 0.3) 0%, transparent 70%)"
                  : currentMood === "mystery"
                    ? "radial-gradient(circle at 50% 50%, rgba(74, 111, 165, 0.3) 0%, transparent 70%)"
                    : "radial-gradient(circle at 50% 50%, rgba(90, 154, 107, 0.2) 0%, transparent 70%)",
        }}
      />
    </div>
  );
}

export default App;
