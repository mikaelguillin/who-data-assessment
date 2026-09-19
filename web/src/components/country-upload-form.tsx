import { Loader2Icon, UploadIcon } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"
import { mutate } from "swr"

import { uploadCountryExtract } from "@/lib/api"
import { COUNTRIES } from "@/lib/countries"
import { formatCountryLabel } from "@/lib/format"
import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export function CountryUploadForm({ onSuccess }: { onSuccess?: () => void }) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [flagEmoji, setFlagEmoji] = useState<string | null>(null)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const name = String(new FormData(form).get("country_name") ?? "").trim()
    if (!name || !file || file.size === 0) {
      setError("Choose a CSV, Excel, or JSON extract and enter a country name.")
      return
    }
    const data = new FormData()
    data.set("country_name", name)
    data.set("file", file)
    if (flagEmoji) data.set("flag_emoji", flagEmoji)
    setPending(true)
    setError(null)
    try {
      const result = await uploadCountryExtract(data)
      const verb = result.replaced ? "Replaced" : "Ingested"
      toast.success(
        `${verb} ${result.record_count.toLocaleString()} records for ${formatCountryLabel(result)}`
      )
      form.reset()
      setFile(null)
      setFlagEmoji(null)
      await mutate("/api/overview")
      await mutate("/api/countries")
      onSuccess?.()
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed"
      setError(message)
      toast.error(message)
    } finally {
      setPending(false)
    }
  }

  return (
    <form aria-label="Upload country extract" onSubmit={handleSubmit}>
      <FieldGroup className="grid gap-3 md:grid-cols-[1fr_1fr_auto_auto] md:items-start">
        <Field data-invalid={error ? true : undefined}>
          <FieldLabel htmlFor="country-file">Extract file</FieldLabel>
          <Input
            id="country-file"
            name="file"
            type="file"
            accept=".csv,.xlsx,.xlsm,.json,text/csv,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            disabled={pending}
            aria-invalid={error ? true : undefined}
            onChange={(event) => setFile(event.currentTarget.files?.[0] ?? null)}
          />
          <FieldDescription>CSV, Excel (.xlsx), or JSON in a supported layout.</FieldDescription>
        </Field>
        <Field data-invalid={error ? true : undefined}>
          <FieldLabel htmlFor="country-name">Country name</FieldLabel>
          <Input
            id="country-name"
            name="country_name"
            placeholder="e.g. Kenya"
            disabled={pending}
            aria-invalid={error ? true : undefined}
          />
        </Field>
        <Field>
          <FieldLabel htmlFor="country-flag">Flag</FieldLabel>
          <Select
            value={flagEmoji}
            onValueChange={(next) => setFlagEmoji(next ?? null)}
            disabled={pending}
            items={COUNTRIES.map((country) => ({
              value: country.flag,
              label: country.flag,
            }))}
          >
            <SelectTrigger id="country-flag">
              <SelectValue placeholder="Flag" />
            </SelectTrigger>
            <SelectContent align="start" alignItemWithTrigger={false}>
              <SelectGroup>
                {COUNTRIES.map((country) => (
                  <SelectItem key={country.iso2} value={country.flag} aria-label={country.name}>
                    {country.flag}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </Field>
        <Field className="mt-7">
          <Button type="submit" disabled={pending}>
            {pending ? (
              <Loader2Icon data-icon="inline-start" className="animate-spin" />
            ) : (
              <UploadIcon data-icon="inline-start" />
            )}
            {pending ? "Ingesting…" : "Upload extract"}
          </Button>
        </Field>
      </FieldGroup>
      {error ? <FieldError className="mt-2">{error}</FieldError> : null}
    </form>
  )
}
