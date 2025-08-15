import { create } from 'zustand';
import { FlowStage } from '@/types';

interface AppState {
  currentSessionId: string | null;
  flowStages: FlowStage[];
  isMonitoring: boolean;
  setCurrentSessionId: (id: string | null) => void;
  setFlowStages: (stages: FlowStage[]) => void;
  setIsMonitoring: (monitoring: boolean) => void;
  updateStageStatus: (stageName: string, status: 'pending' | 'active' | 'completed') => void;
}

export const useStore = create<AppState>((set) => ({
  currentSessionId: null,
  flowStages: [
    { name: 'initialize', status: 'pending', description: 'Initializing monitoring flow' },
    { name: 'analyze_ticket', status: 'pending', description: 'Analyzing ticket content' },
    { name: 'execute_crew', status: 'pending', description: 'Executing database crew' },
    { name: 'finalize', status: 'pending', description: 'Finalizing results' },
  ],
  isMonitoring: false,
  setCurrentSessionId: (id) => set({ currentSessionId: id }),
  setFlowStages: (stages) => set({ flowStages: stages }),
  setIsMonitoring: (monitoring) => set({ isMonitoring: monitoring }),
  updateStageStatus: (stageName, status) =>
    set((state) => ({
      flowStages: state.flowStages.map((stage) =>
        stage.name === stageName ? { ...stage, status } : stage
      ),
    })),
}));