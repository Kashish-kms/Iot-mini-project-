import React from 'react';

interface LogoProps {
  className?: string;
  size?: number;
  showText?: boolean;
}

export const Logo: React.FC<LogoProps> = ({ className = '', size = 34, showText = true }) => {
  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* SVG Icon: Hybrid Eye + Translucent Layered Veil */}
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg
          viewBox="0 0 100 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full drop-shadow-[0_0_12px_rgba(34,211,238,0.5)] transition-transform duration-300 hover:scale-105"
        >
          <defs>
            <linearGradient id="cyanVioletGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#22D3EE" />
              <stop offset="100%" stopColor="#8B5CF6" />
            </linearGradient>
            <linearGradient id="veilLayer1" x1="0%" y1="50%" x2="100%" y2="50%">
              <stop offset="0%" stopColor="#22D3EE" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.2" />
            </linearGradient>
            <linearGradient id="veilLayer2" x1="100%" y1="50%" x2="0%" y2="50%">
              <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.7" />
              <stop offset="100%" stopColor="#22D3EE" stopOpacity="0.1" />
            </linearGradient>
            <radialGradient id="irisCore" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#22D3EE" />
              <stop offset="50%" stopColor="#3B82F6" />
              <stop offset="100%" stopColor="#0F172A" />
            </radialGradient>
          </defs>

          {/* Outer Protective Veil Shields (Frosted Curvature) */}
          <path
            d="M 12 50 C 25 24, 75 24, 88 50 C 75 76, 25 76, 12 50 Z"
            stroke="url(#cyanVioletGrad)"
            strokeWidth="3.5"
            strokeLinecap="round"
            fill="none"
          />
          {/* Layer 1: Translucent Vertical Veils */}
          <path
            d="M 28 32 C 34 42, 34 58, 28 68 C 38 64, 42 56, 42 50 C 42 44, 38 36, 28 32 Z"
            fill="url(#veilLayer1)"
          />
          {/* Layer 2: Opposite Translucent Veil */}
          <path
            d="M 72 32 C 66 42, 66 58, 72 68 C 62 64, 58 56, 58 50 C 58 44, 62 36, 72 32 Z"
            fill="url(#veilLayer2)"
          />

          {/* Center Iris Core: Ambient Sensor Pupil */}
          <circle cx="50" cy="50" r="14" fill="url(#irisCore)" stroke="#22D3EE" strokeWidth="1.8" />
          <circle cx="50" cy="50" r="5.5" fill="#FFFFFF" />
          <circle cx="52" cy="47" r="2.2" fill="#22D3EE" />

          {/* Privacy Shroud Arc (Subtle Top Canopy) */}
          <path
            d="M 32 20 Q 50 14 68 20"
            stroke="#22D3EE"
            strokeWidth="2.5"
            strokeLinecap="round"
            opacity="0.85"
          />
          <path
            d="M 36 80 Q 50 86 64 80"
            stroke="#8B5CF6"
            strokeWidth="2.5"
            strokeLinecap="round"
            opacity="0.75"
          />
        </svg>
      </div>

      {showText && (
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="font-heading font-bold text-xl tracking-tight text-white">
              Veil<span className="text-cyan-neon">Sense</span>
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-full bg-cyan-neon/10 text-cyan-neon border border-cyan-neon/30">
              v1.0
            </span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono tracking-widest uppercase">
            Zero-Intrusion IoT
          </span>
        </div>
      )}
    </div>
  );
};
