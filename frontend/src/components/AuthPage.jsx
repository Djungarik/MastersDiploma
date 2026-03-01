import { useState } from "react";
import useAppStore from "../store/useAppStore";
import { login, register } from "../services/authService";

/**
 * Login/Register page with fantasy-themed UI
 */
export function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { setUser } = useAppStore();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Validation
    if (!email || !password) {
      setError("Please fill in all fields");
      return;
    }

    if (!isLogin) {
      if (!username) {
        setError("Please enter a username");
        return;
      }
      if (password !== confirmPassword) {
        setError("Passwords do not match");
        return;
      }
      if (password.length < 6) {
        setError("Password must be at least 6 characters");
        return;
      }
    }

    setIsLoading(true);

    try {
      let user;
      if (isLogin) {
        user = await login(email, password);
      } else {
        user = await register(email, username, password);
      }
      setUser(user);
    } catch (err) {
      setError(err.message || "Authentication failed");
    } finally {
      setIsLoading(false);
    }
  };

  const switchMode = () => {
    setIsLogin(!isLogin);
    setError("");
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* Background decoration */}
      <div className="fixed inset-0 pointer-events-none opacity-30">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-mystic-600 rounded-full filter blur-[100px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-gold-600 rounded-full filter blur-[120px]" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <span className="text-gold-400 text-3xl">✧</span>
            <h1 className="font-display text-4xl text-parchment-100 tracking-widest">
              Adaptive OST
            </h1>
            <span className="text-gold-400 text-3xl">✧</span>
          </div>
          <p className="text-parchment-400 text-sm">
            AI-Powered Soundtrack for Tabletop Adventures
          </p>
        </div>

        {/* Auth Card */}
        <div className="glass-card p-8 animated-border">
          <h2 className="font-display text-2xl text-parchment-100 text-center mb-6">
            {isLogin ? "Welcome Back" : "Join the Quest"}
          </h2>

          {/* Error message */}
          {error && (
            <div className="mb-4 p-3 bg-blood-600/20 border border-blood-500/30 rounded-lg">
              <p className="text-blood-300 text-sm text-center">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div>
              <label className="block text-parchment-300 text-sm mb-1">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-ink-800/50 border border-gold-400/20 rounded-lg
                           text-parchment-100 placeholder-parchment-600
                           focus:outline-none focus:border-gold-400/50 focus:ring-1 focus:ring-gold-400/30
                           transition-colors"
                placeholder="adventurer@realm.com"
                disabled={isLoading}
              />
            </div>

            {/* Username (register only) */}
            {!isLogin && (
              <div>
                <label className="block text-parchment-300 text-sm mb-1">
                  Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-4 py-3 bg-ink-800/50 border border-gold-400/20 rounded-lg
                             text-parchment-100 placeholder-parchment-600
                             focus:outline-none focus:border-gold-400/50 focus:ring-1 focus:ring-gold-400/30
                             transition-colors"
                  placeholder="DragonSlayer42"
                  disabled={isLoading}
                />
              </div>
            )}

            {/* Password */}
            <div>
              <label className="block text-parchment-300 text-sm mb-1">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-ink-800/50 border border-gold-400/20 rounded-lg
                           text-parchment-100 placeholder-parchment-600
                           focus:outline-none focus:border-gold-400/50 focus:ring-1 focus:ring-gold-400/30
                           transition-colors"
                placeholder="••••••••"
                disabled={isLoading}
              />
            </div>

            {/* Confirm Password (register only) */}
            {!isLogin && (
              <div>
                <label className="block text-parchment-300 text-sm mb-1">
                  Confirm Password
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-ink-800/50 border border-gold-400/20 rounded-lg
                             text-parchment-100 placeholder-parchment-600
                             focus:outline-none focus:border-gold-400/50 focus:ring-1 focus:ring-gold-400/30
                             transition-colors"
                  placeholder="••••••••"
                  disabled={isLoading}
                />
              </div>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 mt-2
                         bg-gradient-to-r from-mystic-600 to-mystic-500 
                         hover:from-mystic-500 hover:to-mystic-400
                         disabled:from-ink-700 disabled:to-ink-700 disabled:cursor-not-allowed
                         text-parchment-100 font-display text-sm tracking-wide
                         rounded-lg transition-all duration-300
                         shadow-lg shadow-mystic-600/20 hover:shadow-mystic-500/30"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="w-4 h-4 animate-spin"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  {isLogin ? "Entering..." : "Creating..."}
                </span>
              ) : (
                <span>
                  {isLogin ? "Enter the Realm" : "Begin Your Journey"}
                </span>
              )}
            </button>
          </form>

          {/* Switch mode */}
          <div className="mt-6 text-center">
            <button
              onClick={switchMode}
              className="text-parchment-400 hover:text-gold-400 text-sm transition-colors"
              disabled={isLoading}
            >
              {isLogin ? (
                <>
                  New adventurer?{" "}
                  <span className="text-gold-400">Create an account</span>
                </>
              ) : (
                <>
                  Already have an account?{" "}
                  <span className="text-gold-400">Sign in</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-parchment-600 text-xs mt-6">
          Your adventure awaits...
        </p>
      </div>
    </div>
  );
}

export default AuthPage;
