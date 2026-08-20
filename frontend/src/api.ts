import type { BomItem, BuildHistoryItem, BuildResult, ImportJob, ImportSummary, InventoryItem, LegacyDashboard, LegacyProject } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";
async function request<T>(path: string, init?: RequestInit): Promise<T> { const response = await fetch(`${API_BASE}${path}`, init); const payload = await response.json().catch(() => ({})); if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `Request failed (${response.status})`); return payload as T; }
export const api = {
  getInventory: () => request<InventoryItem[]>("/inventory"),
  getLowStock: () => request<InventoryItem[]>("/inventory/low-stock"),
  getImports: () => request<ImportJob[]>("/inventory/imports"),
  importInventory: (file: File) => { const body = new FormData(); body.append("file", file); return request<ImportSummary>("/inventory/import", { method: "POST", body }); },
  getLegacyDashboard: () => request<LegacyDashboard>("/dashboard"),
  getProjects: () => request<LegacyProject[]>("/projects"),
  getProjectBom: (projectId: number) => request<BomItem[]>(`/projects/${projectId}/bom`),
  getProjectBuilds: (projectId: number) => request<BuildHistoryItem[]>(`/projects/${projectId}/builds`),
  buildProject: async (projectId: number, quantity: number): Promise<BuildResult> => {
    const response = await fetch(`${API_BASE}/projects/${projectId}/build`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ quantity }) });
    const payload = await response.json().catch(() => ({}));
    if (response.status === 409 && payload.detail) return payload.detail as BuildResult;
    if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : `Request failed (${response.status})`);
    return payload as BuildResult;
  },
};