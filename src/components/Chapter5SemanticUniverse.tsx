'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Compass, Sparkles, CheckCircle2 } from 'lucide-react';
import gsap from 'gsap';

interface SemanticUniverseProps {
  onPulse: (active: boolean, progress: number) => void;
}

export default function Chapter5SemanticUniverse({ onPulse }: SemanticUniverseProps) {
  const [query, setQuery] = useState('Staff Engineer with custom virtualization & latency-critical index experience');
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const presets = [
    'Infrastructure Engineer: C++ & Linux namespaces',
    'AI Specialist: Distributed model fine-tuning',
    'Frontend Lead: Vite, Tailwind & WebGL core',
  ];

  const handlePulseTrigger = () => {
    if (isSearching) return;
    setIsSearching(true);
    setShowResults(false);

    // Animate pulse progress via GSAP
    const progressVal = { value: 0 };
    gsap.to(progressVal, {
      value: 1,
      duration: 3.5,
      ease: 'power2.inOut',
      onUpdate: () => {
        onPulse(true, progressVal.value);
      },
      onComplete: () => {
        onPulse(false, 0);
        setIsSearching(false);
        setShowResults(true);
      },
    });
  };

  return (
    <section
      id="semantic"
      className="relative flex min-h-screen w-full flex-col justify-center bg-brand-black px-6 py-20"
    >
      <div className="mx-auto max-w-4xl w-full flex flex-col items-center">
        {/* Title */}
        <div className="text-center mb-12">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 rounded-full border border-brand-cyan/30 bg-brand-cyan/5 px-3 py-1 text-xs text-brand-cyan mb-4"
          >
            <Compass className="h-3.5 w-3.5" />
            <span>Chapter 5 — Semantic Galaxy</span>
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl font-extrabold tracking-tight text-white md:text-5xl"
          >
            The Semantic Universe
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="mt-4 text-md text-zinc-400 max-w-xl mx-auto"
          >
            Instead of matching static search words, we cluster candidates by their actual semantic achievements. Watch 100,000 resumes reorganize around your description.
          </motion.p>
        </div>

        {/* Console Search Bar */}
        <div className="glass-panel w-full p-6 md:p-8 rounded-3xl border border-white/[0.08] shadow-[0_15px_40px_rgba(0,0,0,0.6)]">
          <div className="flex flex-col gap-4">
            <div className="relative flex items-center">
              <Search className="absolute left-4 h-5 w-5 text-zinc-500" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={isSearching}
                className="w-full rounded-2xl bg-white/[0.03] border border-white/[0.08] pl-12 pr-4 py-4 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue transition-all disabled:opacity-50 font-sans"
                placeholder="Describe your ideal candidate in natural language..."
              />
            </div>

            {/* Presets */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] font-mono text-zinc-500 uppercase">Try:</span>
              {presets.map((preset) => (
                <button
                  key={preset}
                  onClick={() => setQuery(preset)}
                  disabled={isSearching}
                  className="rounded-full bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.05] hover:border-white/[0.1] px-3.5 py-1 text-xs text-zinc-400 hover:text-white transition-all interactive disabled:opacity-50"
                >
                  {preset}
                </button>
              ))}
            </div>

            {/* Trigger Button */}
            <button
              onClick={handlePulseTrigger}
              disabled={isSearching}
              className="mt-4 w-full flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-brand-blue via-brand-cyan to-brand-purple py-4 font-semibold text-white transition-all transform hover:scale-[1.01] shadow-lg shadow-brand-blue/15 hover:shadow-brand-cyan/20 disabled:opacity-50 interactive"
            >
              <Sparkles className={`h-4 w-4 ${isSearching ? 'animate-spin' : ''}`} />
              <span>{isSearching ? 'Analyzing and Reorganizing Space...' : 'Emit Semantic Pulse'}</span>
            </button>
          </div>
        </div>

        {/* Dynamic Results converging */}
        <div className="mt-8 w-full min-h-[120px] flex items-center justify-center">
          <AnimatePresence mode="wait">
            {isSearching && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="text-center font-mono text-xs text-brand-cyan animate-pulse"
              >
                [ PULSING HIGH-DIMENSIONAL SPACE ] <br />
                Candidates are vectorizing and converging...
              </motion.div>
            )}

            {showResults && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="w-full grid grid-cols-1 md:grid-cols-3 gap-4"
              >
                <div className="glass-panel p-4 rounded-xl border border-brand-green/20 bg-brand-green/[0.01] flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5 text-brand-green flex-shrink-0" />
                  <div>
                    <h4 className="text-sm font-bold text-white">Sarah Chen</h4>
                    <span className="text-[10px] font-mono text-zinc-500">Vector Math Specialist</span>
                    <div className="text-xs font-bold text-brand-green">98% Match</div>
                  </div>
                </div>

                <div className="glass-panel p-4 rounded-xl border border-brand-blue/20 bg-brand-blue/[0.01] flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5 text-brand-blue flex-shrink-0" />
                  <div>
                    <h4 className="text-sm font-bold text-white">David K.</h4>
                    <span className="text-[10px] font-mono text-zinc-500">C++ Compiler Dev</span>
                    <div className="text-xs font-bold text-brand-blue">89% Match</div>
                  </div>
                </div>

                <div className="glass-panel p-4 rounded-xl border border-white/[0.05] bg-white/[0.01] flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5 text-zinc-500 flex-shrink-0" />
                  <div>
                    <h4 className="text-sm font-bold text-white">Marcus Vance</h4>
                    <span className="text-[10px] font-mono text-zinc-500">Linux System Engineer</span>
                    <div className="text-xs font-bold text-zinc-400">82% Match</div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

      </div>
    </section>
  );
}
