'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FileSearch, CheckCircle2, AlertTriangle, ShieldCheck, GitBranch } from 'lucide-react';

interface EvidenceCard {
  id: string;
  title: string;
  status: 'verified' | 'unverified' | 'neutral';
  confidence?: number;
  description: string;
  source?: string;
}

export default function Chapter4Investigation() {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  // Define structured node data
  const candidateCard: EvidenceCard = {
    id: 'candidate',
    title: 'Sarah Chen',
    status: 'neutral',
    description: 'Principal Systems Architect. Stated claims: custom container development, core C++, high-scale distributed indexing.',
  };

  const projectCards: EvidenceCard[] = [
    {
      id: 'project-vector',
      title: 'Project Vector',
      status: 'verified',
      description: 'Distributed embedding database built to index 100M+ dense representations.',
    },
    {
      id: 'project-titan',
      status: 'verified',
      title: 'Project Titan',
      description: 'Custom container runtime built on bare metal Linux isolation namespaces.',
    },
  ];

  const skillCards: EvidenceCard[] = [
    {
      id: 'skill-cpp',
      title: 'High-Scale C++ Engine',
      status: 'verified',
      confidence: 98,
      description: 'Engineered memory-mapped caches and lock-free thread structures.',
      source: 'GitHub repo "VectorDB" (142 commits)',
    },
    {
      id: 'skill-latency',
      title: '12K req/s Query Latency',
      status: 'verified',
      confidence: 100,
      description: 'Documented load tests verify sub-millisecond lookups at scale.',
      source: 'PR #234 benchmarking reports',
    },
    {
      id: 'skill-isolation',
      title: 'Kernel Isolation Systems',
      status: 'verified',
      confidence: 94,
      description: 'Custom cgroups and seccomp profile builder written in Rust.',
      source: 'Project Titan source tree (4,200 lines)',
    },
    {
      id: 'skill-k8s',
      title: 'Kubernetes Cluster Admin',
      status: 'unverified',
      confidence: 32,
      description: 'Stated claim of managing production clusters of 500+ worker nodes.',
      source: 'Zero configuration history or commit records found in logs.',
    },
  ];

  return (
    <section
      id="investigation"
      className="relative flex min-h-screen w-full flex-col justify-center bg-brand-black px-6 py-20 select-none"
    >
      <div className="mx-auto max-w-7xl w-full">
        {/* Title */}
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 rounded-full border border-brand-purple/30 bg-brand-purple/5 px-3 py-1 text-xs text-brand-purple mb-4"
          >
            <FileSearch className="h-3.5 w-3.5" />
            <span>Chapter 4 — Evidence Board</span>
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl font-extrabold tracking-tight text-white md:text-5xl"
          >
            The Evidence Investigation
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="mt-4 text-lg text-zinc-400 max-w-xl mx-auto"
          >
            Our engine cross-verifies credentials by linking candidates to raw projects and actual code evidence. Hover cards to trace connections.
          </motion.p>
        </div>

        {/* Structured Evidence Board */}
        <div className="relative glass-panel rounded-3xl p-6 md:p-10 border border-white/[0.05] bg-brand-dark/40 overflow-hidden">
          
          <div className="grid grid-cols-1 lg:grid-cols-11 gap-4 items-center">
            
            {/* Lane 1: Candidate (Lg: col-span-3) */}
            <div className="lg:col-span-3 flex flex-col justify-center h-full py-4">
              <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-3 block text-center lg:text-left">
                Candidate Profile
              </span>
              <motion.div
                onMouseEnter={() => setHoveredCard('candidate')}
                onMouseLeave={() => setHoveredCard(null)}
                className={`glass-panel p-5 rounded-2xl border transition-all duration-300 cursor-pointer w-full ${
                  hoveredCard === 'candidate'
                    ? 'border-brand-blue bg-brand-blue/[0.04] shadow-[0_0_25px_rgba(59,130,246,0.2)]'
                    : 'border-white/10'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[9px] font-mono bg-white/[0.08] px-2 py-0.5 rounded text-zinc-300">SYSTEMS</span>
                  <span className="h-2 w-2 rounded-full bg-brand-blue animate-pulse" />
                </div>
                <h3 className="text-lg font-bold text-white mb-2">{candidateCard.title}</h3>
                <p className="text-xs text-zinc-400 leading-relaxed font-sans">{candidateCard.description}</p>
              </motion.div>
            </div>

            {/* Link 1: Candidate -> Projects (Lg: col-span-1) */}
            <div className="hidden lg:block lg:col-span-1 h-64 pointer-events-none">
              <svg className="w-full h-full">
                <g>
                  {/* Path to Project 1 */}
                  <path
                    d="M 0 128 Q 50 128, 100 64"
                    fill="none"
                    stroke={hoveredCard === 'candidate' || hoveredCard === 'project-vector' ? '#10b981' : '#ffffff'}
                    strokeWidth={hoveredCard === 'candidate' || hoveredCard === 'project-vector' ? 3 : 1.5}
                    strokeOpacity={hoveredCard === 'candidate' || hoveredCard === 'project-vector' ? 0.8 : 0.15}
                    className="transition-all duration-300"
                  />
                  {/* Path to Project 2 */}
                  <path
                    d="M 0 128 Q 50 128, 100 192"
                    fill="none"
                    stroke={hoveredCard === 'candidate' || hoveredCard === 'project-titan' ? '#10b981' : '#ffffff'}
                    strokeWidth={hoveredCard === 'candidate' || hoveredCard === 'project-titan' ? 3 : 1.5}
                    strokeOpacity={hoveredCard === 'candidate' || hoveredCard === 'project-titan' ? 0.8 : 0.15}
                    className="transition-all duration-300"
                  />
                </g>
              </svg>
            </div>

            {/* Lane 2: Projects (Lg: col-span-3) */}
            <div className="lg:col-span-3 flex flex-col gap-6 justify-center h-full py-4">
              <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block text-center lg:text-left">
                Verified Projects
              </span>
              {projectCards.map((project) => (
                <motion.div
                  key={project.id}
                  onMouseEnter={() => setHoveredCard(project.id)}
                  onMouseLeave={() => setHoveredCard(null)}
                  className={`glass-panel p-5 rounded-2xl border transition-all duration-300 cursor-pointer w-full ${
                    hoveredCard === project.id
                      ? 'border-brand-blue bg-brand-blue/[0.04] shadow-[0_0_25px_rgba(59,130,246,0.2)]'
                      : 'border-brand-green/20'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[9px] font-mono bg-brand-green/10 text-brand-green border border-brand-green/20 px-2 py-0.5 rounded">
                      VERIFIED PROJECT
                    </span>
                    <span className="h-2 w-2 rounded-full bg-brand-green" />
                  </div>
                  <h3 className="text-md font-bold text-white mb-2">{project.title}</h3>
                  <p className="text-xs text-zinc-400 leading-relaxed font-sans">{project.description}</p>
                </motion.div>
              ))}
            </div>

            {/* Link 2: Projects -> Skills (Lg: col-span-1) */}
            <div className="hidden lg:block lg:col-span-1 h-96 pointer-events-none">
              <svg className="w-full h-full">
                <g>
                  {/* Project Vector -> Skill C++ */}
                  <path
                    d="M 0 96 Q 50 96, 100 48"
                    fill="none"
                    stroke={hoveredCard === 'project-vector' || hoveredCard === 'skill-cpp' ? '#10b981' : '#ffffff'}
                    strokeWidth={hoveredCard === 'project-vector' || hoveredCard === 'skill-cpp' ? 3 : 1.5}
                    strokeOpacity={hoveredCard === 'project-vector' || hoveredCard === 'skill-cpp' ? 0.8 : 0.15}
                    className="transition-all duration-300"
                  />
                  {/* Project Vector -> Skill Latency */}
                  <path
                    d="M 0 96 Q 50 96, 100 144"
                    fill="none"
                    stroke={hoveredCard === 'project-vector' || hoveredCard === 'skill-latency' ? '#10b981' : '#ffffff'}
                    strokeWidth={hoveredCard === 'project-vector' || hoveredCard === 'skill-latency' ? 3 : 1.5}
                    strokeOpacity={hoveredCard === 'project-vector' || hoveredCard === 'skill-latency' ? 0.8 : 0.15}
                    className="transition-all duration-300"
                  />
                  {/* Project Titan -> Skill Isolation */}
                  <path
                    d="M 0 288 Q 50 288, 100 240"
                    fill="none"
                    stroke={hoveredCard === 'project-titan' || hoveredCard === 'skill-isolation' ? '#10b981' : '#ffffff'}
                    strokeWidth={hoveredCard === 'project-titan' || hoveredCard === 'skill-isolation' ? 3 : 1.5}
                    strokeOpacity={hoveredCard === 'project-titan' || hoveredCard === 'skill-isolation' ? 0.8 : 0.15}
                    className="transition-all duration-300"
                  />
                  {/* Project Titan -> Skill K8s */}
                  <path
                    d="M 0 288 Q 50 288, 100 336"
                    fill="none"
                    stroke={hoveredCard === 'project-titan' || hoveredCard === 'skill-k8s' ? '#ef4444' : '#ffffff'}
                    strokeWidth={hoveredCard === 'project-titan' || hoveredCard === 'skill-k8s' ? 3 : 1.5}
                    strokeOpacity={hoveredCard === 'project-titan' || hoveredCard === 'skill-k8s' ? 0.8 : 0.15}
                    className="transition-all duration-300"
                  />
                </g>
              </svg>
            </div>

            {/* Lane 3: Skills & Evidence (Lg: col-span-3) */}
            <div className="lg:col-span-3 flex flex-col gap-4 justify-center h-full py-4">
              <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block text-center lg:text-left">
                Extracted Claims & Evidence
              </span>
              {skillCards.map((skill) => (
                <motion.div
                  key={skill.id}
                  onMouseEnter={() => setHoveredCard(skill.id)}
                  onMouseLeave={() => setHoveredCard(null)}
                  className={`glass-panel p-4 rounded-xl border transition-all duration-300 cursor-pointer w-full relative ${
                    hoveredCard === skill.id
                      ? 'border-brand-blue bg-brand-blue/[0.04] shadow-[0_0_25px_rgba(59,130,246,0.2)]'
                      : skill.status === 'verified'
                      ? 'border-brand-green/20'
                      : 'border-brand-red/20'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[8px] font-mono text-zinc-500">CLAIM EVIDENCE</span>
                    <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded ${
                      skill.status === 'verified' ? 'bg-brand-green/10 text-brand-green' : 'bg-brand-red/10 text-brand-red'
                    }`}>
                      {skill.status === 'verified' ? `VERIFIED (${skill.confidence}%)` : `DISPUTED (${skill.confidence}%)`}
                    </span>
                  </div>
                  <h3 className="text-xs font-bold text-white mb-1">{skill.title}</h3>
                  <p className="text-[10px] text-zinc-400 leading-normal mb-1">{skill.description}</p>
                  
                  {skill.source && hoveredCard === skill.id && (
                    <motion.div
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="text-[9px] text-brand-cyan font-mono flex items-center gap-1 border-t border-white/[0.05] pt-1.5 mt-1.5"
                    >
                      <GitBranch className="h-2.5 w-2.5 flex-shrink-0" strokeWidth={2.5} />
                      <span className="truncate">{skill.source}</span>
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </div>

          </div>

          {/* Details Bar */}
          <div className="mt-8 border-t border-white/[0.05] pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-zinc-500">
            <span className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-brand-blue" />
              <span>Evidence Audit Trail Activated // 5 Verified Anchors</span>
            </span>
            <span>Target Confidence: &gt;90% Match Requirement</span>
          </div>

        </div>
      </div>
    </section>
  );
}
