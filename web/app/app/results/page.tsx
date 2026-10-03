import type { Metadata } from "next";
import { AppNav } from "@/components/AppNav";
import { Results } from "./Results";

export const metadata: Metadata = { title: "Your trial reels" };

export default function ResultsPage() {
  return (
    <>
      <AppNav right="new" />
      <main className="px-4 pt-12">
        <Results />
      </main>
    </>
  );
}
