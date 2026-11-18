export type ApiError = { detail?: string };

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

export async function api<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as ApiError;
    throw new Error(body.detail ?? `请求失败 (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type User = { id: number; username: string; full_name: string; is_active: boolean; roles: string[] };
export type Customer = { id: number; customer_code: string; name: string; contact_name?: string | null; email?: string | null; phone?: string | null; address?: string | null; created_at: string };
export type Contract = { id: number; contract_code: string; customer_id: number; scope: string; review_status: string; created_at: string };
export type Sample = { id: number; sample_code: string; customer_id: number; contract_id: number; model: string; quantity: number; status: string; received_at: string };
export type Task = { id: number; task_code: string; sample_id: number; template_id: number; status: string; assigned_to?: number | null; created_at: string };
export type Equipment = { id: number; equipment_code: string; name: string; status: string; calibration_due_at?: string | null };
export type Template = { id: number; template_code: string; name: string; test_type: string; is_active: boolean };
export type RawData = { id: number; task_id: number; record_type: string; values: Record<string, unknown>; recorded_at: string };
export type Report = { id: number; report_code: string; task_id: number; version: number; status: string; created_at: string };
export type Nonconformity = { id: number; nc_code: string; title: string; status: string; created_at: string };

export const statusLabel: Record<string, string> = {
  pending: '待评审', accepted: '已通过', rejected: '已拒绝', needs_clarification: '需澄清', received: '已接收',
  planned: '待执行', in_progress: '进行中', completed: '已完成', reviewed: '已审核', approved: '已批准', draft: '草稿',
  open: '开放', investigating: '调查中', action_pending: '待采取措施', effectiveness_check: '效果确认', closed: '已关闭',
  available: '可用', in_use: '使用中', out_of_service: '停用', retired: '退役',
};

export function label(value: string): string { return statusLabel[value] ?? value; }
