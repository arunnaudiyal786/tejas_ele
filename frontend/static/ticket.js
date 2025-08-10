// JavaScript for Ticket Management Page

let refreshInterval = null;

// Initialize the ticket management page
document.addEventListener('DOMContentLoaded', function() {
    refreshOpenTickets();
    refreshAllTickets();
    refreshAgentStatus();
    
    // Set up auto-refresh for tickets
    refreshInterval = setInterval(() => {
        refreshOpenTickets();
        refreshAgentStatus();
    }, 10000); // Refresh every 10 seconds

    // Set up form submissions
    document.getElementById('newTicketForm').addEventListener('submit', handleNewTicketSubmission);
    document.getElementById('resolveForm').addEventListener('submit', handleResolveSubmission);
    document.getElementById('terminateForm').addEventListener('submit', handleTerminateSubmission);
});

// Handle new ticket form submission
async function handleNewTicketSubmission(event) {
    event.preventDefault();
    
    const queryId = parseInt(document.getElementById('newTicketQueryId').value);
    const description = document.getElementById('newTicketDescription').value.trim();
    
    if (!description) {
        showMessage('Please enter a description', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/tickets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query_id: queryId,
                description: description
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(`Ticket created successfully! Ticket ID: ${data.ticket_id}`, 'success');
            
            // Clear form
            document.getElementById('newTicketForm').reset();
            document.getElementById('queryInfo').style.display = 'none';
            
            // Refresh ticket lists
            refreshOpenTickets();
            refreshAllTickets();
        } else {
            showMessage(data.detail || 'Failed to create ticket', 'error');
        }
    } catch (error) {
        console.error('Error creating ticket:', error);
        showMessage('Network error while creating ticket', 'error');
    }
}

