import type { NextConfig } from "next";

import path from "path";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
    ],
  },
  turbopack: {
    resolveAlias: {
      "@shared": path.resolve(__dirname, "../shared"),
    },
  },
  webpack: (config) => {
    config.resolve.alias["@shared"] = path.resolve(__dirname, "../shared");
    return config;
  },
};

export default nextConfig;
