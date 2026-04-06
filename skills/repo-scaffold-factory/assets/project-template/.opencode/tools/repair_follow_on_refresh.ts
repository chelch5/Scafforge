// @ts-ignore - the generated runtime mirrors @opencode-ai/plugin during tool execution.
import { tool } from "@opencode-ai/plugin"
// @ts-ignore - the generated runtime mirrors Node builtins during tool execution.
import { readFile, writeFile } from "node:fs/promises"
import {
  loadManifest,
  refreshRestartSurfaces,
  workflowStatePath,
} from "../lib/workflow"

function parseWorkflowState(raw: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("workflow_state_json must encode an object.")
    }
    return parsed as Record<string, unknown>
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    throw new Error(`Unable to parse workflow_state_json: ${message}`)
  }
}

export default tool({
  description: "Refresh canonical workflow repair follow-on state from a managed repair run using the generated runtime persistence contract.",
  args: {
    workflow_state_json: tool.schema.string().describe("Serialized workflow payload to persist through the runtime bundle writer."),
  },
  async execute(args: { workflow_state_json: string }) {
    const manifest = await loadManifest()
    const requestedWorkflow = parseWorkflowState(args.workflow_state_json)
    const workflowPath = workflowStatePath()
    const existingWorkflow = await readFile(workflowPath, "utf-8").catch(() => "{}")
    const workflow = parseWorkflowState(existingWorkflow)

    for (const [key, value] of Object.entries(requestedWorkflow)) {
      ;(workflow as Record<string, unknown>)[key] = value
    }

    await writeFile(workflowPath, JSON.stringify(workflow, null, 2) + "\n", { encoding: "utf-8" })
    await refreshRestartSurfaces({ manifest, workflow: workflow as any })

    return JSON.stringify(
      {
        active_ticket: manifest.active_ticket,
        process_version: workflow.process_version,
        parallel_mode: workflow.parallel_mode,
        pending_process_verification: workflow.pending_process_verification,
        repair_follow_on: workflow.repair_follow_on,
        process_last_changed_at: workflow.process_last_changed_at,
        process_last_change_summary: workflow.process_last_change_summary,
      },
      null,
      2,
    )
  },
})
