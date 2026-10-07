'use client';

import React, { useState } from 'react';
import {
  ShieldCheck,
  Lock,
  EyeOff,
  MicOff,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  Key,
  Server,
  Cpu,
  Layers,
  ArrowRight
} from 'lucide-react';

export default function PrivacyPage() {
  const [activeStep, setActiveStep] = useState(1);

  const threatModel = {
    inScope: [
      {
        threat: 'Network Eavesdropping & Packet Sniffing',
        vector: 'Adversary monitoring local Wi-Fi or gateway traffic.',
        mitigation: 'Encrypted via TLS 1.3 with AES-256-GCM cipher suite. Payload is unreadable in transit.',
        status: 'Mitigated'
      },
      {
        threat: 'Unauthorized Broker Access & Rogue Publishing',
        vector: 'Attacker attempting to publish forged sensor packets or actuation commands.',
        mitigation: 'Broker enforces X.509 client certificate authentication and strict topic Access Control Lists (ACL).',
        status: 'Mitigated'
      },
      {
        threat: 'Replay Attacks & Packet Duplication',
        vector: 'Attacker recording legitimate encrypted packets and re-transmitting them.',
        mitigation: 'Every packet contains monotonic timestamps and window sequence numbers; rejected by backend if stale.',
        status: 'Mitigated'
      },
      {
        threat: 'Occupancy Identity De-Anonymization',
        vector: 'Attempting to identify specific individuals through high-frequency motion signatures.',
        mitigation: 'On-device 30-second aggregation obscures micro-gait signatures. Raw 1s buffers are discarded immediately.',
        status: 'Mitigated'
      }
    ],
    outOfScope: [
      {
        threat: 'Physical Microcontroller Tampering',
        reason: 'Direct physical probing of ESP32 GPIO pins with oscilloscope or logic analyzer is considered out of ambient threat scope.'
      },
      {
        threat: 'Physical Sensor Disconnection or Obstruction',
        reason: 'Physical vandalism (e.g. covering DHT22 or PIR sensor with tape) is handled as a hardware fault rather than a cyber vulnerability.'
      },
      {
        threat: 'Compromise of the Host Server Operating System',
        reason: 'Root privilege compromise on the server hosting Mosquitto and Docker falls under general IT infrastructure hardening.'
      }
    ]
  };

  const comparisonData = [
    {
      category: 'Optical / Video Surveillance',
      conventional: 'HD Video Streams (1080p / 4K), face crops, room imagery uploaded to cloud',
      veilsense: 'Zero optical elements. Physically impossible to capture imagery.',
      verdict: 'Completely Excluded'
    },
    {
      category: 'Acoustic / Voice Recording',
      conventional: 'Far-field microphone arrays, keyword wake audio, speech recordings',
      veilsense: 'Zero microphones or acoustic sensors. Speech is physically inaudible to hardware.',
      verdict: 'Completely Excluded'
    },
    {
      category: 'Biometric & Gait Profiling',
      conventional: 'Facial embeddings, gait frequency, millimeter-wave silhouette tracking',
      veilsense: 'Single PIR infrared pulse counter aggregated into coarse 30s counts.',
      verdict: 'Fully Anonymized'
    },
    {
      category: 'Data Granularity at Transmission',
      conventional: 'Continuous raw sub-second streams streamed directly over internet',
      veilsense: '30-second window summary statistics (mean, variance, pulse count).',
      verdict: 'Edge Aggregated'
    },
    {
      category: 'Identity & PII Storage',
      conventional: 'User accounts linked to room IDs, personal schedules, device MACs',
      veilsense: 'Strictly anonymous room telemetry; zero user identity tied to readings.',
      verdict: 'Zero PII Retained'
    }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-cyan-neon" />
          <h1 className="text-3xl font-heading font-bold text-white">Security & Privacy Architecture</h1>
        </div>
        <p className="text-sm text-slate-400 mt-1 max-w-3xl">
          Comprehensive threat modeling, STRIDE analysis, and formal Privacy-by-Design verification for the VeilSense IoT platform.
        </p>
      </div>

      {/* 1. "Collected vs. Never Collected" Comparison Matrix */}
      <div className="glass-panel-glow rounded-2xl p-6 sm:p-8 border-cyan-neon/30 space-y-6">
        <div>
          <h3 className="font-heading font-bold text-white text-xl">The Privacy Boundary: Collected vs. Never Collected</h3>
          <p className="text-xs text-slate-400 mt-1">
            Explicit architectural guarantees contrasting VeilSense against conventional commercial smart monitoring systems.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-white/5 border-b border-white/10 text-slate-400 uppercase text-[10px]">
              <tr>
                <th className="py-3 px-4">Telemetry Dimension</th>
                <th className="py-3 px-4 text-rose-400">Conventional Smart Home / IoT</th>
                <th className="py-3 px-4 text-cyan-neon">VeilSense Zero-Intrusion Model</th>
                <th className="py-3 px-4 text-emerald-400">Security Guarantee</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {comparisonData.map((row, i) => (
                <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-3.5 px-4 text-white font-semibold font-sans">{row.category}</td>
                  <td className="py-3.5 px-4 text-rose-300 font-sans">{row.conventional}</td>
                  <td className="py-3.5 px-4 text-cyan-neon font-sans font-medium">{row.veilsense}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold">
                      {row.verdict}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. On-Device Aggregation Explainer */}
      <div className="glass-panel rounded-2xl p-6 sm:p-8 border-white/10 space-y-6" id="aggregation">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-violet-neon" />
            <h3 className="font-heading font-bold text-white text-xl">On-Device Edge Aggregation Explained</h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            How VeilSense prevents acoustic or biometric leakage at the physical micro-controller boundary.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          <div className="p-5 rounded-xl bg-white/5 border border-white/10 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-amber-400 font-bold">Step 1: 1 Hz Raw Sampling</span>
              <span className="text-slate-500">Volatile RAM</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              DHT22 and MQ-135 are sampled every 1,000 milliseconds. Readings are accumulated in temporary RAM floats (`tempAccumulator += t`).
            </p>
            <div className="p-2.5 rounded bg-black/40 font-mono text-[10px] text-slate-400">
              30 raw micro-samples collected inside private device memory.
            </div>
          </div>

          <div className="p-5 rounded-xl bg-cyan-neon/10 border border-cyan-neon/30 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-cyan-neon font-bold">Step 2: 30s Statistical Window</span>
              <span className="text-cyan-neon">Compression</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              At the 30-second boundary, the microprocessor computes arithmetic mean and pulse count. Fine-grained biometric vibrations disappear.
            </p>
            <div className="p-2.5 rounded bg-black/40 font-mono text-[10px] text-cyan-neon">
              avgTemp = sum / 30; avgPPM = sum / 30;
            </div>
          </div>

          <div className="p-5 rounded-xl bg-white/5 border border-white/10 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-emerald-400 font-bold">Step 3: Immediate Buffer Zeroing</span>
              <span className="text-emerald-400">Purge Complete</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Raw 1-second samples are cleared from memory immediately (`tempAccumulator = 0.0`). Only the single aggregate is signed and sent over TLS.
            </p>
            <div className="p-2.5 rounded bg-black/40 font-mono text-[10px] text-emerald-300">
              Zero historical raw sensor traces persist on device.
            </div>
          </div>
        </div>
      </div>

      {/* 3. Formal Threat Model: In-Scope vs. Out-of-Scope (STRIDE) */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* In-Scope */}
        <div className="md:col-span-7 glass-panel rounded-2xl p-6 border-white/10 space-y-4">
          <div className="flex items-center gap-2 border-b border-white/10 pb-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <div>
              <h3 className="font-heading font-bold text-white text-base">In-Scope Threats (Actively Mitigated)</h3>
              <p className="text-xs text-slate-400">Network, protocol, and data leakage threat vectors</p>
            </div>
          </div>

          <div className="space-y-3 pt-1">
            {threatModel.inScope.map((item, i) => (
              <div key={i} className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <strong className="text-white font-mono">{item.threat}</strong>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-mono font-bold">
                    {item.status}
                  </span>
                </div>
                <p className="text-slate-400 text-[11px]"><strong className="text-slate-300">Vector:</strong> {item.vector}</p>
                <p className="text-cyan-neon text-[11px]"><strong className="text-slate-300">Mitigation:</strong> {item.mitigation}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Out-of-Scope */}
        <div className="md:col-span-5 glass-panel rounded-2xl p-6 border-white/10 space-y-4">
          <div className="flex items-center gap-2 border-b border-white/10 pb-3">
            <XCircle className="w-5 h-5 text-slate-500" />
            <div>
              <h3 className="font-heading font-bold text-white text-base">Out-of-Scope Threats</h3>
              <p className="text-xs text-slate-400">Explicitly documented architectural boundaries</p>
            </div>
          </div>

          <div className="space-y-3 pt-1">
            {threatModel.outOfScope.map((item, i) => (
              <div key={i} className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 space-y-1 text-xs">
                <strong className="text-slate-200 font-mono block">{item.threat}</strong>
                <p className="text-slate-400 text-[11px] leading-relaxed">{item.reason}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 4. Cryptographic & Auth Verification Checklist */}
      <div className="glass-panel rounded-2xl p-6 border-white/10 space-y-4" id="checklist">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <Lock className="w-5 h-5 text-cyan-neon" />
            <h3 className="font-heading font-bold text-white text-base">Cryptographic & Compliance Checklist</h3>
          </div>
          <span className="text-xs font-mono text-emerald-400">All 5 Controls Enforced</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 pt-1 text-xs font-mono">
          <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white block font-sans">TLS 1.3 Transport</strong>
              <span className="text-slate-400 text-[11px]">Port 8883 AES-256-GCM encrypted pipe.</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white block font-sans">X.509 Certificate Auth</strong>
              <span className="text-slate-400 text-[11px]">Mutual TLS edge verification.</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white block font-sans">MQTT Topic Isolation</strong>
              <span className="text-slate-400 text-[11px]">Telemetry and actuation topic ACLs.</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white block font-sans">Stateless JWT Auth</strong>
              <span className="text-slate-400 text-[11px]">HS256 tokens for dashboard API calls.</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white block font-sans">Zero Audio/Optical Hardware</strong>
              <span className="text-slate-400 text-[11px]">Physical impossibility of surveillance.</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong className="text-white block font-sans">GDPR Article 25 Compliant</strong>
              <span className="text-slate-400 text-[11px]">Privacy by Design & Default standard.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
