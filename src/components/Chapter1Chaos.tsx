'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, ChevronDown } from 'lucide-react';
import Link from 'next/link';

export default function Chapter1Chaos() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.35,
        delayChildren: 0.4,
      },
    },
  } as const;

  const itemVariants = {
    hidden: { opacity: 0, y: 24 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.9,
        ease: [0.25, 0.4, 0.25, 1],
      },
    },
  } as const;

  return (
    <section
      id="chaos"
      className="relative flex min-h-screen w-full flex-col items-center justify-center select-none overflow-hidden"
    >
      {/* Full-Bleed Background Image via CSS */}
      <div
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/images/hero-bg.png')" }}
      />
      {/* Gradient overlays — darken center for text, keep edges bright */}
      <div className="absolute inset-0 z-[1] bg-gradient-to-b from-black/60 via-black/50 to-transparent" />
      <div
        className="absolute inset-0 z-[1]"
        style={{
          background: 'radial-gradient(ellipse 80% 60% at 50% 45%, rgba(0,0,0,0.65) 0%, rgba(0,0,0,0.15) 70%, transparent 100%)',
        }}
      />
      <div className="absolute inset-0 z-[1] bg-gradient-to-t from-[#09090b] via-[#09090b]/40 to-transparent" />

      {/* Content */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 flex max-w-4xl flex-col items-center gap-6 px-6 text-center"
      >
        {/* Headline */}
        <motion.h1
          variants={itemVariants}
          className="text-5xl font-extrabold tracking-tight text-white md:text-7xl lg:text-[5.5rem] leading-[1.05]"
          style={{ textShadow: '0 2px 30px rgba(0,0,0,0.5), 0 4px 60px rgba(0,0,0,0.3)' }}
        >
          Where Intelligence{' '}
          <br className="hidden md:block" />
          Meets Talent
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          variants={itemVariants}
          className="max-w-2xl text-base font-normal text-zinc-200 md:text-lg leading-relaxed"
        >
          For recruiters who want more than keyword filters — AI that reasons with you.
          <br className="hidden md:block" />
          Harness semantic intelligence to discover extraordinary talent others overlook.
        </motion.p>

        {/* CTA Button */}
        <motion.div variants={itemVariants} className="mt-4">
          <Link
            href="/tools"
            className="group inline-flex items-center gap-2.5 rounded-full border border-white/30 bg-white/[0.06] px-8 py-3.5 text-sm font-medium text-white backdrop-blur-sm transition-all duration-300 hover:bg-white/[0.14] hover:border-white/50 hover:shadow-[0_0_30px_rgba(255,255,255,0.08)] interactive"
          >
            <span>Meet Your Intelligence Engine</span>
            <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1" />
          </Link>
        </motion.div>
      </motion.div>

      {/* Scroll Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2.5, duration: 1 }}
        className="absolute bottom-8 left-1/2 z-10 -translate-x-1/2 flex flex-col items-center gap-1.5"
      >
        <span className="text-[11px] text-zinc-400/70 tracking-[0.2em] uppercase font-light">
          Scroll to Explore
        </span>
        <motion.div
          animate={{ y: [0, 6, 0] }}
          transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
        >
          <ChevronDown className="h-4 w-4 text-zinc-400/50" />
        </motion.div>
      </motion.div>
    </section>
  );
}
