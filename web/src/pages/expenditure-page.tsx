import { useState } from "react"
import { Link, useParams } from "react-router-dom"
import { toast } from "sonner"
import useSWR, { mutate } from "swr"

import { ConfidenceBadge } from "@/components/confidence-badge"
import { FilterSelect } from "@/components/filter-select"
import { fetchExpenditure, fetchShaRefs, fetchSrhrRefs, overrideClassification } from "@/lib/api"
import { formatAmount } from "@/lib/format"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export function ExpenditurePage() {
  const { id } = useParams()
  const expenditureId = Number(id)
  const { data, error, isLoading } = useSWR(
    Number.isFinite(expenditureId) ? `/api/expenditures/${expenditureId}` : null,
    () => fetchExpenditure(expenditureId)
  )
  const { data: shaRefs } = useSWR("/api/refs/sha", fetchShaRefs)
  const { data: srhrRefs } = useSWR("/api/refs/srhr", fetchSrhrRefs)
  const [open, setOpen] = useState(false)
  const [sha, setSha] = useState("")
  const [srhr, setSrhr] = useState("")
  const [reviewer, setReviewer] = useState("analyst")
  const [rationale, setRationale] = useState("Analyst override after source review")
  const [saving, setSaving] = useState(false)

  if (error) {
    return (
      <Alert>
        <AlertTitle>Record not found</AlertTitle>
        <AlertDescription>Return to the transaction list and try another id.</AlertDescription>
      </Alert>
    )
  }

  if (isLoading || !data) {
    return <Skeleton className="h-96 w-full" />
  }

  async function onSave() {
    setSaving(true)
    try {
      await overrideClassification(expenditureId, {
        sha_code: sha || null,
        srhr_code: srhr || null,
        reviewer,
        rationale,
      })
      await mutate(`/api/expenditures/${expenditureId}`)
      await mutate("/api/overview")
      toast.success("Classification updated")
      setOpen(false)
    } catch (saveError) {
      toast.error(saveError instanceof Error ? saveError.message : "Override failed")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-1">
          <p className="text-sm text-muted-foreground">
            <Link to="/transactions" className="hover:underline">
              Transactions
            </Link>
          </p>
          <h1 className="text-2xl font-medium">{data.source_transaction_id}</h1>
        </div>
        <Dialog
          open={open}
          onOpenChange={(next) => {
            setOpen(next)
            if (next) {
              setSha(data.classification?.sha_code ?? "")
              setSrhr(data.classification?.srhr_code ?? "")
            }
          }}
        >
          <DialogTrigger render={<Button>Override classification</Button>} />
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Analyst override</DialogTitle>
              <DialogDescription>
                Store a reviewed SHA / SRHR label. This does not change the source extract.
              </DialogDescription>
            </DialogHeader>
            <FieldGroup>
              <Field>
                <FieldLabel>SHA</FieldLabel>
                <FilterSelect
                  placeholder="Unmapped"
                  value={sha || "unmapped"}
                  onChange={(value) => setSha(value === "unmapped" ? "" : value)}
                  options={[
                    { value: "unmapped", label: "Unmapped" },
                    ...(shaRefs ?? []).map((item) => ({
                      value: item.code,
                      label: `${item.code} — ${item.description}`,
                    })),
                  ]}
                />
              </Field>
              <Field>
                <FieldLabel>SRHR</FieldLabel>
                <FilterSelect
                  placeholder="Select SRHR"
                  value={srhr}
                  onChange={setSrhr}
                  options={(srhrRefs ?? []).map((item) => ({
                    value: item.code,
                    label: `${item.code} — ${item.description}`,
                  }))}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="reviewer">Reviewer</FieldLabel>
                <Input id="reviewer" value={reviewer} onChange={(event) => setReviewer(event.target.value)} />
              </Field>
              <Field>
                <FieldLabel htmlFor="rationale">Rationale</FieldLabel>
                <Textarea
                  id="rationale"
                  value={rationale}
                  onChange={(event) => setRationale(event.target.value)}
                />
              </Field>
            </FieldGroup>
            <DialogFooter>
              <Button disabled={saving} onClick={onSave}>
                {saving ? "Saving…" : "Save override"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {data.flags.some((flag) => flag.flag_code === "description_untrusted") ? (
        <Alert>
          <AlertTitle>Untrusted description</AlertTitle>
          <AlertDescription>
            Free text contained prompt-injection markers. Classification used the chart of accounts only.
          </AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Harmonised fields</CardTitle>
            <CardDescription>Common structure after country adapters</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2 text-sm">
            <p>Country: {data.country_code}</p>
            <p>Date: {data.transaction_date ?? "—"}</p>
            <p>Fiscal year: {data.fiscal_year ?? "—"}</p>
            <p>
              Ministry: {data.ministry_code} — {data.ministry_name}
            </p>
            <p>Account: {data.account_code}</p>
            <p>Supplier: {data.supplier ?? "—"}</p>
            <p>Amount: {formatAmount(data.amount_native, data.currency_original)}</p>
            <p>Original amount: {data.amount_original ?? "—"}</p>
            <p>Payment method: {data.payment_method ?? "—"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Classification</CardTitle>
            <CardDescription>{data.classification?.method ?? "none"}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2 text-sm">
            <ConfidenceBadge value={data.classification?.confidence ?? null} />
            <p>SHA: {data.classification?.sha_code ?? "unmapped"}</p>
            <p className="text-muted-foreground">{data.classification?.sha_description}</p>
            <p>SRHR: {data.classification?.srhr_code ?? "—"}</p>
            <p className="text-muted-foreground">{data.classification?.srhr_description}</p>
            <p>{data.classification?.rationale}</p>
            <p className="text-muted-foreground">
              {data.classification?.classified_by} · {data.classification?.classified_at}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lineage</CardTitle>
          <CardDescription>Trace back to the original extract</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-sm">
          <p>Source ref: {data.source_row_ref}</p>
          {data.ingestion_run ? (
            <p>
              Ingested from {data.ingestion_run.source_filename} ({data.ingestion_run.source_format}) on{" "}
              {data.ingestion_run.ingested_at}
            </p>
          ) : null}
          <p>Description (raw): {data.description_raw ?? "—"}</p>
          <pre className="overflow-auto bg-muted p-3 text-xs">{data.raw_payload_json}</pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Quality flags</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {data.flags.length === 0 ? (
            <p className="text-sm text-muted-foreground">No flags</p>
          ) : (
            data.flags.map((flag) => (
              <Badge key={`${flag.flag_code}-${flag.detail}`} variant="outline">
                {flag.flag_code}
                {flag.detail ? `: ${flag.detail}` : ""}
              </Badge>
            ))
          )}
        </CardContent>
      </Card>

      {data.lines.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Sub-transactions</CardTitle>
            <CardDescription>Stored for lineage; parent amount is classified</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Sub ID</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.lines.map((line) => (
                  <TableRow key={line.source_sub_id}>
                    <TableCell>{line.source_sub_id}</TableCell>
                    <TableCell>{line.description}</TableCell>
                    <TableCell>{line.amount}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
