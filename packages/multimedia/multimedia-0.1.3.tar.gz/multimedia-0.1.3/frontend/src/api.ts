import type { VideoListResponse, VideoDetail, SystemStatus, TagListResponse, Tag, VideoListByTagResponse } from './types';

const API_BASE = '/api';
const TOKEN_KEY = 'multimedia_token';

export function getStoredToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

function getAuthHeaders(): HeadersInit {
  const token = getStoredToken();
  if (token) {
    return { 'Authorization': `Bearer ${token}` };
  }
  return {};
}

export function getAuthenticatedUrl(url: string): string {
  const token = getStoredToken();
  if (token) {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}token=${encodeURIComponent(token)}`;
  }
  return url;
}

async function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = {
    ...getAuthHeaders(),
    ...options.headers,
  };
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    clearStoredToken();
    window.location.reload();
  }
  return response;
}

// Export for use in components that need direct fetch access
export async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  return apiFetch(url, options);
}

export interface AuthStatus {
  requires_auth: boolean;
  authenticated: boolean;
}

export async function checkAuth(): Promise<AuthStatus> {
  const response = await fetch(`${API_BASE}/auth/check`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error('Failed to check auth');
  return response.json();
}

export async function fetchVideos(params: {
  page?: number;
  per_page?: number;
  search?: string;
  sort?: string;
}): Promise<VideoListResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.per_page) searchParams.set('per_page', String(params.per_page));
  if (params.search) searchParams.set('search', params.search);
  if (params.sort) searchParams.set('sort', params.sort);

  const response = await apiFetch(`${API_BASE}/videos?${searchParams}`);
  if (!response.ok) throw new Error('Failed to fetch videos');
  return response.json();
}

export async function fetchVideo(id: number): Promise<VideoDetail> {
  const response = await apiFetch(`${API_BASE}/videos/${id}`);
  if (!response.ok) throw new Error('Failed to fetch video');
  return response.json();
}

export async function triggerRescan(): Promise<{ status: string }> {
  const response = await apiFetch(`${API_BASE}/videos/rescan`, { method: 'POST' });
  if (!response.ok) throw new Error('Failed to trigger rescan');
  return response.json();
}

export async function fetchStatus(): Promise<SystemStatus> {
  const response = await apiFetch(`${API_BASE}/videos/status/info`);
  if (!response.ok) throw new Error('Failed to fetch status');
  return response.json();
}

// Tag API functions

export async function fetchTags(): Promise<TagListResponse> {
  const response = await apiFetch(`${API_BASE}/tags`);
  if (!response.ok) throw new Error('Failed to fetch tags');
  return response.json();
}

export async function fetchVideosByTag(
  tagId: number,
  params: {
    page?: number;
    per_page?: number;
    search?: string;
    sort?: string;
  }
): Promise<VideoListByTagResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.per_page) searchParams.set('per_page', String(params.per_page));
  if (params.search) searchParams.set('search', params.search);
  if (params.sort) searchParams.set('sort', params.sort);

  const response = await apiFetch(`${API_BASE}/tags/${tagId}/videos?${searchParams}`);
  if (!response.ok) throw new Error('Failed to fetch videos by tag');
  return response.json();
}

export async function fetchVideoTags(videoId: number): Promise<Tag[]> {
  const response = await apiFetch(`${API_BASE}/tags/video/${videoId}`);
  if (!response.ok) throw new Error('Failed to fetch video tags');
  return response.json();
}

export async function addTagToVideo(videoId: number, tagName: string): Promise<Tag> {
  const response = await apiFetch(`${API_BASE}/tags/video/${videoId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: tagName }),
  });
  if (!response.ok) throw new Error('Failed to add tag');
  return response.json();
}

export async function removeTagFromVideo(videoId: number, tagId: number): Promise<void> {
  const response = await apiFetch(`${API_BASE}/tags/video/${videoId}/${tagId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to remove tag');
}

export async function fetchUntaggedCount(): Promise<{ count: number }> {
  const response = await apiFetch(`${API_BASE}/tags/untagged/count`);
  if (!response.ok) throw new Error('Failed to fetch untagged count');
  return response.json();
}

export async function fetchUntaggedVideos(params: {
  page?: number;
  per_page?: number;
  search?: string;
  sort?: string;
}): Promise<VideoListResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set('page', String(params.page));
  if (params.per_page) searchParams.set('per_page', String(params.per_page));
  if (params.search) searchParams.set('search', params.search);
  if (params.sort) searchParams.set('sort', params.sort);

  const response = await apiFetch(`${API_BASE}/tags/untagged/videos?${searchParams}`);
  if (!response.ok) throw new Error('Failed to fetch untagged videos');
  return response.json();
}
