'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Brain } from 'lucide-react';
import Link from 'next/link';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  const navItems = [
    { label: 'Chaos', href: '#chaos' },
    { label: 'Broken ATS', href: '#ats' },
    { label: 'AI Awakening', href: '#awakens' },
    { label: 'Investigation', href: '#investigation' },
    { label: 'Semantic Universe', href: '#semantic' },
    { label: 'AI Reasoning', href: '#reasoning' },
  ];

  const handleScroll = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    setIsOpen(false);
    const target = document.querySelector(href);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <nav className="fixed top-0 left-0 z-50 w-full px-4 py-4 md:px-8">
      <div className="mx-auto flex max-w-7xl items-center justify-between rounded-full bg-white/[0.02] px-6 py-3 backdrop-blur-md border border-white/[0.05] shadow-[0_8px_32px_0_rgba(0,0,0,0.4)]">
        {/* Logo */}
        <a href="#chaos" onClick={(e) => handleScroll(e, '#chaos')} className="flex items-center gap-2 text-lg font-bold tracking-tight text-white interactive">
          <Brain className="h-5 w-5 text-brand-blue animate-pulse" />
          <span>TalentMind <span className="text-brand-cyan">AI</span></span>
        </a>

        {/* Desktop nav */}
        <div className="hidden items-center gap-8 md:flex">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              onClick={(e) => handleScroll(e, item.href)}
              className="text-xs font-medium text-zinc-400 transition-colors hover:text-white interactive"
            >
              {item.label}
            </a>
          ))}
        </div>

        <div className="hidden md:block">
          <Link
            href="/tools"
            className="rounded-full bg-gradient-to-r from-brand-blue to-brand-purple px-5 py-2 text-xs font-semibold text-white shadow-lg shadow-brand-blue/20 transition-all hover:scale-105 hover:shadow-brand-purple/30 interactive"
          >
            Launch Engine
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="block text-zinc-400 hover:text-white md:hidden interactive"
          aria-label={isOpen ? "Close Menu" : "Open Menu"}
        >
          {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile nav panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-20 left-4 right-4 z-40 rounded-2xl bg-brand-dark/95 p-6 backdrop-blur-xl border border-white/[0.08] shadow-2xl md:hidden"
          >
            <div className="flex flex-col gap-4">
              {navItems.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  onClick={(e) => handleScroll(e, item.href)}
                  className="text-sm font-medium text-zinc-300 transition-colors hover:text-white interactive"
                >
                  {item.label}
                </a>
              ))}
              <Link
                href="/tools"
                className="mt-2 w-full rounded-full bg-gradient-to-r from-brand-blue to-brand-purple py-3 text-center text-sm font-semibold text-white shadow-lg interactive"
              >
                Launch Engine
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
