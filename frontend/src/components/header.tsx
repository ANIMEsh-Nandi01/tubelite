"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export function Header() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  function submit(event: FormEvent) { event.preventDefault(); if (query.trim()) router.push(`/search?q=${encodeURIComponent(query.trim())}`); }
  return <header className="sticky top-0 z-20 border-b border-white/10 bg-[#08080a]/90 backdrop-blur"><div className="mx-auto flex h-18 max-w-7xl items-center gap-5 px-5 sm:px-8 lg:px-10"><Link className="shrink-0 text-xl font-black tracking-tight" href="/"><span className="mr-1 inline-block text-indigo-400">▶</span>TubeLite</Link><form className="hidden max-w-xl flex-1 md:block" onSubmit={submit}><label className="sr-only" htmlFor="search">Search videos</label><input id="search" value={query} onChange={(event) => setQuery(event.target.value)} className="w-full rounded-full border border-white/10 bg-white/5 px-5 py-2.5 text-sm outline-none placeholder:text-zinc-500 focus:border-indigo-400" placeholder="Search videos" /></form><nav className="ml-auto flex items-center gap-2"><Link className="rounded-full px-3 py-2 text-sm text-zinc-300 hover:text-white" href="/login">Sign in</Link><Link className="rounded-full bg-indigo-500 px-4 py-2 text-sm font-semibold transition hover:bg-indigo-400" href="/upload">Upload</Link></nav></div></header>;
}
