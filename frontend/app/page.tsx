'use client';

import { useState } from 'react';
import TicketSubmit from '@/components/TicketSubmit';
import AgentStatus from '@/components/AgentStatus';
import SessionHistory from '@/components/SessionHistory';
import StatusTable from '@/components/StatusTable';
import Layout from '@/components/Layout';

export default function Home() {
  const [activeTab, setActiveTab] = useState('monitor');

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === 'monitor' ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="space-y-6">
            <TicketSubmit />
            <StatusTable />
          </div>
          <div>
            <AgentStatus />
          </div>
        </div>
      ) : (
        <SessionHistory />
      )}
    </Layout>
  );
}