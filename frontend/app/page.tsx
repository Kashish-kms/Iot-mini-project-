'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Logo } from '@/components/Logo';
import {
  ShieldCheck,
  Lock,
  Cpu,
  Activity,
  ArrowRight,
  EyeOff,
  MicOff,
  Layers,
  Sparkles,
  Server,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Wind,
  Thermometer,
  Droplets,
  Radio,
  Github
} from 'lucide-react';

export default function LandingPage() {
  const [activeLayer, setActiveLayer] = useState(1);
  const [telemetry, setTelemetry] = useState({
    temp: 22.4,
    hum: 46.2,
    ppm: 418.0,
    motion: 1,
    risk: 'Safe',
    confidence: 96,
  });

  // Small live pulse simulation on hero mini-preview
  useEffect(() => {
    const timer = setInterval(() => {
      setTelemetry((prev) => ({
        temp: +(22.0 + Math.sin(Date.now() / 8000) * 0.8).toFixed(1),
        hum: +(46.0 + Math.cos(Date.now() / 9000) * 1.2).toFixed(1),
        ppm: +(415.0 + Math.sin(Date.now() / 6000) * 15).toFixed(1),
        motion: Math.random() > 0.3 ? 1 : 0,
        risk: 'Safe',
        confidence: 96,
      }));
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  const architectureLayers = [
    {
      id: 1,
      name: 'Layer 1: Edge Sensing Node',
      subtitle: 'ESP32 Microcontroller + Non-Intrusive Sensors',
      color: 'border-cyan-neon/40 text-cyan-neon',
      bg: 'bg-cyan-neon/10',
      badge: 'On-Device Privacy',
      details:
        'Samples DHT22 (temp/humidity), MQ-135 (VOC/CO2 air quality), and PIR (binary infrared motion) at 1 Hz. Aggregates micro-samples into 30-second statistical windows and immediately purges raw volatile memory.',
      specs: [
        'Zero cameras or microphones',
        '30-second rolling edge aggregation',
        'Hardware-level PIR interrupts',
        'Local SHA-256 payload signing',
      ],
    },
    {
      id: 2,
      name: 'Layer 2: Encrypted Transport',
      subtitle: 'TLS 1.3 / mTLS Authenticated MQTT',
      color: 'border-violet-neon/40 text-violet-neon',
      bg: 'bg-violet-neon/10',
      badge: 'X.509 Cryptography',
      details:
        'Transmits encrypted JSON aggregate packets over port 8883 to Eclipse Mosquitto. Enforces mutual TLS with X.509 certificates and strict topic ACLs isolating telemetry and actuation channels.',
      specs: [
        'TLS 1.3 AES-256-GCM cipher suite',
        'Mutual certificate authentication (mTLS)',
        'QoS 1 reliable window delivery',
        'Zero external IP exposure',
      ],
    },
    {
      id: 3,
      name: 'Layer 3: Cloud Preprocessing',
      subtitle: 'FastAPI Data Pipeline & Feature Engineering',
      color: 'border-amber-400/40 text-amber-400',
      bg: 'bg-amber-400/10',
      badge: 'Data Cleansing',
      details:
        'Applies Interquartile Range (IQR) outlier detection to filter transient electrical glitches. Engineers rolling statistics (mean, variance), rates of change (dTemp/dt, dPPM/dt), and Steadman heat index.',
      specs: [
        'IQR outlier cleaning (factor = 2.5)',
        'Diurnal cyclical trigonometric features',
        'Occupancy persistence index',
        'SQLite WAL high-throughput persistence',
      ],
    },
    {
      id: 4,
      name: 'Layer 4: Intelligence & Actuation',
      subtitle: 'Machine Learning Classification & Live Control',
      color: 'border-emerald-400/40 text-emerald-400',
      bg: 'bg-emerald-400/10',
      badge: 'ML Ensemble (99.9% Acc)',
      details:
        'Trained Random Forest Classifier infers environmental hazard risk (Safe, Moderate, High Risk) with 99.9% accuracy. Triggers automated ventilation actuation via MQTT when air quality stagnates.',
      specs: [
        'Production Random Forest + Logistic Regression',
        'Real-time WebSocket event streaming',
        'Smart ventilation relay actuation loop',
        'What-if hypothetical simulation studio',
      ],
    },
  ];

  return (
    <div className="relative overflow-hidden pb-20">
      {/* Hero Section */}
      <section className="relative pt-16 md:pt-24 pb-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Hero Left Content */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-neon/10 border border-cyan-neon/30 text-cyan-neon text-xs font-mono">
              <ShieldCheck className="w-4 h-4" />
              <span>NON-INTRUSIVE AMBIENT COMPUTING</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-heading font-extrabold text-white tracking-tight leading-[1.1]">
              Intelligence without{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-neon via-blue-400 to-violet-neon">
                intrusion.
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-300 max-w-2xl leading-relaxed">
              VeilSense monitors room climate, air quality, and occupancy using{' '}
              <strong className="text-white font-medium">zero cameras and zero audio</strong>. Powered by
              on-device 30-second edge aggregation, TLS-encrypted MQTT, and machine learning risk
              classification.
            </p>

            {/* Privacy Badges Strip */}
            <div className="flex flex-wrap gap-2.5 pt-1">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-300">
                <EyeOff className="w-3.5 h-3.5 text-rose-400" />
                No Cameras
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-300">
                <MicOff className="w-3.5 h-3.5 text-rose-400" />
                No Microphones
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-300">
                <Lock className="w-3.5 h-3.5 text-emerald-400" />
                mTLS 1.3 Ingestion
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-300">
                <Cpu className="w-3.5 h-3.5 text-cyan-neon" />
                Edge Aggregated
              </span>
            </div>

            {/* CTAs */}
            <div className="flex flex-wrap gap-4 pt-4">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-neon to-blue-600 text-[#070B14] font-semibold text-sm shadow-[0_0_25px_rgba(34,211,238,0.4)] hover:shadow-[0_0_35px_rgba(34,211,238,0.6)] hover:scale-[1.02] transition-all"
              >
                <Activity className="w-4 h-4" />
                <span>Launch Live Dashboard</span>
                <ArrowRight className="w-4 h-4" />
              </Link>

              <Link
                href="/models"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-surface-card border border-white/15 text-white font-medium text-sm hover:bg-white/10 hover:border-cyan-neon/40 transition-all"
              >
                <Cpu className="w-4 h-4 text-violet-neon" />
                <span>Explore ML Lab</span>
              </Link>

              <Link
                href="/privacy"
                className="inline-flex items-center gap-2 px-5 py-3.5 rounded-xl bg-transparent border border-white/10 text-slate-300 text-sm hover:text-white hover:border-white/20 transition-all"
              >
                <ShieldCheck className="w-4 h-4 text-cyan-neon" />
                <span>Threat Model</span>
              </Link>
            </div>
          </div>

          {/* Hero Right: Live Interactive Mini-Preview Telemetry Card */}
          <div className="lg:col-span-5">
            <div className="glass-panel-glow rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-neon/10 rounded-full blur-2xl pointer-events-none" />

              {/* Card Header */}
              <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-5">
                <div className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                  <span className="text-xs font-mono text-emerald-400 font-semibold tracking-wide">
                    ESP32-NODE-01 • ONLINE
                  </span>
                </div>
                <span className="text-[11px] font-mono text-slate-400 px-2 py-0.5 rounded bg-white/5 border border-white/10">
                  TLS 1.3 AES-256
                </span>
              </div>

              {/* 4 Sensor Gauges */}
              <div className="grid grid-cols-2 gap-3 mb-5">
                {/* Temp */}
                <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 text-xs">
                    <span>Temperature</span>
                    <Thermometer className="w-3.5 h-3.5 text-amber-400" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-2xl font-mono font-bold text-white">{telemetry.temp}</span>
                    <span className="text-xs text-slate-400">°C</span>
                  </div>
                  <span className="text-[10px] text-emerald-400 mt-1">Comfortable (ASHRAE 55)</span>
                </div>

                {/* Humidity */}
                <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 text-xs">
                    <span>Humidity</span>
                    <Droplets className="w-3.5 h-3.5 text-cyan-neon" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-2xl font-mono font-bold text-white">{telemetry.hum}</span>
                    <span className="text-xs text-slate-400">% RH</span>
                  </div>
                  <span className="text-[10px] text-cyan-neon mt-1">Optimal Moisture</span>
                </div>

                {/* Air Quality MQ-135 */}
                <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 text-xs">
                    <span>Air Quality</span>
                    <Wind className="w-3.5 h-3.5 text-violet-neon" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-2xl font-mono font-bold text-white">{telemetry.ppm}</span>
                    <span className="text-xs text-slate-400">PPM</span>
                  </div>
                  <span className="text-[10px] text-emerald-400 mt-1">Clean Ambient Level</span>
                </div>

                {/* Motion / Occupancy */}
                <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 flex flex-col justify-between">
                  <div className="flex items-center justify-between text-slate-400 text-xs">
                    <span>Occupancy (PIR)</span>
                    <Activity className="w-3.5 h-3.5 text-emerald-400" />
                  </div>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-2xl font-mono font-bold text-white">
                      {telemetry.motion ? 'Active' : 'Idle'}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400 mt-1">Zero Optical Imaging</span>
                </div>
              </div>

              {/* Risk Assessment Meter */}
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-mono text-emerald-400 uppercase tracking-wider block">
                    ML Risk Classification
                  </span>
                  <span className="text-lg font-heading font-bold text-white">
                    Status: <span className="text-emerald-400">Safe Environmental State</span>
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-xs font-mono text-emerald-300 font-bold">
                    {telemetry.confidence}% Conf.
                  </span>
                  <span className="text-[10px] text-slate-400 block font-mono">Random Forest</span>
                </div>
              </div>

              {/* Bottom Quick Action */}
              <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
                <span className="font-mono text-[11px]">Aggregated 30s Window #8640</span>
                <Link
                  href="/dashboard"
                  className="text-cyan-neon hover:underline flex items-center gap-1 font-mono text-[11px]"
                >
                  View Full Metrics <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem vs Solution Comparison Section */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-3xl font-heading font-bold text-white">The Surveillance Dilemma in Modern IoT</h2>
          <p className="mt-3 text-slate-400 text-sm leading-relaxed">
            Standard smart home and workplace devices routinely harvest visual, acoustic, and biometric
            information to infer room occupancy, creating massive privacy vulnerabilities.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Left: Legacy Surveillance */}
          <div className="glass-panel rounded-2xl p-6 sm:p-8 border-rose-500/20 relative">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-heading font-bold text-white">Conventional Intrusive IoT</h3>
                <p className="text-xs text-rose-300 font-mono">High Risk • Privacy Invasive</p>
              </div>
            </div>

            <ul className="space-y-4 text-xs sm:text-sm text-slate-300">
              <li className="flex items-start gap-3">
                <span className="text-rose-400 font-bold">✕</span>
                <span>
                  <strong className="text-white">Continuous Video & Audio Feeds:</strong> Constant optical
                  monitoring and voice recording creates significant employee and homeowner distrust.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-rose-400 font-bold">✕</span>
                <span>
                  <strong className="text-white">Biometric Identity Profiling:</strong> Facial recognition, gait
                  tracking, and voice fingerprinting link ambient state directly to individuals.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-rose-400 font-bold">✕</span>
                <span>
                  <strong className="text-white">Raw High-Frequency Streaming:</strong> Unfiltered 60 FPS
                  streams uploaded to third-party clouds are subject to interception and subpoena.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-rose-400 font-bold">✕</span>
                <span>
                  <strong className="text-white">Broad Threat Surface:</strong> Camera lens hacking, microphone
                  wiretapping, and unauthorized cloud credential exfiltration.
                </span>
              </li>
            </ul>
          </div>

          {/* Right: VeilSense Zero-Intrusion Model */}
          <div className="glass-panel-glow rounded-2xl p-6 sm:p-8 border-cyan-neon/30 relative">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2.5 rounded-xl bg-cyan-neon/10 border border-cyan-neon/30 text-cyan-neon">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-heading font-bold text-white">VeilSense Zero-Intrusion Model</h3>
                <p className="text-xs text-cyan-neon font-mono">Privacy-First Ambient Intelligence</p>
              </div>
            </div>

            <ul className="space-y-4 text-xs sm:text-sm text-slate-300">
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                <span>
                  <strong className="text-white">Zero Optical or Acoustic Sensors:</strong> Hardware only
                  features temperature, humidity, gas PPM, and passive infrared motion triggers.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                <span>
                  <strong className="text-white">Strict On-Device 30s Aggregation:</strong> Micro-samples are
                  averaged inside ESP32 RAM; raw 1-second buffers are immediately destroyed.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                <span>
                  <strong className="text-white">Cryptographic TLS 1.3 / mTLS:</strong> Authenticated
                  broker-to-node transport with mutual certificate validation and strict topic isolation.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                <span>
                  <strong className="text-white">Machine Learning Classification:</strong> Supervised Random
                  Forest classifies ambient hazard and ventilation risk without identifying any person.
                </span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Animated 4-Layer Architecture Diagram Section */}
      <section className="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-neon/10 border border-violet-neon/30 text-violet-neon text-xs font-mono mb-2">
            <Layers className="w-3.5 h-3.5" />
            <span>INTERACTIVE ARCHITECTURE PIPELINE</span>
          </div>
          <h2 className="text-3xl font-heading font-bold text-white">
            End-to-End Privacy-Preserving Architecture
          </h2>
          <p className="mt-2 text-slate-400 text-sm">
            Click any layer to inspect its cryptographic guarantees, hardware details, and data transforms.
          </p>
        </div>

        {/* 4 Layer Blocks Horizontal Flow */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {architectureLayers.map((layer) => {
            const isSelected = activeLayer === layer.id;
            return (
              <button
                key={layer.id}
                onClick={() => setActiveLayer(layer.id)}
                className={`p-5 rounded-2xl text-left transition-all border relative ${
                  isSelected
                    ? `${layer.bg} ${layer.color} shadow-[0_0_25px_rgba(34,211,238,0.2)] scale-[1.02]`
                    : 'glass-panel border-white/10 hover:border-white/20 text-slate-400'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-white/5 border border-white/10">
                    Step {layer.id}
                  </span>
                  <span className="text-[10px] font-mono text-cyan-neon">{layer.badge}</span>
                </div>
                <h4 className="font-heading font-bold text-base text-white">{layer.name}</h4>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">{layer.subtitle}</p>

                {/* Packet flow indicator */}
                <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-[11px] font-mono">
                  <span>Inspect Details</span>
                  <ArrowRight className="w-3 h-3 text-cyan-neon" />
                </div>
              </button>
            );
          })}
        </div>

        {/* Layer Deep Dive Inspector Panel */}
        {(() => {
          const selected = architectureLayers.find((l) => l.id === activeLayer) || architectureLayers[0];
          return (
            <div className="glass-panel-glow rounded-2xl p-6 sm:p-8 border-cyan-neon/30">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-4 mb-6">
                <div>
                  <span className="text-xs font-mono text-cyan-neon uppercase tracking-wider">
                    Detailed Specification
                  </span>
                  <h3 className="text-2xl font-heading font-bold text-white mt-1">{selected.name}</h3>
                  <p className="text-sm text-slate-400">{selected.subtitle}</p>
                </div>
                <span className="self-start md:self-auto px-3 py-1 rounded-full bg-cyan-neon/10 border border-cyan-neon/30 text-xs font-mono text-cyan-neon">
                  {selected.badge}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                <div>
                  <h4 className="text-sm font-semibold text-white mb-2 font-mono uppercase tracking-wider">
                    Core Functionality
                  </h4>
                  <p className="text-sm text-slate-300 leading-relaxed mb-6">{selected.details}</p>

                  <h4 className="text-sm font-semibold text-white mb-2 font-mono uppercase tracking-wider">
                    Security & Design Properties
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {selected.specs.map((spec, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-2 p-2.5 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-300"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 text-cyan-neon flex-shrink-0" />
                        <span>{spec}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Code / Packet Sample Preview */}
                <div className="p-5 rounded-xl bg-[#030712] border border-white/10 font-mono text-xs text-slate-300 space-y-2">
                  <div className="flex items-center justify-between pb-2 border-b border-white/10 text-slate-500">
                    <span>Transmitted Payload Schema (30s Window)</span>
                    <span className="text-[10px] text-emerald-400">ANONYMIZED</span>
                  </div>
                  <pre className="text-cyan-neon overflow-x-auto">
{`{
  "device_id": "ESP32-NODE-01",
  "window_seconds": 30,
  "temperature": 22.45,       // °C (DHT22 avg)
  "humidity": 46.80,          // % RH (DHT22 avg)
  "air_quality_ppm": 428.5,   // MQ-135 calibrated
  "motion_detected": 1,       // PIR binary state
  "motion_count": 4,          // Pulse frequency
  "timestamp": "2026-10-07 21:45:00",
  "tls_verified": true        // X.509 authenticated
}`}
                  </pre>
                  <p className="text-[11px] text-slate-500 pt-2 border-t border-white/5">
                    Note: Zero facial vectors, zero ambient audio recordings, zero MAC address tracking.
                  </p>
                </div>
              </div>
            </div>
          );
        })()}
      </section>

      {/* Tech Stack Strip */}
      <section className="py-12 border-y border-white/10 bg-white/[0.01]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs font-mono text-slate-400 uppercase tracking-widest mb-6">
            Engineered with Production-Grade Open Technologies
          </p>
          <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-10 text-slate-300 text-sm font-mono">
            <span className="flex items-center gap-2 hover:text-cyan-neon transition-colors">
              <Zap className="w-4 h-4 text-cyan-neon" /> Next.js 14 App Router
            </span>
            <span className="flex items-center gap-2 hover:text-cyan-neon transition-colors">
              <Server className="w-4 h-4 text-emerald-400" /> Python FastAPI
            </span>
            <span className="flex items-center gap-2 hover:text-cyan-neon transition-colors">
              <Cpu className="w-4 h-4 text-violet-neon" /> Scikit-Learn (Random Forest)
            </span>
            <span className="flex items-center gap-2 hover:text-cyan-neon transition-colors">
              <HardDriveIcon className="w-4 h-4 text-amber-400" /> ESP32 FreeRTOS
            </span>
            <span className="flex items-center gap-2 hover:text-cyan-neon transition-colors">
              <Lock className="w-4 h-4 text-cyan-neon" /> Mosquitto TLS 1.3
            </span>
            <span className="flex items-center gap-2 hover:text-cyan-neon transition-colors">
              <Activity className="w-4 h-4 text-blue-400" /> SQLite WAL Mode
            </span>
          </div>
        </div>
      </section>

      {/* Bottom CTA Banner */}
      <section className="pt-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="glass-panel-glow rounded-3xl p-10 sm:p-14 border-cyan-neon/30 relative overflow-hidden">
          <div className="max-w-2xl mx-auto space-y-5">
            <h2 className="text-3xl sm:text-4xl font-heading font-bold text-white">
              Ready to Experience Zero-Intrusion Room Intelligence?
            </h2>
            <p className="text-slate-300 text-sm leading-relaxed">
              Explore the live dashboard, run what-if predictions in the ML Lab, review our threat model, or
              inspect the ESP32 firmware schematics.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4 pt-3">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-cyan-neon text-[#070B14] font-semibold text-sm hover:shadow-[0_0_25px_rgba(34,211,238,0.5)] transition-all"
              >
                <span>Launch Dashboard</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <a
                href="https://github.com/Kashish-kms/Iot-mini-project-"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-white/10 border border-white/15 text-white font-medium text-sm hover:bg-white/15 transition-all"
              >
                <Github className="w-4 h-4" />
                <span>View on GitHub</span>
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function HardDriveIcon(props: any) {
  return <Cpu {...props} />;
}
