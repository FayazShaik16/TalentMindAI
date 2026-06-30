'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import Chapter1Chaos from '@/components/Chapter1Chaos';
import Chapter2BrokenATS from '@/components/Chapter2BrokenATS';
import Chapter3AIAwakens from '@/components/Chapter3AIAwakens';
import Chapter4Investigation from '@/components/Chapter4Investigation';
import Chapter5SemanticUniverse from '@/components/Chapter5SemanticUniverse';
import Chapter6AIReasoning from '@/components/Chapter6AIReasoning';
import Chapter7FinalReveal from '@/components/Chapter7FinalReveal';

const StoryCanvas = dynamic(() => import('@/components/StoryCanvas'), {
  ssr: false,
});

export default function Home() {
  const [activeChapter, setActiveChapter] = useState('chaos');
  const [isPulsing, setIsPulsing] = useState(false);
  const [pulseProgress, setPulseProgress] = useState(0);

  useEffect(() => {
    const chapters = ['chaos', 'ats', 'awakens', 'investigation', 'semantic', 'reasoning', 'reveal'];
    const observers: IntersectionObserver[] = [];

    const observerCallback = (entries: IntersectionObserverEntry[]) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          setActiveChapter(entry.target.id);
        }
      });
    };

    const observerOptions = {
      root: null,
      rootMargin: '-40% 0px -40% 0px', // Triggers when the section occupies the center band of the screen
      threshold: 0,
    };

    chapters.forEach((id) => {
      const el = document.getElementById(id);
      if (el) {
        const observer = new IntersectionObserver(observerCallback, observerOptions);
        observer.observe(el);
        observers.push(observer);
      }
    });

    return () => {
      observers.forEach((obs) => obs.disconnect());
    };
  }, []);

  const handlePulse = (active: boolean, progress: number) => {
    setIsPulsing(active);
    setPulseProgress(progress);
  };

  return (
    <div className="relative min-h-screen text-white bg-brand-black w-full overflow-x-hidden">
      {/* Dynamic Background Canvas */}
      <StoryCanvas
        chapter={activeChapter}
        isPulsing={isPulsing}
        pulseProgress={pulseProgress}
      />



      {/* Global Navigation */}
      <Navbar />

      {/* Narrative Scroll Flow */}
      <main className="relative z-10 w-full">
        <Chapter1Chaos />
        <Chapter2BrokenATS />
        <Chapter3AIAwakens />
        <Chapter4Investigation />
        <Chapter5SemanticUniverse onPulse={handlePulse} />
        <Chapter6AIReasoning />
        <Chapter7FinalReveal />
      </main>

      {/* Editorial Footer */}
      <Footer />
    </div>
  );
}
