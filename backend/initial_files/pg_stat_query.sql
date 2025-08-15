SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    backend_start,
    query,
    wait_event_type,
    wait_event
FROM pg_stat_activity 
WHERE state = 'active'
ORDER BY query_start;