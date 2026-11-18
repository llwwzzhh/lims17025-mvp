import { useEffect, useMemo, useState } from 'react';
import { api, type Contract, type Customer, type Equipment, type Nonconformity, type RawData, type Report, type Sample, type Task, type Template, type User, label } from './api';

type Section = 'overview' | 'customers' | 'contracts' | 'samples' | 'tasks' | 'equipment' | 'reports' | 'quality';
type LoginResponse = { access_token: string; token_type: string };

const sections: { key: Section; title: string; permission?: string }[] = [
  { key: 'overview', title: '工作台' }, { key: 'customers', title: '客户' }, { key: 'contracts', title: '合同' },
  { key: 'samples', title: '样品' }, { key: 'tasks', title: '试验任务' }, { key: 'equipment', title: '设备' },
  { key: 'reports', title: '报告' }, { key: 'quality', title: '质量管理' },
];

function Login({ onLogin }: { onLogin: (token: string, user: User) => void }) {
  const [username, setUsername] = useState(''); const [password, setPassword] = useState('');
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const token = await api<LoginResponse>('/api/auth/token', '', { method: 'POST', body: JSON.stringify({ username, password }) });
      const user = await api<User>('/api/auth/me', token.access_token);
      onLogin(token.access_token, user);
    } catch (e) { setError(e instanceof Error ? e.message : '登录失败'); }
    finally { setBusy(false); }
  }
  return <main className="login-wrap"><form className="login-card" onSubmit={submit}>
    <div className="brand-mark">L</div><p className="eyebrow">LABORATORY QUALITY SYSTEM</p><h1>登录实验室 LIMS</h1>
    <label>用户名<input autoComplete="username" required value={username} onChange={e => setUsername(e.target.value)} /></label>
    <label>密码<input type="password" autoComplete="current-password" required value={password} onChange={e => setPassword(e.target.value)} /></label>
    {error && <p className="error" role="alert">{error}</p>}<button className="primary full" disabled={busy}>{busy ? '登录中…' : '安全登录'}</button>
    <p className="muted small">访问凭证仅保存在当前标签页内存中。</p>
  </form></main>;
}

