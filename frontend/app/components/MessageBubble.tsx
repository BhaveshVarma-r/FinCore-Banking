"use client"

import ReactMarkdown from "react-markdown"
import { Bot, User } from "lucide-react"
import MetadataPanel from "./MetadataPanel"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  metadata?: {
    session_id?: string
    agents_invoked?: string[]
    risk_level?: string
    latency_ms?: number
    mcp_calls?: any[]
    kg_queries?: string[]
    requires_human?: boolean
    critique_score?: number
    critique_passed?: boolean
    query_complexity?: string
    planner_plan?: any
    agent_outputs?: Record<string, any>
    critique_result?: any
  }
}

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user"
  const m = message.metadata

  return (
    <div className={`flex gap-3 animate-slide-in ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div className={`
        w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1
        ${isUser ? "bg-indigo-600" : "fincore-gradient"} text-white
      `}>
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      <div className={`max-w-2xl flex flex-col ${isUser ? "items-end" : "items-start"}`}>
        {isUser ? (
          <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-3">
            <p className="text-sm">{message.content}</p>
          </div>
        ) : (
          <div className="bg-white border border-slate-100 shadow-sm rounded-2xl rounded-tl-sm px-4 py-3 w-full">
            <div className="prose text-sm text-slate-800">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>

            {m && (
              <MetadataPanel
                sessionId={m.session_id}
                agentsInvoked={m.agents_invoked || []}
                riskLevel={m.risk_level}
                latencyMs={m.latency_ms}
                mcpCalls={m.mcp_calls || []}
                kgQueries={m.kg_queries || []}
                requiresHuman={m.requires_human}
                critiqueScore={m.critique_score}
                critiquePassed={m.critique_passed}
                queryComplexity={m.query_complexity}
                plannerPlan={m.planner_plan}
                agentOutputs={m.agent_outputs || {}}
                critiqueResult={m.critique_result}
              />
            )}
          </div>
        )}
        <span className="text-xs text-slate-400 mt-1 px-1">
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit", minute: "2-digit"
          })}
        </span>
      </div>
    </div>
  )
}