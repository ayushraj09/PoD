import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // ponytail: every page here reads per-request data (cookies, live counts), so no component caching
  cacheComponents: false,
  turbopack: {
    root: __dirname,
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
