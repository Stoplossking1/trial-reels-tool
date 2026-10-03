import type { Metadata } from "next";
import { Footer, Nav } from "@/components/ui";
import { site } from "@/lib/site";

export const metadata: Metadata = { title: "Terms", alternates: { canonical: "/terms" } };

export default function Terms() {
  return (
    <>
      <Nav />
      <main className="prose-guide mx-auto max-w-2xl px-4 pt-16">
        <h1 className="text-4xl font-medium tracking-tight">Terms</h1>
        <p>Last updated 3 October 2026. These terms are a placeholder and will be replaced before paid launch.</p>
        <h2>Your videos</h2>
        <p>You keep all rights to the videos you upload and the variations we make from them. You confirm you have the right to use everything in the video you upload.</p>
        <h2>What we do</h2>
        <p>We make variations of your video for you to post yourself. We don&apos;t promise any number of views or how Instagram will treat the uploads.</p>
        <h2>Payment</h2>
        <p>Your first run is free. After that you pay per video. A run that fails is not charged.</p>
        <h2>Contact</h2>
        <p>{site.email}</p>
      </main>
      <Footer />
    </>
  );
}
