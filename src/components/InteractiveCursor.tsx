'use client';

import React, { useEffect, useState } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

export default function InteractiveCursor() {
  const [isVisible, setIsVisible] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const mouseX = useMotionValue(-100);
  const mouseY = useMotionValue(-100);

  const springConfig = { damping: 40, stiffness: 450, mass: 0.3 };
  const cursorX = useSpring(mouseX, springConfig);
  const cursorY = useSpring(mouseY, springConfig);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      mouseX.set(e.clientX);
      mouseY.set(e.clientY);
      if (!isVisible) setIsVisible(true);
    };

    const handleMouseLeave = () => {
      setIsVisible(false);
    };

    const handleMouseEnter = () => {
      setIsVisible(true);
    };

    const handleMouseOver = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (
        target &&
        (target.tagName === 'A' ||
          target.tagName === 'BUTTON' ||
          target.closest('button') ||
          target.closest('a') ||
          target.classList.contains('interactive') ||
          target.closest('.interactive'))
      ) {
        setIsHovered(true);
      } else {
        setIsHovered(false);
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('mouseenter', handleMouseEnter);
    window.addEventListener('mouseover', handleMouseOver);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('mouseenter', handleMouseEnter);
      window.removeEventListener('mouseover', handleMouseOver);
    };
  }, [mouseX, mouseY, isVisible]);

  if (!isVisible) return null;

  return (
    <>
      {/* Outer Rotating Target Reticle */}
      <motion.div
        className="pointer-events-none fixed top-0 left-0 z-[10000] hidden h-12 w-12 -translate-x-1/2 -translate-y-1/2 md:block"
        style={{
          x: cursorX,
          y: cursorY,
        }}
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: isHovered ? 4 : 10, ease: 'linear' }}
          className="w-full h-full flex items-center justify-center"
        >
          <svg
            width="48"
            height="48"
            viewBox="0 0 48 48"
            className="w-full h-full transition-colors duration-300"
            style={{
              color: isHovered ? '#8b5cf6' : '#06b6d4',
            }}
          >
            {/* Outer Circular dashed tracking reticle */}
            <circle
              cx="24"
              cy="24"
              r="20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.2"
              strokeDasharray={isHovered ? '2 4' : '4 6'}
              strokeOpacity="0.4"
            />
            {/* Crosshair ticks */}
            <line x1="24" y1="2" x2="24" y2="6" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.8" />
            <line x1="24" y1="42" x2="24" y2="46" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.8" />
            <line x1="2" y1="24" x2="6" y2="24" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.8" />
            <line x1="42" y1="24" x2="46" y2="24" stroke="currentColor" strokeWidth="1.5" strokeOpacity="0.8" />
          </svg>
        </motion.div>
      </motion.div>

      {/* Inner Glowing Core Dot */}
      <motion.div
        className="pointer-events-none fixed top-0 left-0 z-[10000] hidden h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full shadow-[0_0_10px_rgba(6,182,212,0.8)] md:block"
        style={{
          x: mouseX,
          y: mouseY,
          scale: isHovered ? 1.4 : 1,
          backgroundColor: isHovered ? '#8b5cf6' : '#06b6d4',
          boxShadow: isHovered ? '0 0 15px rgba(139, 92, 246, 0.8)' : '0 0 10px rgba(6,182,212,0.8)',
        }}
      />
    </>
  );
}
