import { useState, useEffect, useRef } from 'react';
import { addTagToVideo, removeTagFromVideo, fetchTags } from '../api';
import type { Tag, TagWithCount } from '../types';

interface EditTagsModalProps {
  videoId: number;
  tags: Tag[];
  onClose: () => void;
  onTagsUpdated: (tags: Tag[]) => void;
}

export default function EditTagsModal({ videoId, tags, onClose, onTagsUpdated }: EditTagsModalProps) {
  const [currentTags, setCurrentTags] = useState<Tag[]>(tags);
  const [newTagName, setNewTagName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [allTags, setAllTags] = useState<TagWithCount[]>([]);
  const [suggestions, setSuggestions] = useState<TagWithCount[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchTags().then((res) => setAllTags(res.tags)).catch(console.error);
  }, []);

  useEffect(() => {
    if (newTagName.trim()) {
      const query = newTagName.toLowerCase();
      const currentTagIds = new Set(currentTags.map((t) => t.id));
      const filtered = allTags
        .filter((t) => !currentTagIds.has(t.id) && t.name.toLowerCase().includes(query))
        .slice(0, 8);
      setSuggestions(filtered);
      setShowSuggestions(filtered.length > 0);
      setSelectedIndex(-1);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [newTagName, allTags, currentTags]);

  const selectSuggestion = (tag: TagWithCount) => {
    setNewTagName(tag.name);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : prev));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      selectSuggestion(suggestions[selectedIndex]);
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  const handleAddTag = async (e: React.FormEvent) => {
    e.preventDefault();
    const tagName = newTagName.trim();
    if (!tagName) return;

    // Check if tag already exists
    if (currentTags.some((t) => t.name.toLowerCase() === tagName.toLowerCase())) {
      setError('Tag already exists');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const newTag = await addTagToVideo(videoId, tagName);
      const updatedTags = [...currentTags, newTag].sort((a, b) => a.name.localeCompare(b.name));
      setCurrentTags(updatedTags);
      onTagsUpdated(updatedTags);
      setNewTagName('');
    } catch (err) {
      setError('Failed to add tag');
      console.error('Failed to add tag:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveTag = async (tagId: number) => {
    setLoading(true);
    setError(null);

    try {
      await removeTagFromVideo(videoId, tagId);
      const updatedTags = currentTags.filter((t) => t.id !== tagId);
      setCurrentTags(updatedTags);
      onTagsUpdated(updatedTags);
    } catch (err) {
      setError('Failed to remove tag');
      console.error('Failed to remove tag:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal">
        <div className="modal-header">
          <h2>Edit Tags</h2>
          <button className="modal-close" onClick={onClose}>
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>

        <div className="modal-body">
          <form className="add-tag-form" onSubmit={handleAddTag}>
            <div className="tag-input-wrapper">
              <input
                ref={inputRef}
                type="text"
                className="tag-input"
                placeholder="Add a tag..."
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => newTagName.trim() && suggestions.length > 0 && setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                disabled={loading}
                autoComplete="off"
              />
              {showSuggestions && (
                <div className="tag-suggestions" ref={suggestionsRef}>
                  {suggestions.map((tag, index) => (
                    <div
                      key={tag.id}
                      className={`tag-suggestion${index === selectedIndex ? ' selected' : ''}`}
                      onMouseDown={() => selectSuggestion(tag)}
                    >
                      <span className="suggestion-name">{tag.name}</span>
                      <span className="suggestion-count">{tag.video_count}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button type="submit" className="add-tag-button" disabled={loading || !newTagName.trim()}>
              Add
            </button>
          </form>

          {error && <div className="tag-error">{error}</div>}

          <div className="current-tags">
            {currentTags.length === 0 ? (
              <p className="no-tags">No tags yet</p>
            ) : (
              <div className="tag-list">
                {currentTags.map((tag) => (
                  <div key={tag.id} className="tag-item">
                    <span className="tag-name">{tag.name}</span>
                    <button
                      className="tag-remove"
                      onClick={() => handleRemoveTag(tag.id)}
                      disabled={loading}
                      title="Remove tag"
                    >
                      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
