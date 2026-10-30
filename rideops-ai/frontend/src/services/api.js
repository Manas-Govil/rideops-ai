import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: BACKEND_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Handle API error formatting to avoid exposing raw stack traces.
 */
const formatError = (error) => {
  if (error.response) {
    // Backend returned 4xx or 5xx
    const detail = error.response.data?.detail || error.response.data?.message;
    return detail || `Server returned error (${error.response.status}).`;
  } else if (error.request) {
    // Network / unreachable
    return 'Unable to reach RideOps backend. Make sure the FastAPI server is running on port 8000.';
  } else {
    return error.message || 'An unexpected error occurred.';
  }
};

/**
 * Submits a natural language mobility question to the multi-agent system.
 * @param {string} question
 */
export const queryRideOps = async (question) => {
  try {
    const response = await apiClient.post('/api/query', { question });
    return response.data;
  } catch (error) {
    throw new Error(formatError(error));
  }
};

/**
 * Fetches system health and database connection status.
 */
export const getHealth = async () => {
  try {
    const response = await apiClient.get('/api/health');
    return response.data;
  } catch (error) {
    return {
      status: 'unreachable',
      database_connected: false,
      total_trips: 0,
      environment: 'unknown',
      error: formatError(error),
    };
  }
};

/**
 * Fetches recent audit events from rideops.agent_audit_log.
 * @param {number} limit
 */
export const getAuditLogs = async (limit = 20) => {
  try {
    const response = await apiClient.get(`/api/audit-logs?limit=${limit}`);
    return response.data;
  } catch (error) {
    throw new Error(formatError(error));
  }
};

/**
 * Fetches approved RideOps schema documentation and views description.
 */
export const getSchema = async () => {
  try {
    const response = await apiClient.get('/api/schema');
    return response.data;
  } catch (error) {
    throw new Error(formatError(error));
  }
};

export default apiClient;
