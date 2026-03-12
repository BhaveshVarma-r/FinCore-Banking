"use client"

import { Bot, BarChart3, X, Zap, Shield, CreditCard, Scale } from "lucide-react"
import Link from "next/link"

const QUICK_QUERIES = [
  { text: "Check my account balance" },
  { text: "Am I eligible for a home loan?" },
  { text: "I see a suspicious transaction" },
  { text: "MSME loan documents needed"},
  { text: "Show inactive accounts" },
  { text: "Personal loan with car loan" },
]

const AGENT_INFO = [
  { name: "Account Agent", icon: CreditCard, color: "text-blue-300", desc: "Balances, transactions" },
  { name: "Loan Agent", icon: Zap, color: "text-green-300", desc: "Eligibility, EMI" },
  { name: "Fraud Agent", icon: Shield, color: "text-red-300", desc: "Security, disputes" },
  { name: "Compliance Agent", icon: Scale, color: "text-purple-300", desc: "RBI rules, docs" },
]

interface SidebarProps {
  customerId: string
  onCustomerIdChange: (id: string) => void
  onQuickQuery: (query: string) => void
  onClear: () => void
  open: boolean
}

export default function Sidebar({
  customerId, onCustomerIdChange, onQuickQuery, onClear, open
}: SidebarProps) {
  return (
    <div className={`
      ${open ? "w-72" : "w-0"} transition-all duration-300 overflow-hidden
      flex-shrink-0 fincore-gradient text-white flex flex-col h-full
    `}>
      <div className="p-5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg">FinCore AI</h1>
            <p className="text-xs text-white/60">Banking Assistant v2</p>
          </div>
        </div>
      </div>

      <div className="p-4 border-b border-white/10">
        <label className="text-xs text-white/60 mb-1 block uppercase tracking-wide">
          Customer ID
        </label>
        <input
          type="text"
          value={customerId}
          onChange={e => onCustomerIdChange(e.target.value)}
          placeholder="CUST1001"
          className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-sm text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-white/30"
        />
        <p className="text-xs text-white/40 mt-1">CUST1000 to CUST1049</p>
      </div>

      <div className="p-4 flex-1 overflow-y-auto space-y-4">
        <div>
          <p className="text-xs text-white/60 mb-2 uppercase tracking-wide font-medium">
            Quick Queries
          </p>
          <div className="space-y-1.5">
            {QUICK_QUERIES.map((q, i) => (
              <button
                key={i}
                onClick={() => onQuickQuery(q.text)}
                className="w-full text-left bg-white/10 hover:bg-white/20 border border-white/10 rounded-lg px-3 py-2 text-sm transition-all flex items-center gap-2"
              >
                <Zap className="w-3 h-3 text-white/40" />
                <span className="text-white/80 text-xs">{q.text}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs text-white/60 mb-2 uppercase tracking-wide font-medium">
            Active Agents
          </p>
          <div className="space-y-1.5">
            {AGENT_INFO.map(agent => (
              <div key={agent.name}
                className="flex items-center gap-2 px-3 py-2 bg-white/5 rounded-lg">
                <agent.icon className={`w-4 h-4 ${agent.color}`} />
                <div>
                  <p className="text-xs text-white/80 font-medium">{agent.name}</p>
                  <p className="text-xs text-white/40">{agent.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-white/10 space-y-2">
        <Link
          href="/demo"
          className="flex items-center justify-center gap-2 w-full bg-white/10 hover:bg-white/20 border border-white/10 rounded-lg px-3 py-2 text-sm transition-all"
        >
          <BarChart3 className="w-4 h-4" />
          Test Scenarios and Demo
        </Link>
        <button
          onClick={onClear}
          className="w-full bg-white/5 hover:bg-white/15 border border-white/10 rounded-lg px-3 py-2 text-sm transition-all text-white/70"
        >
          Clear Chat
        </button>
      </div>
    </div>
  )
}