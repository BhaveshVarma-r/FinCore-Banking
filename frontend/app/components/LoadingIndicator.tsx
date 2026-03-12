import { Bot } from "lucide-react"

export default function LoadingIndicator() {
  return (
    <div className="flex gap-3 animate-slide-in">
      <div className="w-8 h-8 rounded-full fincore-gradient flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="flex items-center gap-3 p-4 bg-white rounded-2xl rounded-tl-sm border border-slate-100 shadow-sm">
        <div className="flex gap-1">
          <div className="w-2 h-2 rounded-full bg-indigo-500 loading-dot" />
          <div className="w-2 h-2 rounded-full bg-indigo-500 loading-dot" />
          <div className="w-2 h-2 rounded-full bg-indigo-500 loading-dot" />
        </div>
        <span className="text-xs text-slate-400">
          Planner analyzing query...
        </span>
      </div>
    </div>
  )
}