export interface Tag {
  id: number;
  name: string;
}

export interface TagWithCount extends Tag {
  video_count: number;
}

export interface Video {
  id: number;
  title: string;
  thumbnail_url: string;
  duration: string;
  resolution: string;
  relative_date: string;
  file_size_human: string;
  tags: Tag[];
}

export interface VideoDetail extends Video {
  file_path: string;
  width: number;
  height: number;
  codec: string | null;
  fps: number | null;
  bitrate: number | null;
  file_size: number;
  file_modified_at: string;
  stream_url: string;
  tags: Tag[];
  is_transcoded: boolean;
}

export interface VideoListResponse {
  videos: Video[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ScanStatus {
  scanning: boolean;
  total_files: number;
  processed_files: number;
  remaining_files: number;
  current_file: string | null;
  new_files: number;
  skipped_files: number;
  error_count: number;
  last_scanned_at: string | null;
}

export interface SystemStatus {
  total_videos: number;
  multimedia_dir: string;
  database_path: string;
  scan: ScanStatus;
}

export interface TagListResponse {
  tags: TagWithCount[];
}

export interface VideoListByTagResponse extends VideoListResponse {
  tag: Tag;
}
