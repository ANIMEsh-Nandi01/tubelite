"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setLoading(true);
    const data = new FormData(event.currentTarget);
    const body = mode === "login" ? { email: data.get("email"), password: data.get("password") } : { username: data.get("username"), email: data.get("email"), password: data.get("password") };
    try { const response = await fetch(`${apiUrl}/api/auth/${mode}`, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); if (!response.ok) throw new Error((await response.json() as { detail?: string }).detail ?? "Unable to continue"); window.location.assign("/"); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to continue"); } finally { setLoading(false); }
  }
  return <main className="grid min-h-screen place-items-center bg-[#08080a] px-5 text-white"><section className="w-full max-w-md rounded-3xl border border-white/10 bg-[#121217] p-7 shadow-2xl sm:p-9"><Link className="text-lg font-black" href="/"><span className="text-indigo-400">▶</span> TubeLite</Link><p className="mt-8 text-sm text-indigo-300">{mode === "login" ? "Welcome back" : "Start your channel"}</p><h1 className="mt-1 text-3xl font-bold">{mode === "login" ? "Sign in" : "Create an account"}</h1><form className="mt-7 space-y-4" onSubmit={submit}>{mode === "signup" && <input required name="username" className="field" minLength={3} placeholder="Username" />}<input required name="email" type="email" className="field" placeholder="Email address" /><input required name="password" type="password" minLength={8} className="field" placeholder="Password" />{error && <p className="text-sm text-rose-300">{error}</p>}<button disabled={loading} className="w-full rounded-xl bg-indigo-500 py-3 font-semibold transition hover:bg-indigo-400 disabled:opacity-60">{loading ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}</button></form><button className="mt-6 text-sm text-zinc-400 underline hover:text-white" onClick={() => setMode(mode === "login" ? "signup" : "login")}>{mode === "login" ? "New here? Create an account" : "Already have an account? Sign in"}</button></section></main>;
}
