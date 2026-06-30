'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, X, ShieldAlert } from 'lucide-react';

export default function Chapter2BrokenATS() {
  const [scanStep, setScanStep] = useState<'idle' | 'scanning' | 'results'>('idle');

  useEffect(() => {
    // Automatically trigger scanner loop in view
    const timer1 = setTimeout(() => setScanStep('scanning'), 2000);
    const timer2 = setTimeout(() => setScanStep('results'), 5000);

    // Reset loop every 9 seconds
    const interval = setInterval(() => {
      setScanStep('idle');
      setTimeout(() => setScanStep('scanning'), 1000);
      setTimeout(() => setScanStep('results'), 4000);
    }, 9000);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearInterval(interval);
    };
  }, []);

  return (
    <section
      id="ats"
      className="relative flex min-h-screen w-full flex-col items-center justify-center bg-brand-black px-6 py-20"
    >
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-12">
        {/* Editorial Headers */}
        <div className="text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl font-extrabold tracking-tight text-white md:text-5xl"
          >
            Recruitment was built for{' '}
            <span className="text-brand-red">documents</span>.
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="mt-4 text-lg text-zinc-400 md:text-xl"
          >
            It should be built for <span className="text-brand-green glow-text-cyan">people</span>.
          </motion.p>
        </div>

        {/* ATS Panel Simulator */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="glass-panel w-full max-w-4xl overflow-hidden rounded-2xl"
        >
          {/* ATS Top Bar */}
          <div className="flex items-center justify-between border-b border-white/[0.08] bg-white/[0.02] px-6 py-4">
            <div className="flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-brand-red opacity-80" />
              <div className="h-3 w-3 rounded-full bg-brand-cyan opacity-80" />
              <div className="h-3 w-3 rounded-full bg-brand-purple opacity-80" />
              <span className="ml-3 font-mono text-xs text-zinc-500">Legacy_ATS_v4.2.3 // Keyword_Filter</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-brand-red animate-pulse">
                {scanStep === 'scanning' ? '• SCANNING KEYWORDS' : scanStep === 'results' ? 'SCAN COMPLETE' : 'AWAITING INPUT'}
              </span>
            </div>
          </div>

          {/* Scanner Area */}
          <div className="relative grid grid-cols-1 gap-px bg-white/[0.05] md:grid-cols-2">
            {/* Scan Beam Indicator */}
            {scanStep === 'scanning' && (
              <motion.div
                initial={{ top: '0%' }}
                animate={{ top: '100%' }}
                transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
                className="absolute left-0 right-0 z-10 h-1 bg-gradient-to-r from-transparent via-brand-cyan to-transparent shadow-[0_0_12px_rgba(6,182,212,0.8)]"
              />
            )}

            {/* Candidate A (The True Talent) */}
            <div className="relative bg-brand-dark/60 p-6 md:p-8">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">Sarah Chen</h3>
                  <p className="text-xs text-brand-blue font-semibold">Staff AI Systems Engineer</p>
                </div>
                <div className="text-right">
                  <span className="font-mono text-xs text-zinc-500">Match score</span>
                  <div className="text-2xl font-bold text-brand-red">
                    {scanStep === 'results' ? '28%' : scanStep === 'scanning' ? 'Scanning...' : '--%'}
                  </div>
                </div>
              </div>

              {/* Sarah's details */}
              <div className="mt-6 space-y-4">
                <div>
                  <h4 className="text-xs font-semibold uppercase text-zinc-500">Core Experience</h4>
                  <p className="mt-1 text-sm text-zinc-300 leading-relaxed">
                    Designed and built a custom C++ neural inference clusters reducing latency by 45%. Devised high-scale ML training workflows and novel distributed index mapping systems for high-throughput vectors.
                  </p>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase text-zinc-500">Keywords Parsed</h4>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <span className="rounded bg-brand-red/10 px-2.5 py-1 text-xs text-brand-red border border-brand-red/20 flex items-center gap-1">
                      <X className="h-3 w-3" /> FastAPI
                    </span>
                    <span className="rounded bg-brand-red/10 px-2.5 py-1 text-xs text-brand-red border border-brand-red/20 flex items-center gap-1">
                      <X className="h-3 w-3" /> Docker
                    </span>
                    <span className="rounded bg-brand-green/10 px-2.5 py-1 text-xs text-brand-green border border-brand-green/20 flex items-center gap-1">
                      <Check className="h-3 w-3" /> Python
                    </span>
                    <span className="rounded bg-brand-red/10 px-2.5 py-1 text-xs text-brand-red border border-brand-red/20 flex items-center gap-1">
                      <X className="h-3 w-3" /> AWS
                    </span>
                  </div>
                </div>
              </div>

              {/* Status Badge */}
              <AnimatePresence>
                {scanStep === 'results' && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 flex items-center justify-center bg-brand-black/90 backdrop-blur-sm"
                  >
                    <div className="text-center flex flex-col items-center">
                      <div className="rounded-full bg-brand-red/10 p-4 border border-brand-red/20 mb-3">
                        <ShieldAlert className="h-10 w-10 text-brand-red" />
                      </div>
                      <span className="text-2xl font-bold uppercase tracking-widest text-brand-red">AUTO-REJECTED</span>
                      <p className="mt-2 text-xs text-zinc-500 max-w-[200px]">Missing critical keywords: FastAPI, Docker, AWS</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Candidate B (The Keyword Spammer) */}
            <div className="relative bg-brand-dark/60 p-6 md:p-8">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">John Doe</h3>
                  <p className="text-xs text-zinc-500">Junior Full-Stack Dev</p>
                </div>
                <div className="text-right">
                  <span className="font-mono text-xs text-zinc-500">Match score</span>
                  <div className="text-2xl font-bold text-brand-green">
                    {scanStep === 'results' ? '98%' : scanStep === 'scanning' ? 'Scanning...' : '--%'}
                  </div>
                </div>
              </div>

              {/* John's details */}
              <div className="mt-6 space-y-4">
                <div>
                  <h4 className="text-xs font-semibold uppercase text-zinc-500">Core Experience</h4>
                  <p className="mt-1 text-sm text-zinc-400 leading-relaxed line-clamp-3">
                    Knowledgeable in Python, FastAPI, Docker, AWS, LLM, and React. Created standard REST endpoints with FastAPI. Deployed basic Docker containers to AWS EC2 instance. Active developer with python.
                  </p>
                </div>
                <div>
                  <h4 className="text-xs font-semibold uppercase text-zinc-500">Keywords Parsed</h4>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <span className="rounded bg-brand-green/10 px-2.5 py-1 text-xs text-brand-green border border-brand-green/20 flex items-center gap-1">
                      <Check className="h-3 w-3" /> FastAPI
                    </span>
                    <span className="rounded bg-brand-green/10 px-2.5 py-1 text-xs text-brand-green border border-brand-green/20 flex items-center gap-1">
                      <Check className="h-3 w-3" /> Docker
                    </span>
                    <span className="rounded bg-brand-green/10 px-2.5 py-1 text-xs text-brand-green border border-brand-green/20 flex items-center gap-1">
                      <Check className="h-3 w-3" /> Python
                    </span>
                    <span className="rounded bg-brand-green/10 px-2.5 py-1 text-xs text-brand-green border border-brand-green/20 flex items-center gap-1">
                      <Check className="h-3 w-3" /> AWS
                    </span>
                  </div>
                </div>
              </div>

              {/* Status Badge */}
              <AnimatePresence>
                {scanStep === 'results' && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 flex items-center justify-center bg-brand-black/90 backdrop-blur-sm"
                  >
                    <div className="text-center flex flex-col items-center">
                      <div className="rounded-full bg-brand-green/10 p-4 border border-brand-green/20 mb-3">
                        <Check className="h-10 w-10 text-brand-green" />
                      </div>
                      <span className="text-2xl font-bold uppercase tracking-widest text-brand-green">PASSED TO INTERVIEW</span>
                      <p className="mt-2 text-xs text-zinc-500 max-w-[200px]">Matches critical keywords: FastAPI, Docker, AWS, Python</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
