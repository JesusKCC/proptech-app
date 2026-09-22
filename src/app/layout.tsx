import type { Metadata } from 'next';
import './globals.css';
import { Providers } from '../components/providers/Providers';

export const metadata: Metadata = {
  title: 'PropTech - Plataforma de Gestión de Activos Comerciales',
  description: 'Visor interactivo de planos arquitectónicos y gestión comercial de malls en Perú',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="min-h-screen flex flex-col bg-slate-50 text-slate-900 antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
