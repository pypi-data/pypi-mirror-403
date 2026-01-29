import { useEffect, useRef, useState } from 'react';
import { getAuthenticatedUrl, fetchWithAuth } from '../api';

interface VideoPlayerProps {
  streamUrl: string;
  title: string;
  isTranscoded?: boolean;
  videoId?: number;
}

interface TranscodeProgress {
  status: 'pending' | 'transcoding' | 'complete';
  transcoded_seconds: number;
  total_seconds: number;
  percent: number;
  is_complete: boolean;
}

export default function VideoPlayer({ streamUrl, title, isTranscoded, videoId }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [useHls, setUseHls] = useState(false);
  const [hlsLoaded, setHlsLoaded] = useState(false);
  const [progress, setProgress] = useState<TranscodeProgress | null>(null);

  useEffect(() => {
    // Add webkit-playsinline for legacy iOS support
    if (videoRef.current) {
      videoRef.current.setAttribute('webkit-playsinline', '');
    }
  }, []);

  // Poll transcoding progress
  useEffect(() => {
    if (!isTranscoded || !videoId) return;

    const pollProgress = async () => {
      try {
        const response = await fetchWithAuth(`/api/stream/${videoId}/hls/progress`);
        if (response.ok) {
          const data = await response.json();
          setProgress(data);
          return data.is_complete;
        }
      } catch (e) {
        // Ignore errors
      }
      return false;
    };

    // Initial poll
    pollProgress();

    // Continue polling until complete
    const interval = setInterval(async () => {
      const complete = await pollProgress();
      if (complete) {
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isTranscoded, videoId]);

  useEffect(() => {
    if (!isTranscoded || !videoId || !videoRef.current) return;

    const video = videoRef.current;

    // Check if browser natively supports HLS (Safari)
    const nativeHlsSupport = video.canPlayType('application/vnd.apple.mpegurl') !== '';

    if (nativeHlsSupport) {
      // Safari/iOS - use native HLS support
      setUseHls(true);
      setHlsLoaded(true);
    } else {
      // Chrome/Firefox - need to dynamically load hls.js
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/hls.js@latest';
      script.onload = () => {
        setUseHls(true);
        setHlsLoaded(true);
      };
      document.head.appendChild(script);
    }
  }, [isTranscoded, videoId]);

  useEffect(() => {
    if (!useHls || !hlsLoaded || !isTranscoded || !videoId || !videoRef.current) return;

    const video = videoRef.current;
    const hlsUrl = getAuthenticatedUrl(`/api/stream/${videoId}/hls/playlist.m3u8`);

    // Check if native HLS support
    if (video.canPlayType('application/vnd.apple.mpegurl') !== '') {
      video.src = hlsUrl;
      video.play().catch(() => {});
    } else if ((window as any).Hls && (window as any).Hls.isSupported()) {
      // Use hls.js for Chrome/Firefox
      const hls = new (window as any).Hls();
      hls.loadSource(hlsUrl);
      hls.attachMedia(video);
      hls.on((window as any).Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(() => {});
      });
    }
  }, [useHls, hlsLoaded, isTranscoded, videoId]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // For non-transcoded videos, use regular MP4 streaming
  if (!isTranscoded) {
    return (
      <div className="video-player-container">
        <video
          ref={videoRef}
          controls
          autoPlay
          playsInline
          preload="auto"
          className="video-player"
          title={title}
        >
          <source
            src={getAuthenticatedUrl(streamUrl)}
            type='video/mp4; codecs="avc1.42E01E, mp4a.40.2"'
          />
          Your browser does not support HTML5 video.
        </video>
      </div>
    );
  }

  // For transcoded videos, use HLS with progress indicator
  return (
    <div className="video-player-container">
      <video
        ref={videoRef}
        controls
        autoPlay
        playsInline
        preload="auto"
        className="video-player"
        title={title}
      >
        Your browser does not support HTML5 video.
      </video>
      {progress && !progress.is_complete && (
        <div className="transcode-progress">
          <div className="transcode-progress-bar">
            <div
              className="transcode-progress-fill"
              style={{ width: `${progress.percent}%` }}
            />
          </div>
          <div className="transcode-progress-text">
            Transcoding: {formatTime(progress.transcoded_seconds)} / {formatTime(progress.total_seconds)} ({progress.percent}% seekable)
          </div>
        </div>
      )}
    </div>
  );
}
