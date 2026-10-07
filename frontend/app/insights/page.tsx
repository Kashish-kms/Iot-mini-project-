'use client';

import React, { useState, useEffect } from 'react';
import { fetchEdaInsights } from '@/lib/api';
import { EdaInsights } from '@/lib/types';
import {
  BarChart2,
  TrendingUp,
  Sun,
  Activity,
  Layers,
  Info,
  Thermometer,
  Droplets,
  Wind,
  CheckCircle2
} from 'lucide-react';

export default function InsightsPage() {
  const [eda, setEda] = useState<EdaInsights | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEdaInsights().then((data) => {
      setEda(data);
      setLoading(false);
    });
  }, []);

  if (loading || !eda) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center text-slate-400 font-mono text-xs">
        Loading Exploratory Data Analysis telemetry...
      </div>
    );
  }

  const { statistics, correlation_matrix, hourly_patterns, label_distribution } = eda;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <BarChart2 className="w-5 h-5 text-cyan-neon" />
          <h1 className="text-2xl font-heading font-bold text-white">Exploratory Data Analysis (EDA)</h1>
        </div>
        <p className="text-xs text-slate-400 mt-1">
          Statistical feature correlations, diurnal diurnal curves, and distribution profiles of room environment telemetry.
        </p>
      </div>

      {/* 1. Class Label Balance Profile */}
      <div className="glass-panel rounded-2xl p-6 border-white/10 space-y-4">
        <h3 className="font-heading font-bold text-white text-base">Target Class Label Distribution</h3>
        <p className="text-xs text-slate-400">
          Distribution of room hazard risk across {statistics.total_samples?.toLocaleString()} aggregated windows.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {label_distribution.map((item, idx) => {
            const color = item.label === 'High Risk' ? '#F43F5E' : item.label === 'Moderate' ? '#F59E0B' : '#10B981';
            return (
              <div key={idx} className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold" style={{ color }}>{item.label}</span>
                  <span className="text-xs font-mono text-white font-bold">{item.percentage}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-700" style={{ width: `${item.percentage}%`, backgroundColor: color }} />
                </div>
                <span className="text-[11px] text-slate-500 font-mono block text-right">
                  {item.value?.toLocaleString()} samples
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. Feature Correlation Matrix Heatmap */}
      <div className="glass-panel-glow rounded-2xl p-6 border-cyan-neon/30 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-heading font-bold text-white text-base">Pearson Correlation Matrix Heatmap</h3>
            <p className="text-xs text-slate-400">
              Evaluates linear dependence across non-intrusive sensor features and risk level.
            </p>
          </div>
          <span className="text-[11px] font-mono text-cyan-neon px-2.5 py-1 rounded bg-cyan-neon/10 border border-cyan-neon/20">
            5 x 5 Normalized Matrix
          </span>
        </div>

        <div className="overflow-x-auto pt-2">
          <table className="w-full text-center text-xs font-mono">
            <thead>
              <tr className="text-slate-400 border-b border-white/10">
                <th className="py-2.5 px-3 text-left">Feature</th>
                {correlation_matrix.columns.map((col, i) => (
                  <th key={i} className="py-2.5 px-3 uppercase text-[10px]">{col.replace('_', ' ')}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {correlation_matrix.columns.map((rowName, rIdx) => (
                <tr key={rIdx}>
                  <td className="py-2.5 px-3 text-left text-slate-300 font-semibold">{rowName.replace('_', ' ')}</td>
                  {correlation_matrix.values[rIdx]?.map((val, cIdx) => {
                    // Color mapping: +1 = strong cyan, -1 = violet, 0 = neutral
                    const intensity = Math.abs(val);
                    const isPositive = val >= 0;
                    const bg = isPositive
                      ? `rgba(34, 211, 238, ${Math.min(0.85, intensity * 0.7)})`
                      : `rgba(244, 63, 94, ${Math.min(0.85, intensity * 0.7)})`;

                    return (
                      <td key={cIdx} className="py-2.5 px-3">
                        <div
                          className="py-1.5 px-2 rounded-lg font-bold text-white transition-all hover:scale-105"
                          style={{ backgroundColor: bg }}
                        >
                          {val > 0 ? `+${val.toFixed(2)}` : val.toFixed(2)}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300 flex items-start gap-3 mt-4">
          <Info className="w-4 h-4 text-cyan-neon flex-shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong>Key Insight:</strong> Air Quality (MQ-135 PPM) demonstrates a strong positive correlation (+0.88) with the environmental risk classification, while Temperature and Humidity exhibits inverse diurnal correlation (-0.42), validating the physiological comfort envelope.
          </p>
        </div>
      </div>

      {/* 3. 24-Hour Diurnal Curves (Hourly Profiles) */}
      <div className="glass-panel rounded-2xl p-6 border-white/10 space-y-4">
        <div>
          <h3 className="font-heading font-bold text-white text-base">Diurnal 24-Hour Circadian Cycles</h3>
          <p className="text-xs text-slate-400">
            Average thermal, humidity, and VOC accumulation profiles grouped by hour of the day (00:00 - 23:00).
          </p>
        </div>

        {/* Diurnal Bar Chart Matrix */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
          {/* Temperature Diurnal */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-amber-400 flex items-center gap-1.5"><Thermometer className="w-3.5 h-3.5" /> Temp Diurnal (°C)</span>
              <span className="text-slate-400">Mean: {statistics.temperature.mean}°C</span>
            </div>
            <div className="flex items-end gap-1 h-32 pt-2">
              {hourly_patterns.map((h, i) => {
                const heightPct = Math.min(100, Math.max(15, ((h.temperature - 18) / 12) * 100));
                return (
                  <div
                    key={i}
                    className="flex-1 bg-amber-400/40 hover:bg-amber-400 rounded-t transition-all cursor-pointer"
                    style={{ height: `${heightPct}%` }}
                    title={`Hour ${h.hour}:00 -> ${h.temperature}°C`}
                  />
                );
              })}
            </div>
            <div className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>00:00 (Night)</span>
              <span>12:00 (Noon)</span>
              <span>23:00</span>
            </div>
          </div>

          {/* Humidity Diurnal */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-cyan-neon flex items-center gap-1.5"><Droplets className="w-3.5 h-3.5" /> Humidity Diurnal (%)</span>
              <span className="text-slate-400">Mean: {statistics.humidity.mean}%</span>
            </div>
            <div className="flex items-end gap-1 h-32 pt-2">
              {hourly_patterns.map((h, i) => {
                const heightPct = Math.min(100, Math.max(15, ((h.humidity - 30) / 40) * 100));
                return (
                  <div
                    key={i}
                    className="flex-1 bg-cyan-neon/40 hover:bg-cyan-neon rounded-t transition-all cursor-pointer"
                    style={{ height: `${heightPct}%` }}
                    title={`Hour ${h.hour}:00 -> ${h.humidity}%`}
                  />
                );
              })}
            </div>
            <div className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>00:00</span>
              <span>12:00</span>
              <span>23:00</span>
            </div>
          </div>

          {/* Air Quality MQ-135 Diurnal */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-violet-neon flex items-center gap-1.5"><Wind className="w-3.5 h-3.5" /> Air Quality PPM</span>
              <span className="text-slate-400">Mean: {statistics.air_quality_ppm.mean} PPM</span>
            </div>
            <div className="flex items-end gap-1 h-32 pt-2">
              {hourly_patterns.map((h, i) => {
                const heightPct = Math.min(100, Math.max(15, ((h.air_quality_ppm - 350) / 400) * 100));
                return (
                  <div
                    key={i}
                    className="flex-1 bg-violet-neon/40 hover:bg-violet-neon rounded-t transition-all cursor-pointer"
                    style={{ height: `${heightPct}%` }}
                    title={`Hour ${h.hour}:00 -> ${h.air_quality_ppm} PPM`}
                  />
                );
              })}
            </div>
            <div className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>00:00 (Idle)</span>
              <span>14:00 (Occupied Peak)</span>
              <span>23:00</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
