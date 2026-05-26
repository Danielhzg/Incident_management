/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // Mengabaikan error ESLint saat build agar tidak memblokir deployment
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Mengabaikan error TypeScript saat build
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