// Verify query exists and show its information
async function verifyQuery() {
    const queryId = parseInt(document.getElementById('newTicketQueryId').value);
    
    if (!queryId) {
        showMessage('Please enter a query ID', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/queries/${queryId}`);
        const data = await response.json();
        
        if (response.ok) {
            const query = data.query;
            const queryInfo = document.getElementById('queryInfo');
            const queryDetails = document.getElementById('queryDetails');
            
            queryDetails.innerHTML = `
                <p><strong>Query Name:</strong> ${query.query_name || 'Unnamed'}</p>
                <p><strong>Status:</strong> <span class="status ${query.status}">${query.status}</span></p>
                <p><strong>Created:</strong> ${formatDate(query.created_at)}</p>
                ${query.pg_session_pid ? `<p><strong>Session PID:</strong> ${query.pg_session_pid}</p>` : ''}
                <div class="query-text">${query.query_text}</div>
            `;
            
            queryInfo.style.display = 'block';
            showMessage('Query found and verified', 'success');
        } else {
            showMessage(data.detail || 'Query not found', 'error');
            document.getElementById('queryInfo').style.display = 'none';
        }
    } catch (error) {
        console.error('Error verifying query:', error);
        showMessage('Network error while verifying query', 'error');
    }
}

// Refresh open tickets
async function refreshOpenTickets() {
    try {
        const response = await fetch('/api/tickets/open');
        const data = await response.json();
        
        const openTicketsList = document.getElementById('openTicketsList');
        
        if (data.tickets.length === 0) {
            openTicketsList.innerHTML = '<p>No open tickets found.</p>';
            return;
        }
        
        openTicketsList.innerHTML = data.tickets.map(ticket => `
            <div class="ticket-item">
                <h4>Ticket #${ticket.ticket_id} (Query #${ticket.query_id})</h4>
                <p><strong>Status:</strong> <span class="status ${ticket.status}">${ticket.status}</span></p>
                <p><strong>Query:</strong> ${ticket.query_name || 'Unnamed Query'} - <span class="status ${ticket.query_status}">${ticket.query_status}</span></p>
                <p><strong>Created:</strong> ${formatDate(ticket.created_at)}</p>
                ${ticket.pg_session_pid ? `<p><strong>Session PID:</strong> ${ticket.pg_session_pid}</p>` : ''}
                <p><strong>Description:</strong> ${ticket.description}</p>
                
                <div class="query-text">${ticket.query_text}</div>
                
                <div class="actions">
                    <button onclick="openResolveModal(${ticket.ticket_id})" class="btn-primary">Resolve Ticket</button>
                    ${ticket.pg_session_pid && ticket.query_status === 'running' ? 
                        `<button onclick="openTerminateModal(${ticket.pg_session_pid}, ${ticket.ticket_id})" class="btn-danger">Terminate Session</button>` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to refresh open tickets:', error);
    }
}

// Refresh all tickets
async function refreshAllTickets() {
    try {
        const response = await fetch('/api/tickets');
        const data = await response.json();
        
        const allTicketsList = document.getElementById('allTicketsList');
        
        if (data.tickets.length === 0) {
            allTicketsList.innerHTML = '<p>No tickets found.</p>';
            return;
        }
        
        // Apply status filter if selected
        const statusFilter = document.getElementById('statusFilter').value;
        let filteredTickets = data.tickets;
        
        if (statusFilter) {
            filteredTickets = data.tickets.filter(ticket => ticket.status === statusFilter);
        }
        
        if (filteredTickets.length === 0) {
            allTicketsList.innerHTML = '<p>No tickets found matching the current filter.</p>';
            return;
        }
        
        allTicketsList.innerHTML = filteredTickets.map(ticket => `
            <div class="ticket-item">
                <h4>Ticket #${ticket.ticket_id} (Query #${ticket.query_id})</h4>
                <p><strong>Status:</strong> <span class="status ${ticket.status}">${ticket.status}</span></p>
                <p><strong>Query:</strong> ${ticket.query_name || 'Unnamed Query'} - <span class="status ${ticket.query_status}">${ticket.query_status}</span></p>
                <p><strong>Created:</strong> ${formatDate(ticket.created_at)}</p>
                ${ticket.resolved_at ? `<p><strong>Resolved:</strong> ${formatDate(ticket.resolved_at)}</p>` : ''}
                <p><strong>Description:</strong> ${ticket.description}</p>
                ${ticket.resolution_details ? `<p><strong>Resolution:</strong> ${ticket.resolution_details}</p>` : ''}
                
                ${ticket.status === 'open' ? `
                    <div class="actions">
                        <button onclick="openResolveModal(${ticket.ticket_id})" class="btn-primary">Resolve Ticket</button>
                    </div>
                ` : ''}
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to refresh all tickets:', error);
    }
}

// Apply status filter
function applyFilter() {
    refreshAllTickets();
}

// Open resolve ticket modal
function openResolveModal(ticketId) {
    document.getElementById('resolveTicketId').value = ticketId;
    document.getElementById('resolutionDetails').value = '';
    document.getElementById('resolveModal').style.display = 'block';
}

// Close resolve ticket modal
function closeResolveModal() {
    document.getElementById('resolveModal').style.display = 'none';
}

// Handle resolve ticket form submission
async function handleResolveSubmission(event) {
    event.preventDefault();
    
    const ticketId = parseInt(document.getElementById('resolveTicketId').value);
    const resolutionDetails = document.getElementById('resolutionDetails').value.trim();
    
    if (!resolutionDetails) {
        showMessage('Please enter resolution details', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/tickets/${ticketId}/resolve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `resolution_details=${encodeURIComponent(resolutionDetails)}`
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(`Ticket ${ticketId} resolved successfully`, 'success');
            closeResolveModal();
            refreshOpenTickets();
            refreshAllTickets();
        } else {
            showMessage(data.detail || 'Failed to resolve ticket', 'error');
        }
    } catch (error) {
        console.error('Error resolving ticket:', error);
        showMessage('Network error while resolving ticket', 'error');
    }
}

// Open terminate session modal
function openTerminateModal(pid, ticketId) {
    document.getElementById('terminatePid').value = pid;
    document.getElementById('terminateInfo').innerHTML = `
        <p><strong>Session PID:</strong> ${pid}</p>
        <p><strong>Related Ticket:</strong> #${ticketId}</p>
    `;
    document.getElementById('terminateModal').style.display = 'block';
}

// Close terminate session modal
function closeTerminateModal() {
    document.getElementById('terminateModal').style.display = 'none';
}

// Handle terminate session form submission
async function handleTerminateSubmission(event) {
    event.preventDefault();
    
    const pid = parseInt(document.getElementById('terminatePid').value);
    
    try {
        const response = await fetch('/api/sessions/terminate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ pid: pid })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(`Session ${pid} terminated successfully`, 'success');
            closeTerminateModal();
            refreshOpenTickets();
        } else {
            showMessage(data.detail || 'Failed to terminate session', 'error');
        }
    } catch (error) {
        console.error('Error terminating session:', error);
        showMessage('Network error while terminating session', 'error');
    }
}

// Refresh agent status (placeholder for future CrewAI integration)
async function refreshAgentStatus() {
    try {
        // For now, show a simple status check
        const openTicketsResponse = await fetch('/api/tickets/open');
        const openTicketsData = await openTicketsResponse.json();
        
        const agentStatus = document.getElementById('agentStatus');
        const openTicketCount = openTicketsData.tickets.length;
        
        agentStatus.innerHTML = `
            <div class="status-info">
                <p><strong>Agent Status:</strong> <span class="status active">Monitoring</span></p>
                <p><strong>Open Tickets:</strong> ${openTicketCount}</p>
                <p><strong>Last Check:</strong> ${formatDate(new Date().toISOString())}</p>
                <p><em>CrewAI agent will automatically process open tickets with running queries.</em></p>
            </div>
        `;
        
        if (openTicketCount > 0) {
            agentStatus.innerHTML += `
                <div class="message warning">
                    <strong>Note:</strong> ${openTicketCount} open ticket(s) waiting for AI agent processing.
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Failed to refresh agent status:', error);
        const agentStatus = document.getElementById('agentStatus');
        agentStatus.innerHTML = `
            <div class="message error">
                Failed to check agent status. Please refresh the page.
            </div>
        `;
    }
}

// Utility function to format dates
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch (error) {
        return dateString;
    }
}

// Show message to user
function showMessage(message, type = 'info') {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    
    // Insert at top of main content
    const main = document.querySelector('main');
    main.insertBefore(messageDiv, main.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

// Handle page visibility change to pause/resume auto-refresh
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    } else {
        if (!refreshInterval) {
            refreshInterval = setInterval(() => {
                refreshOpenTickets();
                refreshAgentStatus();
            }, 10000);
        }
    }
});

// Clean up interval when page unloads
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});