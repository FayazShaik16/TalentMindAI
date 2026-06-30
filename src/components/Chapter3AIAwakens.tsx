'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Sparkles, ShieldCheck, Compass, GitMerge, FileText, BarChart } from 'lucide-react';

interface NodeInfo {
  id: number;
  title: string;
  shortDesc: string;
  longDesc: string;
  icon: React.ReactNode;
}

export default function Chapter3AIAwakens() {
  const [activeNode, setActiveNode] = useState<number | null>(null);

  const nodes: NodeInfo[] = [
    {
      id: 1,
      title: 'Job Intelligence',
      shortDesc: 'Deconstructs roles into core behavioral demands and skills.',
      longDesc: 'Transforms static job descriptions into dynamic, multi-dimensional talent blueprints, mapping implicit roles, technology dependencies, and actual day-to-day requirements rather than plain keyword filters.',
      icon: <FileText className="h-6 w-6 text-brand-blue" />,
    },
    {
      id: 2,
      title: 'Career Intelligence',
      shortDesc: 'Analyzes velocity, scope, and non-linear trajectories.',
      longDesc: 'Understands career paths. Identifies hyper-growth trajectories, startup-to-enterprise transitions, and high-velocity career switches that keywords typically filter out.',
      icon: <BarChart className="h-6 w-6 text-brand-cyan" />,
    },
    {
      id: 3,
      title: 'Evidence Verification',
      shortDesc: 'Validates claims against real-world engineering metrics.',
      longDesc: 'Cross-references CV claims with actual codebases, portfolio systems, and open-source contributions. Separates surface-level buzzwords from hands-on mastery.',
      icon: <ShieldCheck className="h-6 w-6 text-brand-green" />,
    },
    {
      id: 4,
      title: 'Behavior Analysis',
      shortDesc: 'Evaluates culture, alignment, and cognitive skills.',
      longDesc: 'Extracts team-fit indicators, communication styles, problem-solving depth, and leadership potential by modeling natural language evidence from work samples.',
      icon: <Compass className="h-6 w-6 text-brand-purple" />,
    },
    {
      id: 5,
      title: 'Semantic Understanding',
      shortDesc: 'Matches skills and concepts across vocabularies.',
      longDesc: 'Translates technical contexts. Recognizes that an engineer who "wrote compiler passes in Rust" possesses the core skills required for high-performance compiler roles, even if the resume lacks generic buzzwords.',
      icon: <GitMerge className="h-6 w-6 text-brand-cyan" />,
    },
    {
      id: 6,
      title: 'Recruiter Brain',
      shortDesc: 'Synthesizes all details into clear, written logic.',
      longDesc: 'Acts as the cognitive layer. Generates structured, readable hiring rationale, ranking profiles transparently and pointing out exact matches or areas for further verification.',
      icon: <Brain className="h-6 w-6 text-brand-blue" />,
    },
  ];

  return (
    <section
      id="awakens"
      className="relative flex min-h-screen w-full flex-col justify-center bg-brand-black px-6 py-20"
    >
      <div className="mx-auto max-w-6xl w-full">
        {/* Header */}
        <div className="text-center md:text-left mb-16">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 rounded-full border border-brand-blue/30 bg-brand-blue/5 px-3 py-1 text-xs text-brand-blue mb-4"
          >
            <Sparkles className="h-3.5 w-3.5 animate-pulse" />
            <span>Chapter 3 — Intelligence Systems</span>
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl font-extrabold tracking-tight text-white md:text-6xl"
          >
            The AI <span className="bg-gradient-to-r from-brand-blue to-brand-purple bg-clip-text text-transparent glow-text-blue">Awakens</span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="mt-4 text-lg text-zinc-400 max-w-xl"
          >
            Our core engine activates, linking six neural modules to parse, evaluate, and justify candidate matching in high dimensions.
          </motion.p>
        </div>

        {/* Node Layout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-stretch">
          {/* List of 6 Modules */}
          <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
            {nodes.map((node) => (
              <motion.button
                key={node.id}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: node.id * 0.1 }}
                onClick={() => setActiveNode(node.id === activeNode ? null : node.id)}
                className={`glass-panel text-left p-6 rounded-2xl flex gap-4 transition-all duration-300 interactive ${
                  activeNode === node.id
                    ? 'border-brand-blue bg-brand-blue/[0.04] ring-1 ring-brand-blue'
                    : 'hover:border-white/20 hover:bg-white/[0.05]'
                }`}
              >
                <div className="rounded-xl bg-white/[0.03] p-3 border border-white/[0.05] h-fit">
                  {node.icon}
                </div>
                <div>
                  <h3 className="text-md font-bold text-white mb-1">{node.title}</h3>
                  <p className="text-xs text-zinc-400 line-clamp-2 leading-relaxed">{node.shortDesc}</p>
                </div>
              </motion.button>
            ))}
          </div>

          {/* Details Panel */}
          <div className="h-full min-h-[300px]">
            <AnimatePresence mode="wait">
              {activeNode !== null ? (
                (() => {
                  const node = nodes.find((n) => n.id === activeNode)!;
                  return (
                    <motion.div
                      key={node.id}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      className="glass-panel p-8 rounded-2xl border border-brand-blue/30 bg-brand-blue/[0.02] shadow-[0_0_40px_rgba(59,130,246,0.15)] flex flex-col justify-between h-full"
                    >
                      <div>
                        <div className="rounded-2xl bg-white/[0.03] p-4 border border-white/[0.05] w-fit mb-6">
                          {node.icon}
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-4">{node.title}</h3>
                        <p className="text-sm text-zinc-300 leading-relaxed font-sans">{node.longDesc}</p>
                      </div>
                      <div className="mt-8 pt-6 border-t border-white/[0.05] flex items-center justify-between">
                        <span className="text-xs font-mono text-zinc-500">Module Status: ACTIVE</span>
                        <span className="h-2 w-2 rounded-full bg-brand-green animate-pulse" />
                      </div>
                    </motion.div>
                  );
                })()
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="glass-panel p-8 rounded-2xl border border-white/[0.05] flex flex-col items-center justify-center text-center h-full min-h-[300px]"
                >
                  <Brain className="h-12 w-12 text-zinc-600 mb-4 animate-pulse" />
                  <h3 className="text-md font-bold text-zinc-300 mb-2">Select a Neural Module</h3>
                  <p className="text-xs text-zinc-500 max-w-[200px] leading-relaxed">
                    Click any node module to expand its parameters and explore the AI brain.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  );
}
