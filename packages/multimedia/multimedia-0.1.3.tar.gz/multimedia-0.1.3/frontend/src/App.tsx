import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import LoginPage from './components/LoginPage';
import HomePage from './pages/HomePage';
import VideoPage from './pages/VideoPage';
import TagsPage from './pages/TagsPage';
import TagVideosPage from './pages/TagVideosPage';
import UntaggedVideosPage from './pages/UntaggedVideosPage';
import BulkEditTagsPage from './pages/BulkEditTagsPage';
import { checkAuth } from './api';

function App() {
  const [authState, setAuthState] = useState<'loading' | 'authenticated' | 'login'>('loading');

  useEffect(() => {
    const verifyAuth = async () => {
      try {
        const status = await checkAuth();
        if (!status.requires_auth || status.authenticated) {
          setAuthState('authenticated');
        } else {
          setAuthState('login');
        }
      } catch {
        setAuthState('login');
      }
    };

    verifyAuth();
  }, []);

  if (authState === 'loading') {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (authState === 'login') {
    return <LoginPage onAuthenticated={() => setAuthState('authenticated')} />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="video/:id" element={<VideoPage />} />
          <Route path="tags" element={<TagsPage />} />
          <Route path="tags/bulk-edit" element={<BulkEditTagsPage />} />
          <Route path="tags/untagged" element={<UntaggedVideosPage />} />
          <Route path="tag/:tagId" element={<TagVideosPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
