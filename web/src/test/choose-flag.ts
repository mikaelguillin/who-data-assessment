import { screen } from "@testing-library/react"
import type { UserEvent } from "@testing-library/user-event"

export async function chooseFlag(user: UserEvent, name: string) {
  await user.click(screen.getByRole("combobox", { name: /^flag$/i }))
  await user.click(await screen.findByRole("option", { name: new RegExp(`^${name}$`, "i") }))
}
