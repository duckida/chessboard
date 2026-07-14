import type { Metadata } from "next";
import { LINE_Seed_JP, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const jetbrainsMono = JetBrains_Mono({subsets:['latin'],variable:'--font-mono'});

const lineSeed = LINE_Seed_JP({
  variable: "--font-line-sans",
  subsets: ["latin"],
  weight: "400",
  adjustFontFallback: false,
});

export const metadata: Metadata = {
  title: "Chessboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={cn("h-full", "antialiased", lineSeed.variable, "font-mono", jetbrainsMono.variable)}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
