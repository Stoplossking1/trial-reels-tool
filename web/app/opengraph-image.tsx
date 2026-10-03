import { ImageResponse } from "next/og";

export const alt = "TrialReelMax: Drop in 1 video. Get 5 trial reels.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OG() {
  const phones = [0, 1, 2, 3, 4];
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", background: "#fafafa", padding: 64, fontFamily: "sans-serif" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14, fontSize: 30, fontWeight: 600, color: "#0a0a0a" }}>
          <div style={{ display: "flex", position: "relative", width: 34, height: 34 }}>
            <div style={{ position: "absolute", left: 0, top: 0, width: 18, height: 30, borderRadius: 5, background: "#0a0a0a" }} />
            <div style={{ position: "absolute", left: 13, top: 5, width: 19, height: 27, borderRadius: 5, background: "#ff3d71", border: "3px solid #fafafa" }} />
          </div>
          TrialReelMax
        </div>
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
          <div style={{ display: "flex", flexDirection: "column", fontSize: 78, fontWeight: 500, lineHeight: 1.02, letterSpacing: -3, color: "#0a0a0a" }}>
            <span>Drop in 1 video.</span>
            <span>Get 5 trial reels.</span>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            {phones.map((i) => (
              <div key={i} style={{ width: 70, height: 124, borderRadius: 14, background: i === 0 ? "#ff3d71" : "#111114", border: "4px solid #111114" }} />
            ))}
          </div>
        </div>
      </div>
    ),
    size,
  );
}
