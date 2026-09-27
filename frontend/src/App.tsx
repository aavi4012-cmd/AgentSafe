import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, CheckCircle2, Lock, Shield, ShieldAlert, SlidersHorizontal, LogOut, ArrowRight } from 'lucide-react';

type TabKey = 'dashboard' | 'agents' | 'tools' | 'policies' | 'approvals' | 'simulator';

type Agent = { id: number; name: string; description: string; status: string };
type Tool = { id: number; name: string; category: string; sensitivity: string; operation: string; default_risk: number };
type Policy = { id: number; name: string; description: string; effect: string; environment: string };
type Approval = { id: number; agent_name: string; requested_action: string; reason: string; risk_score: number; status: string };
type Stats = { total_actions: number; allowed: number; blocked: number; pending_approval: number; risk_distribution: Record<string, number> };
type ActionItem = { id: number; agent_name: string; tool_name: string; risk_score: number; risk_level: string; decision: string; timestamp: string };

type Result = {
  agent: string;
  tool: string;
  environment: string;
  risk_score: number;
  risk_level: string;
  decision: string;
  explanation: string;
  risk_factors: string[];
  recommended_policy: string;
  blocked: boolean;
  requires_approval: boolean;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const navItems: { id: TabKey; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'agents', label: 'Agents' },
  { id: 'tools', label: 'Tools' },
  { id: 'policies', label: 'Policies' },
  { id: 'approvals', label: 'Approvals' },
  { id: 'simulator', label: 'Simulate Action' },
];

const riskClasses: Record<string, string> = {
  LOW: 'text-emerald-700 bg-emerald-50 border border-emerald-200',
  MEDIUM: 'text-amber-700 bg-amber-50 border border-amber-200',
  HIGH: 'text-orange-700 bg-orange-50 border border-orange-200',
  CRITICAL: 'text-rose-700 bg-rose-50 border border-rose-200',
};

const decisionClasses: Record<string, string> = {
  ALLOW: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
  BLOCK: 'bg-rose-50 text-rose-700 border border-rose-200',
  REQUIRE_APPROVAL: 'bg-amber-50 text-amber-700 border border-amber-200',
};

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error('Request failed');
  return res.json() as Promise<T>;
}

