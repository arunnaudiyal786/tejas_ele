// Main JavaScript for Long-Running Query Manager

let sampleQueries = [];
let refreshInterval = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadSampleQueries();
    refreshQueries();
    refreshTickets();
    refreshSessions();
    
    // Set up auto-refresh for queries and sessions
    refreshInterval = setInterval(() => {
        refreshQueries();
        refreshSessions();
    }, 5000); // Refresh every 5 seconds

    // Set up ticket form submission
    document.getElementById('ticketForm').addEventListener('submit', handleTicketSubmission);
});

// Load sample queries from API
async function loadSampleQueries() {
    try {
        const response = await fetch('/api/sample-queries');
        const data = await response.json();
        sampleQueries = data.queries;
        
        const select = document.getElementById('sampleQuerySelect');
        select.innerHTML = '<option value="">Select a sample query...</option>';
        
        sampleQueries.forEach((query, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `${query.name} - ${query.description}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load sample queries:', error);
        showMessage('Failed to load sample queries', 'error');
    }
}

// Load selected sample query into the textarea
function loadSampleQuery() {
    const select = document.getElementById('sampleQuerySelect');
    const selectedIndex = select.value;
    
    if (selectedIndex !== '') {
        const query = sampleQueries[selectedIndex];
        document.getElementById('queryName').value = query.name;
        document.getElementById('queryText').value = query.query.trim();
    }
}

// Execute a query
async function executeQuery() {
    const queryText = document.getElementById('queryText').value.trim();
    const queryName = document.getElementById('queryName').value.trim() || null;
    
    if (!queryText) {
        showMessage('Please enter a query', 'error');
        return;
    }
    
    const executeBtn = document.getElementById('executeBtn');
    executeBtn.disabled = true;
    executeBtn.innerHTML = '<span class="loading"></span> Executing...';
    
    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query_text: queryText,
                query_name: queryName
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(`Query started successfully! Query ID: ${data.query_id}`, 'success');
            document.getElementById('queryResult').style.display = 'block';
            document.getElementById('queryStatus').innerHTML = `
                <p><strong>Query ID:</strong> ${data.query_id}</p>
                <p><strong>Status:</strong> <span class="status running">Running</span></p>
                <p>Query is executing in the background. Check the queries list below for updates.</p>
            `;
            
            // Clear form
            document.getElementById('queryText').value = '';
            document.getElementById('queryName').value = '';
            document.getElementById('sampleQuerySelect').value = '';
            
            // Refresh queries list
            setTimeout(refreshQueries, 1000);
        } else {
            showMessage(data.detail || 'Failed to execute query', 'error');
        }
    } catch (error) {
        console.error('Error executing query:', error);
        showMessage('Network error while executing query', 'error');
    } finally {
        executeBtn.disabled = false;
        executeBtn.textContent = 'Execute Query';
    }
}

// Refresh queries list
async function refreshQueries() {
    try {
        const response = await fetch('/api/queries');
        const data = await response.json();
        
        const queriesList = document.getElementById('queriesList');
        
        if (data.queries.length === 0) {
            queriesList.innerHTML = '<p>No queries found.</p>';
            return;
        }
        
        queriesList.innerHTML = data.queries.map(query => `
            <div class="query-item">
                <h4>Query #${query.id} ${query.query_name ? '- ' + query.query_name : ''}</h4>
                <p><strong>Status:</strong> <span class="status ${query.status}">${query.status}</span></p>
                <p><strong>Created:</strong> ${formatDate(query.created_at)}</p>
                ${query.completed_at ? `<p><strong>Completed:</strong> ${formatDate(query.completed_at)}</p>` : ''}
                ${query.pg_session_pid ? `<p><strong>Session PID:</strong> ${query.pg_session_pid}</p>` : ''}
                ${query.result_rows ? `<p><strong>Rows:</strong> ${query.result_rows}</p>` : ''}
                ${query.error_message ? `<p><strong>Error:</strong> <span style="color: red;">${query.error_message}</span></p>` : ''}
                
                <div class="query-text">${query.query_text}</div>
                
                <div class="actions">
                    ${query.status === 'running' ? `
                        <button onclick="createTicketForQuery(${query.id})" class="btn-secondary">Create Ticket</button>
                        ${query.pg_session_pid ? `<button onclick="terminateSession(${query.pg_session_pid})" class="btn-danger">Terminate</button>` : ''}
                    ` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to refresh queries:', error);
    }
}

// Refresh active sessions
async function refreshSessions() {
    try {
        const response = await fetch('/api/sessions');
        const data = await response.json();
        
        const sessionsList = document.getElementById('sessionsList');
        
        if (data.sessions.length === 0) {
            sessionsList.innerHTML = '<p>No active sessions found.</p>';
            return;
        }
        
        sessionsList.innerHTML = data.sessions.map(session => `
            <div class="session-item">
                <h4>Session PID: ${session.pid}</h4>
                <p><strong>Status:</strong> <span class="status ${session.state}">${session.state}</span></p>
                <p><strong>Application:</strong> ${session.application_name || 'N/A'}</p>
                <p><strong>Client:</strong> ${session.client_addr || 'localhost'}</p>
                <p><strong>Started:</strong> ${session.query_start ? formatDate(session.query_start) : 'N/A'}</p>
                
                <div class="query-text">${session.query}</div>
                
                <div class="actions">
                    <button onclick="terminateSession(${session.pid})" class="btn-danger">Terminate Session</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to refresh sessions:', error);
    }
}

// Refresh tickets list
async function refreshTickets() {
    try {
        const response = await fetch('/api/tickets');
        const data = await response.json();
        
        const ticketsList = document.getElementById('ticketsList');
        
        if (data.tickets.length === 0) {
            ticketsList.innerHTML = '<p>No tickets found.</p>';
            return;
        }
        
        // Show only the 5 most recent tickets
        const recentTickets = data.tickets.slice(0, 5);
        
        ticketsList.innerHTML = recentTickets.map(ticket => `
            <div class="ticket-item">
                <h4>Ticket #${ticket.ticket_id} (Query #${ticket.query_id})</h4>
                <p><strong>Status:</strong> <span class="status ${ticket.status}">${ticket.status}</span></p>
                <p><strong>Query:</strong> ${ticket.query_name || 'Unnamed Query'}</p>
                <p><strong>Created:</strong> ${formatDate(ticket.created_at)}</p>
                ${ticket.resolved_at ? `<p><strong>Resolved:</strong> ${formatDate(ticket.resolved_at)}</p>` : ''}
                <p><strong>Description:</strong> ${ticket.description}</p>
                ${ticket.resolution_details ? `<p><strong>Resolution:</strong> ${ticket.resolution_details}</p>` : ''}
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to refresh tickets:', error);
    }
}

// Create ticket for a specific query
function createTicketForQuery(queryId) {
    document.getElementById('ticketQueryId').value = queryId;
    document.getElementById('ticketDescription').value = '';
    document.getElementById('ticketModal').style.display = 'block';
}

// Handle ticket form submission
async function handleTicketSubmission(event) {
    event.preventDefault();
    
    const queryId = parseInt(document.getElementById('ticketQueryId').value);
    const description = document.getElementById('ticketDescription').value.trim();
    
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
            closeTicketModal();
            refreshTickets();
        } else {
            showMessage(data.detail || 'Failed to create ticket', 'error');
        }
    } catch (error) {
        console.error('Error creating ticket:', error);
        showMessage('Network error while creating ticket', 'error');
    }
}

// Terminate a database session
async function terminateSession(pid) {
    if (!confirm(`Are you sure you want to terminate session ${pid}? This may cause data loss.`)) {
        return;
    }
    
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
            refreshQueries();
            refreshSessions();
        } else {
            showMessage(data.detail || 'Failed to terminate session', 'error');
        }
    } catch (error) {
        console.error('Error terminating session:', error);
        showMessage('Network error while terminating session', 'error');
    }
}

// Close ticket modal
function closeTicketModal() {
    document.getElementById('ticketModal').style.display = 'none';
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
                refreshQueries();
                refreshSessions();
            }, 5000);
        }
    }
});

// Clean up interval when page unloads
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});