function App() {
  const [token, setToken] = useState(''); const [user, setUser] = useState<User | null>(null);
  const [section, setSection] = useState<Section>('overview'); const [refresh, setRefresh] = useState(0);
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const [customers, setCustomers] = useState<Customer[]>([]); const [contracts, setContracts] = useState<Contract[]>([]);
  const [samples, setSamples] = useState<Sample[]>([]); const [tasks, setTasks] = useState<Task[]>([]);
  const [equipment, setEquipment] = useState<Equipment[]>([]); const [templates, setTemplates] = useState<Template[]>([]);
  const [reports, setReports] = useState<Report[]>([]); const [ncs, setNcs] = useState<Nonconformity[]>([]); const [rawData, setRawData] = useState<RawData[]>([]);
  const [modal, setModal] = useState<Section | null>(null);

  function login(value: string, account: User) { setToken(value); setUser(account); setError(''); }
  function logout() { setToken(''); setUser(null); setSection('overview'); }
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    setBusy(true); setError('');
    Promise.allSettled([
      api<Customer[]>('/api/customers', token), api<Contract[]>('/api/contracts', token), api<Sample[]>('/api/samples', token),
      api<Task[]>('/api/tasks', token), api<Equipment[]>('/api/equipment', token), api<Template[]>('/api/test-templates', token),
      api<Report[]>('/api/reports', token), api<Nonconformity[]>('/api/nonconformities', token), api<RawData[]>('/api/raw-data', token),
    ]).then(results => {
      if (cancelled) return;
      const setters = [setCustomers, setContracts, setSamples, setTasks, setEquipment, setTemplates, setReports, setNcs, setRawData] as const;
      results.forEach((result, index) => { if (result.status === 'fulfilled') setters[index](result.value as never); });
      const failures = results.filter(r => r.status === 'rejected');
      if (failures.length === results.length) setError('无法加载数据，请检查服务连接或账户权限。');
      setBusy(false);
    });
    return () => { cancelled = true; };
  }, [token, refresh]);

  const stats = useMemo(() => [
    { title: '客户', value: customers.length, color: 'blue' }, { title: '待评审合同', value: contracts.filter(x => x.review_status === 'pending').length, color: 'orange' },
    { title: '在检样品', value: samples.filter(x => !['released', 'returned'].includes(x.status)).length, color: 'green' },
    { title: '进行中任务', value: tasks.filter(x => x.status === 'in_progress').length, color: 'purple' },
    { title: '开放不符合项', value: ncs.filter(x => x.status !== 'closed').length, color: 'red' },
  ], [customers, contracts, samples, tasks, ncs]);

  if (!user) return <Login onLogin={login} />;
  const visibleSections = sections.filter(item => !item.permission || user.roles.includes('admin') || user.roles.some(role => role));
  return <div className="app-shell">
    <aside className="sidebar"><a className="brand" href="#home" onClick={e => { e.preventDefault(); setSection('overview'); }}><span className="brand-mark small-mark">L</span><span><b>LabFlow</b><small>QUALITY SYSTEM</small></span></a>
      <p className="nav-caption">工作空间</p><nav>{visibleSections.map(item => <button key={item.key} className={section === item.key ? 'nav-item active' : 'nav-item'} onClick={() => setSection(item.key)}><span className="nav-dot" />{item.title}{item.key === 'quality' && ncs.some(x => x.status !== 'closed') && <i className="nav-badge">{ncs.filter(x => x.status !== 'closed').length}</i>}</button>)}</nav>
      <div className="sidebar-bottom"><span className="online-dot" />系统运行中 <small>API v0.1.0</small></div>
    </aside>
    <main className="main-area"><header className="topbar"><div><span className="breadcrumb">实验室 / </span><b>{sections.find(s => s.key === section)?.title}</b></div><div className="account"><span className="avatar">{user.full_name.slice(0, 1)}</span><span><b>{user.full_name}</b><small>{user.roles.join(' · ') || '用户'}</small></span><button className="logout" onClick={logout}>退出</button></div></header>
      <section className="page-content"><div className="page-heading"><div><p className="eyebrow">LAB OPERATIONS</p><h1>{section === 'overview' ? `你好，${user.full_name}` : sections.find(s => s.key === section)?.title}</h1><p className="muted">{section === 'overview' ? '实验室质量管理与检测流程一览。' : `管理${sections.find(s => s.key === section)?.title}业务记录及工作流程。`}</p></div><div className="heading-actions"><button className="secondary" onClick={() => setRefresh(x => x + 1)}>刷新</button>{section !== 'overview' && section !== 'quality' && <button className="primary" onClick={() => setModal(section)}>＋ 新建记录</button>}</div></div>
        {error && <div className="error-banner" role="alert">{error}<button onClick={() => setError('')}>关闭</button></div>}
        {busy && <div className="loading">正在载入实验室记录…</div>}
        {section === 'overview' && <><div className="stats-grid">{stats.map(x => <article className="stat-card" key={x.title}><div className={`stat-icon ${x.color}`} /><p>{x.title}</p><strong>{x.value}</strong></article>)}</div><div className="dashboard-grid"><article className="panel"><div className="panel-head"><div><h2>近期任务</h2><p>检测执行状态</p></div><button className="text-button" onClick={() => setSection('tasks')}>查看全部 →</button></div><DataTable columns={['任务编号', '样品', '状态', '创建时间']} rows={tasks.slice(0, 5).map(x => [x.task_code, String(x.sample_id), label(x.status), new Date(x.created_at).toLocaleDateString()])} empty="暂无任务记录" /></article><article className="panel"><div className="panel-head"><div><h2>待关注事项</h2><p>质量管理提示</p></div></div><div className="attention-list"><div><span className="attention-icon amber">!</span><p><b>{contracts.filter(x => x.review_status === 'pending').length} 份合同待评审</b><small>通过评审后方可登记样品</small></p></div><div><span className="attention-icon rose">!</span><p><b>{ncs.filter(x => x.status !== 'closed').length} 个开放不符合项</b><small>需跟进调查与纠正措施</small></p></div><div><span className="attention-icon mint">✓</span><p><b>{equipment.filter(x => x.status === 'available').length} 台设备可用</b><small>创建任务前请核对校准有效期</small></p></div></div></article></div></>}
        {section === 'customers' && <DataTable columns={['客户编号', '客户名称', '联系人', '邮箱', '电话']} rows={customers.map(x => [x.customer_code, x.name, x.contact_name ?? '—', x.email ?? '—', x.phone ?? '—'])} empty="暂无客户，请创建一条记录" />}
        {section === 'contracts' && <DataTable columns={['合同编号', '客户 ID', '检测范围', '评审状态', '创建时间']} rows={contracts.map(x => [x.contract_code, String(x.customer_id), x.scope, label(x.review_status), new Date(x.created_at).toLocaleDateString()])} empty="暂无合同记录" />}
        {section === 'samples' && <DataTable columns={['样品编号', '型号', '数量', '合同 ID', '状态', '接收时间']} rows={samples.map(x => [x.sample_code, x.model, String(x.quantity), String(x.contract_id), label(x.status), new Date(x.received_at).toLocaleDateString()])} empty="暂无样品记录" />}
        {section === 'tasks' && <DataTable columns={['任务编号', '样品 ID', '模板 ID', '状态', '创建时间']} rows={tasks.map(x => [x.task_code, String(x.sample_id), String(x.template_id), label(x.status), new Date(x.created_at).toLocaleDateString()])} empty="暂无试验任务" />}
        {section === 'equipment' && <DataTable columns={['设备编号', '设备名称', '状态', '校准到期']} rows={equipment.map(x => [x.equipment_code, x.name, label(x.status), x.calibration_due_at ? new Date(x.calibration_due_at).toLocaleDateString() : '未设置'])} empty="暂无设备" />}
        {section === 'reports' && <DataTable columns={['报告编号', '任务 ID', '版本', '状态', '创建时间']} rows={reports.map(x => [x.report_code, String(x.task_id), `v${x.version}`, label(x.status), new Date(x.created_at).toLocaleDateString()])} empty="暂无报告" />}
        {section === 'quality' && <div className="dashboard-grid"><article className="panel"><div className="panel-head"><div><h2>不符合项</h2><p>纠正与预防措施跟踪</p></div></div><DataTable columns={['编号', '标题', '状态', '创建时间']} rows={ncs.map(x => [x.nc_code, x.title, label(x.status), new Date(x.created_at).toLocaleDateString()])} empty="暂无不符合项" /></article><article className="panel"><div className="panel-head"><div><h2>原始数据</h2><p>检测记录数量 {rawData.length}</p></div></div><DataTable columns={['记录 ID', '任务 ID', '类型', '记录时间']} rows={rawData.slice(0, 8).map(x => [String(x.id), String(x.task_id), x.record_type, new Date(x.recorded_at).toLocaleString()])} empty="暂无原始数据" /></article></div>}
      </section>
    </main>
    {modal && <CreateModal section={modal} token={token} customers={customers} contracts={contracts} samples={samples} templates={templates} onClose={() => setModal(null)} onCreated={() => { setModal(null); setRefresh(x => x + 1); }} />}
  </div>;
}

