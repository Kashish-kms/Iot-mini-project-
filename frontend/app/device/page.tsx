'use client';

import React, { useState, useEffect } from 'react';
import { fetchDeviceStatus } from '@/lib/api';
import { DeviceStatus } from '@/lib/types';
import {
  HardDrive,
  Cpu,
  Wifi,
  Lock,
  Activity,
  CheckCircle2,
  RefreshCw,
  Terminal,
  Zap,
  Server,
  Layers,
  Thermometer,
  Wind
} from 'lucide-react';

export default function DevicePage() {
  const [device, setDevice] = useState<DeviceStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const loadStatus = async () => {
    try {
      const data = await fetchDeviceStatus();
      setDevice(data);
    } catch (err) {
      console.error('Error fetching device diagnostics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    const timer = setInterval(loadStatus, 5000);
    return () => clearInterval(timer);
  }, []);

  if (loading || !device) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center text-slate-400 font-mono text-xs">
        Connecting to ESP32 Edge Node telemetry...
      </div>
    );
  }

  const uptimeHours = Math.floor(device.uptime_seconds / 3600);
  const uptimeMins = Math.floor((device.uptime_seconds % 3600) / 60);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <HardDrive className="w-5 h-5 text-cyan-neon" />
            <h1 className="text-2xl font-heading font-bold text-white">Edge Node Diagnostics & Pinout</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time microcontroller hardware health, memory status, sensor bus metrics, and GPIO pin mapping.
          </p>
        </div>

        <button
          onClick={loadStatus}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white/5 border border-white/10 hover:border-cyan-neon/40 text-xs font-mono text-slate-200 transition-colors self-start md:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5 text-cyan-neon" />
          <span>Poll Node</span>
        </button>
      </div>

      {/* 1. ESP32 Node Telemetry Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel rounded-2xl p-4 border-white/10 space-y-1">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Hardware Status</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          </div>
          <div className="text-xl font-heading font-bold text-white flex items-center gap-2">
            {device.device_id}
          </div>
          <span className="text-[10px] font-mono text-emerald-400">Online • IP {device.ip_address}</span>
        </div>

        <div className="glass-panel rounded-2xl p-4 border-white/10 space-y-1">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Wi-Fi Signal (RSSI)</span>
            <Wifi className="w-4 h-4 text-cyan-neon" />
          </div>
          <div className="text-xl font-heading font-bold text-white">
            {device.wifi_rssi_dbm} dBm
          </div>
          <span className="text-[10px] font-mono text-cyan-neon">Signal Quality: Excellent</span>
        </div>

        <div className="glass-panel rounded-2xl p-4 border-white/10 space-y-1">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Free Heap RAM</span>
            <Cpu className="w-4 h-4 text-violet-neon" />
          </div>
          <div className="text-xl font-heading font-bold text-white">
            {Math.round(device.free_heap_bytes / 1024)} KB
          </div>
          <span className="text-[10px] font-mono text-violet-300">520 KB Total SRAM</span>
        </div>

        <div className="glass-panel rounded-2xl p-4 border-white/10 space-y-1">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>System Uptime</span>
            <span className="text-slate-400 text-[10px] font-mono">{device.firmware_version}</span>
          </div>
          <div className="text-xl font-heading font-bold text-white">
            {uptimeHours}h {uptimeMins}m
          </div>
          <span className="text-[10px] font-mono text-slate-400">Window: {device.sampling_interval_sec}s aggregate</span>
        </div>
      </div>

      {/* 2. Sensor Bus Health Diagnostics */}
      <div className="glass-panel rounded-2xl p-6 border-white/10 space-y-4">
        <h3 className="font-heading font-bold text-white text-base">Sensor Health & Diagnostic Registers</h3>
        <p className="text-xs text-slate-400">
          Individual bus communication integrity, ADC calibration parameters, and hardware interrupt statistics.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          {/* DHT22 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-heading font-bold text-white flex items-center gap-1.5">
                <Thermometer className="w-4 h-4 text-amber-400" /> DHT22 Digital Bus
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold">
                NOMINAL
              </span>
            </div>
            <div className="text-xs font-mono space-y-1 text-slate-300">
              <div className="flex justify-between"><span>GPIO Pin:</span> <strong className="text-white">GPIO 4</strong></div>
              <div className="flex justify-between"><span>Protocol:</span> <span>Single-Wire Proprietary</span></div>
              <div className="flex justify-between"><span>Read Latency:</span> <span className="text-cyan-neon">12 ms</span></div>
              <div className="flex justify-between"><span>Sample Rate:</span> <span>1.0 Hz (Cached)</span></div>
            </div>
          </div>

          {/* MQ-135 */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-heading font-bold text-white flex items-center gap-1.5">
                <Wind className="w-4 h-4 text-violet-neon" /> MQ-135 Gas Sensor
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold">
                WARMED UP
              </span>
            </div>
            <div className="text-xs font-mono space-y-1 text-slate-300">
              <div className="flex justify-between"><span>ADC Pin:</span> <strong className="text-white">GPIO 34 (ADC1_CH6)</strong></div>
              <div className="flex justify-between"><span>Preheat Time:</span> <span>48 Hours Complete</span></div>
              <div className="flex justify-between"><span>Heater Resistor:</span> <span className="text-cyan-neon">21.4 Ω</span></div>
              <div className="flex justify-between"><span>Clean Air R0:</span> <span>76.63 kΩ</span></div>
            </div>
          </div>

          {/* PIR */}
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-heading font-bold text-white flex items-center gap-1.5">
                <Activity className="w-4 h-4 text-emerald-400" /> PIR Motion Sensor
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold">
                ACTIVE
              </span>
            </div>
            <div className="text-xs font-mono space-y-1 text-slate-300">
              <div className="flex justify-between"><span>Interrupt Pin:</span> <strong className="text-white">GPIO 27</strong></div>
              <div className="flex justify-between"><span>Trigger Mode:</span> <span>RISING Edge ISR</span></div>
              <div className="flex justify-between"><span>Lifetime Pulses:</span> <span className="text-cyan-neon">842</span></div>
              <div className="flex justify-between"><span>Debounce Time:</span> <span>200 ms</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Interactive Wiring & Pinout Schematic */}
      <div className="glass-panel-glow rounded-2xl p-6 sm:p-8 border-cyan-neon/30 space-y-6">
        <div>
          <h3 className="font-heading font-bold text-white text-xl">Hardware Wiring & Pinout Diagram</h3>
          <p className="text-xs text-slate-400 mt-1">
            Schematic wiring between the ESP32 DevKit v1 microcontroller, environmental sensors, and ventilation relay.
          </p>
        </div>

        {/* Visual Schematic Diagram */}
        <div className="p-6 rounded-2xl bg-[#030712] border border-white/10 font-mono text-xs overflow-x-auto">
          <div className="min-w-[650px] space-y-4">
            <div className="text-center font-bold text-cyan-neon text-sm border-b border-white/10 pb-2">
              ESP32 Dev Module (30-Pin) Hardware Interconnect Map
            </div>

            <div className="grid grid-cols-12 gap-4 items-center py-4">
              {/* Left Sensors */}
              <div className="col-span-4 space-y-3">
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30">
                  <div className="font-bold text-amber-400">DHT22 Sensor</div>
                  <div className="text-[11px] text-slate-400">Pin 1: VCC → 3.3V</div>
                  <div className="text-[11px] text-amber-300 font-bold">Pin 2: DATA → GPIO 4 (10k Pullup)</div>
                  <div className="text-[11px] text-slate-400">Pin 4: GND → GND</div>
                </div>

                <div className="p-3 rounded-xl bg-violet-neon/10 border border-violet-neon/30">
                  <div className="font-bold text-violet-neon">MQ-135 Gas Sensor</div>
                  <div className="text-[11px] text-slate-400">VCC → 5V / VIN</div>
                  <div className="text-[11px] text-violet-300 font-bold">AOUT → GPIO 34 (ADC1_CH6)</div>
                  <div className="text-[11px] text-slate-400">GND → GND</div>
                </div>
              </div>

              {/* Center ESP32 MCU */}
              <div className="col-span-4 p-5 rounded-2xl bg-cyan-neon/10 border-2 border-cyan-neon/40 text-center space-y-2 shadow-[0_0_25px_rgba(34,211,238,0.2)]">
                <Cpu className="w-8 h-8 text-cyan-neon mx-auto" />
                <div className="font-bold text-white text-sm">ESP32 DevKit v1</div>
                <div className="text-[10px] text-cyan-neon">Dual Core Xtensa 240MHz</div>
                <div className="text-[10px] text-slate-400">FreeRTOS + WiFiClientSecure</div>
                <div className="p-1 rounded bg-black/50 text-[10px] text-emerald-400 font-bold mt-2">
                  mTLS 1.3 Handshake Active
                </div>
              </div>

              {/* Right Actuators & PIR */}
              <div className="col-span-4 space-y-3">
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                  <div className="font-bold text-emerald-400">PIR Motion (HC-SR501)</div>
                  <div className="text-[11px] text-slate-400">VCC → 5V / VIN</div>
                  <div className="text-[11px] text-emerald-300 font-bold">OUT → GPIO 27 (ISR Int)</div>
                  <div className="text-[11px] text-slate-400">GND → GND</div>
                </div>

                <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/30">
                  <div className="font-bold text-blue-400">Ventilation Relay</div>
                  <div className="text-[11px] text-slate-400">VCC → 5V / VIN</div>
                  <div className="text-[11px] text-blue-300 font-bold">IN → GPIO 18 (Active HIGH)</div>
                  <div className="text-[11px] text-slate-400">GND → GND</div>
                </div>
              </div>
            </div>

            <div className="text-[11px] text-slate-500 border-t border-white/5 pt-2 text-center">
              Power supply requirement: 5V 2A micro-USB. Dedicated ground plane to isolate analog MQ-135 ADC reads.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
