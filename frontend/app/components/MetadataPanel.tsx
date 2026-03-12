"use client"

import { useState } from "react"
import { ChevronDown, ChevronRight } from "lucide-react"
import AuditTrail from "./AuditTrail"

interface MetadataProps {
  sessionId?: string
  agentsInvoked?: string[]
  riskLevel?: string
  latencyMs?: number
  mcpCalls?: any[]
  kgQueries?: string[]
  requiresHuman?: boolean
  critiqueScore?: number
  critiquePassed?: boolean
  queryComplexity?: string
  plannerPlan?: any
  agentOutputs?: Record<string, any>
  critiqueResult?: any
}

export default function MetadataPanel({
  sessionId = "",
  agentsInvoked = [],
  riskLevel = "low",
  latencyMs,
  mcpCalls = [],
  kgQueries = [],
  requiresHuman = false,
  critiqueScore,
  critiquePassed,
  queryComplexity,
  plannerPlan,
  agentOutputs = {},
  critiqueResult,
}: MetadataProps) {
  const [open, setOpen] = useState(false)

  if (agentsInvoked.length === 0 && !latencyMs) return null

  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600 transition-colors"
      >
        {open
          ? <ChevronDown className="w-3 h-3" />
          : <ChevronRight className="w-3 h-3" />
        }
        View response details
      </button>

      {open && (
        <div className="mt-2 space-y-1">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs grid grid-cols-2 gap-x-6 gap-y-1.5">
            {latencyMs !== undefined && (
              <>
                <span className="text-slate-500">Latency</span>
                <span className={`font-medium ${latencyMs < 4000 ? "text-green-600" : "text-red-600"}`}>
                  {latencyMs}ms {latencyMs < 4000 ? "✅ within SLA" : "⚠️ over SLA"}
                </span>
              </>
            )}
            {agentsInvoked.length > 0 && (
              <>
                <span className="text-slate-500">Agents invoked</span>
                <span className="font-medium">{agentsInvoked.join(", ")}</span>
              </>
            )}
            {queryComplexity && (
              <>
                <span className="text-slate-500">Query complexity</span>
                <span className="font-medium capitalize">{queryComplexity}</span>
              </>
            )}
            {critiqueScore !== undefined && (
              <>
                <span className="text-slate-500">Critique score</span>
                <span className={`font-medium ${critiquePassed ? "text-green-600" : "text-orange-600"}`}>
                  {critiqueScore}/100 {critiquePassed ? "✅" : "⚠️"}
                </span>
              </>
            )}
            {mcpCalls.length > 0 && (
              <>
                <span className="text-slate-500">MCP calls</span>
                <span className="font-medium">{mcpCalls.length}</span>
              </>
            )}
            {kgQueries.length > 0 && (
              <>
                <span className="text-slate-500">KG queries</span>
                <span className="font-medium">{kgQueries.length}</span>
              </>
            )}
            {riskLevel && riskLevel !== "low" && (
              <>
                <span className="text-slate-500">Risk level</span>
                <span className={`font-medium capitalize ${
                  riskLevel === "critical" ? "text-red-700" :
                  riskLevel === "high" ? "text-orange-600" :
                  "text-yellow-600"
                }`}>{riskLevel}</span>
              </>
            )}
            {requiresHuman && (
              <>
                <span className="text-slate-500">Escalation</span>
                <span className="font-medium text-red-600">Human review triggered</span>
              </>
            )}
          </div>

          <AuditTrail
            sessionId={sessionId}
            mcpCalls={mcpCalls}
            kgQueries={kgQueries}
            agentOutputs={agentOutputs}
            plannerPlan={plannerPlan}
            critiqueResult={critiqueResult}
          />
        </div>
      )}
    </div>
  )
}