import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fetchTags, fetchUntaggedCount } from '../api';
import type { TagWithCount } from '../types';

export default function TagsPage() {
  const [tags, setTags] = useState<TagWithCount[]>([]);
  const [untaggedCount, setUntaggedCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadTags = async () => {
      try {
        const [tagsResponse, untaggedResponse] = await Promise.all([
          fetchTags(),
          fetchUntaggedCount(),
        ]);
        setTags(tagsResponse.tags);
        setUntaggedCount(untaggedResponse.count);
      } catch (error) {
        console.error('Failed to load tags:', error);
      } finally {
        setLoading(false);
      }
    };

    loadTags();
  }, []);

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading tags...</p>
      </div>
    );
  }

  if (tags.length === 0 && untaggedCount === 0) {
    return (
      <div className="tags-page">
        <div className="tags-header-row">
          <h1 className="page-title">Tags</h1>
          <Link to="/tags/bulk-edit" className="bulk-edit-link">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
            </svg>
            Bulk Edit
          </Link>
        </div>
        <div className="empty-state">
          <svg viewBox="0 0 24 24" width="64" height="64" fill="currentColor">
            <path d="M21.41 11.58l-9-9C12.05 2.22 11.55 2 11 2H4c-1.1 0-2 .9-2 2v7c0 .55.22 1.05.59 1.42l9 9c.36.36.86.58 1.41.58.55 0 1.05-.22 1.41-.59l7-7c.37-.36.59-.86.59-1.41 0-.55-.23-1.06-.59-1.42zM5.5 7C4.67 7 4 6.33 4 5.5S4.67 4 5.5 4 7 4.67 7 5.5 6.33 7 5.5 7z"/>
          </svg>
          <p>No tags yet</p>
          <p className="empty-hint">Add tags to videos to organize your collection</p>
        </div>
      </div>
    );
  }

  return (
    <div className="tags-page">
      <div className="tags-header-row">
        <h1 className="page-title">Tags</h1>
        <Link to="/tags/bulk-edit" className="bulk-edit-link">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
          </svg>
          Bulk Edit
        </Link>
      </div>
      <div className="tags-grid">
        {untaggedCount > 0 && (
          <Link to="/tags/untagged" className="tag-card tag-card-untagged">
            <span className="tag-name">Untagged</span>
            <span className="tag-count">
              {untaggedCount} video{untaggedCount !== 1 ? 's' : ''}
            </span>
          </Link>
        )}
        {tags.map((tag) => (
          <Link key={tag.id} to={`/tag/${tag.id}`} className="tag-card">
            <span className="tag-name">{tag.name}</span>
            <span className="tag-count">
              {tag.video_count} video{tag.video_count !== 1 ? 's' : ''}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
