'use client';

import { useState, useEffect } from 'react';
import { ChevronDown, CheckCircle, XCircle, Clock, History } from 'lucide-react';
import { getSessions, getSessionResult } from '@/lib/api';
import { Session, SessionResult } from '@/types';

export default function SessionHistory() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [expandedSession, setExpandedSession] = useState<string | null>(null);
  const [sessionResults, setSessionResults] = useState<Record<string, SessionResult>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessions();
    const interval = setInterval(fetchSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchSessions = async () => {
    try {
      const data = await getSessions();
      setSessions(data.sessions);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpanded = async (sessionId: string) => {
    if (expandedSession === sessionId) {
      setExpandedSession(null);
    } else {
      setExpandedSession(sessionId);
      if (!sessionResults[sessionId]) {
        try {
          const result = await getSessionResult(sessionId);
          setSessionResults(prev => ({ ...prev, [sessionId]: result.result }));
        } catch (error) {
          console.error('Failed to fetch session result:', error);
        }
      }
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-blue-500" />;
    }
  };

  if (loading) {
    return (
      <div className="dashboard-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-blue-600 rounded-lg">
            <History className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-heading">Loading History</h2>
            <p className="text-body">Fetching session data...</p>
          </div>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div
              key={i}
              className="h-12 bg-gray-100 rounded-lg animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-purple-600 rounded-lg">
          <History className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-heading">Session History</h2>
          <p className="text-body">Complete analysis timeline</p>
        </div>
      </div>
        
      {sessions.length === 0 ? (
        <div className="text-center py-8">
          <div className="mx-auto w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-4">
            <History className="w-6 h-6 text-gray-600" />
          </div>
          <p className="text-heading mb-2">No History Yet</p>
          <p className="text-body">Start your first analysis to see results here</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((session, index) => (
            <div
              key={session.session_id}
              className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
            >
              <button
                onClick={() => toggleExpanded(session.session_id)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    session.status === 'completed' ? 'bg-green-500' :
                    session.status === 'failed' ? 'bg-red-500' :
                    'bg-blue-500'
                  }`}>
                    {session.status === 'completed' ? (
                      <CheckCircle className="w-4 h-4 text-white" />
                    ) : session.status === 'failed' ? (
                      <XCircle className="w-4 h-4 text-white" />
                    ) : (
                      <Clock className="w-4 h-4 text-white" />
                    )}
                  </div>
                  <div className="text-left">
                    <p className="text-subheading">{session.session_id}</p>
                    <p className="text-small text-gray-500 bg-gray-100 px-2 py-1 rounded mt-1">
                      {new Date(session.started_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <ChevronDown className={`w-4 h-4 text-gray-600 transition-transform ${
                  expandedSession === session.session_id ? 'rotate-180' : ''
                }`} />
              </button>
                
              {expandedSession === session.session_id && (
                <div className="px-4 pb-4">
                  {sessionResults[session.session_id] ? (
                    <div className="space-y-3">
                      {sessionResults[session.session_id].query_status && (
                        <div className="border border-gray-200 rounded-lg p-3">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-2 h-2 bg-blue-500 rounded-full" />
                            <span className="text-subheading">Status</span>
                          </div>
                          <span className={`px-2 py-1 rounded text-small font-medium ${
                            sessionResults[session.session_id].query_status === 'active' ? 'status-active' :
                            sessionResults[session.session_id].query_status === 'completed' ? 'status-completed' :
                            'status-pending'
                          }`}>
                            {sessionResults[session.session_id].query_status}
                          </span>
                        </div>
                      )}
                            
                      {sessionResults[session.session_id].query_resolution && (
                        <div className="border border-gray-200 rounded-lg p-3">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-2 h-2 bg-purple-500 rounded-full" />
                            <span className="text-subheading">Resolution</span>
                          </div>
                          <p className="text-body">
                            {sessionResults[session.session_id].query_resolution}
                          </p>
                        </div>
                      )}
                            
                      {sessionResults[session.session_id].query_resolution_reason && (
                        <div className="border border-gray-200 rounded-lg p-3">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-2 h-2 bg-orange-500 rounded-full" />
                            <span className="text-subheading">Analysis Reason</span>
                          </div>
                          <p className="text-body leading-relaxed">
                            {sessionResults[session.session_id].query_resolution_reason}
                          </p>
                        </div>
                      )}
                            
                      {sessionResults[session.session_id].query_resolution_action && (
                        <div className="border border-green-200 rounded-lg p-3 bg-green-50">
                          <div className="flex items-center gap-2 mb-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full" />
                            <span className="text-subheading text-green-700">Recommended Action</span>
                          </div>
                          <p className="text-green-700 font-medium leading-relaxed">
                            {sessionResults[session.session_id].query_resolution_action}
                          </p>
                        </div>
                      )}
                            
                      <details className="border border-gray-200 rounded-lg p-3">
                        <summary className="cursor-pointer text-subheading hover:text-gray-900 transition-colors">
                          📄 View Raw JSON Data
                        </summary>
                        <pre className="mt-3 text-small overflow-auto bg-gray-900 text-green-400 p-3 rounded-lg">
                          {JSON.stringify(sessionResults[session.session_id], null, 2)}
                        </pre>
                      </details>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center py-6 text-gray-500">
                      <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mr-2" />
                      Loading session details...
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}