'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Logo } from './Logo';
import {
  Activity,
  Database,
  BarChart2,
  Cpu,
  ShieldCheck,
  HardDrive,
  Info,
  ExternalLink,
  Sun,
  Moon,
  Radio,
  Lock,
  Menu,
  X,
  UserCheck
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isLightMode, setIsLightMode] = useState(false);
  const [isDemoMode, setIsDemoMode] = useState(true);

  useEffect(() => {
    // Check saved theme
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('veilsense_theme');
      if (savedTheme === 'light') {
        setIsLightMode(true);
        document.documentElement.classList.add('light');
      }
      const savedDemo = localStorage.getItem('veilsense_demo_mode');
      if (savedDemo !== null) {
        setIsDemoMode(savedDemo === 'true');
      }
    }
  }, []);

  const toggleTheme = () => {
    const next = !isLightMode;
    setIsLightMode(next);
    if (typeof window !== 'undefined') {
      if (next) {
        document.documentElement.classList.add('light');
        localStorage.setItem('veilsense_theme', 'light');
      } else {
        document.documentElement.classList.remove('light');
        localStorage.setItem('veilsense_theme', 'dark');
      }
    }
  };

  const toggleDemoMode = () => {
    const next = !isDemoMode;
    setIsDemoMode(next);
    if (typeof window !== 'undefined') {
      localStorage.setItem('veilsense_demo_mode', next.toString());
      window.dispatchEvent(new CustomEvent('veilsense_demo_changed', { detail: next }));
    }
  };

  const navLinks = [
    { name: 'Dashboard', href: '/dashboard', icon: Activity },
    { name: 'Data', href: '/data', icon: Database },
    { name: 'Insights (EDA)', href: '/insights', icon: BarChart2 },
    { name: 'ML Lab', href: '/models', icon: Cpu },
    { name: 'Privacy Center', href: '/privacy', icon: ShieldCheck },
    { name: 'Hardware', href: '/device', icon: HardDrive },
    { name: 'About', href: '/about', icon: Info },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-[#070B14]/85 backdrop-blur-xl transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2 group">
          <Logo size={32} />
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center gap-1">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-neon/15 text-cyan-neon border border-cyan-neon/30 shadow-[0_0_12px_rgba(34,211,238,0.2)]'
                    : 'text-slate-300 hover:text-white hover:bg-white/5 border border-transparent'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-neon' : 'text-slate-400'}`} />
                <span>{link.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right Action Bar */}
        <div className="hidden sm:flex items-center gap-2.5">
          {/* Live Indicator */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-[11px] font-mono text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <Radio className="w-3 h-3" />
            <span>LIVE</span>
          </div>

          {/* Demo Mode Toggle */}
          <button
            onClick={toggleDemoMode}
            title="Toggle between Live Hardware and Demo Simulation Mode"
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono transition-all border ${
              isDemoMode
                ? 'bg-violet-neon/15 border-violet-neon/40 text-violet-300'
                : 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300'
            }`}
          >
            <Lock className="w-3 h-3" />
            <span>{isDemoMode ? 'Demo Mode' : 'Hardware Stream'}</span>
          </button>

          {/* Theme Switcher */}
          <button
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
          >
            {isLightMode ? <Moon className="w-4 h-4 text-amber-300" /> : <Sun className="w-4 h-4 text-cyan-neon" />}
          </button>

          {/* Seeded Demo Login Badge */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-300">
            <UserCheck className="w-3.5 h-3.5 text-cyan-neon" />
            <span className="hidden xl:inline text-[11px] font-mono">demo@veilsense.io</span>
          </div>

          {/* GitHub Repo Link */}
          <a
            href="https://github.com/Kashish-kms/Iot-mini-project-"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub Repository"
            className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-300 hover:text-white hover:bg-white/10 transition-colors flex items-center gap-1"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>

        {/* Mobile menu trigger */}
        <div className="flex items-center gap-2 lg:hidden">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-300"
            aria-label="Toggle navigation"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-b border-white/10 bg-[#070B14]/95 px-4 pt-2 pb-6 space-y-2 backdrop-blur-2xl">
          <div className="grid grid-cols-2 gap-2 pt-2">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium ${
                    isActive
                      ? 'bg-cyan-neon/15 text-cyan-neon border border-cyan-neon/30'
                      : 'text-slate-300 bg-white/5'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{link.name}</span>
                </Link>
              );
            })}
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-white/10 text-xs">
            <button
              onClick={toggleDemoMode}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-neon/15 border border-violet-neon/30 text-violet-300"
            >
              <span>{isDemoMode ? 'Demo Mode: ON' : 'Demo Mode: OFF'}</span>
            </button>
            <button
              onClick={toggleTheme}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-slate-200"
            >
              {isLightMode ? 'Dark Theme' : 'Light Theme'}
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
