import { useState } from "react"
import useSWR from "swr"

import { FilterSelect } from "@/components/filter-select"
import { fetchCountries, fetchMappings } from "@/lib/api"
import { formatCountryLabel } from "@/lib/format"
import { Badge } from "@/components/ui/badge"
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty"
import { Field, FieldLabel } from "@/components/ui/field"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export function MappingsPage() {
  const [country, setCountry] = useState("all")
  const { data, isLoading } = useSWR(
    country === "all" ? "/api/mappings" : `/api/mappings?country=${country}`,
    () => fetchMappings(country === "all" ? undefined : country)
  )
  const { data: countries } = useSWR("/api/countries", fetchCountries)

  if (isLoading || !data) {
    return <Skeleton className="h-96 w-full" />
  }

  const gaps = data.items.filter((item) => !item.mapped)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-medium">Chart-of-account maps</h1>
        <p className="text-sm text-muted-foreground">
          Configurable CoA → SHA / SRHR rules. Gaps are accounts seen in source data with no map.
        </p>
      </div>

      <Field className="max-w-xs">
        <FieldLabel>Country</FieldLabel>
        <FilterSelect
          value={country}
          onChange={setCountry}
          placeholder="All countries"
          options={[
            { value: "all", label: "All" },
            ...(countries ?? []).map((item) => ({
              value: item.country_code,
              label: formatCountryLabel(item),
            })),
          ]}
        />
      </Field>

      {data.items.length === 0 ? (
        <Empty>
          <EmptyHeader>
            <EmptyTitle>No mappings</EmptyTitle>
            <EmptyDescription>Upload a country extract to populate country accounts.</EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Country</TableHead>
              <TableHead>Account</TableHead>
              <TableHead>Label</TableHead>
              <TableHead>SHA</TableHead>
              <TableHead>SRHR</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Notes</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.items.map((item) => (
              <TableRow key={`${item.country_code}-${item.account_code}`}>
                <TableCell>{item.country_code}</TableCell>
                <TableCell>{item.account_code}</TableCell>
                <TableCell className="max-w-80 truncate">{item.account_label}</TableCell>
                <TableCell>{item.sha_code ?? "—"}</TableCell>
                <TableCell>{item.srhr_code ?? "—"}</TableCell>
                <TableCell>
                  {item.mapped ? (
                    <Badge variant={item.generic ? "outline" : "secondary"}>
                      {item.generic ? "generic" : item.confidence}
                    </Badge>
                  ) : (
                    <Badge variant="destructive">gap</Badge>
                  )}
                </TableCell>
                <TableCell className="max-w-96 truncate text-muted-foreground">{item.notes}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {gaps.length > 0 ? (
        <p className="text-sm text-muted-foreground">{gaps.length} unmapped account codes</p>
      ) : null}
    </div>
  )
}
