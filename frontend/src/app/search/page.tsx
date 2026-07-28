import { Header } from "@/components/header";
import { VideoCard } from "@/components/video-card";
import { getVideos } from "@/lib/api";

export default async function SearchPage({ searchParams }: PageProps<"/search">) {
  const params = await searchParams;
  const query = typeof params.q === "string" ? params.q : "";
  const videos = await getVideos(query);
  return <div className="min-h-screen bg-[#08080a] text-white"><Header /><main className="mx-auto max-w-7xl px-5 py-10 sm:px-8 lg:px-10"><p className="text-sm text-indigo-300">Search results</p><h1 className="mt-1 text-3xl font-bold">{query ? <>Videos for “{query}”</> : "Search TubeLite"}</h1><div className="mt-9 grid gap-x-5 gap-y-9 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">{videos.map((video) => <VideoCard key={video.id} video={video} />)}</div>{videos.length === 0 && <p className="mt-16 text-zinc-400">No videos found. Try another search.</p>}</main></div>;
}
