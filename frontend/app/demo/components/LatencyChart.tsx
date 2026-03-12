"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts"

interface LatencyChartProps {
  data: { name: string; latency: number; passed: boolean }[]
}

export default function LatencyChart({ data }: LatencyChartProps) {
  if (data.length === 0) return null

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 mb-6">
      <h3 className="font-semibold text-slate-800 mb-3 text-sm">Response Latency vs 4000ms SLA</h3>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip
            formatter={(v) => [`${v}ms`, "Latency"]}
            contentStyle={{ fontSize: 11, borderRadius: 8 }}
          />
          <ReferenceLine y={4000} stroke="#ef4444" strokeDasharray="4 4"
            label={{ value: "4s SLA", position: "right", fontSize: 10, fill: "#ef4444" }} />
          <Bar dataKey="latency" radius={[4, 4, 0, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.latency < 4000 ? "#10b981" : "#ef4444"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}