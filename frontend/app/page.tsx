"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Loader2, Menu, Activity } from "lucide-react"
import axios from "axios"
import Sidebar from "./components/Sidebar"
import MessageBubble from "./components/MessageBubble"
import LoadingIndicator from "./components/LoadingIndicator"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

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

const WELCOME: Message = {
  id: "0",
  role: "assistant",
  content: `**Welcome to FinCore Banking Assistant v2!**

I have a full multi-agent pipeline with:

- **Planner Agent** that analyzes query complexity and creates an execution plan
- **Router Agent** that selects the right specialist agents
- **4 Specialist Agents**: Account, Loan, Fraud, Compliance
- **Aggregator Agent** that synthesizes all outputs
- **Critique Agent** that validates responses for accuracy and compliance
- **Audit Database** that records every decision, MCP call, and KG query

Every response shows the full audit trail. Enter your Customer ID (try CUST1001) and ask anything.`,
  timestamp: new Date(),
}

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([WELCOME])
  const [input, setInput] = useState("")
  const [customerId, setCustomerId] = useState("CUST1001")
  const [sessionId, setSessionId] = useState("")
  const [loading, setLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    setSessionId(crypto.randomUUID())
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  const sendMessage = async (text?: string) => {
    const query = (text || input).trim()
    if (!query || loading) return

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: query,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setInput("")
    setLoading(true)

    try {
      const res = await axios.post(`${API_URL}/api/chat`, {
        query,
        customer_id: customerId,
        session_id: sessionId,
        conversation_history: messages.slice(-4).map(m => ({
          role: m.role,
          content: m.content,
        })),
      })

      const data = res.data
      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.response || "I could not process your request. Please try again.",
        timestamp: new Date(),
        metadata: {
          session_id: data.session_id,
          agents_invoked: data.agents_invoked || [],
          risk_level: data.risk_level,
          latency_ms: data.total_latency_ms,
          mcp_calls: data.mcp_calls_log || [],
          kg_queries: data.kg_queries_log || [],
          requires_human: data.requires_human,
          critique_score: data.critique_result?.overall_score,
          critique_passed: data.critique_result?.passes,
          query_complexity: data.query_complexity,
          planner_plan: data.planner_plan,
          agent_outputs: data.agent_outputs || {},
          critique_result: data.critique_result,
        },
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err: any) {
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `**Connection Error**: Could not reach the backend at \`${API_URL}\`.\n\nMake sure the backend is running:\n\`\`\`\npython -m uvicorn src.main:app --reload --port 8000\n\`\`\`\n\nError: ${err.message}`,
        timestamp: new Date(),
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const clearChat = () => {
    setMessages([WELCOME])
    setSessionId(crypto.randomUUID())
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar
        customerId={customerId}
        onCustomerIdChange={setCustomerId}
        onQuickQuery={q => sendMessage(q)}
        onClear={clearChat}
        open={sidebarOpen}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="bg-white border-b border-slate-100 px-4 py-3 flex items-center justify-between shadow-sm flex-shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(v => !v)}
              className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <Menu className="w-5 h-5 text-slate-600" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="font-semibold text-slate-800">FinCore AI Assistant</span>
              <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-medium">
                v2
              </span>
            </div>
            <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
              {customerId}
            </span>
          </div>
          <div className="hidden md:flex items-center gap-1.5 text-xs text-slate-400">
            <Activity className="w-3.5 h-3.5" />
            <span>Planner + Router + 4 Agents + Critique + Audit DB + MCP + Neo4j</span>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          {messages.map(m => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {loading && <LoadingIndicator />}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-slate-100 p-4 flex-shrink-0">
          <div className="flex gap-3 items-end max-w-4xl mx-auto">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
              placeholder="Ask about accounts, loans, or report a suspicious transaction..."
              rows={1}
              disabled={loading}
              className="flex-1 resize-none border border-slate-200 rounded-2xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-400 transition-all disabled:opacity-60"
              style={{ minHeight: "48px", maxHeight: "120px" }}
              onInput={e => {
                const t = e.target as HTMLTextAreaElement
                t.style.height = "auto"
                t.style.height = Math.min(t.scrollHeight, 120) + "px"
              }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="w-12 h-12 rounded-2xl fincore-gradient text-white flex items-center justify-center flex-shrink-0 disabled:opacity-50 hover:shadow-lg hover:scale-105 active:scale-95 transition-all duration-200"
            >
              {loading
                ? <Loader2 className="w-5 h-5 animate-spin" />
                : <Send className="w-5 h-5" />
              }
            </button>
          </div>
          <p className="text-center text-xs text-slate-400 mt-2">
            Enter to send · Shift+Enter for new line · All responses are grounded in retrieved data and validated by Critique Agent
          </p>
        </div>
      </div>
    </div>
  )
}