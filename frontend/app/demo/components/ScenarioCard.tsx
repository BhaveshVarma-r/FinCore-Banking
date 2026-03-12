"use client"

import { useState } from "react"
import ReactMarkdown from "react-markdown"
import {
  PlayCircle, RefreshCw, CheckCircle, XCircle,
  AlertTriangle, Clock, ChevronDown, ChevronRight,
  Database, Zap, Star
} from "lucide-react"

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

const AGENT_COLORS: Record<string, string> = {
  account: "#6366f1", loan: "#10b981", fraud: "#ef4444", compliance: "#8b5cf6"
}

function AuditTrail({ mcp_calls, kg_queries, planner_plan }: {
  mcp_calls?: any[]
  kg_queries?: string[]
  planner_plan?: any
}) {
  const [open, setOpen] = useState(false)
  const total = (mcp_calls?.length || 0) + (kg_queries?.length || 0)
  if (total === 0 && !planner_plan) return null

  return (
    <div className="mt-3 border border-slate-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2 bg-slate-50 hover:bg-slate-100 transition-colors text-xs font-medium text-slate-600"
      >
        <div className="flex items-center gap-2">
          <Database className="w-3.5 h-3.5 text-indigo-500" />
          Audit Trail
          <span className="bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded-full">
            {total} ops
          </span>
        </div>
        {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
      </button>

      {open && (
        <div className="p-3 space-y-3">
          {planner_plan?.execution_plan && (
            <div>
              <p className="text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wide">
                Planner Execution Plan
              </p>
              <div className="space-y-1">
                {planner_plan.execution_plan.map((step: any, i: number) => (
                  <div key={i} className="bg-indigo-50 rounded p-2 text-xs">
                    <span className="font-medium text-indigo-700">Step {step.step}:</span>
                    <span className="text-indigo-600 ml-1">[{step.agent}]</span>
                    <span className="text-slate-600 ml-1">{step.action}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {mcp_calls && mcp_calls.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wide flex items-center gap-1">
                <Database className="w-3 h-3" /> MCP Calls ({mcp_calls.length})
              </p>
              <div className="space-y-1">
                {mcp_calls.map((c: any, i: number) => (
                  <div key={i} className="font-mono text-xs bg-slate-50 rounded p-2 flex justify-between">
                    <span className="text-indigo-700">{c.server} / {c.tool}</span>
                    <span className={c.success ? "text-green-600" : "text-red-600"}>
                      {c.success ? "OK" : "ERR"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {kg_queries && kg_queries.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-500 mb-1.5 uppercase tracking-wide flex items-center gap-1">
                <Zap className="w-3 h-3" /> KG Queries ({kg_queries.length})
              </p>
              <div className="space-y-1">
                {kg_queries.map((q: string, i: number) => (
                  <div key={i} className="font-mono text-xs bg-purple-50 text-purple-700 rounded p-2">
                    {q.length > 80 ? q.slice(0, 80) + "..." : q}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ScenarioCard({
  scenario, customerId, onRun, running
}: {
  scenario: ScenarioResult
  customerId: string
  onRun: (id: number) => void
  running: boolean
}) {
  const [showResponse, setShowResponse] = useState(false)

  const statusIcon = {
    idle: <PlayCircle className="w-4 h-4 text-slate-400" />,
    running: <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />,
    passed: <CheckCircle className="w-4 h-4 text-green-500" />,
    failed: <XCircle className="w-4 h-4 text-red-500" />,
    error: <AlertTriangle className="w-4 h-4 text-orange-500" />,
  }[scenario.status]

  const cardBorder = {
    idle: "border-slate-200",
    running: "border-blue-200",
    passed: "border-green-200",
    failed: "border-red-200",
    error: "border-orange-200",
  }[scenario.status]

  return (
    <div className={`bg-white rounded-xl border ${cardBorder} shadow-sm overflow-hidden`}>
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {statusIcon}
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-indigo-600">#{scenario.scenario_id}</span>
                <h3 className="font-semibold text-slate-800 text-sm truncate">{scenario.name}</h3>
              </div>
              <p className="text-xs text-slate-500 mt-0.5 truncate">{scenario.query}</p>
            </div>
          </div>
          <button
            onClick={() => onRun(scenario.scenario_id)}
            disabled={running || scenario.status === "running"}
            className="flex items-center gap-1.5 px-3 py-1.5 fincore-gradient text-white text-xs font-medium rounded-lg disabled:opacity-50 hover:shadow-md transition-all flex-shrink-0"
          >
            {scenario.status === "running"
              ? <RefreshCw className="w-3 h-3 animate-spin" />
              : <PlayCircle className="w-3 h-3" />
            }
            Run
          </button>
        </div>

        <div className="mt-2 flex flex-wrap gap-1">
          {scenario.expected_agents.map(a => (
            <span key={a} className="text-xs px-1.5 py-0.5 rounded border"
              style={{ color: AGENT_COLORS[a], borderColor: AGENT_COLORS[a] + "50",
                       backgroundColor: AGENT_COLORS[a] + "10" }}>
              {a}
            </span>
          ))}
        </div>

        {scenario.status !== "idle" && (
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            {scenario.latency_ms !== undefined && (
              <span className={`flex items-center gap-1 ${scenario.within_sla ? "text-green-600" : "text-red-600"}`}>
                <Clock className="w-3 h-3" />
                {scenario.latency_ms}ms {scenario.within_sla ? "✅" : "⚠️"}
              </span>
            )}
            {scenario.critique_score !== undefined && (
              <span className={`flex items-center gap-1 ${scenario.critique_passed ? "text-green-600" : "text-orange-600"}`}>
                <Star className="w-3 h-3" />
                {scenario.critique_score}/100
              </span>
            )}
            {scenario.requires_human && (
              <span className="text-red-600 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Escalated
              </span>
            )}
          </div>
        )}

        {scenario.response && (
          <div className="mt-2">
            <button
              onClick={() => setShowResponse(!showResponse)}
              className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
            >
              {showResponse ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              {showResponse ? "Hide response" : "View response"}
            </button>
            {showResponse && (
              <div className="mt-2 p-3 bg-slate-50 rounded-lg text-xs max-h-40 overflow-y-auto prose">
                <ReactMarkdown>{scenario.response}</ReactMarkdown>
              </div>
            )}
          </div>
        )}

        {scenario.error && (
          <div className="mt-2 p-2 bg-red-50 rounded text-xs text-red-600">
            {scenario.error}
          </div>
        )}

        {scenario.status === "passed" && (
          <AuditTrail
            mcp_calls={scenario.mcp_calls}
            kg_queries={scenario.kg_queries}
            planner_plan={scenario.planner_plan}
          />
        )}
      </div>
    </div>
  )
}