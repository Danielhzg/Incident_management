import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";

export const metadata: Metadata = {
  title: "Incident Management System",
  description: "Event-driven Incident Management System with real-time dashboard, race condition handling, and AI-powered analytics.",
  keywords: ["incident management", "SRE", "DevOps", "monitoring", "real-time"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
