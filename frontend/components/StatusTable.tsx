'use client';

import { useState, useEffect } from 'react';
import { useStore } from '@/lib/store';
import { getSessionResult } from '@/lib/api';
import { SessionResult } from '@/types';
import { CheckCircle, Clock, Database, Activity } from 'lucide-react';

export default function StatusTable() {
  const { currentSessionId, isMonitoring } = useStore();
  const [result, setResult] = useState<SessionResult | null>(null);

  useEffect(() => {
    if (!currentSessionId || isMonitoring) return;

    const fetchResult = async () => {
      try {
        const data = await getSessionResult(currentSessionId);
        setResult(data.result);
      } catch (error) {
        console.error('Failed to fetch result:', error);
      }
    };

    fetchResult();
  }, [currentSessionId, isMonitoring]);

  if (!result) {
    return (
      <div className="dashboard-card p-6 text-center">
        <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
          <Database className="w-6 h-6 text-gray-600" />
        </div>
        <h3 className="text-heading mb-2">Awaiting Results</h3>
        <p className="text-body">Complete a session to view analysis results</p>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <Activity className="w-4 h-4" />;
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="dashboard-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-green-600 rounded-lg">
          <Database className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-heading">Analysis Results</h2>
          <p className="text-body">Latest session findings</p>
        </div>
      </div>
      
      <div className="space-y-4">
        {result.query_status && (
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-subheading">Query Status</span>
              <div className={`flex items-center gap-2 px-3 py-1 rounded-lg ${
                result.query_status === 'active' ? 'status-active' :
                result.query_status === 'completed' ? 'status-completed' :
                'status-pending'
              }`}>
                {getStatusIcon(result.query_status)}
                <span className="capitalize font-medium">{result.query_status}</span>
              </div>
            </div>
          </div>
        )}
        
        {result.query_resolution && (
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="space-y-2">
              <span className="text-subheading">Resolution</span>
              <div className="text-body bg-gray-50 rounded-lg p-3">
                {result.query_resolution}
              </div>
            </div>
          </div>
        )}
        
        {result.query_resolution_reason && (
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="space-y-2">
              <span className="text-subheading">Analysis Reason</span>
              <div className="text-body bg-gray-50 rounded-lg p-3 leading-relaxed">
                {result.query_resolution_reason}
              </div>
            </div>
          </div>
        )}
        
        {result.query_resolution_action && (
          <div className="border border-green-200 rounded-lg p-4 bg-green-50">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-subheading text-green-700">Recommended Action</span>
              </div>
              <div className="text-green-700 bg-white rounded-lg p-3 font-medium">
                {result.query_resolution_action}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}