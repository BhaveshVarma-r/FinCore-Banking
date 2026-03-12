"use client"

import { useState } from "react"
import { PlayCircle, RefreshCw, Home } from "lucide-react"
import Link from "next/link"
import axios from "axios"
import StatsBar from "./components/StatsBar"
import LatencyChart from "./components/LatencyChart"
import ScenarioCard from "./components/ScenarioCard"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface ScenarioResult {
  scenario_id: number
  name: string
  query: string
  expected_agents: string[]
  actual_agents?: string[]
  status: "idle" | "running" | "passed" | "failed" | "error"
  latency_ms?: number
  within_sla?: boolean
  response?: string
  mcp_calls?: any[]
  kg_queries?: string[]
  agent_outputs?: Record<string, any>
  error?: string
  risk_level?: string
  requires_human?: boolean
  critique_score?: number
  critique_passed?: boolean
  planner_plan?: any
}

const INITIAL: ScenarioResult[] = [
  { scenario_id: 1, name: "Account Balance and Transactions", query: "What is my current account balance and my last 5 transactions?", expected_agents: ["account"], status: "idle" },
  { scenario_id: 2, name: "Home Loan Eligibility", query: "Am I eligible for a Rs.20 lakh home loan given my current EMIs?", expected_agents: ["loan", "account"], status: "idle" },
  { scenario_id: 3, name: "Fraud Transaction Dispute", query: "I see a transaction I didn't make, Rs.45,000 to an unknown account. Please help!", expected_agents: ["fraud"], status: "idle" },
  { scenario_id: 4, name: "MSME Loan Documents", query: "What documents do I need for an MSME loan and what are the RBI rules?", expected_agents: ["compliance", "loan"], status: "idle" },
  { scenario_id: 5, name: "Account Upgrade", query: "I want to upgrade my savings account to a premium account. What are the benefits?", expected_agents: ["account", "compliance"], status: "idle" },
  { scenario_id: 6, name: "Missing Transfer", query: "My friend transferred money to me but it has not reflected. My balance looks wrong.", expected_agents: ["account", "fraud"], status: "idle" },
  { scenario_id: 7, name: "Personal Loan with Car Loan", query: "Can I get a personal loan? I already have a car loan.", expected_agents: ["loan", "compliance"], status: "idle" },
  { scenario_id: 8, name: "Inactive Accounts", query: "Show me all accounts I own and tell me which ones have been inactive for over 6 months.", expected_agents: ["account"], status: "idle" },
]

export default function DemoPage() {
  const [scenarios, setScenarios] = useState<ScenarioResult[]>(INITIAL)
  const [customerId, setCustomerId] = useState("CUST1001")
  const [runningAll, setRunningAll] = useState(false)
  const [runningId, setRunningId] = useState<number | null>(null)

  const runOne = async (id: number) => {
    setRunningId(id)
    setScenarios(prev => prev.map(s =>
      s.scenario_id === id ? { ...s, status: "running" } : s
    ))
    try {
      const res = await axios.post(`${API_URL}/api/test-scenarios/run`, {
        scenario_id: id, customer_id: customerId,
      })
      const { result, latency_ms, within_sla } = res.data
      setScenarios(prev => prev.map(s => {
        if (s.scenario_id !== id) return s
        return {
          ...s,
          status: result.success ? "passed" : "failed",
          latency_ms,
          within_sla,
          actual_agents: result.agents_invoked || [],
          response: result.response,
          mcp_calls: result.mcp_calls_log || [],
          kg_queries: result.kg_queries_log || [],
          agent_outputs: result.agent_outputs,
          risk_level: result.risk_level,
          requires_human: result.requires_human,
          critique_score: result.critique_result?.overall_score,
          critique_passed: result.critique_result?.passes,
          planner_plan: result.planner_plan,
          error: result.success ? undefined : result.error,
        }
      }))
    } catch (err: any) {
      setScenarios(prev => prev.map(s =>
        s.scenario_id === id ? { ...s, status: "error", error: err.message } : s
      ))
    } finally {
      setRunningId(null)
    }
  }

  const runAll = async () => {
    setRunningAll(true)
    for (const s of scenarios) {
      await runOne(s.scenario_id)
      await new Promise(r => setTimeout(r, 300))
    }
    setRunningAll(false)
  }

  const reset = () => setScenarios(INITIAL)

  const ran = scenarios.filter(s => s.latency_ms !== undefined)
  const passed = scenarios.filter(s => s.status === "passed").length
  const failed = scenarios.filter(s => s.status === "failed" || s.status === "error").length
  const withinSla = ran.filter(s => s.within_sla).length
  const avgLatency = ran.length ? ran.reduce((a, s) => a + (s.latency_ms || 0), 0) / ran.length : 0
  const avgCritique = ran.filter(s => s.critique_score).length
    ? ran.filter(s => s.critique_score).reduce((a, s) => a + (s.critique_score || 0), 0) / ran.filter(s => s.critique_score).length
    : 0

  const chartData = ran.map(s => ({
    name: `S${s.scenario_id}`,
    latency: s.latency_ms || 0,
    passed: s.status === "passed",
  }))

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="fincore-gradient text-white">
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">FinCore Test Suite</h1>
            <p className="text-white/60 text-sm">
              8 Integration Scenarios with Audit Trail, Planner Plans, and Critique Scores
            </p>
          </div>
          <Link href="/"
            className="flex items-center gap-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg px-4 py-2 text-sm transition-all">
            <Home className="w-4 h-4" /> Chat
          </Link>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <StatsBar
          passed={passed} failed={failed} withinSla={withinSla}
          avgLatency={avgLatency} avgCritiqueScore={avgCritique}
          totalRan={ran.length}
        />

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 mb-6 flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-600 font-medium">Customer ID:</label>
            <input type="text" value={customerId} onChange={e => setCustomerId(e.target.value)}
              className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm w-32 focus:outline-none focus:ring-2 focus:ring-indigo-500/30" />
          </div>
          <button onClick={runAll} disabled={runningAll}
            className="flex items-center gap-2 px-4 py-2 fincore-gradient text-white rounded-lg text-sm font-medium disabled:opacity-50 hover:shadow-md transition-all">
            {runningAll ? <RefreshCw className="w-4 h-4 animate-spin" /> : <PlayCircle className="w-4 h-4" />}
            {runningAll ? "Running..." : "Run All 8 Scenarios"}
          </button>
          <button onClick={reset} disabled={runningAll}
            className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-lg text-sm transition-all">
            <RefreshCw className="w-4 h-4" /> Reset
          </button>
        </div>

        <LatencyChart data={chartData} />

        <div className="grid md:grid-cols-2 gap-4">
          {scenarios.map(s => (
            <ScenarioCard
              key={s.scenario_id}
              scenario={s}
              customerId={customerId}
              onRun={runOne}
              running={runningAll || runningId === s.scenario_id}
            />
          ))}
        </div>
      </div>
    </div>
  )
}