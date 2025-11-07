import { chmod } from 'node:fs/promises'
import { resolve } from 'node:path'
import { execSync } from 'node:child_process'

const hookDir = resolve(process.cwd(), '.husky')
const preCommitPath = resolve(hookDir, 'pre-commit')

try {
  await chmod(preCommitPath, 0o755)
  execSync(`git config core.hooksPath ${hookDir}`)
  console.log('Git hooks configured to use .husky/')
} catch (error) {
  console.warn('Unable to configure git hooks automatically. Configure manually if needed.')
  console.warn(error.message)
}
