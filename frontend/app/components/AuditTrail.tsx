"use client"

import { useState } from "react"
import {
  ChevronDown, ChevronRight, Database, Zap,
  Bot, CheckCircle, XCircle, Clock, Shield
} from "lucide-react"

interface AuditTrailProps {
  sessionId: string
  mcpCalls?: any[]
  kgQueries?: string[]
  agentOutputs?: Record<string, any>
  plannerPlan?: any
  critiqueResult?: any
}

export default function AuditTrail({
  sessionId,
  mcpCalls = [],
  kgQueries = [],
  agentOutputs = {},
  plannerPlan,
  critiqueResult,
}: AuditTrailProps) {
  const [open, setOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<
    "planner" | "mcp" | "kg" | "agents" | "critique"
  >("planner")

  const total = mcpCalls.length + kgQueries.length
  if (total === 0 && !plannerPlan && !critiqueResult) return null

  const tabs = [
    { id: "planner", label: "Planner", count: plannerPlan ? 1 : 0 },
    { id: "mcp", label: "MCP Calls", count: mcpCalls.length },
    { id: "kg", label: "KG Queries", count: kgQueries.length },
    { id: "agents", label: "Agents", count: Object.keys(agentOutputs).length },
    { id: "critique", label: "Critique", count: critiqueResult ? 1 : 0 },
  ] as const

  return (
    <div className="mt-3 border border-slate-200 rounded-xl overflow-hidden bg-white">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-slate-50 hover:bg-slate-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-indigo-500" />
          <span className="text-sm font-semibold text-slate-700">Audit Trail</span>
          <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
            {total} operations
          </span>
          <span className="text-xs text-slate-400">Session: {sessionId.slice(0, 8)}...</span>
        </div>
        {open
          ? <ChevronDown className="w-4 h-4 text-slate-400" />
          : <ChevronRight className="w-4 h-4 text-slate-400" />
        }
      </button>

      {open && (
        <div>
          {/* Tabs */}
          <div className="flex border-b border-slate-100 bg-white overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium
                  border-b-2 transition-colors whitespace-nowrap
                  ${activeTab === tab.id
                    ? "border-indigo-500 text-indigo-700 bg-indigo-50"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                  }
                `}
              >
                {tab.label}
                {tab.count > 0 && (
                  <span className={`
                    px-1.5 py-0.5 rounded-full text-xs
                    ${activeTab === tab.id
                      ? "bg-indigo-200 text-indigo-700"
                      : "bg-slate-100 text-slate-500"
                    }
                  `}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          <div className="p-4 max-h-64 overflow-y-auto">
            {/* Planner Tab */}
            {activeTab === "planner" && plannerPlan && (
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="bg-indigo-50 rounded-lg p-2">
                    <p className="text-slate-500">Complexity</p>
                    <p className="font-semibold text-indigo-700 capitalize">
                      {plannerPlan.query_complexity || "N/A"}
                    </p>
                  </div>
                  <div className="bg-indigo-50 rounded-lg p-2">
                    <p className="text-slate-500">Steps</p>
                    <p className="font-semibold text-indigo-700">
                      {plannerPlan.execution_plan?.length || 0}
                    </p>
                  </div>
                  <div className="bg-indigo-50 rounded-lg p-2">
                    <p className="text-slate-500">Multi-Agent</p>
                    <p className="font-semibold text-indigo-700">
                      {plannerPlan.requires_multiple_agents ? "Yes" : "No"}
                    </p>
                  </div>
                </div>

                {plannerPlan.execution_plan?.map((step: any, i: number) => (
                  <div key={i} className="flex items-start gap-3 bg-slate-50 rounded-lg p-3">
                    <div className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
                      {step.step}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-indigo-600 capitalize">
                          [{step.agent}]
                        </span>
                        <span className="text-xs text-slate-600">{step.action}</span>
                      </div>
                      {step.depends_on?.length > 0 && (
                        <p className="text-xs text-slate-400 mt-0.5">
                          Depends on steps: {step.depends_on.join(", ")}
                        </p>
                      )}
                    </div>
                  </div>
                ))}

                {plannerPlan.reasoning && (
                  <div className="bg-amber-50 rounded-lg p-3">
                    <p className="text-xs font-medium text-amber-700 mb-1">Planner Reasoning</p>
                    <p className="text-xs text-amber-600">{plannerPlan.reasoning}</p>
                  </div>
                )}
              </div>
            )}

            {/* MCP Calls Tab */}
            {activeTab === "mcp" && (
              <div className="space-y-2">
                {mcpCalls.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-4">No MCP calls logged</p>
                ) : (
                  mcpCalls.map((call: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 bg-slate-50 rounded-lg p-3">
                      <div className={`
                        w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5
                        ${call.success ? "bg-green-100" : "bg-red-100"}
                      `}>
                        {call.success
                          ? <CheckCircle className="w-3 h-3 text-green-600" />
                          : <XCircle className="w-3 h-3 text-red-600" />
                        }
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-xs font-semibold text-indigo-700">
                            {call.server}
                          </span>
                          <span className="text-slate-400">→</span>
                          <span className="font-mono text-xs text-slate-700">{call.tool}</span>
                          <span className="text-xs text-slate-400 bg-slate-100 px-1.5 rounded">
                            via {call.agent}
                          </span>
                        </div>
                        {call.params && Object.keys(call.params).length > 0 && (
                          <p className="text-xs text-slate-500 mt-0.5 font-mono">
                            params: {JSON.stringify(call.params).slice(0, 80)}
                          </p>
                        )}
                        {call.error && (
                          <p className="text-xs text-red-500 mt-0.5">{call.error}</p>
                        )}
                      </div>
                      <span className="text-xs text-slate-400 flex-shrink-0">
                        {call.timestamp?.slice(11, 19)}
                      </span>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* KG Queries Tab */}
            {activeTab === "kg" && (
              <div className="space-y-2">
                {kgQueries.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-4">No KG queries logged</p>
                ) : (
                  kgQueries.map((q: string, i: number) => (
                    <div key={i} className="bg-purple-50 rounded-lg p-3 flex items-start gap-2">
                      <Zap className="w-3.5 h-3.5 text-purple-500 flex-shrink-0 mt-0.5" />
                      <p className="text-xs font-mono text-purple-700 break-all">{q}</p>
                    </div>
                  ))
                )}
              </div>
            )}

            {/* Agents Tab */}
            {activeTab === "agents" && (
              <div className="space-y-2">
                {Object.entries(agentOutputs).map(([name, output]: [string, any]) => (
                  <div key={name} className="bg-slate-50 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <Bot className="w-3.5 h-3.5 text-indigo-500" />
                      <span className="text-xs font-semibold text-slate-700 capitalize">
                        {name} Agent
                      </span>
                    </div>
                    {typeof output === "object" && output !== null && (
                      <div className="text-xs text-slate-500 space-y-0.5">
                        {output.risk_level && (
                          <p>Risk: <span className="font-medium">{output.risk_level}</span></p>
                        )}
                        {output.case_id && (
                          <p>Case ID: <span className="font-mono font-medium">{output.case_id}</span></p>
                        )}
                        {output.loan_type && (
                          <p>Loan type: <span className="font-medium capitalize">{output.loan_type}</span></p>
                        )}
                        {typeof output.eligible === "boolean" && (
                          <p>Eligible: <span className={`font-medium ${output.eligible ? "text-green-600" : "text-red-600"}`}>
                            {output.eligible ? "Yes" : "No"}
                          </span></p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Critique Tab */}
            {activeTab === "critique" && critiqueResult && (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className={`
                    flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold
                    ${critiqueResult.passes
                      ? "bg-green-100 text-green-700"
                      : "bg-red-100 text-red-700"
                    }
                  `}>
                    {critiqueResult.passes
                      ? <CheckCircle className="w-4 h-4" />
                      : <XCircle className="w-4 h-4" />
                    }
                    {critiqueResult.passes ? "PASSED" : "FAILED"}
                  </div>
                  <div className="text-2xl font-bold text-slate-700">
                    {critiqueResult.overall_score}
                    <span className="text-sm font-normal text-slate-400">/100</span>
                  </div>
                </div>

                {critiqueResult.scores && Object.keys(critiqueResult.scores).length > 0 && (
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(critiqueResult.scores).map(([key, val]: [string, any]) => (
                      <div key={key} className="bg-slate-50 rounded-lg p-2">
                        <p className="text-xs text-slate-500 capitalize">
                          {key.replace(/_/g, " ")}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="flex-1 bg-slate-200 rounded-full h-1.5">
                            <div
                              className={`h-1.5 rounded-full ${
                                val >= 7 ? "bg-green-500" :
                                val >= 5 ? "bg-yellow-500" : "bg-red-500"
                              }`}
                              style={{ width: `${(val / 10) * 100}%` }}
                            />
                          </div>
                          <span className="text-xs font-semibold text-slate-700">{val}/10</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {critiqueResult.issues?.length > 0 && (
                  <div className="bg-orange-50 rounded-lg p-3">
                    <p className="text-xs font-semibold text-orange-700 mb-1.5">Issues Found</p>
                    <ul className="space-y-1">
                      {critiqueResult.issues.map((issue: string, i: number) => (
                        <li key={i} className="text-xs text-orange-600 flex items-start gap-1.5">
                          <span className="mt-0.5">-</span> {issue}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {critiqueResult.hallucinations_detected?.length > 0 && (
                  <div className="bg-red-50 rounded-lg p-3">
                    <p className="text-xs font-semibold text-red-700 mb-1">
                      Hallucinations Detected
                    </p>
                    {critiqueResult.hallucinations_detected.map((h: string, i: number) => (
                      <p key={i} className="text-xs text-red-600">- {h}</p>
                    ))}
                  </div>
                )}

                {critiqueResult.compliance_violations?.length > 0 && (
                  <div className="bg-red-50 rounded-lg p-3">
                    <p className="text-xs font-semibold text-red-700 mb-1 flex items-center gap-1">
                      <Shield className="w-3 h-3" /> Compliance Violations
                    </p>
                    {critiqueResult.compliance_violations.map((v: string, i: number) => (
                      <p key={i} className="text-xs text-red-600">- {v}</p>
                    ))}
                  </div>
                )}

                {critiqueResult.feedback && (
                  <div className="bg-blue-50 rounded-lg p-3">
                    <p className="text-xs font-semibold text-blue-700 mb-1">Feedback</p>
                    <p className="text-xs text-blue-600">{critiqueResult.feedback}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}