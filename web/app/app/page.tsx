import type { Metadata } from "next";
import { AppNav } from "@/components/AppNav";
import { UploadFlow } from "./UploadFlow";

export const metadata: Metadata = { title: "Make your trial reels" };

export default function AppPage() {
  return (
    <>
      <AppNav />
      <main className="px-4 pt-14">
        <UploadFlow />
      </main>
    </>
  );
}
