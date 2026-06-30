'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Rocket } from 'lucide-react';
import Link from 'next/link';

export default function Chapter7FinalReveal() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.4,
        delayChildren: 0.2,
      },
    },
  } as const;

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring',
        stiffness: 70,
        damping: 15,
      },
    },
  } as const;

  const handleCTAClick = (e: React.MouseEvent, type: string) => {
    e.preventDefault();
    alert(`Thank you for exploring! Initializing: ${type}`);
  };

  return (
    <section
      id="reveal"
      className="relative flex min-h-screen w-full flex-col items-center justify-center bg-brand-black px-6 text-center select-none"
    >
      {/* Glow layer behind text */}
      <div className="absolute inset-0 bg-gradient-to-t from-brand-black via-transparent to-brand-black opacity-90 pointer-events-none" />

      <motion.div
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-50px' }}
        className="relative z-10 flex max-w-4xl flex-col items-center gap-8 md:gap-12"
      >
        <div className="space-y-4 md:space-y-6">
          <motion.h2
            variants={itemVariants}
            className="text-4xl font-extrabold tracking-tight text-white md:text-7xl lg:text-8xl"
          >
            We don&apos;t search resumes. <br />
            <span className="bg-gradient-to-r from-brand-cyan via-brand-blue to-brand-purple bg-clip-text text-transparent glow-text-blue">
              We understand careers.
            </span>
          </motion.h2>
          
          <motion.p
            variants={itemVariants}
            className="text-lg font-medium text-zinc-400 md:text-2xl lg:text-3xl max-w-2xl mx-auto"
          >
            And we explain every recommendation.
          </motion.p>
        </div>

        {/* CTA Buttons */}
        <motion.div
          variants={itemVariants}
          className="flex flex-col sm:flex-row items-center gap-4 w-full justify-center"
        >
          <Link
            href="/tools"
            className="w-full sm:w-auto rounded-full bg-white px-8 py-4 text-sm font-bold text-black shadow-xl shadow-white/5 transition-all hover:scale-105 hover:bg-zinc-200 flex items-center justify-center gap-2.5 interactive"
          >
            <Rocket className="h-4.5 w-4.5 text-brand-blue" />
            <span>Launch TalentMind</span>
          </Link>
        </motion.div>
      </motion.div>
    </section>
  );
}
