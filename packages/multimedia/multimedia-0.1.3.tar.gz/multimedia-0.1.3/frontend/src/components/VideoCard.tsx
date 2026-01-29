import { Link } from 'react-router-dom';
import type { Video } from '../types';
import { getAuthenticatedUrl } from '../api';

interface VideoCardProps {
  video: Video;
}

export default function VideoCard({ video }: VideoCardProps) {
  return (
    <Link to={`/video/${video.id}`} className="video-card">
      <div className="thumbnail-container">
        <img
          src={getAuthenticatedUrl(video.thumbnail_url)}
          alt={video.title}
          loading="lazy"
        />
        <span className="duration">{video.duration}</span>
      </div>
      <div className="video-info">
        <h3 className="title">{video.title}</h3>
        <div className="metadata">
          <span className="resolution">{video.resolution}</span>
          <span className="separator">·</span>
          <span className="date">{video.relative_date}</span>
        </div>
        <span className="file-size">{video.file_size_human}</span>
        {video.tags.length > 0 && (
          <div className="card-tags">
            {video.tags.map(tag => (
              <Link
                key={tag.id}
                to={`/tag/${tag.id}`}
                className="card-tag"
                onClick={(e) => e.stopPropagation()}
              >
                {tag.name}
              </Link>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}
