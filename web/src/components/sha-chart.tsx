import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"

import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import type { CountItem } from "@/types"

const chartConfig = {
  count: { label: "Records", color: "var(--primary)" },
} satisfies ChartConfig

export function ShaChart({ items }: { items: CountItem[] }) {
  const data = items.map((item) => ({
    key: item.key,
    count: item.count,
    label: item.label ?? item.key,
  }))

  return (
    <ChartContainer config={chartConfig} className="aspect-auto h-72 w-full">
      <BarChart data={data} margin={{ left: 8, right: 8 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="key" tickLine={false} axisLine={false} interval={0} angle={-25} textAnchor="end" height={70} />
        <YAxis allowDecimals={false} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="count" fill="var(--color-count)" radius={0} />
      </BarChart>
    </ChartContainer>
  )
}

export default ShaChart
