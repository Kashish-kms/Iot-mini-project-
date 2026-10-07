import React from 'react';

interface RiskGaugeProps {
  riskLevel: number; // 0, 1, 2
  confidence: number; // 0 to 1
  size?: number;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({ riskLevel, confidence, size = 180 }) => {
  // Score mapping: Safe: 15-35, Moderate: 45-65, High: 75-95
  const score = riskLevel === 2 ? 88 : riskLevel === 1 ? 54 : 18;
  const radius = size * 0.38;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.75; // 270 degree arc
  const strokeDashoffset = arcLength - (score / 100) * arcLength;

  const color = riskLevel === 2 ? '#F43F5E' : riskLevel === 1 ? '#F59E0B' : '#10B981';
  const label = riskLevel === 2 ? 'High Risk' : riskLevel === 1 ? 'Moderate' : 'Safe';

  return (
    <div className="relative flex flex-col items-center justify-center select-none" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="transform -rotate-135">
        {/* Background Track Arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth="10"
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeLinecap="round"
        />

        {/* Foreground Progress Arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
          style={{
            filter: `drop-shadow(0 0 10px ${color})`,
          }}
        />
      </svg>

      {/* Center Digital Display */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-3xl font-heading font-extrabold text-white tracking-tight">{score}</span>
        <span
          className="text-xs font-mono font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full mt-1"
          style={{
            backgroundColor: `${color}20`,
            color: color,
            border: `1px solid ${color}40`,
          }}
        >
          {label}
        </span>
        <span className="text-[10px] text-slate-400 font-mono mt-1">
          {Math.round(confidence * 100)}% Confidence
        </span>
      </div>
    </div>
  );
};
