import { lazy, Suspense } from "react"
import { Link } from "react-router-dom"
import useSWR from "swr"

import { CountryUploadForm } from "@/components/country-upload-form"
import { fetchOverview } from "@/lib/api"
import { formatAmount, formatShare } from "@/lib/format"
import { Badge } from "@/components/ui/badge"
import { buttonVariants } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

const ShaChart = lazy(() => import("@/components/sha-chart"))

export function OverviewPage() {
  const { data, error, isLoading, mutate } = useSWR("/api/overview", fetchOverview)

  if (error) {
    return (
      <Alert>
        <AlertTitle>Could not load overview</AlertTitle>
        <AlertDescription>Start the API with `fastapi dev` and retry.</AlertDescription>
      </Alert>
    )
  }

  if (isLoading || !data) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
      </div>
    )
  }

  const hasCountries = data.countries.length > 0

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-medium">Overview</h1>
        <p className="text-sm text-muted-foreground">
          Upload a country extract to harmonise and classify it. Amounts stay in original currency.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload country extract</CardTitle>
          <CardDescription>
            Supported layouts: CSV (TXN_ID / ACCOUNT_CODE), Excel (Depenses + Plan_comptable), or JSON
            (metadata + transactions). Re-uploading the same country replaces its records.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CountryUploadForm
            onSuccess={() => {
              void mutate()
            }}
          />
        </CardContent>
      </Card>

      {!hasCountries ? (
        <Empty className="border">
          <EmptyHeader>
            <EmptyTitle>No countries ingested yet</EmptyTitle>
            <EmptyDescription>
              Upload a CSV, Excel, or JSON extract to populate the review workspace.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Records ingested</CardTitle>
                <CardDescription>All source transactions</CardDescription>
              </CardHeader>
              <CardContent className="text-3xl font-light">
                {data.expenditure_count.toLocaleString()}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Review queue</CardTitle>
                <CardDescription>Low confidence, unmapped, or untrusted text</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                <p className="text-3xl font-light">{data.review_count.toLocaleString()}</p>
                <p className="text-sm text-muted-foreground">{formatShare(data.review_share)} of records</p>
                <Link className={buttonVariants({ size: "sm" })} to="/transactions?review_only=1">
                  Open queue
                </Link>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Spend by currency</CardTitle>
                <CardDescription>No FX conversion</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-2 text-sm">
                {data.spend_by_currency.map((item) => (
                  <div key={item.currency} className="flex items-center justify-between">
                    <span>{item.currency}</span>
                    <span>{formatAmount(item.amount, item.currency)}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            {data.countries.map((country) => (
              <Card key={country.country_code}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {country.flag_emoji ? <span aria-hidden="true">{country.flag_emoji}</span> : null}
                    {country.country_name}
                  </CardTitle>
                  <CardDescription>{country.country_code}</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col gap-2 text-sm">
                  <p>{country.record_count.toLocaleString()} records</p>
                  <p className="text-muted-foreground">{country.review_count.toLocaleString()} in review</p>
                  {country.currencies.map((item) => (
                    <p key={item.currency}>
                      {formatAmount(item.amount, item.currency)} ({item.count} rows)
                    </p>
                  ))}
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Records by SHA code</CardTitle>
              <CardDescription>Current classification, including unmapped capital</CardDescription>
            </CardHeader>
            <CardContent>
              <Suspense fallback={<Skeleton className="h-72 w-full" />}>
                <ShaChart items={data.by_sha} />
              </Suspense>
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>SRHR</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {data.by_srhr.map((item) => (
                  <div key={item.key} className="flex items-center justify-between text-sm">
                    <span>{item.label ?? item.key}</span>
                    <Badge variant="secondary">{item.count}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Quality flags</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {data.by_flag.map((item) => (
                  <div key={item.key} className="flex items-center justify-between text-sm">
                    <span>{item.key}</span>
                    <Badge variant="outline">{item.count}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
