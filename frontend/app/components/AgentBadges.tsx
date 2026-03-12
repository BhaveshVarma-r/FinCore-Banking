interface AgentBadgesProps {
  agents: string[]
}

const AGENT_CONFIG: Record<string, { color: string; icon: string }> = {
  account: { color: "bg-blue-100 text-blue-700", icon: "" },
  loan: { color: "bg-green-100 text-green-700", icon: "" },
  fraud: { color: "bg-red-100 text-red-700", icon: "" },
  compliance: { color: "bg-purple-100 text-purple-700", icon: "" },
  planner: { color: "bg-amber-100 text-amber-700", icon: "" },
  critique: { color: "bg-slate-100 text-slate-700", icon: "" },
}

export default function AgentBadges({ agents }: AgentBadgesProps) {
  return (
    <div className="flex flex-wrap gap-1 mt-2">
      {agents.map(agent => {
        const cfg = AGENT_CONFIG[agent]
        if (!cfg) return null
        return (
          <span key={agent} className={`agent-badge ${cfg.color}`}>
            {cfg.icon} {agent}
          </span>
        )
      })}
    </div>
  )
}