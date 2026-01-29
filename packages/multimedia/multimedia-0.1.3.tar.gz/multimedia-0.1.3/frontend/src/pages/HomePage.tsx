import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import VideoGrid from '../components/VideoGrid';
import { fetchVideos } from '../api';
import type { Video } from '../types';

export default function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const search = searchParams.get('search') || '';
  const sort = searchParams.get('sort') || 'title_asc';

  useEffect(() => {
    const loadVideos = async () => {
      setLoading(true);
      try {
        const response = await fetchVideos({ page, search, sort, per_page: 24 });
        setVideos(response.videos);
        setTotalPages(response.total_pages);
        setTotal(response.total);
      } catch (error) {
        console.error('Failed to load videos:', error);
      } finally {
        setLoading(false);
      }
    };

    loadVideos();
  }, [page, search, sort]);

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
    <div className="home-page">
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
