import type { NextConfig } from "next";

const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true
  },
};

module.exports = {
  allowedDevOrigins: ['127.0.0.1'],
}

export default nextConfig;
