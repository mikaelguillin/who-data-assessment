import { render, screen } from "@testing-library/react"
import { expect, test } from "vitest"

import { ConfidenceBadge } from "@/components/confidence-badge"

test("colors high, medium, and low with semantic tokens", () => {
  const { rerender } = render(<ConfidenceBadge value="high" />)
  expect(screen.getByText("high")).toHaveClass("bg-success", "text-success-foreground")

  rerender(<ConfidenceBadge value="medium" />)
  expect(screen.getByText("medium")).toHaveClass("bg-warning", "text-warning-foreground")

  rerender(<ConfidenceBadge value="low" />)
  expect(screen.getByText("low")).toHaveClass("bg-destructive", "text-destructive-foreground")
})

test("keeps unmapped on the tinted destructive treatment", () => {
  render(<ConfidenceBadge value="unmapped" />)
  const badge = screen.getByText("unmapped")
  expect(badge).toHaveClass("bg-destructive/10", "text-destructive")
  expect(badge).not.toHaveClass("text-destructive-foreground")
})

test("renders unknown when confidence is missing", () => {
  render(<ConfidenceBadge value={null} />)
  expect(screen.getByText("unknown")).toHaveClass("border-border")
})
