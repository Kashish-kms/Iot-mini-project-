import type { Metadata } from 'next';
import './globals.css';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';

export const metadata: Metadata = {
  title: 'VeilSense | Privacy-Aware Intelligent Smart IoT Monitoring Platform',
  description: 'Intelligence without intrusion: Edge-aggregated room environmental and occupancy monitoring powered by non-intrusive sensors, TLS MQTT, and machine learning risk classification.',
  keywords: ['IoT', 'Privacy', 'Smart Home', 'Edge Computing', 'ESP32', 'Machine Learning', 'FastAPI', 'Next.js', 'DHT22', 'MQ-135'],
  authors: [{ name: 'VeilSense Research' }],
  icons: {
    icon: '/icon.svg',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#070B14] text-slate-100 min-h-screen flex flex-col antialiased selection:bg-cyan-neon/30 selection:text-cyan-neon">
        {/* Subtle Cyber Grid Background */}
        <div className="fixed inset-0 cyber-grid pointer-events-none opacity-40 z-0" />
        
        {/* Ambient Aurora Glow Layers */}
        <div className="fixed top-[-10%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-cyan-neon/10 blur-[130px] pointer-events-none z-0" />
        <div className="fixed top-[20%] right-[-10%] w-[50vw] h-[50vw] rounded-full bg-violet-neon/10 blur-[140px] pointer-events-none z-0" />
        <div className="fixed bottom-[-10%] left-[25%] w-[50vw] h-[50vw] rounded-full bg-emerald-500/5 blur-[150px] pointer-events-none z-0" />

        {/* Top Navbar */}
        <Navbar />

        {/* Main Content Area */}
        <main className="flex-1 relative z-10">
          {children}
        </main>

        {/* Global Footer */}
        <Footer />
      </body>
    </html>
  );
}
