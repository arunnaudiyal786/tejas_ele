const API_URL = 'http://localhost:8000';

export async function startMonitoring(ticketContent: string) {
  const response = await fetch(`${API_URL}/start-monitoring`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ticket_content: ticketContent }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to start monitoring');
  }
  
  return response.json();
}

export async function getSessionStatus(sessionId: string) {
  const response = await fetch(`${API_URL}/status/${sessionId}`);
  
  if (!response.ok) {
    throw new Error('Failed to get session status');
  }
  
  return response.json();
}

export async function getSessions() {
  const response = await fetch(`${API_URL}/sessions`);
  
  if (!response.ok) {
    throw new Error('Failed to get sessions');
  }
  
  return response.json();
}

export async function getSessionResult(sessionId: string) {
  const response = await fetch(`${API_URL}/session/${sessionId}/result`);
  
  if (!response.ok) {
    throw new Error('Failed to get session result');
  }
  
  return response.json();
}