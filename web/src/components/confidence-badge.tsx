import { Badge } from "@/components/ui/badge"

const VARIANTS = {
  high: "secondary",
  medium: "outline",
  low: "outline",
  unmapped: "destructive",
} as const

export function ConfidenceBadge({ value }: { value: string | null }) {
  if (!value) return <Badge variant="outline">unknown</Badge>
  const variant = VARIANTS[value as keyof typeof VARIANTS] ?? "outline"
  return <Badge variant={variant}>{value}</Badge>
}
