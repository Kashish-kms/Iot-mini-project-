import React from 'react';
import Link from 'next/link';
import { Logo } from './Logo';
import { ShieldCheck, Lock, Github, Heart, Cpu } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-white/10 bg-[#070B14] text-slate-400 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Col 1: Brand */}
          <div className="space-y-4 md:col-span-1">
            <Logo size={28} />
            <p className="text-slate-400 text-xs leading-relaxed">
              Privacy-aware intelligent smart IoT monitoring platform. Edge-aggregated room intelligence with zero optical or acoustic intrusion.
            </p>
            <div className="flex items-center gap-2 text-cyan-neon font-mono text-[11px]">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Zero-Intrusion Certified</span>
            </div>
          </div>

          {/* Col 2: Navigation */}
          <div>
            <h4 className="text-white font-medium mb-3 text-xs uppercase tracking-wider font-mono">Platform</h4>
            <ul className="space-y-2">
              <li><Link href="/dashboard" className="hover:text-cyan-neon transition-colors">Live Dashboard</Link></li>
              <li><Link href="/data" className="hover:text-cyan-neon transition-colors">Telemetry Explorer</Link></li>
              <li><Link href="/insights" className="hover:text-cyan-neon transition-colors">EDA & Diurnal Patterns</Link></li>
              <li><Link href="/models" className="hover:text-cyan-neon transition-colors">Machine Learning Lab</Link></li>
              <li><Link href="/device" className="hover:text-cyan-neon transition-colors">ESP32 Diagnostics</Link></li>
            </ul>
          </div>

          {/* Col 3: Privacy & Security */}
          <div>
            <h4 className="text-white font-medium mb-3 text-xs uppercase tracking-wider font-mono">Privacy By Design</h4>
            <ul className="space-y-2">
              <li><Link href="/privacy" className="hover:text-cyan-neon transition-colors">Threat Model & STRIDE</Link></li>
              <li><Link href="/privacy#checklist" className="hover:text-cyan-neon transition-colors">TLS 1.3 / mTLS Verification</Link></li>
              <li><Link href="/privacy#aggregation" className="hover:text-cyan-neon transition-colors">On-Device Aggregation</Link></li>
              <li><Link href="/about#timeline" className="hover:text-cyan-neon transition-colors">12-Day Development Timeline</Link></li>
            </ul>
          </div>

          {/* Col 4: Repository & Source */}
          <div className="space-y-3">
            <h4 className="text-white font-medium mb-3 text-xs uppercase tracking-wider font-mono">Open Source</h4>
            <p className="text-xs text-slate-400">
              Complete source code, firmware sketch, machine learning models, and infrastructure recipes:
            </p>
            <a
              href="https://github.com/Kashish-kms/Iot-mini-project-"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white hover:border-cyan-neon/40 hover:text-cyan-neon transition-all"
            >
              <Github className="w-4 h-4" />
              <span className="font-mono text-[11px]">Kashish-kms/Iot-mini-project-</span>
            </a>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-[11px] text-slate-500 font-mono">
            © 2026 VeilSense IoT Platform. Designed for privacy-first ambient computing.
          </p>
          <div className="flex items-center gap-4 text-[11px] text-slate-500 font-mono">
            <span className="flex items-center gap-1">
              <Lock className="w-3 h-3 text-emerald-400" />
              AES-256 TLS Ingestion
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Cpu className="w-3 h-3 text-cyan-neon" />
              ESP32 Edge Microcontroller
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
