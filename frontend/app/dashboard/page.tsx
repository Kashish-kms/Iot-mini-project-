'use client';

import React, { useState, useEffect } from 'react';
import {
  fetchLatestReading,
  fetchReadings,
  fetchAlerts,
  fetchDeviceStatus,
  actuateFan,
  requestRiskPrediction,
  WS_BASE,
  MOCK_LATEST_READING
} from '@/lib/api';
import { TelemetryReading, RiskPrediction, DeviceStatus, AlertItem } from '@/lib/types';
import { Sparkline } from '@/components/Sparkline';
import { RiskGauge } from '@/components/RiskGauge';
import { TelemetryChart } from '@/components/TelemetryChart';
import {
  Activity,
  Thermometer,
  Droplets,
  Wind,
  ShieldCheck,
  Lock,
  Radio,
  Fan,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Clock,
  Zap,
  Sliders
} from 'lucide-react';

export default function DashboardPage() {
  const [latest, setLatest] = useState<TelemetryReading>(MOCK_LATEST_READING);
  const [series, setSeries] = useState<TelemetryReading[]>([]);
  const [timeRange, setTimeRange] = useState('24h');
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [device, setDevice] = useState<DeviceStatus | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [fanState, setFanState] = useState(0); // 0: off, 1: on
  const [autoMode, setAutoMode] = useState(true);
  const [isDemo, setIsDemo] = useState(true);
  const [prediction, setPrediction] = useState<RiskPrediction | null>(null);
  const [loading, setLoading] = useState(true);

  // Load initial data
  const loadData = async () => {
    try {
      const [latestRes, seriesRes, alertsRes, deviceRes] = await Promise.all([
        fetchLatestReading(),
        fetchReadings(timeRange, 50),
        fetchAlerts(),
        fetchDeviceStatus()
      ]);
      setLatest(latestRes);
      setSeries(seriesRes.items);
      setAlerts(alertsRes);
      setDevice(deviceRes);
      setFanState(latestRes.fan_active);

      // Fetch ML inference for current reading
      const predRes = await requestRiskPrediction({
        temperature: latestRes.temperature,
        humidity: latestRes.humidity,
        air_quality_ppm: latestRes.air_quality_ppm,
        motion_detected: latestRes.motion_detected
      });
      setPrediction(predRes);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    // Setup live WebSocket connection with reconnection logic
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(WS_BASE);
      ws.onopen = () => {
        setWsConnected(true);
      };
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'TELEMETRY_UPDATE' && msg.data) {
            setLatest((prev) => ({ ...prev, ...msg.data }));
            setFanState(msg.data.fan_active);
            setSeries((prev) => [msg.data, ...prev.slice(0, 49)]);
            if (msg.data.probabilities) {
              setPrediction({
                risk_level: msg.data.risk_level,
                risk_label: msg.data.risk_label,
                confidence: msg.data.risk_confidence,
                probabilities: msg.data.probabilities,
                top_contributing_factors: msg.data.top_contributing_factors || [],
                recommendations: msg.data.recommendations || []
              });
            }
          }
        } catch (e) {
          // ignore pong
        }
      };
      ws.onerror = () => setWsConnected(false);
      ws.onclose = () => setWsConnected(false);
    } catch {
      setWsConnected(false);
    }

    // Client-side demo fallback animation if WebSocket is quiet
    const fallbackTimer = setInterval(() => {
      setLatest((prev) => {
        const drift = (Math.random() - 0.48) * 0.15;
        const newTemp = +(prev.temperature + drift).toFixed(2);
        const newHum = +(prev.humidity + (Math.random() - 0.5) * 0.2).toFixed(2);
        const motion = Math.random() < 0.35 ? 1 : 0;
        const newPpm = +(prev.air_quality_ppm + (motion ? 2.5 : -1.2)).toFixed(1);
        const clampedPpm = Math.max(380, Math.min(1100, newPpm));
        return {
          ...prev,
          temperature: newTemp,
          humidity: newHum,
          air_quality_ppm: clampedPpm,
          motion_detected: motion,
          timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19)
        };
      });
    }, 4000);

    return () => {
      if (ws) ws.close();
      clearInterval(fallbackTimer);
    };
  }, [timeRange]);

  const handleActuation = async (action: 'FAN_ON' | 'FAN_OFF' | 'AUTO') => {
    if (action === 'AUTO') {
      setAutoMode(true);
      await actuateFan('AUTO');
    } else {
      setAutoMode(false);
      setFanState(action === 'FAN_ON' ? 1 : 0);
      await actuateFan(action);
    }
  };

  const handleResolveAlert = (id: number) => {
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, resolved: 1 } : a)));
  };

  // Sparkline history buffers
  const tempHistory = series.map((s) => s.temperature).reverse();
  const humHistory = series.map((s) => s.humidity).reverse();
  const ppmHistory = series.map((s) => s.air_quality_ppm).reverse();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* 1. System Status & Security Bar */}
      <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4 border-white/10">
        <div className="flex flex-wrap items-center gap-3">
          {/* Connection state */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs font-mono">
            <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-400 animate-ping' : 'bg-amber-400'}`} />
            <Radio className="w-3.5 h-3.5 text-cyan-neon" />
            <span className="text-white font-semibold">
              {wsConnected ? 'WS Stream: Active' : 'Autonomous Fallback'}
            </span>
          </div>

          {/* TLS Lock Badge */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-neon/10 border border-cyan-neon/30 text-xs font-mono text-cyan-neon">
            <Lock className="w-3.5 h-3.5" />
            <span>TLS 1.3 AES-256 GCM</span>
          </div>

          {/* ESP32 Status */}
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs font-mono text-slate-300">
            <span className="text-slate-400">Node:</span>
            <span className="text-white font-semibold">{latest.device_id || 'ESP32-NODE-01'}</span>
            <span className="text-emerald-400 ml-1">● Online</span>
          </div>
        </div>

        {/* Right Info & Refresh */}
        <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5" />
            <span>Last Sync: {latest.timestamp.substring(11, 19)}</span>
          </div>
          <button
            onClick={loadData}
            title="Refresh telemetry"
            className="p-1.5 rounded-lg bg-white/5 border border-white/10 hover:text-white transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* 2. Smart Ventilation Actuation Controller Banner */}
      <div className="glass-panel-glow rounded-2xl p-4 sm:p-5 flex flex-wrap items-center justify-between gap-4 border-cyan-neon/30">
        <div className="flex items-center gap-3">
          <div
            className={`p-3 rounded-xl border transition-all ${
              fanState === 1
                ? 'bg-cyan-neon/20 border-cyan-neon text-cyan-neon animate-spin'
                : 'bg-white/5 border-white/10 text-slate-400'
            }`}
          >
            <Fan className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-heading font-bold text-white text-base">Smart Ventilation Actuator</h3>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold uppercase ${
                  fanState === 1
                    ? 'bg-cyan-neon/20 text-cyan-neon border border-cyan-neon/40'
                    : 'bg-slate-700/50 text-slate-300 border border-slate-600'
                }`}
              >
                {fanState === 1 ? 'High-Flow Active' : 'Standby / Eco'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Control mode: <strong className="text-white">{autoMode ? 'AI Autonomous Regulation' : 'Manual Override'}</strong> • Topic: <span className="font-mono text-cyan-neon">veilsense/actuation/fan</span>
            </p>
          </div>
        </div>

        {/* Actuation Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleActuation('AUTO')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all border ${
              autoMode
                ? 'bg-cyan-neon/20 border-cyan-neon text-cyan-neon font-bold'
                : 'bg-white/5 border-white/10 text-slate-400 hover:text-white'
            }`}
          >
            AI Auto
          </button>
          <button
            onClick={() => handleActuation('FAN_ON')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all border ${
              !autoMode && fanState === 1
                ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300 font-bold'
                : 'bg-white/5 border-white/10 text-slate-400 hover:text-white'
            }`}
          >
            Force Fan ON
          </button>
          <button
            onClick={() => handleActuation('FAN_OFF')}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all border ${
              !autoMode && fanState === 0
                ? 'bg-rose-500/20 border-rose-500 text-rose-300 font-bold'
                : 'bg-white/5 border-white/10 text-slate-400 hover:text-white'
            }`}
          >
            Force Fan OFF
          </button>
        </div>
      </div>

      {/* 3. 4 Main KPI Cards with Micro Sparklines */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Temperature */}
        <div className="glass-panel rounded-2xl p-5 border-white/10 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span className="font-mono uppercase">Temperature</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <Thermometer className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-3xl font-heading font-extrabold text-white">
                {latest.temperature}
              </span>
              <span className="text-sm font-mono text-slate-400 ml-1">°C</span>
            </div>
            <Sparkline data={tempHistory.length > 1 ? tempHistory : [22.1, 22.3, 22.5, 22.4]} color="#F59E0B" />
          </div>
          <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono">
            <span className="text-emerald-400 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> Optimal (21-25°C)
            </span>
            <span className="text-slate-400">DHT22 Digital</span>
          </div>
        </div>

        {/* KPI 2: Humidity */}
        <div className="glass-panel rounded-2xl p-5 border-white/10 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span className="font-mono uppercase">Relative Humidity</span>
            <div className="p-2 rounded-lg bg-cyan-neon/10 text-cyan-neon">
              <Droplets className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-3xl font-heading font-extrabold text-white">
                {latest.humidity}
              </span>
              <span className="text-sm font-mono text-slate-400 ml-1">% RH</span>
            </div>
            <Sparkline data={humHistory.length > 1 ? humHistory : [46, 47, 46.5, 46.8]} color="#22D3EE" />
          </div>
          <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono">
            <span className="text-cyan-neon flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> No Mold Risk
            </span>
            <span className="text-slate-400">Capacitive Sensor</span>
          </div>
        </div>

        {/* KPI 3: Air Quality PPM (MQ-135) */}
        <div className="glass-panel rounded-2xl p-5 border-white/10 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span className="font-mono uppercase">Air Quality Index</span>
            <div className="p-2 rounded-lg bg-violet-neon/10 text-violet-neon">
              <Wind className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-3xl font-heading font-extrabold text-white">
                {latest.air_quality_ppm}
              </span>
              <span className="text-sm font-mono text-slate-400 ml-1">PPM</span>
            </div>
            <Sparkline data={ppmHistory.length > 1 ? ppmHistory : [410, 415, 422, 428]} color="#8B5CF6" />
          </div>
          <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono">
            <span className={latest.air_quality_ppm > 700 ? 'text-rose-400' : 'text-emerald-400'}>
              {latest.air_quality_ppm > 700 ? 'Elevated Stagnation' : 'Clean Ambient Air'}
            </span>
            <span className="text-slate-400">MQ-135 MOX</span>
          </div>
        </div>

        {/* KPI 4: Occupancy / Motion */}
        <div className="glass-panel rounded-2xl p-5 border-white/10 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span className="font-mono uppercase">Room Occupancy</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-3xl font-heading font-extrabold text-white">
                {latest.motion_detected ? 'Occupied' : 'Idle'}
              </span>
              <span className="text-xs font-mono text-slate-400 ml-2">
                ({latest.motion_count || 0} pulses/30s)
              </span>
            </div>
            <div className="w-8 h-8 rounded-full flex items-center justify-center bg-white/5 border border-white/10">
              <span className={`w-3 h-3 rounded-full ${latest.motion_detected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono">
            <span className="text-slate-300">PIR Infrared Array</span>
            <span className="text-cyan-neon">Zero Optical Data</span>
          </div>
        </div>
      </div>

      {/* 4. Telemetry Multi-Range Time Series Chart & Risk Classification Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Real-Time Telemetry Chart */}
        <div className="lg:col-span-8 glass-panel rounded-2xl p-6 border-white/10 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-heading font-bold text-white text-lg">Continuous Telemetry Streams</h3>
              <p className="text-xs text-slate-400">Aggregated 30-second edge telemetry windows</p>
            </div>
            <span className="text-xs font-mono text-cyan-neon px-2.5 py-1 rounded-lg bg-cyan-neon/10 border border-cyan-neon/20">
              Active Range: {timeRange}
            </span>
          </div>

          <TelemetryChart
            data={series}
            timeRange={timeRange}
            onRangeChange={(range) => setTimeRange(range)}
          />
        </div>

        {/* Right: ML Risk Classification Panel */}
        <div className="lg:col-span-4 glass-panel rounded-2xl p-6 border-white/10 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-cyan-neon" />
                <h3 className="font-heading font-bold text-white text-base">ML Risk Inference</h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-violet-neon/10 text-violet-neon border border-violet-neon/30">
                Random Forest
              </span>
            </div>

            {/* Gauge */}
            <div className="flex justify-center my-2">
              <RiskGauge
                riskLevel={prediction?.risk_level ?? latest.risk_level}
                confidence={prediction?.confidence ?? latest.risk_confidence}
                size={170}
              />
            </div>

            {/* Contributing factors */}
            <div className="space-y-2 mt-4">
              <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                Top Contributing Risk Drivers
              </span>
              {(prediction?.top_contributing_factors || [
                { factor: 'MQ-135 Gas PPM Ratio', contribution: '48%', impact: 'High' },
                { factor: 'Room Occupancy Persistence', contribution: '28%', impact: 'Medium' },
                { factor: 'Thermal Comfort Envelope', contribution: '24%', impact: 'Low' },
              ]).map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 rounded-lg bg-white/5 border border-white/5 text-xs font-mono"
                >
                  <span className="text-slate-300">{item.factor}</span>
                  <span className="text-cyan-neon font-bold">{item.contribution}</span>
                </div>
              ))}
            </div>
          </div>

          {/* AI Advice */}
          <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-300 space-y-1">
            <span className="font-mono text-[10px] text-cyan-neon uppercase tracking-wider block">
              Automated Recommendation
            </span>
            <p className="text-xs leading-relaxed text-slate-300">
              {prediction?.recommendations?.[0] || 'Room environmental quality is optimal. Maintain low-power eco ventilation.'}
            </p>
          </div>
        </div>
      </div>

      {/* 5. 24-Hour Hourly Occupancy & Air Quality Heatmap */}
      <div className="glass-panel rounded-2xl p-6 border-white/10 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-heading font-bold text-white text-base">24-Hour Diurnal Activity & Air Stagnation Heatmap</h3>
            <p className="text-xs text-slate-400">
              Aggregated hourly occupancy index (color intensity) and peak PPM gas levels
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-emerald-500/20" /> Low</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-amber-500/40" /> Moderate</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-rose-500/60" /> Peak</span>
          </div>
        </div>

        {/* 24-Hour Grid */}
        <div className="grid grid-cols-6 sm:grid-cols-12 lg:grid-cols-24 gap-1.5 pt-2">
          {Array.from({ length: 24 }).map((_, h) => {
            const isWorkHour = h >= 9 && h <= 18;
            const isEvening = h >= 19 && h <= 22;
            const intensity = isWorkHour ? (h === 14 ? 'bg-rose-500/50 border-rose-500/60' : 'bg-cyan-neon/30 border-cyan-neon/40') : (isEvening ? 'bg-amber-500/25 border-amber-500/30' : 'bg-white/5 border-white/5');
            const ppmVal = Math.round(400 + (isWorkHour ? 220 : 30) + Math.sin(h) * 40);

            return (
              <div
                key={h}
                className={`p-2 rounded-lg border flex flex-col items-center justify-between transition-all hover:scale-105 cursor-pointer ${intensity}`}
                title={`Hour ${h}:00 - Estimated PPM: ${ppmVal}, ${isWorkHour ? 'High' : 'Low'} Occupancy`}
              >
                <span className="text-[10px] font-mono text-slate-400">{h}:00</span>
                <span className="text-[11px] font-mono font-bold text-white mt-1">{ppmVal}</span>
                <span className="text-[9px] font-mono text-cyan-neon mt-0.5">{isWorkHour ? 'BUSY' : 'CALM'}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 6. Real-Time Anomaly & Security Alerts Feed */}
      <div className="glass-panel rounded-2xl p-6 border-white/10 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <h3 className="font-heading font-bold text-white text-base">Security & Environmental Alerts Feed</h3>
          </div>
          <span className="text-xs font-mono text-slate-400">Showing last {alerts.length} events</span>
        </div>

        <div className="space-y-2.5">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all ${
                alert.resolved
                  ? 'bg-white/[0.02] border-white/5 opacity-60'
                  : alert.severity === 'critical'
                  ? 'bg-rose-500/10 border-rose-500/30'
                  : alert.severity === 'warning'
                  ? 'bg-amber-500/10 border-amber-500/30'
                  : 'bg-cyan-neon/10 border-cyan-neon/20'
              }`}
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                      alert.severity === 'critical'
                        ? 'bg-rose-500/20 text-rose-300'
                        : alert.severity === 'warning'
                        ? 'bg-amber-500/20 text-amber-300'
                        : 'bg-cyan-neon/20 text-cyan-300'
                    }`}
                  >
                    {alert.severity}
                  </span>
                  <span className="text-xs font-mono text-slate-400">{alert.timestamp}</span>
                  <strong className="text-xs text-white">{alert.title}</strong>
                </div>
                <p className="text-xs text-slate-300 pl-1">{alert.message}</p>
              </div>

              {!alert.resolved ? (
                <button
                  onClick={() => handleResolveAlert(alert.id)}
                  className="self-start sm:self-auto px-3 py-1 rounded-lg bg-white/10 hover:bg-white/20 border border-white/10 text-xs font-mono text-white transition-colors"
                >
                  Mark Resolved
                </button>
              ) : (
                <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Resolved
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
