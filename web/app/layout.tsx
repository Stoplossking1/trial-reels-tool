import type { Metadata, Viewport } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { site } from "@/lib/site";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: { default: `${site.name}: 3 Instagram trial reels from 1 video`, template: `%s · ${site.name}` },
  description: site.description,
  applicationName: site.name,
  keywords: [
    "instagram trial reels", "trial reels", "trial reels generator", "test reel hooks", "reel hook variations",
    "instagram reels a/b test", "reel hooks", "trial reels tool",
  ],
  alternates: { canonical: "/" },
  openGraph: { type: "website", siteName: site.name, url: site.url, title: `${site.name}: ${site.tagline}`, description: site.description, locale: "en_US" },
  twitter: { card: "summary_large_image", title: `${site.name}: ${site.tagline}`, description: site.description },
  robots: { index: true, follow: true, googleBot: { index: true, follow: true, "max-image-preview": "large", "max-snippet": -1 } },
  formatDetection: { telephone: false },
};

export const viewport: Viewport = { themeColor: "#fafafa", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
