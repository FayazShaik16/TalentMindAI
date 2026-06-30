import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import LenisProvider from "@/components/LenisProvider";
import InteractiveCursor from "@/components/InteractiveCursor";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TalentMind AI — Candidate Intelligence Engine",
  description: "TalentMind AI is an award-winning candidate intelligence platform that understands candidate career paths and explains every matching recommendation with transparency.",
  keywords: ["AI Recruitment", "Candidate Intelligence", "Career Matching", "Semantic Search", "Talent Acquisition"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-brand-black text-white selection:bg-brand-blue/30 selection:text-white font-sans">
        <LenisProvider>
          <InteractiveCursor />
          {children}
        </LenisProvider>
      </body>
    </html>
  );
}
