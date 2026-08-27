const API = '/api';

async function request(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API}${path}`, { ...options, headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

// ── Auth ──────────────────────────────────────────────────────
export const auth = {
  register: (d) => request('/auth/register', { method: 'POST', body: JSON.stringify(d) }),
  login: (d) => request('/auth/login', { method: 'POST', body: JSON.stringify(d) }),
  me: () => request('/auth/me'),
};

// ── Workspaces ────────────────────────────────────────────────
export const workspaces = {
  list: () => request('/workspaces/'),
  create: (d) => request('/workspaces/', { method: 'POST', body: JSON.stringify(d) }),
  get: (id) => request(`/workspaces/${id}`),
};

// ── Agents ────────────────────────────────────────────────────
export const agents = {
  templates: () => request('/agents/templates'),
  list: (wsId) => request(`/agents/workspace/${wsId}`),
  get: (id) => request(`/agents/${id}`),
  create: (wsId, d) => request(`/agents/workspace/${wsId}`, { method: 'POST', body: JSON.stringify(d) }),
  createFromTemplate: (wsId, tid) => request(`/agents/workspace/${wsId}/from-template/${tid}`, { method: 'POST' }),
  update: (id, d) => request(`/agents/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
  delete: (id) => request(`/agents/${id}`, { method: 'DELETE' }),
  addSkill: (id, name) => request(`/agents/${id}/skills/${name}`, { method: 'POST' }),
  removeSkill: (id, name) => request(`/agents/${id}/skills/${name}`, { method: 'DELETE' }),
};

// ── Skills ────────────────────────────────────────────────────
export const skills = {
  registry: () => request('/skills/registry'),
  byCategory: (cat) => request(`/skills/registry/${cat}`),
  listWorkspace: (wsId) => request(`/skills/workspace/${wsId}`),
};

// ── Conversations ─────────────────────────────────────────────
export const conversations = {
  channels: (wsId) => request(`/conversations/workspace/${wsId}/channels`),
  createChannel: (wsId, d) => request(`/conversations/workspace/${wsId}/channels`, { method: 'POST', body: JSON.stringify(d) }),
  quickConnectWhatsApp: (wsId) => request(`/conversations/workspace/${wsId}/quick-connect/whatsapp`, { method: 'POST' }),
  quickConnectEmail: (wsId) => request(`/conversations/workspace/${wsId}/quick-connect/email`, { method: 'POST' }),
  setupWebhook: (wsId) => request(`/conversations/workspace/${wsId}/setup-webhook`, { method: 'POST' }),
  webhookStatus: (wsId) => request(`/conversations/workspace/${wsId}/webhook-status`),
  contacts: (wsId) => request(`/conversations/workspace/${wsId}/contacts`),
  createContact: (wsId, d) => request(`/conversations/workspace/${wsId}/contacts`, { method: 'POST', body: JSON.stringify(d) }),
  messages: (wsId, convId) => request(`/conversations/workspace/${wsId}/messages${convId ? `?conversation_id=${convId}` : ''}`),
  memory: (wsId, q) => request(`/conversations/workspace/${wsId}/memory${q ? `?query=${encodeURIComponent(q)}` : ''}`),
  saveMemory: (wsId, d) => request(`/conversations/workspace/${wsId}/memory`, { method: 'POST', body: JSON.stringify(d) }),
};

// ── Settlement ────────────────────────────────────────────────
export const settlement = {
  transactions: (wsId, status) => request(`/settlement/workspace/${wsId}/transactions${status ? `?status=${status}` : ''}`),
  get: (wsId, txId) => request(`/settlement/workspace/${wsId}/transactions/${txId}`),
  create: (wsId, d) => request(`/settlement/workspace/${wsId}/transactions`, { method: 'POST', body: JSON.stringify(d) }),
  transition: (wsId, txId, status, reason) => request(`/settlement/workspace/${wsId}/transactions/${txId}/transition?new_status=${status}&reason=${encodeURIComponent(reason || '')}`, { method: 'POST' }),
  match: (wsId, text) => request(`/settlement/workspace/${wsId}/match?text=${encodeURIComponent(text)}`, { method: 'POST' }),
  unsettled: (wsId) => request(`/settlement/workspace/${wsId}/unsettled`),
  reconcile: (wsId, days) => request(`/settlement/workspace/${wsId}/reconcile?days=${days || 1}`),
  report: (wsId) => request(`/settlement/workspace/${wsId}/report`),
};

// ── Knowledge ─────────────────────────────────────────────────
export const knowledge = {
  list: (wsId, cat) => request(`/knowledge/workspace/${wsId}${cat ? `?category=${cat}` : ''}`),
  create: (wsId, d) => request(`/knowledge/workspace/${wsId}`, { method: 'POST', body: JSON.stringify(d) }),
  update: (wsId, id, d) => request(`/knowledge/workspace/${wsId}/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
  delete: (wsId, id) => request(`/knowledge/workspace/${wsId}/${id}`, { method: 'DELETE' }),
};

// ── Audit ─────────────────────────────────────────────────────
export const audit = {
  logs: (wsId, agentId) => request(`/audit/workspace/${wsId}/logs${agentId ? `?agent_id=${agentId}` : ''}`),
  runs: (wsId, agentId) => request(`/audit/workspace/${wsId}/runs${agentId ? `?agent_id=${agentId}` : ''}`),
};

// ── Legacy (backward compat) ──────────────────────────────────
export const email = {
  list: () => request('/messaging/email/connections'),
  connect: (d) => request('/messaging/email/connect', { method: 'POST', body: JSON.stringify(d) }),
  disconnect: (id) => request(`/messaging/email/connections/${id}`, { method: 'DELETE' }),
};
export const whatsapp = {
  get: () => request('/messaging/whatsapp/connection'),
  connect: (d) => request('/messaging/whatsapp/connect', { method: 'POST', body: JSON.stringify(d) }),
  disconnect: () => request('/messaging/whatsapp/connection', { method: 'DELETE' }),
  test: () => request('/messaging/whatsapp/test', { method: 'POST' }),
};
export const rules = {
  list: () => request('/messaging/rules'),
  create: (d) => request('/messaging/rules', { method: 'POST', body: JSON.stringify(d) }),
  update: (id, d) => request(`/messaging/rules/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
  delete: (id) => request(`/messaging/rules/${id}`, { method: 'DELETE' }),
};
export const dashboard = {
  get: () => request('/messaging/dashboard'),
  messages: () => request('/messaging/messages'),
  usage: () => request('/messaging/usage'),
};
export const billing = {
  plans: () => request('/billing/plans'),
  subscription: () => request('/billing/subscription'),
  checkout: (plan) => request(`/billing/checkout?plan=${plan}`, { method: 'POST' }),
  portal: () => request('/billing/portal', { method: 'POST' }),
};
