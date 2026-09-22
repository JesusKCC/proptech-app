'use client';

import React from 'react';
import { AppNavbar } from '../../components/navbar/AppNavbar';
import { TicketInbox } from '../../components/tickets/TicketInbox';

export default function TicketsPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <AppNavbar />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <TicketInbox />
      </main>
    </div>
  );
}
