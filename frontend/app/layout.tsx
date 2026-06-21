import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Energy Dashboard",
  description: "Suivi consommation électrique & BMW",
  manifest: "/manifest.json",
  appleWebApp: { capable: true, statusBarStyle: "default", title: "Energy" },
};

export const viewport: Viewport = {
  themeColor: "#0f172a",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="bg-slate-950 text-slate-50 min-h-screen font-sans antialiased">
        <nav className="sticky top-0 z-10 bg-slate-900/80 backdrop-blur border-b border-slate-800 px-4 py-3 flex gap-6 text-sm font-medium">
          <a href="/" className="text-blue-400 hover:text-blue-300">Accueil</a>
          <a href="/history" className="text-slate-400 hover:text-slate-200">Historique</a>
          <a href="/analytics" className="text-slate-400 hover:text-slate-200">Analytique</a>
        </nav>
        <main className="max-w-lg mx-auto px-4 py-6 space-y-4">
          {children}
        </main>
      </body>
    </html>
  );
}
