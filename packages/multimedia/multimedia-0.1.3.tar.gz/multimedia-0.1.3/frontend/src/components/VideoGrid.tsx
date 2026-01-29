import VideoCard from './VideoCard';
import type { Video } from '../types';

interface VideoGridProps {
  videos: Video[];
  loading?: boolean;
}

export default function VideoGrid({ videos, loading }: VideoGridProps) {
  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading videos...</p>
      </div>
    );
  }

  if (videos.length === 0) {
    return (
      <div className="empty-state">
        <svg viewBox="0 0 24 24" width="64" height="64" fill="currentColor">
          <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z"/>
        </svg>
        <p>No videos found</p>
      </div>
    );
  }

  return (
    <div className="video-grid">
      {videos.map((video) => (
        <VideoCard key={video.id} video={video} />
      ))}
    </div>
  );
}
