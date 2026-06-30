'use client';

import React, { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';

// Pure deterministic pseudo-random generator to pass strict ESLint purity checks
let seed = 12345;
function lcgRandom() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

interface ParticlesProps {
  chapter: string;
  isPulsing: boolean;
  pulseProgress: number;
}

function ParticlesScene({ chapter, isPulsing, pulseProgress }: ParticlesProps) {
  const pointsRef = useRef<THREE.Points>(null);
  const count = 1200;

  // Precompute shapes
  const shapes = useMemo(() => {
    const temp = {
      chaos: new Float32Array(count * 3),
      ats: new Float32Array(count * 3),
      brain: new Float32Array(count * 3),
      galaxy: new Float32Array(count * 3),
      reveal: new Float32Array(count * 3),
      colors: {
        chaos: new Float32Array(count * 3),
        ats: new Float32Array(count * 3),
        brain: new Float32Array(count * 3),
        galaxy: new Float32Array(count * 3),
        reveal: new Float32Array(count * 3),
      }
    };

    // Helper colors
    const colorWhite = new THREE.Color('#ffffff');
    const colorBlue = new THREE.Color('#3b82f6');
    const colorCyan = new THREE.Color('#06b6d4');
    const colorPurple = new THREE.Color('#8b5cf6');
    const colorGreen = new THREE.Color('#10b981');
    const colorRed = new THREE.Color('#ef4444');
    const colorDark = new THREE.Color('#1e293b');

    for (let i = 0; i < count; i++) {
      const idx = i * 3;

      // 1. Chaos positions: Distributed in a tall box, will drift down
      temp.chaos[idx] = (lcgRandom() - 0.5) * 16;
      temp.chaos[idx + 1] = (lcgRandom() - 0.5) * 12;
      temp.chaos[idx + 2] = (lcgRandom() - 0.5) * 8;

      colorWhite.toArray(temp.colors.chaos, idx);
      // Make a single special candidate gold/yellow that stands out in chaos
      if (i === 42) {
        new THREE.Color('#fbbf24').toArray(temp.colors.chaos, idx);
      }

      // 2. ATS: Flat scanner grid
      const cols = 40;
      const col = i % cols;
      const row = Math.floor(i / cols);
      temp.ats[idx] = (col - cols / 2) * 0.35;
      temp.ats[idx + 1] = (row - (count / cols) / 2) * 0.35;
      temp.ats[idx + 2] = 0;

      // Scanning green and red matrix colors
      if (lcgRandom() > 0.6) {
        colorGreen.toArray(temp.colors.ats, idx);
      } else {
        colorRed.toArray(temp.colors.ats, idx);
      }

      // 3. Brain: Two hemispheres (neural network)
      const isLeft = i < count / 2;
      const u = lcgRandom();
      const v = lcgRandom();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = 2.5 + lcgRandom() * 0.5;

      let bx = r * Math.sin(phi) * Math.cos(theta);
      let by = r * Math.sin(phi) * Math.sin(theta);
      let bz = r * Math.cos(phi);

      // Squash and shift into brain hemispheres
      bx *= 0.75;
      by *= 1.2;
      bz *= 0.8;
      if (isLeft) {
        bx -= 0.6;
      } else {
        bx += 0.6;
      }

      temp.brain[idx] = bx;
      temp.brain[idx + 1] = by;
      temp.brain[idx + 2] = bz;

      // Cyan / Purple synapses colors
      const c = isLeft ? colorCyan : colorPurple;
      c.toArray(temp.colors.brain, idx);

      // 4. Galaxy: Swirling spiral arms
      const arm = i % 4; // 4 spiral arms
      const angle = (i / count) * 12 + arm * (Math.PI / 2);
      const dist = 0.5 + (i / count) * 6;
      const gOffset = 0.2;
      temp.galaxy[idx] = Math.cos(angle) * dist + (lcgRandom() - 0.5) * gOffset;
      temp.galaxy[idx + 1] = (lcgRandom() - 0.5) * 0.3; // Flat disk Y
      temp.galaxy[idx + 2] = Math.sin(angle) * dist + (lcgRandom() - 0.5) * gOffset;

      // Swirling galaxy gradients
      const mixRatio = Math.sin(dist) * 0.5 + 0.5;
      const mixedColor = new THREE.Color().lerpColors(colorCyan, colorPurple, mixRatio);
      mixedColor.toArray(temp.colors.galaxy, idx);

      // 5. Reveal: Sparse ambient cosmos
      temp.reveal[idx] = (lcgRandom() - 0.5) * 25;
      temp.reveal[idx + 1] = (lcgRandom() - 0.5) * 20;
      temp.reveal[idx + 2] = (lcgRandom() - 0.5) * 15;

      colorDark.toArray(temp.colors.reveal, idx);
      if (lcgRandom() > 0.8) {
        colorBlue.toArray(temp.colors.reveal, idx);
      }
    }

    return temp;
  }, []);

  // Set initial position
  const positions = useMemo(() => new Float32Array(count * 3), []);
  const colors = useMemo(() => new Float32Array(count * 3), []);

  useEffect(() => {
    // Copy chaos as starting point
    positions.set(shapes.chaos);
    colors.set(shapes.colors.chaos);
  }, [shapes, positions, colors]);

  // Frame animation
  useFrame((state) => {
    if (!pointsRef.current) return;

    const geo = pointsRef.current.geometry;
    const posAttr = geo.getAttribute('position') as THREE.BufferAttribute;
    const colorAttr = geo.getAttribute('color') as THREE.BufferAttribute;

    const t = state.clock.getElapsedTime();

    // Select target shapes based on active chapter
    let targetPos = shapes.chaos;
    let targetColors = shapes.colors.chaos;
    let activeSpeed = 0.08; // Lerp speed

    if (chapter === 'chaos') {
      targetPos = shapes.chaos;
      targetColors = shapes.colors.chaos;
      activeSpeed = 0.05;
    } else if (chapter === 'ats') {
      targetPos = shapes.ats;
      targetColors = shapes.colors.ats;
      activeSpeed = 0.08;
    } else if (chapter === 'awakens' || chapter === 'investigation') {
      targetPos = shapes.brain;
      targetColors = shapes.colors.brain;
      activeSpeed = 0.06;
    } else if (chapter === 'semantic') {
      targetPos = shapes.galaxy;
      targetColors = shapes.colors.galaxy;
      activeSpeed = 0.07;
    } else if (chapter === 'reasoning' || chapter === 'reveal') {
      targetPos = shapes.reveal;
      targetColors = shapes.colors.reveal;
      activeSpeed = 0.04;
    }

    // Perform interpolation and update attributes
    for (let i = 0; i < count; i++) {
      const idx = i * 3;

      // Handle chaos movement (drift down)
      if (chapter === 'chaos') {
        // Slowly move Y downwards
        let x = posAttr.getX(i);
        let y = posAttr.getY(i) - 0.02;
        let z = posAttr.getZ(i);

        // Reset Y when it drifts past bounds
        if (y < -6) {
          y = 6;
          x = (lcgRandom() - 0.5) * 16;
          z = (lcgRandom() - 0.5) * 8;
        }

        posAttr.setXYZ(i, x, y, z);
      } else if (chapter === 'semantic' && isPulsing) {
        // Galaxy Semantic Pulse - cluster top nodes to center
        // Let's contract the particles inside based on pulseProgress
        const factor = 1 - Math.sin(pulseProgress * Math.PI) * 0.7;
        const tx = shapes.galaxy[idx] * factor;
        const ty = shapes.galaxy[idx + 1] * factor;
        const tz = shapes.galaxy[idx + 2] * factor;

        posAttr.setXYZ(
          i,
          THREE.MathUtils.lerp(posAttr.getX(i), tx, activeSpeed),
          THREE.MathUtils.lerp(posAttr.getY(i), ty, activeSpeed),
          THREE.MathUtils.lerp(posAttr.getZ(i), tz, activeSpeed)
        );
      } else {
        // Normal interpolation
        const tx = targetPos[idx];
        const ty = targetPos[idx + 1];
        const tz = targetPos[idx + 2];

        // Add subtle waving motion in neural network or galaxy states
        let ox = 0;
        let oy = 0;
        const oz = 0;
        if (chapter === 'awakens' || chapter === 'investigation') {
          ox = Math.sin(t + idx) * 0.05;
          oy = Math.cos(t * 0.8 + idx) * 0.05;
        } else if (chapter === 'semantic') {
          // Slow rotation around Y axis
          const rotateSpeed = 0.05;
          const currentX = posAttr.getX(i);
          const currentZ = posAttr.getZ(i);
          const nextAngle = rotateSpeed * 0.01;
          const rx = currentX * Math.cos(nextAngle) - currentZ * Math.sin(nextAngle);
          const rz = currentX * Math.sin(nextAngle) + currentZ * Math.cos(nextAngle);
          posAttr.setXYZ(i, rx, posAttr.getY(i), rz);
          continue;
        }

        posAttr.setXYZ(
          i,
          THREE.MathUtils.lerp(posAttr.getX(i), tx + ox, activeSpeed),
          THREE.MathUtils.lerp(posAttr.getY(i), ty + oy, activeSpeed),
          THREE.MathUtils.lerp(posAttr.getZ(i), tz + oz, activeSpeed)
        );
      }

      // Smoothly interpolate colors
      colorAttr.setXYZ(
        i,
        THREE.MathUtils.lerp(colorAttr.getX(i), targetColors[idx], 0.08),
        THREE.MathUtils.lerp(colorAttr.getY(i), targetColors[idx + 1], 0.08),
        THREE.MathUtils.lerp(colorAttr.getZ(i), targetColors[idx + 2], 0.08)
      );
    }

    // Mark updates
    posAttr.needsUpdate = true;
    colorAttr.needsUpdate = true;
  });

  return (
    <Points ref={pointsRef} positions={positions} colors={colors} stride={3}>
      <PointMaterial
        transparent
        size={0.06}
        sizeAttenuation={true}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        opacity={0.8}
      />
    </Points>
  );
}

// Separate component for line connections to simulate neural synapses in Awakening/Investigation chapters
function NeuralConnections({ chapter }: { chapter: string }) {
  const lineRef = useRef<THREE.LineSegments>(null);

  const active = chapter === 'awakens' || chapter === 'investigation';

  const [lineGeometry, lineColors] = useMemo(() => {
    const maxLines = 150;
    const pos = new Float32Array(maxLines * 2 * 3);
    const cols = new Float32Array(maxLines * 2 * 3);
    return [pos, cols];
  }, []);

  useFrame((state) => {
    if (!lineRef.current) return;

    const geo = lineRef.current.geometry;
    const posAttr = geo.getAttribute('position') as THREE.BufferAttribute;
    const colorAttr = geo.getAttribute('color') as THREE.BufferAttribute;

    const op = active ? 0.35 : 0;
    const mat = lineRef.current.material as THREE.LineBasicMaterial;
    mat.opacity = THREE.MathUtils.lerp(mat.opacity, op, 0.05);

    if (!active) return;

    const t = state.clock.getElapsedTime();

    // Create random connections between virtual nodes
    const nodes = 15;
    const points: THREE.Vector3[] = [];
    const colorCyan = new THREE.Color('#06b6d4');
    const colorPurple = new THREE.Color('#8b5cf6');

    for (let i = 0; i < nodes; i++) {
      // Form hemisphere coordinates
      const isLeft = i < nodes / 2;
      const theta = (i / nodes) * Math.PI * 2 + t * 0.1;
      const phi = Math.sin(t * 0.2 + i) * 1.2;
      const r = 2.0;

      let x = r * Math.sin(phi) * Math.cos(theta);
      let y = r * Math.sin(phi) * Math.sin(theta);
      let z = r * Math.cos(phi);

      x *= 0.75;
      y *= 1.2;
      z *= 0.8;
      if (isLeft) {
        x -= 0.6;
      } else {
        x += 0.6;
      }
      points.push(new THREE.Vector3(x, y, z));
    }

    let lineIdx = 0;
    for (let i = 0; i < nodes; i++) {
      for (let j = i + 1; j < nodes; j++) {
        if (points[i].distanceTo(points[j]) < 2.5 && lineIdx < 150) {
          const p1 = points[i];
          const p2 = points[j];

          posAttr.setXYZ(lineIdx * 2, p1.x, p1.y, p1.z);
          posAttr.setXYZ(lineIdx * 2 + 1, p2.x, p2.y, p2.z);

          // Assign colors
          const c = i < nodes / 2 ? colorCyan : colorPurple;
          colorAttr.setXYZ(lineIdx * 2, c.r, c.g, c.b);
          colorAttr.setXYZ(lineIdx * 2 + 1, c.r, c.g, c.b);

          lineIdx++;
        }
      }
    }

    // Set remaining lines to 0
    for (let i = lineIdx; i < 150; i++) {
      posAttr.setXYZ(i * 2, 0, 0, 0);
      posAttr.setXYZ(i * 2 + 1, 0, 0, 0);
    }

    posAttr.needsUpdate = true;
    colorAttr.needsUpdate = true;
  });

  return (
    <lineSegments ref={lineRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[lineGeometry, 3]}
        />
        <bufferAttribute
          attach="attributes-color"
          args={[lineColors, 3]}
        />
      </bufferGeometry>
      <lineBasicMaterial
        transparent
        opacity={0}
        vertexColors
        blending={THREE.AdditiveBlending}
      />
    </lineSegments>
  );
}

interface StoryCanvasWrapperProps {
  chapter: string;
  isPulsing?: boolean;
  pulseProgress?: number;
}

export default function StoryCanvas({
  chapter,
  isPulsing = false,
  pulseProgress = 0,
}: StoryCanvasWrapperProps) {
  return (
    <div className="fixed inset-0 -z-10 h-screen w-screen bg-brand-black">
      {/* Background Gradients */}
      <div className="absolute inset-0 ambient-glow-1 opacity-60 pointer-events-none" />
      <div className="absolute inset-0 ambient-glow-2 opacity-40 pointer-events-none" />
      <div className="absolute inset-0 grid-bg opacity-20 pointer-events-none" />
      
      {/* Canvas */}
      <Canvas
        camera={{ position: [0, 0, 8], fov: 60 }}
        gl={{ antialias: true, alpha: true }}
      >
        <ambientLight intensity={0.2} />
        <pointLight position={[10, 10, 10]} intensity={1.5} />
        <ParticlesScene
          chapter={chapter}
          isPulsing={isPulsing}
          pulseProgress={pulseProgress}
        />
        <NeuralConnections chapter={chapter} />
      </Canvas>
    </div>
  );
}
