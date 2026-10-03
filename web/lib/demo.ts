/**
 * The 5 hardcoded variants shown in the demo. Made by the real worker from Jordan's video
 * (`worker` CLI, local transcript); files live in public/demo/. Regenerate with scripts/make-demo.sh.
 */
export type Variant = {
  order: number;
  hook: string;
  pattern: string;
  caption: string;
  changes: string[];
  video: string;
  cover: string;
};

import data from "./demo.json";

export const variants: Variant[] = data.variants;
export const original = data.original as { video: string; cover: string; seconds: number };
export const madeIn: string = data.madeIn;
