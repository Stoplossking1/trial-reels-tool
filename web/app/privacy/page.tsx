import type { Metadata } from "next";
import { Footer, Nav } from "@/components/ui";
import { site } from "@/lib/site";

export const metadata: Metadata = { title: "Privacy", alternates: { canonical: "/privacy" } };

export default function Privacy() {
  return (
    <>
      <Nav />
      <main className="prose-guide mx-auto max-w-2xl px-4 pt-16">
        <h1 className="text-4xl font-medium tracking-tight">Privacy</h1>
        <p>Last updated 3 October 2026. This policy is a placeholder and will be replaced before paid launch.</p>
        <h2>What we keep</h2>
        <ul>
          <li>Your Google account email, to sign you in and give you your free run.</li>
          <li>Your uploaded video and the variations, for 14 days, then they are deleted.</li>
          <li>The transcript and the settings of each variation, so we can show you what changed.</li>
        </ul>
        <h2>Who sees it</h2>
        <p>Your video is processed by our speech-to-text and writing providers only to make your variations. We don&apos;t sell your data or use your videos for advertising.</p>
        <h2>Contact</h2>
        <p>{site.email}</p>
      </main>
      <Footer />
    </>
  );
}
