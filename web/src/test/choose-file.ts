import { fireEvent } from "@testing-library/react"

export function chooseFile(input: HTMLElement, file: File) {
  Object.defineProperty(input, "files", { configurable: true, value: [file] })
  fireEvent.change(input)
}
