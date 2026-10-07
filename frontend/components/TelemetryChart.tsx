'use client';

import React, { useState } from 'react';
import { TelemetryReading } from '@/lib/types';

interface TelemetryChartProps {
  data: TelemetryReading[];
  timeRange: string;
  onRangeChange: (range: string) => void;
}

export const TelemetryChart: React.FC<TelemetryChartProps> = ({
  data,
  timeRange,
  onRangeChange,
}) => {
  const [activeMetric, setActiveMetric] = useState<'all' | 'temperature' | 'humidity' | 'air_quality_ppm'>('all');
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-slate-500 font-mono text-xs">
        No telemetry data available for selected range.
      </div>
    );
  }

  // Sample or slice data to ~30-50 points for smooth charting rendering
  const step = Math.max(1, Math.floor(data.length / 40));
  const chartPoints = data
    .filter((_, idx) => idx % step === 0)
    .slice(-40);

  const width = 800;
  const height = 240;
  const padding = { top: 20, right: 30, bottom: 35, left: 45 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  // Scale ranges
  const minTemp = 18;
  const maxTemp = 32;
  const minHum = 25;
  const maxHum = 85;
  const minPpm = 350;
  const maxPpm = 1100;

  const getCoordinates = (points: TelemetryReading[], metric: 'temperature' | 'humidity' | 'air_quality_ppm') => {
    return points.map((p, i) => {
      const x = padding.left + (i / (points.length - 1 || 1)) * graphWidth;
      let val = p[metric];
      let min = minTemp;
      let max = maxTemp;
      if (metric === 'humidity') {
        min = minHum;
        max = maxHum;
      } else if (metric === 'air_quality_ppm') {
        min = minPpm;
        max = maxPpm;
      }
      const y = padding.top + graphHeight - ((val - min) / (max - min || 1)) * graphHeight;
      return { x, y: Math.max(padding.top, Math.min(height - padding.bottom, y)), val, ts: p.timestamp };
    });
  };

  const tempCoords = getCoordinates(chartPoints, 'temperature');
  const humCoords = getCoordinates(chartPoints, 'humidity');
  const ppmCoords = getCoordinates(chartPoints, 'air_quality_ppm');

  const makePath = (coords: Array<{ x: number; y: number }>) => {
    if (coords.length === 0) return '';
    return coords.reduce((acc, curr, i, arr) => {
      if (i === 0) return `M ${curr.x} ${curr.y}`;
      const prev = arr[i - 1];
      const cp1x = prev.x + (curr.x - prev.x) / 2;
      const cp1y = prev.y;
      const cp2x = prev.x + (curr.x - prev.x) / 2;
      const cp2y = curr.y;
      return `${acc} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${curr.x} ${curr.y}`;
    }, '');
  };

  const tempPath = makePath(tempCoords);
  const humPath = makePath(humCoords);
  const ppmPath = makePath(ppmCoords);

  const hoveredPoint = hoverIndex !== null && chartPoints[hoverIndex] ? chartPoints[hoverIndex] : null;

  return (
    <div className="w-full">
      {/* Header Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        {/* Metric Toggles */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-white/5 border border-white/10 text-xs">
          <button
            onClick={() => setActiveMetric('all')}
            className={`px-2.5 py-1 rounded-lg transition-all ${
              activeMetric === 'all' ? 'bg-white/10 text-white font-medium' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All Metrics
          </button>
          <button
            onClick={() => setActiveMetric('temperature')}
            className={`px-2.5 py-1 rounded-lg flex items-center gap-1.5 transition-all ${
              activeMetric === 'temperature' ? 'bg-amber-500/20 text-amber-300 font-medium' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            Temp (°C)
          </button>
          <button
            onClick={() => setActiveMetric('humidity')}
            className={`px-2.5 py-1 rounded-lg flex items-center gap-1.5 transition-all ${
              activeMetric === 'humidity' ? 'bg-cyan-500/20 text-cyan-300 font-medium' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-cyan-neon" />
            Humidity (%)
          </button>
          <button
            onClick={() => setActiveMetric('air_quality_ppm')}
            className={`px-2.5 py-1 rounded-lg flex items-center gap-1.5 transition-all ${
              activeMetric === 'air_quality_ppm' ? 'bg-violet-500/20 text-violet-300 font-medium' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-violet-neon" />
            Air Quality (PPM)
          </button>
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center gap-1 p-1 rounded-xl bg-white/5 border border-white/10 text-xs font-mono">
          {['1h', '6h', '24h', '7d'].map((range) => (
            <button
              key={range}
              onClick={() => onRangeChange(range)}
              className={`px-2.5 py-1 rounded-lg uppercase transition-all ${
                timeRange === range
                  ? 'bg-cyan-neon/20 text-cyan-neon font-bold border border-cyan-neon/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Main SVG Graph */}
      <div className="relative w-full overflow-hidden bg-black/20 rounded-xl border border-white/5 p-2">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto overflow-visible select-none"
          onMouseLeave={() => setHoverIndex(null)}
        >
          {/* Subtle horizontal grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct) => {
            const y = padding.top + pct * graphHeight;
            return (
              <line
                key={pct}
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="rgba(255, 255, 255, 0.05)"
                strokeDasharray="4 4"
              />
            );
          })}

          {/* Paths */}
          {(activeMetric === 'all' || activeMetric === 'temperature') && (
            <path
              d={tempPath}
              fill="none"
              stroke="#F59E0B"
              strokeWidth="2.5"
              strokeLinecap="round"
              className="drop-shadow-[0_0_8px_rgba(245,158,11,0.5)] transition-all duration-300"
            />
          )}

          {(activeMetric === 'all' || activeMetric === 'humidity') && (
            <path
              d={humPath}
              fill="none"
              stroke="#22D3EE"
              strokeWidth="2.5"
              strokeLinecap="round"
              className="drop-shadow-[0_0_8px_rgba(34,211,238,0.5)] transition-all duration-300"
            />
          )}

          {(activeMetric === 'all' || activeMetric === 'air_quality_ppm') && (
            <path
              d={ppmPath}
              fill="none"
              stroke="#8B5CF6"
              strokeWidth="2.5"
              strokeLinecap="round"
              className="drop-shadow-[0_0_8px_rgba(139,92,246,0.5)] transition-all duration-300"
            />
          )}

          {/* Interactive Hover Hit Areas */}
          {chartPoints.map((_, i) => {
            const x = padding.left + (i / (chartPoints.length - 1 || 1)) * graphWidth;
            return (
              <rect
                key={i}
                x={x - (graphWidth / chartPoints.length) / 2}
                y={padding.top}
                width={graphWidth / chartPoints.length}
                height={graphHeight}
                fill="transparent"
                className="cursor-crosshair"
                onMouseEnter={() => setHoverIndex(i)}
              />
            );
          })}

          {/* Hover guideline and dots */}
          {hoverIndex !== null && chartPoints[hoverIndex] && (
            <g>
              <line
                x1={tempCoords[hoverIndex]?.x || 0}
                y1={padding.top}
                x2={tempCoords[hoverIndex]?.x || 0}
                y2={height - padding.bottom}
                stroke="rgba(255, 255, 255, 0.3)"
                strokeDasharray="3 3"
              />
              <circle cx={tempCoords[hoverIndex]?.x} cy={tempCoords[hoverIndex]?.y} r="5" fill="#F59E0B" />
              <circle cx={humCoords[hoverIndex]?.x} cy={humCoords[hoverIndex]?.y} r="5" fill="#22D3EE" />
              <circle cx={ppmCoords[hoverIndex]?.x} cy={ppmCoords[hoverIndex]?.y} r="5" fill="#8B5CF6" />
            </g>
          )}

          {/* X Axis Time Labels */}
          <text x={padding.left} y={height - 10} fill="#64748B" fontSize="10" fontFamily="JetBrains Mono">
            {chartPoints[0]?.timestamp.substring(11, 16) || ''}
          </text>
          <text
            x={padding.left + graphWidth / 2}
            y={height - 10}
            fill="#64748B"
            fontSize="10"
            textAnchor="middle"
            fontFamily="JetBrains Mono"
          >
            {chartPoints[Math.floor(chartPoints.length / 2)]?.timestamp.substring(11, 16) || ''}
          </text>
          <text
            x={width - padding.right}
            y={height - 10}
            fill="#64748B"
            fontSize="10"
            textAnchor="end"
            fontFamily="JetBrains Mono"
          >
            {chartPoints[chartPoints.length - 1]?.timestamp.substring(11, 16) || ''}
          </text>
        </svg>

        {/* Hover Tooltip Overlay */}
        {hoveredPoint && (
          <div className="absolute top-3 right-4 p-2.5 rounded-lg bg-[#070B14]/90 border border-white/20 backdrop-blur-md text-xs font-mono flex items-center gap-4 shadow-xl">
            <span className="text-slate-400">{hoveredPoint.timestamp.substring(11, 19)}</span>
            <span className="text-amber-400 font-bold">{hoveredPoint.temperature}°C</span>
            <span className="text-cyan-neon font-bold">{hoveredPoint.humidity}%</span>
            <span className="text-violet-neon font-bold">{hoveredPoint.air_quality_ppm} PPM</span>
            <span className={hoveredPoint.motion_detected ? 'text-emerald-400' : 'text-slate-500'}>
              {hoveredPoint.motion_detected ? 'Occupied' : 'Idle'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
