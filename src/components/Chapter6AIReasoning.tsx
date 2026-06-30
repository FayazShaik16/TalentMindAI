'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { BrainCircuit, ThumbsUp, ThumbsDown, Check, X } from 'lucide-react';

interface ScoreDetail {
  label: string;
  value: number;
}

interface CandidateCard {
  id: string;
  name: string;
  role: string;
  status: 'recommended' | 'disqualified';
  overallScore: number;
  scores: ScoreDetail[];
  rationale: string;
}

export default function Chapter6AIReasoning() {
  const [activeTab, setActiveTab] = useState<'recommended' | 'disqualified'>('recommended');

  const candidates: CandidateCard[] = [
    {
      id: 'sarah',
      name: 'Sarah Chen',
      role: 'Staff AI Systems Architect',
      status: 'recommended',
      overallScore: 96,
      scores: [
        { label: 'Technical Fit', value: 98 },
        { label: 'Career Fit', value: 95 },
        { label: 'Behavioral Fit', value: 90 },
        { label: 'Evidence Validation', value: 98 },
        { label: 'Growth Potential', value: 94 },
      ],
      rationale: 'Sarah demonstrated profound low-level systems execution by constructing sandboxed process runtimes using Linux isolation namespaces. Her code validation confirms she works comfortably in complex C++ cache layouts, outperforming typical ATS filters which reject her for lacking commercial buzzwords.',
    },
    {
      id: 'john',
      name: 'John Doe',
      role: 'Junior Full-Stack Developer',
      status: 'disqualified',
      overallScore: 32,
      scores: [
        { label: 'Technical Fit', value: 25 },
        { label: 'Career Fit', value: 40 },
        { label: 'Behavioral Fit', value: 65 },
        { label: 'Evidence Validation', value: 10 },
        { label: 'Growth Potential', value: 50 },
      ],
      rationale: 'While John successfully matched 100% of keyword filters by packing high-volume technical acronyms (AWS, Docker, FastAPI, LLM), evidence indexing revealed zero hands-on deployments. Projects consist entirely of standard boilerplate fork architectures and templated routing configurations.',
    },
  ];

  return (
    <section
      id="reasoning"
      className="relative flex min-h-screen w-full flex-col justify-center bg-brand-black px-6 py-20"
    >
      <div className="mx-auto max-w-5xl w-full">
        {/* Title */}
        <div className="text-center mb-12">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 rounded-full border border-brand-blue/30 bg-brand-blue/5 px-3 py-1 text-xs text-brand-blue mb-4"
          >
            <BrainCircuit className="h-3.5 w-3.5" />
            <span>Chapter 6 — AI Reasoning Engine</span>
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl font-extrabold tracking-tight text-white md:text-5xl"
          >
            Recruiter Reasoning
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="mt-4 text-md text-zinc-400 max-w-xl mx-auto"
          >
            Hiring trust comes from complete explanation transparency. Here is how our Recruiter Brain reviews and writes rationale tags for both recommendations and disqualifications.
          </motion.p>
        </div>

        {/* Tab Controls for Responsiveness */}
        <div className="flex justify-center gap-4 mb-8">
          <button
            onClick={() => setActiveTab('recommended')}
            className={`rounded-full px-5 py-2.5 text-xs font-semibold flex items-center gap-2 transition-all interactive ${
              activeTab === 'recommended'
                ? 'bg-brand-green text-white shadow-lg shadow-brand-green/20'
                : 'bg-white/[0.03] text-zinc-400 hover:text-white border border-white/[0.05]'
            }`}
          >
            <ThumbsUp className="h-3.5 w-3.5" />
            <span>Sarah Chen (Recommended)</span>
          </button>
          <button
            onClick={() => setActiveTab('disqualified')}
            className={`rounded-full px-5 py-2.5 text-xs font-semibold flex items-center gap-2 transition-all interactive ${
              activeTab === 'disqualified'
                ? 'bg-brand-red text-white shadow-lg shadow-brand-red/20'
                : 'bg-white/[0.03] text-zinc-400 hover:text-white border border-white/[0.05]'
            }`}
          >
            <ThumbsDown className="h-3.5 w-3.5" />
            <span>John Doe (Disqualified)</span>
          </button>
        </div>

        {/* Reasoning Score Cards */}
        <div className="perspective-[1000px] w-full flex justify-center">
          {candidates.map((cand) => {
            if (cand.status !== activeTab) return null;
            return (
              <motion.div
                key={cand.id}
                initial={{ opacity: 0, rotateY: -15, scale: 0.98 }}
                animate={{ opacity: 1, rotateY: 0, scale: 1 }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
                className={`glass-panel w-full max-w-3xl rounded-3xl p-6 md:p-10 border overflow-hidden shadow-2xl relative ${
                  cand.status === 'recommended' ? 'border-brand-green/30 bg-brand-green/[0.01]' : 'border-brand-red/30 bg-brand-red/[0.01]'
                }`}
              >
                {/* Score Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                  <div>
                    <h3 className="text-2xl font-bold text-white">{cand.name}</h3>
                    <p className="text-xs text-zinc-400">{cand.role}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-zinc-500 uppercase">Match Confidence:</span>
                    <div
                      className={`text-3xl font-extrabold font-mono rounded-2xl px-4 py-2 border ${
                        cand.status === 'recommended'
                          ? 'text-brand-green bg-brand-green/10 border-brand-green/20 glow-text-green'
                          : 'text-brand-red bg-brand-red/10 border-brand-red/20 glow-text-red'
                      }`}
                    >
                      {cand.overallScore}%
                    </div>
                  </div>
                </div>

                {/* Score bars & Rationale Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
                  {/* Scores breakdown */}
                  <div className="space-y-4">
                    <h4 className="text-xs font-semibold uppercase text-zinc-500 tracking-wider">Evaluation Breakdown</h4>
                    {cand.scores.map((score, index) => (
                      <div key={score.label} className="space-y-1.5">
                        <div className="flex justify-between text-xs font-mono text-zinc-400">
                          <span>{score.label}</span>
                          <span>{score.value}%</span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-white/[0.05] overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${score.value}%` }}
                            transition={{ duration: 0.8, delay: index * 0.1 }}
                            className={`h-full rounded-full ${
                              cand.status === 'recommended' ? 'bg-gradient-to-r from-brand-cyan to-brand-green' : 'bg-gradient-to-r from-brand-purple to-brand-red'
                            }`}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Written rationale */}
                  <div className="space-y-4">
                    <h4 className="text-xs font-semibold uppercase text-zinc-500 tracking-wider">AI Recruiter Rationale</h4>
                    <div className="glass-panel p-5 rounded-2xl bg-black/40 border-white/[0.04]">
                      <p className="text-sm text-zinc-300 leading-relaxed font-sans">{cand.rationale}</p>
                    </div>

                    {/* Quick Bullet Checklist */}
                    <div className="space-y-2 pt-2">
                      {cand.status === 'recommended' ? (
                        <>
                          <div className="flex items-start gap-2.5 text-xs text-zinc-400">
                            <div className="rounded-full bg-brand-green/20 p-0.5 border border-brand-green/30 mt-0.5">
                              <Check className="h-3 w-3 text-brand-green" />
                            </div>
                            <span>Strong evidence of system namespaces & core algorithms.</span>
                          </div>
                          <div className="flex items-start gap-2.5 text-xs text-zinc-400">
                            <div className="rounded-full bg-brand-green/20 p-0.5 border border-brand-green/30 mt-0.5">
                              <Check className="h-3 w-3 text-brand-green" />
                            </div>
                            <span>Validated repo execution confirms production proficiency.</span>
                          </div>
                        </>
                      ) : (
                        <>
                          <div className="flex items-start gap-2.5 text-xs text-zinc-400">
                            <div className="rounded-full bg-brand-red/20 p-0.5 border border-brand-red/30 mt-0.5">
                              <X className="h-3 w-3 text-brand-red" />
                            </div>
                            <span>No evidence backing the heavy keyword claims.</span>
                          </div>
                          <div className="flex items-start gap-2.5 text-xs text-zinc-400">
                            <div className="rounded-full bg-brand-red/20 p-0.5 border border-brand-red/30 mt-0.5">
                              <X className="h-3 w-3 text-brand-red" />
                            </div>
                            <span>Project scope restricted to standard web routing clones.</span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
