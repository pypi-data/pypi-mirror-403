import { useState } from 'react';
import { setStoredToken, checkAuth } from '../api';

interface LoginPageProps {
  onAuthenticated: () => void;
}

export default function LoginPage({ onAuthenticated }: LoginPageProps) {
  const [passphrase, setPassphrase] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passphrase.trim()) return;

    setLoading(true);
    setError('');

    try {
      setStoredToken(passphrase);
      const authStatus = await checkAuth();

      if (authStatus.authenticated) {
        onAuthenticated();
      } else {
        setError('Invalid passphrase');
        setStoredToken('');
      }
    } catch {
      setError('Failed to authenticate');
      setStoredToken('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-box">
        <div className="login-logo">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
          </svg>
        </div>
        <h1 className="login-title">Multimedia</h1>
        <p className="login-subtitle">Enter passphrase to continue</p>

        <form onSubmit={handleSubmit} className="login-form">
          <input
            type="password"
            className="login-input"
            placeholder="Passphrase"
            value={passphrase}
            onChange={(e) => setPassphrase(e.target.value)}
            autoFocus
            disabled={loading}
          />
          {error && <div className="login-error">{error}</div>}
          <button
            type="submit"
            className="login-button"
            disabled={loading || !passphrase.trim()}
          >
            {loading ? 'Authenticating...' : 'Enter'}
          </button>
        </form>
      </div>
    </div>
  );
}
