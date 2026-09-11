import axios from 'axios';

const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const client = axios.create({ baseURL: BASE, timeout: 8000 });

export const api = {
  getState: () => client.get('/race/state').then(r => r.data),
  getTelemetry: () => client.get('/telemetry').then(r => r.data),
  getStrategy: () => client.get('/strategy').then(r => r.data),
  getCompetitors: () => client.get('/competitors').then(r => r.data),
  getTyres: () => client.get('/tyres').then(r => r.data),
  getWeather: () => client.get('/weather').then(r => r.data),

  start: () => client.post('/race/start').then(r => r.data),
  pause: () => client.post('/race/pause').then(r => r.data),
  reset: () => client.post('/race/reset').then(r => r.data),
  nextLap: () => client.post('/race/next-lap').then(r => r.data),
  setSpeed: (multiplier) => client.post('/race/speed', { multiplier }).then(r => r.data),
  triggerSafetyCar: () => client.post('/race/safety-car').then(r => r.data),

  simulate: (params) => client.post('/strategy/simulate', params).then(r => r.data),
};

// -------------------------------------------------------------------------
// Tyre Intelligence module — isolating true tyre degradation from fuel,
// traffic and track-evolution effects on a mock practice session.
// -------------------------------------------------------------------------
export const tyreIntelApi = {
  getMeta: () => client.get('/tyre-intel/meta').then(r => r.data),
  getStints: () => client.get('/tyre-intel/stints').then(r => r.data),
  regenerateSession: (seed) => client.post('/tyre-intel/session/regenerate', null, { params: seed ? { seed } : {} }).then(r => r.data),

  getOverview: (stintId) => client.get('/tyre-intel/overview', { params: stintId ? { stintId } : {} }).then(r => r.data),
  getDegradation: (stintId) => client.get('/tyre-intel/degradation', { params: stintId ? { stintId } : {} }).then(r => r.data),
  getLaps: (stintId) => client.get('/tyre-intel/laps', { params: stintId ? { stintId } : {} }).then(r => r.data),
  getDegradationCurve: (params) => client.get('/tyre-intel/degradation-curve', { params }).then(r => r.data),
  getCompare: () => client.get('/tyre-intel/compare').then(r => r.data),
  getRemainingLife: (stintId) => client.get('/tyre-intel/remaining-life', { params: stintId ? { stintId } : {} }).then(r => r.data),
  getLapForensics: (driver, lapNumber) => client.get('/tyre-intel/lap-forensics', { params: { driver, lapNumber } }).then(r => r.data),
  getDemo: () => client.get('/tyre-intel/demo').then(r => r.data),

  runStrategy: (body) => client.post('/tyre-intel/strategy', body).then(r => r.data),
  ask: (question, stintId) => client.post('/tyre-intel/ask', { question, stintId }).then(r => r.data),
  getAskExamples: () => client.get('/tyre-intel/ask/examples').then(r => r.data),
};

export default api;
