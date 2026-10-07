import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: {
    unoptimized: true,
    remotePatterns: [new URL("https://media.formula1.com/**"), new URL("https://www.formula1.com/**")],
  },
};

export default nextConfig;
