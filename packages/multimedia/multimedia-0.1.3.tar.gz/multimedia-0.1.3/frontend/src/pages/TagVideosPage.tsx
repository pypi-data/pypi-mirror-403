import { useState, useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import VideoGrid from '../components/VideoGrid';
import { fetchVideosByTag } from '../api';
import type { Video, Tag } from '../types';

export default function TagVideosPage() {
  const { tagId } = useParams<{ tagId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const [videos, setVideos] = useState<Video[]>([]);
  const [tag, setTag] = useState<Tag | null>(null);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const search = searchParams.get('search') || '';
  const sort = searchParams.get('sort') || 'title_asc';

  useEffect(() => {
    const loadVideos = async () => {
      if (!tagId) return;

      setLoading(true);
      try {
        const response = await fetchVideosByTag(parseInt(tagId, 10), {
          page,
          search,
          sort,
          per_page: 24,
        });
        setVideos(response.videos);
        setTotalPages(response.total_pages);
        setTotal(response.total);
        setTag(response.tag);
      } catch (error) {
        console.error('Failed to load videos:', error);
      } finally {
        setLoading(false);
      }
    };

    loadVideos();
  }, [tagId, page, search, sort]);

  const handlePageChange = (newPage: number) => {
    const params = new URLSearchParams(searchParams);
    params.set('page', String(newPage));
    setSearchParams(params);
  };

  const handleSortChange = (newSort: string) => {
    const params = new URLSearchParams(searchParams);
    params.set('sort', newSort);
    params.delete('page');
    setSearchParams(params);
  };

  return (
    <div className="tag-videos-page">
      <div className="page-header">
        <Link to="/tags" className="back-to-tags">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
          </svg>
          All Tags
        </Link>
        {tag && (
          <h1 className="page-title">
            <span className="tag-icon">
              <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
                <path d="M21.41 11.58l-9-9C12.05 2.22 11.55 2 11 2H4c-1.1 0-2 .9-2 2v7c0 .55.22 1.05.59 1.42l9 9c.36.36.86.58 1.41.58.55 0 1.05-.22 1.41-.59l7-7c.37-.36.59-.86.59-1.41 0-.55-.23-1.06-.59-1.42zM5.5 7C4.67 7 4 6.33 4 5.5S4.67 4 5.5 4 7 4.67 7 5.5 6.33 7 5.5 7z"/>
              </svg>
            </span>
            {tag.name}
          </h1>
        )}
      </div>

      <div className="toolbar">
        <div className="result-count">
          {total > 0 && (
            <span>{total} video{total !== 1 ? 's' : ''}</span>
          )}
        </div>
        <select
          className="sort-select"
          value={sort}
          onChange={(e) => handleSortChange(e.target.value)}
        >
          <option value="date_desc">Newest first</option>
          <option value="date_asc">Oldest first</option>
          <option value="title_asc">Title A-Z</option>
          <option value="title_desc">Title Z-A</option>
        </select>
      </div>

      <VideoGrid videos={videos} loading={loading} />

      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="page-button"
            disabled={page <= 1}
            onClick={() => handlePageChange(page - 1)}
          >
            Previous
          </button>
          <span className="page-info">
            Page {page} of {totalPages}
          </span>
          <button
            className="page-button"
            disabled={page >= totalPages}
            onClick={() => handlePageChange(page + 1)}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
