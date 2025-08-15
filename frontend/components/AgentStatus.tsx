'use client';

import { useEffect } from 'react';
import { CheckCircle, Circle, Activity, Settings, Database, Target } from 'lucide-react';
import { useStore } from '@/lib/store';
import { getSessionStatus } from '@/lib/api';
import toast from 'react-hot-toast';

export default function AgentStatus() {
  const { currentSessionId, flowStages, updateStageStatus, setIsMonitoring, isMonitoring } = useStore();

  useEffect(() => {
    if (!currentSessionId || !isMonitoring) return;

    let intervalId: NodeJS.Timeout;
    let hasShownCompletionToast = false;

    const pollStatus = async () => {
      try {
        const status = await getSessionStatus(currentSessionId);
        
        // Update stages based on status
        if (status.stage === 'initializing') {
          updateStageStatus('initialize', 'active');
        } else if (status.stage === 'analyzing') {
          updateStageStatus('initialize', 'completed');
          updateStageStatus('analyze_ticket', 'active');
        } else if (status.stage === 'executing') {
          updateStageStatus('initialize', 'completed');
          updateStageStatus('analyze_ticket', 'completed');
          updateStageStatus('execute_crew', 'active');
        } else if (status.stage === 'finalized') {
          updateStageStatus('initialize', 'completed');
          updateStageStatus('analyze_ticket', 'completed');
          updateStageStatus('execute_crew', 'completed');
          updateStageStatus('finalize', 'completed');
          
          // Only show toast once when flow completes
          if (!hasShownCompletionToast) {
            hasShownCompletionToast = true;
            setIsMonitoring(false);
            toast.success('Flow completed successfully!', { icon: '✅' });
            clearInterval(intervalId);
          }
          return;
        }
        
        if (status.status === 'failed') {
          setIsMonitoring(false);
          toast.error(`Flow failed: ${status.error}`, { duration: 5000 });
          clearInterval(intervalId);
          return;
        }
      } catch (error) {
        console.error('Failed to poll status:', error);
        // If we get a 404, the session doesn't exist - clear it
        if (error instanceof Error && error.message.includes('Failed to get session status')) {
          console.warn(`Session ${currentSessionId} not found, clearing session`);
          setIsMonitoring(false);
          clearInterval(intervalId);
        }
      }
    };

    intervalId = setInterval(pollStatus, 2000);
    pollStatus(); // Initial call

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [currentSessionId, isMonitoring]);

  const completedStages = flowStages.filter(stage => stage.status === 'completed').length;
  const progressPercentage = (completedStages / flowStages.length) * 100;

  if (!currentSessionId) {
    return (
      <div className="dashboard-card p-6 text-center">
        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
          <Activity className="w-6 h-6 text-blue-600" />
        </div>
        <h3 className="text-heading mb-2">Agents Ready</h3>
        <p className="text-body">Submit a ticket to start AI-powered analysis</p>
      </div>
    );
  }

  return (
    <div className="dashboard-card p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-600 rounded-lg">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-heading">AI Agent Status</h2>
            <p className="text-body">Real-time monitoring progress</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold text-blue-600">{progressPercentage.toFixed(0)}%</div>
          <div className="text-small text-gray-500">Complete</div>
        </div>
      </div>
      
      {/* Progress bar */}
      <div className="mb-6">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>
      
      <div className="space-y-3">
        {flowStages.map((stage, index) => {
          const stageIcons = {
            initialize: Settings,
            analyze_ticket: Database,
            execute_crew: Activity,
            finalize: Target
          };
          const IconComponent = stageIcons[stage.name as keyof typeof stageIcons] || Circle;
          
          return (
            <div
              key={stage.name}
              className={`flex items-center gap-3 p-3 rounded-lg border ${
                stage.status === 'active' ? 'bg-blue-50 border-blue-200' :
                stage.status === 'completed' ? 'bg-green-50 border-green-200' :
                'bg-gray-50 border-gray-200'
              }`}
            >
              <div className={`p-2 rounded-lg ${
                stage.status === 'completed' ? 'bg-green-500' :
                stage.status === 'active' ? 'bg-blue-500' :
                'bg-gray-400'
              }`}>
                {stage.status === 'completed' ? (
                  <CheckCircle className="w-4 h-4 text-white" />
                ) : stage.status === 'active' ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Circle className="w-4 h-4 text-white" />
                )}
              </div>
              
              <div className="flex-1">
                <p className={`font-medium text-sm ${
                  stage.status === 'active' ? 'text-blue-700' :
                  stage.status === 'completed' ? 'text-green-700' : 'text-gray-600'
                }`}>
                  {stage.description}
                </p>
              </div>
              
              {stage.status === 'active' && (
                <span className="status-active">Processing</span>
              )}
              {stage.status === 'completed' && (
                <span className="status-completed">Complete</span>
              )}
              {stage.status === 'pending' && (
                <span className="status-pending">Pending</span>
              )}
            </div>
          );
        })}
      </div>
      
      {currentSessionId && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-small font-medium text-gray-700">Session ID</p>
              <p className="font-mono text-small text-gray-600 bg-gray-100 px-2 py-1 rounded mt-1">
                {currentSessionId}
              </p>
            </div>
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          </div>
        </div>
      )}
    </div>
  );
}