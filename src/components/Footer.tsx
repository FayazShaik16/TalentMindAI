'use client';

import React from 'react';
import { Brain, ArrowUp } from 'lucide-react';

export default function Footer() {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="relative border-t border-white/[0.05] bg-brand-black py-12 md:py-20 z-10">
      <div className="mx-auto max-w-7xl px-6 md:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          {/* Brand Info */}
          <div className="md:col-span-2 flex flex-col gap-4">
            <div className="flex items-center gap-2 text-lg font-bold tracking-tight text-white">
              <Brain className="h-5 w-5 text-brand-blue" />
              <span>TalentMind <span className="text-brand-cyan">AI</span></span>
            </div>
            <p className="text-sm text-zinc-400 max-w-sm">
              The candidate intelligence platform built to understand careers, reason through evidence, and power trusted hiring decisions.
            </p>
          </div>

          {/* Links 1 */}
          <div className="flex flex-col gap-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Platform</span>
            <a href="#awakens" className="text-xs text-zinc-400 hover:text-white transition-colors interactive">Intelligence Engine</a>
            <a href="#investigation" className="text-xs text-zinc-400 hover:text-white transition-colors interactive">Evidence Verification</a>
            <a href="#semantic" className="text-xs text-zinc-400 hover:text-white transition-colors interactive">Semantic Galaxy</a>
          </div>

          {/* Links 2 */}
          <div className="flex flex-col gap-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Company</span>
            <a href="#" className="text-xs text-zinc-400 hover:text-white transition-colors interactive">About Us</a>
            <a href="#" className="text-xs text-zinc-400 hover:text-white transition-colors interactive">Privacy Policy</a>
            <a href="#" className="text-xs text-zinc-400 hover:text-white transition-colors interactive">Terms of Service</a>
          </div>
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-white/[0.05] pt-8 md:mt-16 md:flex-row">
          <span className="text-xs text-zinc-500">
            &copy; 2026 TalentMind AI. All rights reserved. Designed with precision.
          </span>
          <button
            onClick={scrollToTop}
            className="flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.02] px-4 py-2 text-xs font-medium text-zinc-400 transition-all hover:bg-white/[0.08] hover:text-white interactive"
          >
            <span>Back to top</span>
            <ArrowUp className="h-3 w-3" />
          </button>
        </div>
      </div>
    </footer>
  );
}
