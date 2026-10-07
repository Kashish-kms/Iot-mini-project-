'use client';

import React from 'react';
import {
  Info,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Target,
  Layers,
  Award,
  ShieldCheck,
  Cpu,
  FileCheck,
  Github
} from 'lucide-react';

export default function AboutPage() {
  const timelinePhases = [
    {
      phase: 'Phase 1: Requirements & Architecture',
      days: 'Days 1-2',
      status: 'Completed',
      milestones: [
        'Defined zero-optical, zero-acoustic privacy constraint.',
        'Established 4-layer monorepo structure.',
        'Selected DHT22, MQ-135, and PIR sensor trio.'
      ]
    },
    {
      phase: 'Phase 2: Firmware & Edge Aggregation',
      days: 'Days 3-4',
      status: 'Completed',
      milestones: [
        'Developed ESP32 C++ Arduino sketch with 30s averaging buffer.',
        'Configured WiFiClientSecure with embedded X.509 Root CA.',
        'Implemented PIR hardware interrupts and MQ-135 calibration equations.'
      ]
    },
    {
      phase: 'Phase 3: Cryptography & Ingestion Pipeline',
      days: 'Days 5-6',
      status: 'Completed',
      milestones: [
        'Configured Mosquitto broker with TLS 1.3 listener on port 8883.',
        'Created OpenSSL automated certificate generation scripts.',
        'Implemented FastAPI Paho-MQTT consumer and SQLite WAL persistence.'
      ]
    },
    {
      phase: 'Phase 4: ML Modeling & Preprocessing',
      days: 'Days 7-8',
      status: 'Completed',
      milestones: [
        'Engineered IQR outlier removal filter (factor = 2.5).',
        'Built feature extraction pipeline (rolling statistics, heat index, rate-of-change).',
        'Trained and evaluated Baseline (92.3%), LogReg (98.7%), and Random Forest (99.9%).'
      ]
    },
    {
      phase: 'Phase 5: Real-Time Web Platform',
      days: 'Days 9-10',
      status: 'Completed',
      milestones: [
        'Built Next.js 14 App Router dashboard with futuristic glassmorphism theme.',
        'Created WebSocket streaming hub for real-time telemetry updates.',
        'Integrated interactive "What-If" simulation studio and EDA insights.'
      ]
    },
    {
      phase: 'Phase 6: Verification, Hardening & Documentation',
      days: 'Days 11-12',
      status: 'Completed',
      milestones: [
        'Executed end-to-end browser verification and layout QA.',
        'Created comprehensive system manual, threat model, and Docker Compose.',
        'Prepared production GitHub delivery package.'
      ]
    }
  ];

  const risksMatrix = [
    {
      risk: 'MQ-135 Sensor Thermal Drift & Burn-In',
      severity: 'Medium',
      mitigation: 'Implemented digital baseline tracking (R0 calibration) and 48-hour preheat firmware state checks.'
    },
    {
      risk: 'PIR False Positives from Sunlight / HVAC Drafts',
      severity: 'Low',
      mitigation: 'Aggregated raw pulses over 30-second windows with debouncing and dual-condition validation against air quality.'
    },
    {
      risk: 'Network Dropouts & Message Loss',
      severity: 'Medium',
      mitigation: 'MQTT QoS 1 delivery guarantee combined with ESP32 local reconnection backoff logic.'
    },
    {
      risk: 'Inference Latency Degradation',
      severity: 'Low',
      mitigation: 'Random Forest model optimized with Scikit-Learn joblib serialization yielding sub-0.1ms inference latency.'
    }
  ];

  const deliverables = [
    'ESP32 Edge Firmware (`/firmware/veilsense_esp32.ino`) with TLS & 30s aggregation',
    'FastAPI Backend Service (`/backend`) with REST, WebSockets, and SQLite WAL',
    'Machine Learning Pipeline (`/ml`) comparing Baseline, LogReg, and Random Forest',
    'Next.js 14 Web Application (`/frontend`) with glassmorphism UI & live telemetry',
    'TLS 1.3 Infrastructure (`/infra`) with Mosquitto config, OpenSSL cert scripts, and Docker Compose',
    'Comprehensive System Documentation & Threat Model (`/docs` and `README.md`)'
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <Info className="w-6 h-6 text-cyan-neon" />
          <h1 className="text-3xl font-heading font-bold text-white">Project Charter & Methodology</h1>
        </div>
        <p className="text-sm text-slate-400 mt-1 max-w-3xl">
          VeilSense is an academic and production-grade engineering exploration into privacy-preserving ambient computing.
        </p>
      </div>

      {/* 1. Core Objectives */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-panel rounded-2xl p-6 border-white/10 space-y-2">
          <div className="p-2.5 rounded-xl bg-cyan-neon/10 border border-cyan-neon/30 text-cyan-neon w-fit">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="font-heading font-bold text-white text-base">Zero-Intrusion Sensing</h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            Eliminates all optical, acoustic, and facial recording apparatus, utilizing strictly non-intrusive ambient environmental and infrared motion sensors.
          </p>
        </div>

        <div className="glass-panel rounded-2xl p-6 border-white/10 space-y-2">
          <div className="p-2.5 rounded-xl bg-violet-neon/10 border border-violet-neon/30 text-violet-neon w-fit">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="font-heading font-bold text-white text-base">Edge Privacy by Design</h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            Performs mathematical aggregation directly in microcontroller RAM over 30-second intervals, immediately discarding high-frequency micro-biometrics.
          </p>
        </div>

        <div className="glass-panel rounded-2xl p-6 border-white/10 space-y-2">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 w-fit">
            <Award className="w-5 h-5" />
          </div>
          <h3 className="font-heading font-bold text-white text-base">Supervised Machine Learning</h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            Achieves 99.9% classification accuracy using an ensemble Random Forest model to predict air stagnation, heat index discomfort, and ventilation demand.
          </p>
        </div>
      </div>

      {/* 2. 12-Day / 6-Phase Timeline */}
      <div className="glass-panel-glow rounded-2xl p-6 sm:p-8 border-cyan-neon/30 space-y-6" id="timeline">
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div>
            <h3 className="font-heading font-bold text-white text-xl">12-Day / 6-Phase Engineering Roadmap</h3>
            <p className="text-xs text-slate-400">Structured development lifecycle from concept to production delivery</p>
          </div>
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            All 6 Phases Delivered
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pt-2">
          {timelinePhases.map((phase, idx) => (
            <div key={idx} className="p-5 rounded-xl bg-white/5 border border-white/10 space-y-3">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-cyan-neon font-bold">{phase.days}</span>
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                  {phase.status}
                </span>
              </div>
              <h4 className="font-heading font-bold text-white text-sm">{phase.phase}</h4>
              <ul className="space-y-1.5 text-xs text-slate-300 pt-1 border-t border-white/5">
                {phase.milestones.map((m, mIdx) => (
                  <li key={mIdx} className="flex items-start gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-cyan-neon flex-shrink-0 mt-0.5" />
                    <span>{m}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Risks & Mitigations Matrix */}
      <div className="glass-panel rounded-2xl p-6 border-white/10 space-y-4">
        <div>
          <h3 className="font-heading font-bold text-white text-base">Risks & Mitigations Matrix</h3>
          <p className="text-xs text-slate-400">Anticipated engineering vulnerabilities and implemented countermeasures</p>
        </div>

        <div className="overflow-x-auto pt-2">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-white/5 border-b border-white/10 text-slate-400 uppercase text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Identified Risk</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3 text-cyan-neon">Engineering Countermeasure</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {risksMatrix.map((item, i) => (
                <tr key={i} className="hover:bg-white/[0.02]">
                  <td className="py-3 px-3 text-white font-semibold font-sans">{item.risk}</td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px] font-bold">
                      {item.severity}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-300 font-sans">{item.mitigation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Deliverables Checklist */}
      <div className="glass-panel rounded-2xl p-6 border-white/10 space-y-4">
        <div>
          <h3 className="font-heading font-bold text-white text-base">Deliverables Verification Checklist</h3>
          <p className="text-xs text-slate-400">Complete verification of all project artifacts and software assets</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          {deliverables.map((item, i) => (
            <div key={i} className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex items-center gap-3 text-xs text-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>{item}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
