export type Author = { id: string; username: string; avatar_url: string | null };
export type Video = { id: string; title: string; description: string | null; thumbnail_url: string | null; duration: number | null; view_count: number; created_at: string; author: Author };

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const sampleVideos: Video[] = [
  { id: "building-for-the-web", title: "Building things for the web", description: "A practical design session.", thumbnail_url: null, duration: 742, view_count: 1240, created_at: "2026-07-28T00:00:00Z", author: { id: "1", username: "Mira Patel", avatar_url: null } },
  { id: "quiet-mornings", title: "How to make space for quiet mornings", description: "A small ritual with a big impact.", thumbnail_url: null, duration: 510, view_count: 892, created_at: "2026-07-27T00:00:00Z", author: { id: "2", username: "Sunday Studio", avatar_url: null } },
  { id: "city-in-motion", title: "A city in motion", description: "A short film from the street.", thumbnail_url: null, duration: 214, view_count: 2389, created_at: "2026-07-25T00:00:00Z", author: { id: "3", username: "Leah Chen", avatar_url: null } },
  { id: "creative-reset", title: "The creative reset you need", description: "Five ways to restart a stuck project.", thumbnail_url: null, duration: 866, view_count: 634, created_at: "2026-07-23T00:00:00Z", author: { id: "4", username: "Office Hours", avatar_url: null } },
];

export async function getVideos(query?: string): Promise<Video[]> {
  const path = query ? `/api/videos/search?q=${encodeURIComponent(query)}` : "/api/videos";
  try {
    const response = await fetch(`${apiUrl}${path}`, { next: { revalidate: 30 } });
    if (!response.ok) throw new Error("Video request failed");
    return (await response.json() as { items: Video[] }).items;
  } catch {
    const normalized = query?.toLowerCase();
    return normalized ? sampleVideos.filter((video) => video.title.toLowerCase().includes(normalized)) : sampleVideos;
  }
}

export async function getVideo(id: string): Promise<Video | undefined> {
  try {
    const response = await fetch(`${apiUrl}/api/videos/${id}`, { cache: "no-store" });
    return response.ok ? response.json() as Promise<Video> : undefined;
  } catch { return sampleVideos.find((video) => video.id === id); }
}

export function formatDuration(seconds: number | null) {
  if (!seconds) return "—";
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

export function formatViews(count: number) { return new Intl.NumberFormat("en", { notation: "compact" }).format(count); }
