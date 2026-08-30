import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Coding Agent - Cursor-Class Web IDE",
  description: "Autonomous ReAct Coding Agent Platform with Monaco Editor & Docker Sandbox",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="h-screen w-screen overflow-hidden bg-[#121212] text-neutral-200">
        {children}
      </body>
    </html>
  );
}
