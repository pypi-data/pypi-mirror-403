import { useState, useEffect } from 'react';
import { fetchStatus, triggerRescan } from '../api';
import type { ScanStatus } from '../types';

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return 'just now';
  } else if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  } else {
    return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  }
}

export default function IndexingStatus() {
  const [status, setStatus] = useState<ScanStatus | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [rescanPending, setRescanPending] = useState(false);

  useEffect(() => {
    let interval: number | undefined;

    const checkStatus = async () => {
      try {
        const response = await fetchStatus();
        setStatus(response.scan);
        setIsScanning(response.scan.scanning);
      } catch (error) {
        console.error('Failed to fetch status:', error);
      }
    };

    // Initial check
    checkStatus();

    // Poll every 2 seconds
    interval = window.setInterval(checkStatus, 2000);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, []);

  const handleRescan = async () => {
    setRescanPending(true);
    try {
      await triggerRescan();
      // Status will update via polling
    } catch (error) {
      console.error('Failed to trigger rescan:', error);
    } finally {
      setRescanPending(false);
    }
  };

  // Show scanning progress
  if (isScanning && status) {
    const progress = status.total_files > 0
      ? Math.round((status.processed_files / status.total_files) * 100)
      : 0;

    return (
      <div className="indexing-status">
        <div className="indexing-content">
          <div className="indexing-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" className="spin">
              <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/>
            </svg>
          </div>
          <div className="indexing-info">
            <div className="indexing-text">
              Indexing videos: {status.processed_files} / {status.total_files}
              {status.remaining_files > 0 && ` (${status.remaining_files} remaining)`}
            </div>
            <div className="indexing-file" title={status.current_file || ''}>
              {status.current_file}
            </div>
          </div>
          <div className="indexing-progress-container">
            <div className="indexing-progress-bar" style={{ width: `${progress}%` }} />
          </div>
        </div>
      </div>
    );
  }

  // Show rescan button when not scanning
  return (
    <div className="rescan-bar">
      <button
        className="rescan-button"
        onClick={handleRescan}
        disabled={rescanPending}
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
          <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/>
        </svg>
        {rescanPending ? 'Starting...' : 'Rescan Library'}
      </button>
      {status && (
        <span className="video-count">
          {status.processed_files} videos indexed
          {status.last_scanned_at && (
            <span className="last-scanned"> · Last scanned {formatRelativeTime(status.last_scanned_at)}</span>
          )}
        </span>
      )}
    </div>
  );
}
