'use client';

import { useState } from 'react';
import { Send, Database } from 'lucide-react';
import { startMonitoring } from '@/lib/api';
import { useStore } from '@/lib/store';
import toast from 'react-hot-toast';

export default function TicketSubmit() {
  const [ticketContent, setTicketContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { setCurrentSessionId, setIsMonitoring, updateStageStatus, flowStages } = useStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!ticketContent.trim()) {
      toast.error('Please enter ticket content');
      return;
    }

    setIsSubmitting(true);
    
    // Reset all stages
    flowStages.forEach(stage => updateStageStatus(stage.name, 'pending'));
    
    try {
      const result = await startMonitoring(ticketContent);
      setCurrentSessionId(result.session_id);
      setIsMonitoring(true);
      updateStageStatus('initialize', 'active');
      
      toast.success(`Flow started with session: ${result.session_id}`, {
        duration: 5000,
        icon: '🚀',
      });
      
      setTicketContent('');
    } catch (error) {
      toast.error('Failed to start monitoring');
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="dashboard-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-600 rounded-lg">
          <Database className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-heading">Submit JIRA Ticket</h2>
          <p className="text-body">Describe your database issue for AI analysis</p>
        </div>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="ticket-content" className="block text-subheading mb-2">
            Issue Description
          </label>
          <textarea
            id="ticket-content"
            value={ticketContent}
            onChange={(e) => setTicketContent(e.target.value)}
            placeholder="Describe your database issue here...&#10;&#10;Example: 'Slow query performance on user_analytics table causing timeouts'"
            className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none text-body placeholder-gray-500"
            disabled={isSubmitting}
          />
        </div>
        
        <button
          type="submit"
          disabled={isSubmitting || !ticketContent.trim()}
          className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Starting Analysis...</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Start Analysis</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}