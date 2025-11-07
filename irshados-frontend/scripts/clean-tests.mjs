import { rm } from 'node:fs/promises'
import { resolve } from 'node:path'

async function main() {
  const target = resolve(process.cwd(), 'dist-tests')
  await rm(target, { recursive: true, force: true })
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
