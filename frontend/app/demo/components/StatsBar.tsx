import { CheckCircle, XCircle, Clock, Activity, Star } from "lucide-react"

interface StatsBarProps {
  passed: number
  failed: number
  withinSla: number
  avgLatency: number
  avgCritiqueScore: number
  totalRan: number
}

export default function StatsBar({
  passed, failed, withinSla, avgLatency, avgCritiqueScore, totalRan
}: StatsBarProps) {
  const stats = [
    { label: "Passed", value: `${passed}/${totalRan || 8}`, icon: CheckCircle, color: "text-green-600", bg: "bg-green-50 border-green-200" },
    { label: "Failed", value: `${failed}/${totalRan || 8}`, icon: XCircle, color: "text-red-600", bg: "bg-red-50 border-red-200" },
    { label: "Within 4s SLA", value: `${withinSla}/${totalRan || 8}`, icon: Clock, color: "text-blue-600", bg: "bg-blue-50 border-blue-200" },
    { label: "Avg Latency", value: avgLatency ? `${Math.round(avgLatency)}ms` : "N/A", icon: Activity, color: "text-purple-600", bg: "bg-purple-50 border-purple-200" },
    { label: "Avg Critique", value: avgCritiqueScore ? `${Math.round(avgCritiqueScore)}/100` : "N/A", icon: Star, color: "text-amber-600", bg: "bg-amber-50 border-amber-200" },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
      {stats.map(s => (
        <div key={s.label} className={`rounded-xl border p-4 ${s.bg}`}>
          <div className="flex items-center gap-1.5 mb-1">
            <s.icon className={`w-4 h-4 ${s.color}`} />
            <span className="text-xs text-slate-500">{s.label}</span>
          </div>
          <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
        </div>
      ))}
    </div>
  )
}