function DataTable({ columns, rows, empty }: { columns: string[]; rows: string[][]; empty: string }) {
  if (!rows.length) return <div className="empty-state"><span>▤</span><p>{empty}</p></div>;
  return <div className="table-wrap"><table><thead><tr>{columns.map(c => <th key={c}>{c}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{j === 3 && ['待评审', '进行中', '开放', '已批准', '已通过'].includes(cell) ? <span className="status-chip">{cell}</span> : cell}</td>)}</tr>)}</tbody></table></div>;
}

type CreateModalProps = { section: Section; token: string; customers: Customer[]; contracts: Contract[]; samples: Sample[]; templates: Template[]; onClose: () => void; onCreated: () => void };
function CreateModal({ section, token, customers, contracts, samples, templates, onClose, onCreated }: CreateModalProps) {
  const [values, setValues] = useState<Record<string, string>>({}); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const fields: Record<string, { key: string; label: string; type?: string; required?: boolean; options?: { value: string; label: string }[] }[]> = {
    customers: [{ key: 'customer_code', label: '客户编号', required: true }, { key: 'name', label: '客户名称', required: true }, { key: 'contact_name', label: '联系人' }, { key: 'email', label: '邮箱', type: 'email' }, { key: 'phone', label: '电话' }, { key: 'address', label: '地址' }],
    contracts: [{ key: 'contract_code', label: '合同编号', required: true }, { key: 'customer_id', label: '客户', type: 'select', required: true, options: customers.map(x => ({ value: String(x.id), label: `${x.customer_code} — ${x.name}` })) }, { key: 'scope', label: '检测范围', type: 'textarea', required: true }],
    samples: [{ key: 'sample_code', label: '样品编号', required: true }, { key: 'customer_id', label: '客户', type: 'select', required: true, options: customers.map(x => ({ value: String(x.id), label: x.name })) }, { key: 'contract_id', label: '已通过合同', type: 'select', required: true, options: contracts.filter(x => x.review_status === 'accepted').map(x => ({ value: String(x.id), label: x.contract_code })) }, { key: 'model', label: '产品型号', required: true }, { key: 'manufacturer', label: '制造商' }, { key: 'lot_number', label: '批次号' }, { key: 'serial_number', label: '序列号' }, { key: 'quantity', label: '数量', type: 'number', required: true }, { key: 'condition_on_receipt', label: '接收状态' }],
    tasks: [{ key: 'task_code', label: '任务编号', required: true }, { key: 'sample_id', label: '样品', type: 'select', required: true, options: samples.map(x => ({ value: String(x.id), label: x.sample_code })) }, { key: 'template_id', label: '试验模板', type: 'select', required: true, options: templates.filter(x => x.is_active).map(x => ({ value: String(x.id), label: x.name })) }, { key: 'notes', label: '备注', type: 'textarea' }],
    equipment: [{ key: 'equipment_code', label: '设备编号', required: true }, { key: 'name', label: '设备名称', required: true }, { key: 'model', label: '型号' }, { key: 'serial_number', label: '序列号' }, { key: 'location', label: '位置' }, { key: 'calibration_due_at', label: '校准到期时间', type: 'datetime-local' }, { key: 'notes', label: '备注', type: 'textarea' }],
    reports: [{ key: 'report_code', label: '报告编号', required: true }, { key: 'task_id', label: '已审核任务', type: 'select', required: true, options: tasksForReport(samples, templates) }],
  };
  function tasksForReport(_samples: Sample[], _templates: Template[]) { return []; }
  const endpoints: Partial<Record<Section, string>> = { customers: '/api/customers', contracts: '/api/contracts', samples: '/api/samples', tasks: '/api/tasks', equipment: '/api/equipment', reports: '/api/reports' };
  const schema = fields[section] ?? [];
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    const body: Record<string, unknown> = { ...values };
    for (const key of ['customer_id', 'contract_id', 'quantity', 'sample_id', 'template_id', 'task_id']) if (body[key]) body[key] = Number(body[key]);
    if (section === 'contracts') body.method_requirements = {};
    if (section === 'reports') body.content = { notes: values.notes ?? '' };
    if (section === 'tasks') { delete body.notes; body.notes = values.notes || null; }
    try { await api(endpoints[section]!, token, { method: 'POST', body: JSON.stringify(body) }); onCreated(); }
    catch (e) { setError(e instanceof Error ? e.message : '创建失败'); }
    finally { setBusy(false); }
  }
  return <div className="modal-backdrop" role="presentation" onMouseDown={e => { if (e.target === e.currentTarget) onClose(); }}><form className="modal" onSubmit={submit}>
    <div className="modal-head"><div><p className="eyebrow">NEW RECORD</p><h2>新建{sections.find(x => x.key === section)?.title}</h2></div><button type="button" className="icon-button" onClick={onClose} aria-label="关闭">×</button></div>
    <div className="form-grid">{schema.map(field => <label key={field.key} className={field.type === 'textarea' ? 'wide' : ''}>{field.label}{field.type === 'select' ? <select required={field.required} value={values[field.key] ?? ''} onChange={e => setValues({ ...values, [field.key]: e.target.value })}><option value="">请选择</option>{field.options?.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}</select> : field.type === 'textarea' ? <textarea required={field.required} value={values[field.key] ?? ''} onChange={e => setValues({ ...values, [field.key]: e.target.value })} /> : <input required={field.required} type={field.type ?? 'text'} min={field.type === 'number' ? '1' : undefined} value={values[field.key] ?? ''} onChange={e => setValues({ ...values, [field.key]: e.target.value })} />}</label>)}</div>
    {error && <p className="error" role="alert">{error}</p>}<div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>取消</button><button className="primary" disabled={busy}>{busy ? '提交中…' : '创建记录'}</button></div>
  </form></div>;
}

export default App;
