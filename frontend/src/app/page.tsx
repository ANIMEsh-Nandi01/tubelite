import { Header } from "@/components/header";
import { VideoCard } from "@/components/video-card";
import { getVideos } from "@/lib/api";

export default async function Home() {
  const videos = await getVideos();

  return (
    <div className="min-h-screen bg-[#08080a] text-white">
      <Header />
      <main className="mx-auto max-w-7xl px-5 py-10 sm:px-8 lg:px-10">
        <section className="mb-12 overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-indigo-500/20 via-[#17171d] to-[#17171d] p-8 sm:p-12">
          <p className="mb-4 text-xs font-bold tracking-[0.22em] text-indigo-300">FRESHLY UPLOADED</p>
          <h1 className="max-w-2xl text-4xl font-bold tracking-tight sm:text-6xl">Watch what matters.</h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-zinc-300 sm:text-lg">TubeLite is a calmer place for videos worth sharing. Discover new ideas, learn something useful, and join the conversation.</p>
          <a className="mt-7 inline-flex rounded-full bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-indigo-100" href="#latest">Explore videos <span className="ml-2">→</span></a>
        </section>

        <section id="latest">
          <div className="mb-6 flex items-end justify-between gap-4">
            <div><p className="text-sm text-indigo-300">Latest uploads</p><h2 className="text-2xl font-semibold">Made for your next break</h2></div>
            <span className="text-sm text-zinc-400">{videos.length} videos</span>
          </div>
          <div className="grid gap-x-5 gap-y-9 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {videos.map((video) => <VideoCard key={video.id} video={video} />)}
          </div>
        </section>
      </main>
    </div>
  );
}
