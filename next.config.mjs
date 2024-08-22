/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    outputFileTracingIncludes: {
      "/api/**/*": ["./node_modules/**/*.wasm"],
    },
  },
};

export default nextConfig;
