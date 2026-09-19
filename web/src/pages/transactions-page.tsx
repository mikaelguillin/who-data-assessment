import { startTransition, useMemo, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import useSWR from "swr"

import { ConfidenceBadge } from "@/components/confidence-badge"
import { FilterSelect } from "@/components/filter-select"
import { expenditureListKey, fetchCountries, fetchExpenditureList } from "@/lib/api"
import { formatAmount } from "@/lib/format"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { ExpenditureQuery } from "@/types"

const PAGE_SIZE = 25

export function TransactionsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [draftSearch, setDraftSearch] = useState(searchParams.get("q") ?? "")

  const query = useMemo<ExpenditureQuery>(() => {
    const offset = Number(searchParams.get("offset") ?? "0")
    return {
      country: searchParams.get("country") ?? undefined,
      sha: searchParams.get("sha") ?? undefined,
      srhr: searchParams.get("srhr") ?? undefined,
      confidence: searchParams.get("confidence") ?? undefined,
      flag: searchParams.get("flag") ?? undefined,
      q: searchParams.get("q") ?? undefined,
      review_only: searchParams.get("review_only") === "1",
      limit: PAGE_SIZE,
      offset: Number.isFinite(offset) ? offset : 0,
    }
  }, [searchParams])

  const key = expenditureListKey(query)
  const { data, isLoading } = useSWR(key, fetchExpenditureList)
  const { data: countries } = useSWR("/api/countries", fetchCountries)

  function updateParams(patch: Record<string, string | undefined>) {
    startTransition(() => {
      const next = new URLSearchParams(searchParams)
      for (const [name, value] of Object.entries(patch)) {
        if (!value) next.delete(name)
        else next.set(name, value)
      }
      if (!("offset" in patch)) next.delete("offset")
      setSearchParams(next)
    })
  }

  const offset = query.offset ?? 0
  const total = data?.total ?? 0

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-medium">Transactions</h1>
        <p className="text-sm text-muted-foreground">
          Filter harmonised records. Review queue is low / unmapped / untrusted text.
        </p>
      </div>

      <FieldGroup className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Field>
          <FieldLabel>Country</FieldLabel>
          <FilterSelect
            placeholder="All countries"
            value={query.country ?? "all"}
            onChange={(value) => updateParams({ country: value === "all" ? undefined : value })}
            options={[
              { value: "all", label: "All" },
              ...(countries ?? []).map((country) => ({
                value: country.country_code,
                label: country.country_name,
              })),
            ]}
          />
        </Field>
        <Field>
          <FieldLabel>Confidence</FieldLabel>
          <FilterSelect
            placeholder="All"
            value={query.confidence ?? "all"}
            onChange={(value) => updateParams({ confidence: value === "all" ? undefined : value })}
            options={[
              { value: "all", label: "All" },
              { value: "high", label: "High" },
              { value: "medium", label: "Medium" },
              { value: "low", label: "Low" },
              { value: "unmapped", label: "Unmapped" },
            ]}
          />
        </Field>
        <Field>
          <FieldLabel>SRHR</FieldLabel>
          <FilterSelect
            placeholder="All"
            value={query.srhr ?? "all"}
            onChange={(value) => updateParams({ srhr: value === "all" ? undefined : value })}
            options={[
              { value: "all", label: "All" },
              { value: "SRHR.FP", label: "Family planning" },
              { value: "SRHR.MH", label: "Maternal" },
              { value: "SRHR.AH", label: "Adolescent" },
              { value: "SRHR.HIV", label: "HIV" },
              { value: "SRHR.SGBV", label: "SGBV" },
              { value: "SRHR.RC", label: "Cancer" },
              { value: "SRHR.NA", label: "Not SRHR" },
            ]}
          />
        </Field>
        <Field>
          <FieldLabel>Flag</FieldLabel>
          <FilterSelect
            placeholder="All"
            value={query.flag ?? "all"}
            onChange={(value) => updateParams({ flag: value === "all" ? undefined : value })}
            options={[
              { value: "all", label: "All" },
              { value: "description_untrusted", label: "Untrusted text" },
              { value: "missing_amount", label: "Missing amount" },
              { value: "negative_amount", label: "Negative" },
              { value: "duplicate_source_id", label: "Duplicate ID" },
              { value: "date_out_of_range", label: "Date out of range" },
              { value: "multi_currency", label: "Non-primary currency" },
              { value: "has_subtransactions", label: "Sub-transactions" },
            ]}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="search">Search</FieldLabel>
          <Input
            id="search"
            value={draftSearch}
            placeholder="ID or description"
            onChange={(event) => setDraftSearch(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") updateParams({ q: draftSearch || undefined })
            }}
          />
        </Field>
        <Field>
          <FieldLabel>Queue</FieldLabel>
          <Button
            variant={query.review_only ? "default" : "outline"}
            onClick={() => updateParams({ review_only: query.review_only ? undefined : "1" })}
          >
            {query.review_only ? "Showing review only" : "Show review queue"}
          </Button>
        </Field>
      </FieldGroup>

      {isLoading || !data ? (
        <Skeleton className="h-96 w-full" />
      ) : data.items.length === 0 ? (
        <Empty>
          <EmptyHeader>
            <EmptyTitle>No records match</EmptyTitle>
            <EmptyDescription>Clear filters to see the full extract.</EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <div className="flex flex-col gap-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Source ID</TableHead>
                <TableHead>Country</TableHead>
                <TableHead>Account</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>SHA</TableHead>
                <TableHead>Confidence</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((item) => (
                <TableRow key={item.id} className="[content-visibility:auto]">
                  <TableCell>
                    <Link className="underline-offset-2 hover:underline" to={`/transactions/${item.id}`}>
                      {item.source_transaction_id}
                    </Link>
                  </TableCell>
                  <TableCell>{item.country_code}</TableCell>
                  <TableCell>{item.account_code}</TableCell>
                  <TableCell className="max-w-72 truncate">{item.description_raw}</TableCell>
                  <TableCell>{formatAmount(item.amount_native, item.currency_original)}</TableCell>
                  <TableCell>{item.sha_code ?? "—"}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      <ConfidenceBadge value={item.confidence} />
                      {item.flag_codes.includes("description_untrusted") ? (
                        <Badge variant="destructive">untrusted</Badge>
                      ) : null}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <div className="flex items-center justify-between text-sm">
            <p className="text-muted-foreground">
              {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={offset === 0}
                onClick={() => updateParams({ offset: String(Math.max(offset - PAGE_SIZE, 0)) })}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={offset + PAGE_SIZE >= total}
                onClick={() => updateParams({ offset: String(offset + PAGE_SIZE) })}
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
