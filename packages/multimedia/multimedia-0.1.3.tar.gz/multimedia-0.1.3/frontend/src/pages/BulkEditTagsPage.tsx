import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchVideos, fetchVideoTags, addTagToVideo, removeTagFromVideo, getAuthenticatedUrl, fetchTags } from '../api';
import type { Video, Tag, TagWithCount } from '../types';

interface VideoWithTags {
  video: Video;
  tags: Tag[];
  loading: boolean;
}

interface SelectionBox {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
}

export default function BulkEditTagsPage() {
  const [videos, setVideos] = useState<VideoWithTags[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [selectionBox, setSelectionBox] = useState<SelectionBox | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [allTags, setAllTags] = useState<TagWithCount[]>([]);
  const [suggestions, setSuggestions] = useState<TagWithCount[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const rowRefs = useRef<Map<number, HTMLTableRowElement>>(new Map());
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const loadVideos = async () => {
      try {
        const allVideos: Video[] = [];
        let page = 1;
        const perPage = 100;

        while (true) {
          const response = await fetchVideos({ page, per_page: perPage, sort: 'title_asc' });
          allVideos.push(...response.videos);
          if (page >= response.total_pages) break;
          page++;
        }

        const videosWithTags: VideoWithTags[] = allVideos.map((video) => ({
          video,
          tags: [],
          loading: true,
        }));
        setVideos(videosWithTags);
        setLoading(false);

        for (let i = 0; i < videosWithTags.length; i++) {
          try {
            const tags = await fetchVideoTags(videosWithTags[i].video.id);
            setVideos((prev) => {
              const updated = [...prev];
              updated[i] = { ...updated[i], tags, loading: false };
              return updated;
            });
          } catch (error) {
            console.error(`Failed to load tags for video ${videosWithTags[i].video.id}:`, error);
            setVideos((prev) => {
              const updated = [...prev];
              updated[i] = { ...updated[i], loading: false };
              return updated;
            });
          }
        }
      } catch (error) {
        console.error('Failed to load videos:', error);
        setLoading(false);
      }
    };

    loadVideos();
  }, []);

  useEffect(() => {
    fetchTags().then((res) => setAllTags(res.tags)).catch(console.error);
  }, []);

  useEffect(() => {
    if (newTagName.trim()) {
      const query = newTagName.toLowerCase();
      const filtered = allTags
        .filter((t) => t.name.toLowerCase().includes(query))
        .slice(0, 8);
      setSuggestions(filtered);
      setShowSuggestions(filtered.length > 0);
      setSelectedIndex(-1);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [newTagName, allTags]);

  const getRowsInSelectionBox = useCallback((box: SelectionBox): number[] => {
    const selectedVideoIds: number[] = [];
    const minX = Math.min(box.startX, box.endX);
    const maxX = Math.max(box.startX, box.endX);
    const minY = Math.min(box.startY, box.endY);
    const maxY = Math.max(box.startY, box.endY);

    rowRefs.current.forEach((row, videoId) => {
      const rect = row.getBoundingClientRect();
      const containerRect = containerRef.current?.getBoundingClientRect();
      if (!containerRect) return;

      const rowTop = rect.top - containerRect.top + (containerRef.current?.scrollTop || 0);
      const rowBottom = rowTop + rect.height;
      const rowLeft = rect.left - containerRect.left;
      const rowRight = rowLeft + rect.width;

      if (rowBottom >= minY && rowTop <= maxY && rowRight >= minX && rowLeft <= maxX) {
        selectedVideoIds.push(videoId);
      }
    });

    return selectedVideoIds;
  }, []);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLButtonElement) {
      return;
    }
    if ((e.target as HTMLElement).closest('a')) {
      return;
    }

    const containerRect = containerRef.current?.getBoundingClientRect();
    if (!containerRect) return;

    const x = e.clientX - containerRect.left;
    const y = e.clientY - containerRect.top + (containerRef.current?.scrollTop || 0);

    setIsSelecting(true);
    setSelectionBox({ startX: x, startY: y, endX: x, endY: y });

    if (!e.shiftKey) {
      setSelectedIds(new Set());
    }
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isSelecting || !containerRef.current) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - containerRect.left;
    const y = e.clientY - containerRect.top + (containerRef.current.scrollTop || 0);

    setSelectionBox((prev) => prev ? { ...prev, endX: x, endY: y } : null);
  }, [isSelecting]);

  const handleMouseUp = useCallback(() => {
    if (isSelecting && selectionBox) {
      const selectedVideoIds = getRowsInSelectionBox(selectionBox);
      setSelectedIds((prev) => {
        const newSet = new Set(prev);
        selectedVideoIds.forEach((id) => newSet.add(id));
        return newSet;
      });
    }
    setIsSelecting(false);
    setSelectionBox(null);
  }, [isSelecting, selectionBox, getRowsInSelectionBox]);

  useEffect(() => {
    if (isSelecting) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isSelecting, handleMouseMove, handleMouseUp]);

  const handleRowClick = (videoId: number, e: React.MouseEvent) => {
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLButtonElement) {
      return;
    }
    if ((e.target as HTMLElement).closest('a')) {
      return;
    }

    e.preventDefault();
    setSelectedIds((prev) => {
      const newSet = new Set(prev);
      if (e.shiftKey || e.metaKey || e.ctrlKey) {
        if (newSet.has(videoId)) {
          newSet.delete(videoId);
        } else {
          newSet.add(videoId);
        }
      } else {
        newSet.clear();
        newSet.add(videoId);
      }
      return newSet;
    });
  };

  const getSelectedTags = (): Tag[] => {
    const tagMap = new Map<number, Tag>();
    videos
      .filter((v) => selectedIds.has(v.video.id))
      .forEach((v) => {
        v.tags.forEach((tag) => {
          if (!tagMap.has(tag.id)) {
            tagMap.set(tag.id, tag);
          }
        });
      });
    return Array.from(tagMap.values()).sort((a, b) => a.name.localeCompare(b.name));
  };

  const handleAddTagToSelected = async () => {
    const tagName = newTagName.trim();
    if (!tagName || selectedIds.size === 0) return;

    setActionLoading(true);
    try {
      for (const videoId of selectedIds) {
        const newTag = await addTagToVideo(videoId, tagName);
        setVideos((prev) =>
          prev.map((v) =>
            v.video.id === videoId && !v.tags.some((t) => t.id === newTag.id)
              ? { ...v, tags: [...v.tags, newTag].sort((a, b) => a.name.localeCompare(b.name)) }
              : v
          )
        );
      }
      setNewTagName('');
    } catch (error) {
      console.error('Failed to add tag:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRemoveTagFromSelected = async (tagId: number) => {
    if (selectedIds.size === 0) return;

    setActionLoading(true);
    try {
      for (const videoId of selectedIds) {
        const video = videos.find((v) => v.video.id === videoId);
        if (video?.tags.some((t) => t.id === tagId)) {
          await removeTagFromVideo(videoId, tagId);
          setVideos((prev) =>
            prev.map((v) =>
              v.video.id === videoId ? { ...v, tags: v.tags.filter((t) => t.id !== tagId) } : v
            )
          );
        }
      }
    } catch (error) {
      console.error('Failed to remove tag:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSelectAll = () => {
    setSelectedIds(new Set(videos.map((v) => v.video.id)));
  };

  const handleClearSelection = () => {
    setSelectedIds(new Set());
  };

  const selectSuggestion = (tag: TagWithCount) => {
    setNewTagName(tag.name);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (showSuggestions && suggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : prev));
        return;
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        return;
      } else if (e.key === 'Enter' && selectedIndex >= 0) {
        e.preventDefault();
        selectSuggestion(suggestions[selectedIndex]);
        return;
      } else if (e.key === 'Escape') {
        setShowSuggestions(false);
        return;
      }
    }
    if (e.key === 'Enter' && !actionLoading) {
      e.preventDefault();
      handleAddTagToSelected();
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading videos...</p>
      </div>
    );
  }

  const selectedTags = getSelectedTags();

  return (
    <div className="bulk-edit-page">
      <div className="page-header">
        <Link to="/tags" className="back-to-tags">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
          </svg>
          Back to Tags
        </Link>
        <h1 className="page-title">Bulk Edit Tags</h1>
        <p className="page-subtitle">
          {videos.length} videos — Click and drag to select, or Ctrl/Cmd+click for multiple
        </p>
      </div>

      {selectedIds.size > 0 && (
        <div className="selection-toolbar">
          <div className="selection-info">
            <span className="selection-count">{selectedIds.size} selected</span>
            <button className="clear-selection" onClick={handleClearSelection}>
              Clear
            </button>
            <button className="select-all" onClick={handleSelectAll}>
              Select All
            </button>
          </div>

          <div className="selection-actions">
            <div className="selected-tags">
              <span className="selected-tags-label">Tags on selected:</span>
              {selectedTags.length === 0 ? (
                <span className="no-tags-hint">No tags</span>
              ) : (
                <div className="selected-tags-list">
                  {selectedTags.map((tag) => (
                    <span key={tag.id} className="selected-tag">
                      {tag.name}
                      <button
                        className="selected-tag-remove"
                        onClick={() => handleRemoveTagFromSelected(tag.id)}
                        disabled={actionLoading}
                        title={`Remove "${tag.name}" from selected videos`}
                      >
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
                        </svg>
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="add-tag-to-selected">
              <div className="tag-input-wrapper">
                <input
                  ref={inputRef}
                  type="text"
                  className="bulk-tag-input"
                  placeholder="Add tag to selected..."
                  value={newTagName}
                  onChange={(e) => setNewTagName(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onFocus={() => newTagName.trim() && suggestions.length > 0 && setShowSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                  disabled={actionLoading}
                  autoComplete="off"
                />
                {showSuggestions && (
                  <div className="tag-suggestions">
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
              <button
                className="bulk-add-button"
                onClick={handleAddTagToSelected}
                disabled={actionLoading || !newTagName.trim()}
              >
                Add to {selectedIds.size}
              </button>
            </div>
          </div>
        </div>
      )}

      <div
        className="bulk-edit-table-container"
        ref={containerRef}
        onMouseDown={handleMouseDown}
        style={{ position: 'relative', userSelect: 'none' }}
      >
        {selectionBox && isSelecting && (
          <div
            className="selection-rectangle"
            style={{
              position: 'absolute',
              left: Math.min(selectionBox.startX, selectionBox.endX),
              top: Math.min(selectionBox.startY, selectionBox.endY),
              width: Math.abs(selectionBox.endX - selectionBox.startX),
              height: Math.abs(selectionBox.endY - selectionBox.startY),
              pointerEvents: 'none',
            }}
          />
        )}

        <table className="bulk-edit-table">
          <thead>
            <tr>
              <th className="col-filename">Video</th>
              <th className="col-tags">Tags</th>
            </tr>
          </thead>
          <tbody>
            {videos.map(({ video, tags, loading: tagsLoading }) => (
              <tr
                key={video.id}
                ref={(el) => {
                  if (el) rowRefs.current.set(video.id, el);
                }}
                className={selectedIds.has(video.id) ? 'selected' : ''}
                onClick={(e) => handleRowClick(video.id, e)}
              >
                <td className="col-filename">
                  <div className="video-info-cell">
                    <img src={getAuthenticatedUrl(video.thumbnail_url)} alt="" className="mini-thumbnail" />
                    <span className="video-title-text">{video.title}</span>
                  </div>
                </td>
                <td className="col-tags">
                  {tagsLoading ? (
                    <span className="tags-loading">Loading...</span>
                  ) : tags.length === 0 ? (
                    <span className="no-tags-cell">—</span>
                  ) : (
                    <div className="tags-display">
                      {tags.map((tag) => (
                        <span key={tag.id} className="display-tag">
                          {tag.name}
                        </span>
                      ))}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
