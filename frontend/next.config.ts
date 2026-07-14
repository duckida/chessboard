import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
};

module.exports = {
  allowedDevOrigins: ['127.0.0.1'],
}

export default nextConfig;
