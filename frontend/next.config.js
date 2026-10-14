/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || "",
  },
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!apiBase) return [];
    const cleanBase = apiBase.replace(/\/$/, "");
    return [
      {
        source: "/api/:path*",
        destination: `${cleanBase}/api/:path*`,
      },
      {
        source: "/health",
        destination: `${cleanBase}/health`,
      },
      {
        source: "/ready",
        destination: `${cleanBase}/ready`,
      },
    ];
  },
};

module.exports = nextConfig;