function App() {
  const [tab, setTab] = useState<TabKey>('dashboard');
  const [simulator, setSimulator] = useState({
    agent: 'support-agent',
    tool: 'database.delete_user',
    environment: 'production',
    argumentsText: '{"user_id":"123"}',
  });
  const [result, setResult] = useState<Result | null>(null);
  const [approvalRows, setApprovalRows] = useState<Approval[]>([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [operatorName, setOperatorName] = useState('Operator');
  const [waitlist, setWaitlist] = useState({
    name: '',
    email: '',
    company: '',
    role: '',
  });
  const [waitlistSubmitted, setWaitlistSubmitted] = useState(false);

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: () => fetchJson<Stats>(`${API_BASE}/dashboard/stats`),
  });

  const { data: actions, isLoading: actionsLoading } = useQuery({
    queryKey: ['recent-actions'],
    queryFn: () => fetchJson<ActionItem[]>(`${API_BASE}/dashboard/recent-actions`),
  });

  const { data: agents = [], isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => fetchJson<Agent[]>(`${API_BASE}/agents`),
  });

  const { data: tools = [], isLoading: toolsLoading } = useQuery({
    queryKey: ['tools'],
    queryFn: () => fetchJson<Tool[]>(`${API_BASE}/tools`),
  });

  const { data: policies = [], isLoading: policiesLoading } = useQuery({
    queryKey: ['policies'],
    queryFn: () => fetchJson<Policy[]>(`${API_BASE}/policies`),
  });

  const { data: approvals = [], isLoading: approvalsLoading } = useQuery({
    queryKey: ['approvals'],
    queryFn: () => fetchJson<Approval[]>(`${API_BASE}/approvals`),
  });

  useEffect(() => {
    if (approvals.length) {
      setApprovalRows(approvals);
    }
  }, [approvals]);

  useEffect(() => {
    const revealItems = document.querySelectorAll('.reveal-on-scroll');
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
          }
        });
      },
      { threshold: 0.15 },
    );

    revealItems.forEach((item) => observer.observe(item));

    return () => observer.disconnect();
  }, []);

  const statsCards = useMemo(() => {
    if (!stats) return [];
    return [
      { label: 'Total Actions', value: stats.total_actions, icon: Shield },
      { label: 'Allowed', value: stats.allowed, icon: CheckCircle2 },
      { label: 'Blocked', value: stats.blocked, icon: Lock },
      { label: 'Pending Approval', value: stats.pending_approval, icon: SlidersHorizontal },
    ];
  }, [stats]);

  const handleAnalyze = async () => {
    try {
      const payload = {
        agent: simulator.agent,
        tool: simulator.tool,
        environment: simulator.environment,
        arguments: JSON.parse(simulator.argumentsText || '{}'),
        context: { task: 'simulator' },
      };
      const res = await fetch(`${API_BASE}/actions/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Invalid analysis result');
      const data = await res.json();
      setResult(data);
    } catch (error) {
      setResult({
        agent: simulator.agent,
        tool: simulator.tool,
        environment: simulator.environment,
        risk_score: 0,
        risk_level: 'LOW',
        decision: 'ALLOW',
        explanation: 'The simulator failed to parse the action. Check your JSON arguments.',
        risk_factors: ['input validation'],
        recommended_policy: 'Validate the simulator input before evaluating.',
        blocked: false,
        requires_approval: false,
      });
    }
  };

  const handleApprovalDecision = (id: number, nextStatus: 'approved' | 'denied') => {
    setApprovalRows((current) =>
      current.map((approval) =>
        approval.id === id ? { ...approval, status: nextStatus } : approval,
      ),
    );
  };

  const handleLogin = (event: FormEvent) => {
    event.preventDefault();
    const name = loginForm.email.trim() || 'Operator';
    setOperatorName(name.split('@')[0] || 'Operator');
    setIsAuthenticated(true);
  };

  const handleWaitlistSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!waitlist.name.trim() || !waitlist.email.trim()) return;
    setWaitlistSubmitted(true);
  };

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_#fafaf9,_#f4f1ed_40%,_#ece8e3)] p-6">
        <div className="reveal-on-scroll grid w-full max-w-6xl gap-6 overflow-hidden rounded-[28px] border border-stone-200 bg-[#fffdfb] shadow-[0_24px_60px_rgba(41,37,36,0.12)] lg:grid-cols-[1.08fr_0.92fr]">
          <div className="bg-gradient-to-br from-[#f8f3ee] via-[#f4efe9] to-[#e9f3ee] p-8 text-stone-800">
            <div className="mb-8 flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
                <Shield size={22} />
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.28em] text-stone-500">AgentSafe</div>
                <div className="text-xl font-semibold text-stone-800">Traffic cop for AI teams</div>
              </div>
            </div>

            <div className="mb-5 text-[10px] uppercase tracking-[0.28em] text-emerald-700">Built for real people</div>
            <h1 className="max-w-md text-4xl font-semibold leading-tight text-stone-900">Keep your agents moving without the chaos.</h1>
            <p className="mt-4 max-w-md text-sm leading-7 text-stone-600">
              Built for founders, operators, and builders who want a calmer, safer way to ship AI without letting every tool run wild.
            </p>

            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              {[
                'For startup teams',
                'For builders',
                'For ops people',
                'For early adopters',
              ].map((item) => (
                <div key={item} className="rounded-2xl border border-stone-200 bg-white px-3 py-2 text-sm text-stone-700 shadow-[0_8px_18px_rgba(15,23,42,0.03)]">
                  {item}
                </div>
              ))}
            </div>

            <div className="mt-8 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
              No heavy setup. No fancy AI fluff. Just a clear system that tells you when to move, pause, or stop.
            </div>
          </div>

          <div className="p-8">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-[0.28em] text-stone-500">Admin access</div>
                <h2 className="mt-2 text-2xl font-semibold text-stone-800">Try the live control room</h2>
              </div>
              <div className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">Open demo</div>
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
              <label className="block">
                <span className="mb-2 block text-sm text-stone-600">Your name or email</span>
                <input
                  type="text"
                  value={loginForm.email}
                  onChange={(event) => setLoginForm({ ...loginForm, email: event.target.value })}
                  placeholder="alex@startup.com"
                  className="w-full rounded-xl border border-stone-200 bg-stone-50 px-3 py-3 text-stone-800 outline-none transition focus:border-stone-300"
                />
              </label>

              <label className="block">
                <span className="mb-2 block text-sm text-stone-600">Password</span>
                <input
                  type="password"
                  value={loginForm.password}
                  onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })}
                  placeholder="any password works for now"
                  className="w-full rounded-xl border border-stone-200 bg-stone-50 px-3 py-3 text-stone-800 outline-none transition focus:border-stone-300"
                />
              </label>

              <button
                type="submit"
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-stone-900 px-4 py-3 text-sm font-medium text-white transition hover:bg-stone-700"
              >
                Enter the dashboard
                <ArrowRight size={16} />
              </button>
            </form>

            <div className="mt-6 rounded-2xl border border-dashed border-stone-300 bg-stone-50 p-4 text-sm text-stone-600">
              This is an early MVP for contributors and startups. Anyone can access it now while we shape the product with real feedback.
            </div>

            <div className="mt-6 flex items-center justify-between rounded-2xl border border-stone-200 p-3 text-sm text-stone-600">
              <span>Want to contribute?</span>
              <button
                type="button"
                onClick={() => setLoginForm({ email: 'contributor@agentsafe.ai', password: 'demo' })}
                className="font-medium text-emerald-700"
              >
                Use contributor access
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f6f3ee] text-slate-700">
      <aside className="fixed inset-y-0 left-0 w-72 border-r border-stone-200 bg-[#fffdfb] p-5 shadow-[0_0_0_1px_rgba(0,0,0,0.02)]">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
            <Shield />
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-[0.28em] text-stone-500">AI Traffic Control</div>
            <div className="text-xl font-semibold text-stone-800">AgentSafe</div>
          </div>
        </div>

        <div className="mb-5 rounded-2xl border border-stone-200 bg-stone-50 p-3">
          <div className="text-[10px] uppercase tracking-[0.2em] text-stone-500">Signed in</div>
          <div className="mt-2 flex items-center justify-between">
            <span className="font-medium text-stone-800">{operatorName}</span>
            <button
              type="button"
              onClick={() => setIsAuthenticated(false)}
              className="flex items-center gap-1 text-xs text-stone-500 hover:text-stone-800"
            >
              <LogOut size={12} />
              Exit
            </button>
          </div>
        </div>

        <nav className="space-y-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setTab(item.id)}
              className={`w-full rounded-xl px-3 py-2.5 text-left text-sm font-medium transition ${
                tab === item.id ? 'bg-stone-900 text-white shadow-sm' : 'text-stone-600 hover:bg-stone-100'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="mt-8 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
          <div className="mb-2 flex items-center gap-2 text-emerald-700">
            <ShieldAlert size={16} />
            <span className="text-[10px] uppercase tracking-[0.22em]">Traffic Cop</span>
          </div>
          <p className="text-sm text-stone-600">Stop AI chaos before it hits production. AgentSafe gives every agent a green light, yellow warning, or red stop signal.</p>
        </div>
      </aside>

      <main className="ml-72 p-8">
        <header className="mb-8 flex items-center justify-between">
          <div>
            <p className="text-[10px] uppercase tracking-[0.26em] text-stone-500">Traffic control for AI work</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-stone-800">Calm the traffic. Keep the work moving.</h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="rounded-xl border border-emerald-200 bg-emerald-100 px-4 py-2 text-sm font-medium text-emerald-800">
              Live overview
            </div>
            <div className="rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm text-stone-600">
              Operator: {operatorName}
            </div>
          </div>
        </header>

        <section className="reveal-on-scroll mb-6 rounded-3xl border border-stone-200 bg-gradient-to-r from-[#f8f3ee] via-[#f3efe8] to-[#e6f5ee] p-6 text-stone-800 shadow-[0_18px_40px_rgba(12,18,24,0.08)]">
          <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-emerald-700">Built for people shipping AI</div>
          <h2 className="max-w-2xl text-2xl font-semibold leading-tight text-stone-900">
            Every agent gets a clear signal before it does something risky.
          </h2>
          <p className="mt-3 max-w-2xl text-sm text-stone-600">
            AgentSafe helps teams run AI without surprise failures. Green for go, yellow for review, red for stop.
          </p>
        </section>

        <section className="mb-8 grid gap-4 lg:grid-cols-4">
          {[
            {
              title: 'Instant risk visibility',
              text: 'See exactly what each agent is trying to do before it becomes a production problem.',
              icon: Shield,
              accent: 'emerald',
            },
            {
              title: 'Approval before damage',
              text: 'High-risk actions pause automatically and require a human decision instead of a surprise outage.',
              icon: SlidersHorizontal,
              accent: 'amber',
            },
            {
              title: 'No more AI blind spots',
              text: 'Catch sensitive tools, dangerous environments, and risky actions before they run unchecked.',
              icon: AlertTriangle,
              accent: 'rose',
            },
            {
              title: 'Built for real teams',
              text: 'Designed for operators, founders, and AI teams who need calm control instead of panic alerts.',
              icon: CheckCircle2,
              accent: 'sky',
            },
          ].map(({ title, text, icon: Icon, accent }) => (
            <div key={title} className="reveal-on-scroll soft-card rounded-2xl border border-stone-200 bg-white p-4 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
              <div className={`mb-3 inline-flex rounded-xl p-2 ${
                accent === 'emerald' ? 'bg-emerald-100 text-emerald-700' :
                accent === 'amber' ? 'bg-amber-100 text-amber-700' :
                accent === 'rose' ? 'bg-rose-100 text-rose-700' : 'bg-sky-100 text-sky-700'
              }`}>
                <Icon size={18} />
              </div>
              <h3 className="mb-2 text-base font-semibold text-stone-800">{title}</h3>
              <p className="text-sm leading-6 text-stone-600">{text}</p>
            </div>
          ))}
        </section>

        <section className="mb-8 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="reveal-on-scroll soft-card rounded-3xl border border-stone-200 bg-white p-6 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
            <div className="mb-3 text-[10px] uppercase tracking-[0.28em] text-emerald-700">Why teams use it</div>
            <h3 className="text-2xl font-semibold text-stone-900">The system every agent team needs before launch.</h3>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-stone-600">
              AgentSafe gives founders and operators a calm decision layer. Instead of guessing whether an agent should move, the team sees a simple signal and reacts with confidence.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <button className="rounded-xl bg-stone-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-stone-700">
                Request early access
              </button>
              <button className="rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-medium text-stone-700 transition hover:bg-stone-50">
                Join as contributor
              </button>
            </div>
          </div>

          <div className="reveal-on-scroll soft-card rounded-3xl border border-emerald-200 bg-emerald-50 p-6">
            <div className="text-[10px] uppercase tracking-[0.28em] text-emerald-700">Built for</div>
            <div className="mt-4 space-y-3">
              {['Founders shipping AI products', 'Technical contributors', 'Ops and safety teams', 'Early-stage AI startups'].map((item) => (
                <div key={item} className="flex items-center gap-3 rounded-2xl border border-emerald-100 bg-white px-3 py-2 text-sm text-stone-700">
                  <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500" />
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mb-8 rounded-3xl border border-stone-200 bg-white p-6 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
          <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-stone-500">About AgentSafe</div>
          <h3 className="text-2xl font-semibold text-stone-900">A simple control layer for AI work.</h3>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-stone-600">
            We built AgentSafe to make AI operations feel human again. When an agent is about to do something important, the system shows a clear signal — green to move, yellow to review, red to stop. That keeps teams safe, fast, and confident while they scale their AI workflows.
          </p>
        </section>

        <section className="reveal-on-scroll mb-8 rounded-3xl border border-stone-200 bg-gradient-to-r from-[#fdfcfb] via-[#f8f4ee] to-[#edf8f2] p-6 shadow-[0_18px_40px_rgba(12,18,24,0.05)]">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <div className="text-[10px] uppercase tracking-[0.28em] text-stone-500">What makes it different</div>
              <h3 className="mt-2 text-2xl font-semibold text-stone-900">Built to feel like a real operating system for AI teams.</h3>
            </div>
            <div className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[10px] uppercase tracking-[0.22em] text-emerald-700">
              Early access
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                title: 'Clear signal, not confusion',
                text: 'Operators get a fast green/yellow/red answer before a risky action turns into a launch problem.',
              },
              {
                title: 'Built for startup speed',
                text: 'Teams can move quickly without losing control. The system keeps the workflow calm and safe under pressure.',
              },
              {
                title: 'A real contributor path',
                text: 'This MVP is open for founders, builders, and contributors who want to help shape the product from day one.',
              },
            ].map((item) => (
              <div key={item.title} className="rounded-2xl border border-stone-200 bg-white p-4 shadow-[0_8px_20px_rgba(15,23,42,0.03)]">
                <div className="mb-3 h-10 w-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-semibold">•</div>
                <h4 className="mb-2 text-base font-semibold text-stone-800">{item.title}</h4>
                <p className="text-sm leading-6 text-stone-600">{item.text}</p>
              </div>
            ))}
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button className="rounded-xl bg-stone-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-stone-700">
              Request early access
            </button>
            <button className="rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-medium text-stone-700 transition hover:bg-stone-50">
              Become a contributor
            </button>
          </div>
        </section>

        <section className="mb-8 rounded-3xl border border-stone-200 bg-white p-6 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
          <div className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
            <div>
              <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-stone-500">Early access</div>
              <h3 className="text-2xl font-semibold text-stone-900">Join the first operators shipping AI safely.</h3>
              <p className="mt-3 max-w-xl text-sm leading-7 text-stone-600">
                We’re opening the first pilot seats for founders, operators, and builders who want a calmer way to run AI agents without losing control.
              </p>
            </div>

            <form onSubmit={handleWaitlistSubmit} className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
              {waitlistSubmitted ? (
                <div className="flex h-full min-h-[180px] flex-col items-center justify-center text-center">
                  <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                    <CheckCircle2 size={22} />
                  </div>
                  <div className="text-lg font-semibold text-stone-800">You’re on the list.</div>
                  <p className="mt-2 text-sm text-stone-600">We’ll reach out with access details and pilot onboarding soon.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <label className="block text-sm text-stone-600">
                      <span className="mb-1 block">Name</span>
                      <input
                        value={waitlist.name}
                        onChange={(event) => setWaitlist({ ...waitlist, name: event.target.value })}
                        className="w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-stone-800 outline-none focus:border-stone-300"
                        placeholder="Rohan Patel"
                      />
                    </label>
                    <label className="block text-sm text-stone-600">
                      <span className="mb-1 block">Role</span>
                      <input
                        value={waitlist.role}
                        onChange={(event) => setWaitlist({ ...waitlist, role: event.target.value })}
                        className="w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-stone-800 outline-none focus:border-stone-300"
                        placeholder="Founder / Operator"
                      />
                    </label>
                  </div>

                  <label className="block text-sm text-stone-600">
                    <span className="mb-1 block">Email</span>
                    <input
                      type="email"
                      value={waitlist.email}
                      onChange={(event) => setWaitlist({ ...waitlist, email: event.target.value })}
                      className="w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-stone-800 outline-none focus:border-stone-300"
                      placeholder="you@company.com"
                    />
                  </label>

                  <label className="block text-sm text-stone-600">
                    <span className="mb-1 block">Company</span>
                    <input
                      value={waitlist.company}
                      onChange={(event) => setWaitlist({ ...waitlist, company: event.target.value })}
                      className="w-full rounded-xl border border-stone-200 bg-white px-3 py-2.5 text-stone-800 outline-none focus:border-stone-300"
                      placeholder="Startup name"
                    />
                  </label>

                  <button
                    type="submit"
                    className="w-full rounded-xl bg-stone-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-stone-700"
                  >
                    Request early access
                  </button>
                </div>
              )}
            </form>
          </div>
        </section>

        <section className="mb-8 rounded-3xl border border-stone-200 bg-white p-6 shadow-[0_12px_26px_rgba(15,23,42,0.04)]">
          <div className="mb-5 text-[10px] uppercase tracking-[0.28em] text-stone-500">Simple pricing</div>
          <div className="mb-4 flex items-end justify-between gap-4">
            <h3 className="text-2xl font-semibold text-stone-900">Start small. Grow with guardrails.</h3>
            <div className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1 text-[10px] uppercase tracking-[0.22em] text-stone-600">
              Launch pricing
            </div>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            {[
              {
                name: 'Starter',
                price: '$29',
                copy: 'For solo founders and small AI teams who want a clear control layer without overhead.',
                points: ['1 workspace', 'Live agent signal board', 'Approval workflow'],
                featured: false,
              },
              {
                name: 'Pilot',
                price: '$99',
                copy: 'For growing teams running real agents in prod and needing a calmer safety workflow.',
                points: ['Unlimited agents', 'Team approvals', 'Audit timeline'],
                featured: true,
              },
              {
                name: 'Partner',
                price: 'Custom',
                copy: 'For startup teams and operators building custom agent infrastructures and safety policies.',
                points: ['Custom integrations', 'Policy tuning', 'Priority support'],
                featured: false,
              },
            ].map((plan) => (
              <div
                key={plan.name}
                className={`rounded-2xl border p-5 ${
                  plan.featured
                    ? 'border-emerald-200 bg-emerald-50 shadow-[0_12px_24px_rgba(16,185,129,0.10)]'
                    : 'border-stone-200 bg-white'
                }`}
              >
                <div className="mb-3 flex items-center justify-between">
                  <h4 className="text-lg font-semibold text-stone-800">{plan.name}</h4>
                  {plan.featured && <span className="rounded-full bg-emerald-100 px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-emerald-700">Popular</span>}
                </div>
                <div className="mb-3 text-3xl font-semibold text-stone-900">{plan.price}<span className="ml-1 text-sm text-stone-500">/mo</span></div>
                <p className="mb-4 text-sm leading-6 text-stone-600">{plan.copy}</p>
                <ul className="space-y-2 text-sm text-stone-700">
                  {plan.points.map((point) => (
                    <li key={point} className="flex items-center gap-2">
                      <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
                      {point}
                    </li>
                  ))}
                </ul>
                <button className={`mt-5 w-full rounded-xl px-4 py-2.5 text-sm font-medium transition ${
                  plan.featured ? 'bg-stone-900 text-white hover:bg-stone-700' : 'border border-stone-200 bg-white text-stone-700 hover:bg-stone-50'
                }`}>
                  {plan.featured ? 'Get pilot access' : 'Choose plan'}
                </button>
              </div>
            ))}
          </div>
        </section>

        <section className="mb-8 grid gap-4 md:grid-cols-3">
          {[
            {
              title: '1. Detect the move',
              text: 'Every action is checked the moment it appears, before it can trigger a production issue.',
            },
            {
              title: '2. Score the risk',
              text: 'The engine looks at tools, environment, and intent to decide whether the move is safe or unsafe.',
            },
            {
              title: '3. Signal the operator',
              text: 'The teammate sees green, yellow, or red instantly and decides whether the agent should continue.',
            },
          ].map((step) => (
            <div key={step.title} className="reveal-on-scroll soft-card rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
              <div className="mb-3 text-[10px] uppercase tracking-[0.22em] text-stone-500">Flow</div>
              <h3 className="mb-2 text-lg font-semibold text-stone-800">{step.title}</h3>
              <p className="text-sm leading-6 text-stone-600">{step.text}</p>
            </div>
          ))}
        </section>

        {tab === 'dashboard' && (
          <>
            <section className="mb-6 grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
                <div className="mb-2 flex items-center gap-3">
                  <span className="inline-block h-3 w-3 rounded-full bg-emerald-500" />
                  <span className="text-sm font-medium text-emerald-700">Green signal</span>
                </div>
                <div className="text-3xl font-semibold text-emerald-800">{stats?.allowed ?? 0}</div>
              </div>
              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
                <div className="mb-2 flex items-center gap-3">
                  <span className="inline-block h-3 w-3 rounded-full bg-amber-500" />
                  <span className="text-sm font-medium text-amber-700">Yellow signal</span>
                </div>
                <div className="text-3xl font-semibold text-amber-800">{stats?.pending_approval ?? 0}</div>
              </div>
              <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4">
                <div className="mb-2 flex items-center gap-3">
                  <span className="inline-block h-3 w-3 rounded-full bg-rose-500" />
                  <span className="text-sm font-medium text-rose-700">Red signal</span>
                </div>
                <div className="text-3xl font-semibold text-rose-800">{stats?.blocked ?? 0}</div>
              </div>
            </section>

            <section className="grid gap-4 md:grid-cols-4">
              {statsCards.map(({ label, value, icon: Icon }) => (
                <div key={label} className="rounded-2xl border border-stone-200 bg-white p-4 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
                  <div className="mb-4 flex items-center justify-between">
                    <span className="text-sm text-stone-500">{label}</span>
                    <Icon className="text-emerald-700" size={18} />
                  </div>
                  <div className="text-3xl font-semibold text-stone-800">{value ?? 0}</div>
                </div>
              ))}
            </section>

            <section className="mt-8 grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
              <div className="rounded-2xl border border-stone-200 bg-white p-4 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
                <div className="mb-4 flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-stone-800">Recent actions</h2>
                    <p className="text-sm text-stone-500">Latest activity from the security engine</p>
                  </div>
                  <span className="text-[10px] uppercase tracking-[0.22em] text-emerald-700">Audit</span>
                </div>

                <div className="overflow-hidden rounded-xl border border-stone-200">
                  <table className="min-w-full text-left text-sm">
                    <thead className="bg-stone-100 text-stone-600">
                      <tr>
                        <th className="px-4 py-3">Time</th>
                        <th className="px-4 py-3">Agent</th>
                        <th className="px-4 py-3">Action</th>
                        <th className="px-4 py-3">Risk</th>
                        <th className="px-4 py-3">Decision</th>
                      </tr>
                    </thead>
                    <tbody>
                      {actions?.map((item) => (
                        <tr key={item.id} className="border-t border-stone-200 text-stone-700">
                          <td className="px-4 py-3">{new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
                          <td className="px-4 py-3">{item.agent_name}</td>
                          <td className="px-4 py-3">{item.tool_name}</td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex rounded-full px-2 py-1 text-xs ${riskClasses[item.risk_level] ?? 'bg-stone-100 text-stone-700'}`}>
                              {item.risk_score}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`inline-flex rounded-full px-2 py-1 text-xs ${decisionClasses[item.decision] ?? 'bg-stone-100 text-stone-700'}`}>
                              {item.decision}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="rounded-2xl border border-stone-200 bg-white p-4 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
                <h2 className="mb-4 text-lg font-semibold text-stone-800">Risk distribution</h2>
                <div className="space-y-4">
                  {stats && Object.entries(stats.risk_distribution ?? {}).map(([level, value]) => (
                    <div key={level}>
                      <div className="mb-1 flex justify-between text-sm text-stone-600">
                        <span>{level}</span>
                        <span>{value}</span>
                      </div>
                      <div className="h-2.5 rounded-full bg-stone-100">
                        <div
                          className={`h-full rounded-full ${
                            level === 'LOW' ? 'bg-emerald-500' :
                            level === 'MEDIUM' ? 'bg-amber-500' :
                            level === 'HIGH' ? 'bg-orange-500' : 'bg-rose-500'
                          }`}
                          style={{ width: `${Math.min((value / Math.max(stats.total_actions, 1)) * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </>
        )}

        {tab === 'agents' && (
          <section className="grid gap-4 md:grid-cols-3">
            {agents.map((agent) => (
              <div key={agent.id} className="rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-stone-800">{agent.name}</h3>
                  <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-700">{agent.status}</span>
                </div>
                <p className="mb-4 text-sm text-stone-500">{agent.description}</p>
                <div className="flex justify-between text-sm text-stone-600">
                  <span>Actions today</span>
                  <strong>12</strong>
                </div>
                <div className="mt-2 flex justify-between text-sm text-stone-600">
                  <span>Risk events</span>
                  <strong>2</strong>
                </div>
              </div>
            ))}
          </section>
        )}

        {tab === 'tools' && (
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {tools.map((tool) => (
              <div key={tool.id} className="rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="font-semibold text-stone-800">{tool.name}</h3>
                  <span className={`rounded-full px-2 py-1 text-xs ${riskClasses[tool.sensitivity.toUpperCase()] ?? 'bg-stone-100 text-stone-700'}`}>{tool.sensitivity}</span>
                </div>
                <div className="space-y-2 text-sm text-stone-600">
                  <div className="flex justify-between"><span>Category</span><strong>{tool.category}</strong></div>
                  <div className="flex justify-between"><span>Operation</span><strong>{tool.operation}</strong></div>
                  <div className="flex justify-between"><span>Default risk</span><strong>{tool.default_risk}</strong></div>
                </div>
              </div>
            ))}
          </section>
        )}

        {tab === 'policies' && (
          <section className="grid gap-4 md:grid-cols-2">
            {policies.map((policy) => (
              <div key={policy.id} className="rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="font-semibold text-stone-800">{policy.name}</h3>
                  <span className={`rounded-full px-2 py-1 text-xs ${policy.effect === 'deny' ? 'bg-rose-100 text-rose-700' : policy.effect === 'require_approval' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                    {policy.effect}
                  </span>
                </div>
                <p className="text-sm text-stone-500">{policy.description}</p>
                <div className="mt-3 text-sm text-stone-600">Environment: {policy.environment}</div>
              </div>
            ))}
          </section>
        )}

        {tab === 'approvals' && (
          <section className="space-y-4">
            {approvalRows.map((approval) => (
              <div key={approval.id} className="rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
                <div className="mb-3 flex items-center justify-between">
                  <div>
                    <div className="text-lg font-semibold text-stone-800">{approval.agent_name}</div>
                    <div className="text-sm text-stone-500">{approval.requested_action}</div>
                  </div>
                  <span className={`rounded-full px-2 py-1 text-xs ${approval.status === 'approved' ? 'bg-emerald-100 text-emerald-700' : approval.status === 'denied' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'}`}>
                    {approval.status}
                  </span>
                </div>
                <p className="text-sm text-stone-600">Reason: {approval.reason}</p>
                <div className="mt-3 text-sm text-stone-500">Risk: {approval.risk_score}</div>

                {approval.status === 'pending' && (
                  <div className="mt-4 flex gap-3">
                    <button
                      onClick={() => handleApprovalDecision(approval.id, 'approved')}
                      className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-500"
                    >
                      Give green light
                    </button>
                    <button
                      onClick={() => handleApprovalDecision(approval.id, 'denied')}
                      className="rounded-xl bg-rose-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-rose-500"
                    >
                      Red light
                    </button>
                  </div>
                )}
              </div>
            ))}
          </section>
        )}

        {tab === 'simulator' && (
          <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
            <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
              <h2 className="mb-4 text-lg font-semibold text-stone-800">Simulate action</h2>
              <div className="space-y-4">
                <label className="block">
                  <span className="mb-2 block text-sm text-stone-600">Agent</span>
                  <select
                    className="w-full rounded-xl border border-stone-200 bg-stone-50 p-3 text-stone-700 outline-none ring-0 transition focus:border-stone-300"
                    value={simulator.agent}
                    onChange={(e) => setSimulator({ ...simulator, agent: e.target.value })}
                  >
                    <option value="support-agent">Support Agent</option>
                    <option value="research-agent">Research Agent</option>
                    <option value="deployment-agent">Deployment Agent</option>
                  </select>
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm text-stone-600">Tool</span>
                  <select
                    className="w-full rounded-xl border border-stone-200 bg-stone-50 p-3 text-stone-700 outline-none transition focus:border-stone-300"
                    value={simulator.tool}
                    onChange={(e) => setSimulator({ ...simulator, tool: e.target.value })}
                  >
                    <option value="web.search">web.search</option>
                    <option value="read_file">read_file</option>
                    <option value="database.read">database.read</option>
                    <option value="database.write">database.write</option>
                    <option value="database.delete_user">database.delete_user</option>
                    <option value="send_email">send_email</option>
                    <option value="deploy">deploy</option>
                    <option value="send_money">send_money</option>
                  </select>
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm text-stone-600">Environment</span>
                  <select
                    className="w-full rounded-xl border border-stone-200 bg-stone-50 p-3 text-stone-700 outline-none transition focus:border-stone-300"
                    value={simulator.environment}
                    onChange={(e) => setSimulator({ ...simulator, environment: e.target.value })}
                  >
                    <option value="development">development</option>
                    <option value="staging">staging</option>
                    <option value="production">production</option>
                  </select>
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm text-stone-600">Arguments (JSON)</span>
                  <textarea
                    className="min-h-[130px] w-full rounded-xl border border-stone-200 bg-stone-50 p-3 text-stone-700 outline-none transition focus:border-stone-300"
                    value={simulator.argumentsText}
                    onChange={(e) => setSimulator({ ...simulator, argumentsText: e.target.value })}
                  />
                </label>

                <button
                  onClick={handleAnalyze}
                  className="w-full rounded-xl bg-stone-900 px-4 py-3 font-medium text-white transition hover:bg-stone-700"
                >
                  Analyze Action
                </button>
              </div>
            </div>

            <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_8px_22px_rgba(15,23,42,0.04)]">
              {result ? (
                <>
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-stone-800">Result</h2>
                      <div className="text-sm text-stone-500">{result.agent} • {result.tool}</div>
                    </div>
                    <span className={`rounded-full px-2 py-1 text-xs ${decisionClasses[result.decision] ?? 'bg-stone-100 text-stone-700'}`}>
                      {result.decision}
                    </span>
                  </div>

                  <div className="mb-4 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-xl border border-stone-200 bg-stone-50 p-3">
                      <div className="text-[10px] uppercase tracking-[0.2em] text-stone-500">Risk score</div>
                      <div className="mt-2 text-2xl font-semibold text-stone-800">{result.risk_score} / 100</div>
                    </div>
                    <div className="rounded-xl border border-stone-200 bg-stone-50 p-3">
                      <div className="text-[10px] uppercase tracking-[0.2em] text-stone-500">Risk level</div>
                      <div className="mt-2 text-2xl font-semibold text-stone-800">{result.risk_level}</div>
                    </div>
                  </div>

                  <div className="rounded-xl border border-stone-200 bg-stone-50 p-3 text-sm text-stone-700">
                    <div className="mb-2 font-medium text-stone-800">Explanation</div>
                    {result.explanation}
                  </div>

                  <div className="mt-4 rounded-xl border border-stone-200 bg-stone-50 p-3 text-sm">
                    <div className="mb-2 font-medium text-stone-800">Risk factors</div>
                    <ul className="list-disc space-y-1 pl-5 text-stone-600">
                      {result.risk_factors.map((factor) => <li key={factor}>{factor}</li>)}
                    </ul>
                  </div>

                  <div className="mt-4 rounded-xl border border-dashed border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
                    Recommended policy: {result.recommended_policy}
                  </div>
                </>
              ) : (
                <div className="flex h-full min-h-[280px] items-center justify-center rounded-xl border border-dashed border-stone-300 text-stone-500">
                  Analyze an action to inspect the decision.
                </div>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
