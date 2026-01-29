import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import VideoPlayer from '../components/VideoPlayer';
import EditTagsModal from '../components/EditTagsModal';
import { fetchVideo } from '../api';
import type { VideoDetail, Tag } from '../types';

export default function VideoPage() {
  const { id } = useParams<{ id: string }>();
  const [video, setVideo] = useState<VideoDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTagsModal, setShowTagsModal] = useState(false);

  useEffect(() => {
    const loadVideo = async () => {
      if (!id) return;

      setLoading(true);
      setError(null);

      try {
        const response = await fetchVideo(parseInt(id, 10));
        setVideo(response);
      } catch (err) {
        setError('Failed to load video');
        console.error('Failed to load video:', err);
      } finally {
        setLoading(false);
      }
    };

    loadVideo();
  }, [id]);

  const handleTagsUpdated = (updatedTags: Tag[]) => {
    if (video) {
      setVideo({ ...video, tags: updatedTags });
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading video...</p>
      </div>
    );
  }

  if (error || !video) {
    return (
      <div className="error-state">
        <p>{error || 'Video not found'}</p>
        <Link to="/" className="back-link">Back to home</Link>
      </div>
    );
  }

  return (
    <div className="video-page">
      <VideoPlayer
          streamUrl={video.stream_url}
          title={video.title}
          isTranscoded={video.is_transcoded}
          videoId={video.id}
        />

      <div className="video-details">
        <h1 className="video-title">{video.title}</h1>

        <div className="video-meta">
          <span className="resolution">{video.resolution}</span>
          <span className="separator">·</span>
          <span>{video.relative_date}</span>
          <span className="separator">·</span>
          <span>{video.file_size_human}</span>
          {video.is_transcoded && (
            <>
              <span className="separator">·</span>
              <span className="transcoding-badge" title="This video is being transcoded on-the-fly for browser playback">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                  <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/>
                </svg>
                Live Transcoding
              </span>
            </>
          )}
        </div>

        <div className="video-tags-section">
          <div className="tags-header">
            <span className="tags-label">Tags:</span>
            <button className="edit-tags-button" onClick={() => setShowTagsModal(true)}>
              <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
              </svg>
              Edit
            </button>
          </div>
          {video.tags.length > 0 ? (
            <div className="video-tags">
              {video.tags.map((tag) => (
                <Link key={tag.id} to={`/tag/${tag.id}`} className="video-tag">
                  {tag.name}
                </Link>
              ))}
            </div>
          ) : (
            <span className="no-tags-text">No tags</span>
          )}
        </div>

        <div className="video-tech-info">
          <div className="info-row">
            <span className="label">Duration:</span>
            <span>{video.duration}</span>
          </div>
          <div className="info-row">
            <span className="label">Resolution:</span>
            <span>{video.width} x {video.height}</span>
          </div>
          {video.codec && (
            <div className="info-row">
              <span className="label">Codec:</span>
              <span>{video.codec}</span>
            </div>
          )}
          {video.fps && (
            <div className="info-row">
              <span className="label">Frame Rate:</span>
              <span>{video.fps.toFixed(2)} fps</span>
            </div>
          )}
          <div className="info-row">
            <span className="label">File:</span>
            <span className="file-path">{video.file_path}</span>
          </div>
        </div>

        <Link to="/" className="back-link">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
          Back to videos
        </Link>
      </div>

      {showTagsModal && (
        <EditTagsModal
          videoId={video.id}
          tags={video.tags}
          onClose={() => setShowTagsModal(false)}
          onTagsUpdated={handleTagsUpdated}
        />
      )}
    </div>
  );
}
