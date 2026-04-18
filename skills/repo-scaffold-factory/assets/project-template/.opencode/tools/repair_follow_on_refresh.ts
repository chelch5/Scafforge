// @ts-ignore - the generated runtime mirrors @opencode-ai/plugin during tool execution.
import { tool } from "@opencode-ai/plugin"
import {
  evaluateBootstrapState,
  loadManifest,
  loadWorkflowState,
  type RepairFollowOnState,
  saveWorkflowBundle,
  syncWorkflowSelection,
} from "../lib/workflow"

function parseObjectArg(raw: string, label: string): Record<string, unknown> {
  try {
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error(`${label} must encode an object.`)
    }
    return parsed as Record<string, unknown>
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    throw new Error(`Unable to parse ${label}: ${message}`)
  }
}

function normalizeStringArray(value: unknown, label: string): string[] {
  if (!Array.isArray(value)) {
    throw new Error(`${label} must be an array of strings.`)
  }
  const result: string[] = []
  for (const item of value) {
    if (typeof item !== "string" || !item.trim()) {
      throw new Error(`${label} must contain only non-empty strings.`)
    }
    result.push(item.trim())
  }
  return result
}

function normalizeRepairFollowOnPayload(
  payload: Record<string, unknown>,
  current: RepairFollowOnState,
  {
    processVersion,
    changedAt,
  }: {
    processVersion: number
    changedAt: string
  },
): RepairFollowOnState {
  const next: RepairFollowOnState = { ...current }
  if ("outcome" in payload) {
    const outcome = payload.outcome
    if (outcome !== "managed_blocked" && outcome !== "source_follow_up" && outcome !== "clean") {
      throw new Error("repair_follow_on_json.outcome must be one of managed_blocked, source_follow_up, or clean.")
    }
    next.outcome = outcome
  }
  if ("required_stages" in payload) next.required_stages = normalizeStringArray(payload.required_stages, "repair_follow_on_json.required_stages")
  if ("completed_stages" in payload) next.completed_stages = normalizeStringArray(payload.completed_stages, "repair_follow_on_json.completed_stages")
  if ("blocking_reasons" in payload) next.blocking_reasons = normalizeStringArray(payload.blocking_reasons, "repair_follow_on_json.blocking_reasons")
  if ("allowed_follow_on_tickets" in payload) next.allowed_follow_on_tickets = normalizeStringArray(payload.allowed_follow_on_tickets, "repair_follow_on_json.allowed_follow_on_tickets")
  if ("verification_passed" in payload) {
    if (typeof payload.verification_passed !== "boolean") throw new Error("repair_follow_on_json.verification_passed must be boolean.")
    next.verification_passed = payload.verification_passed
  }
  if ("handoff_allowed" in payload) {
    if (typeof payload.handoff_allowed !== "boolean") throw new Error("repair_follow_on_json.handoff_allowed must be boolean.")
    next.handoff_allowed = payload.handoff_allowed
  }
  if ("last_updated_at" in payload) {
    if (payload.last_updated_at !== null && typeof payload.last_updated_at !== "string") {
      throw new Error("repair_follow_on_json.last_updated_at must be string or null.")
    }
    next.last_updated_at = payload.last_updated_at
  }
  next.process_version = processVersion
  next.last_updated_at = typeof next.last_updated_at === "string" && next.last_updated_at.trim() ? next.last_updated_at : changedAt
  return next
}

export default tool({
  description: "Refresh canonical workflow repair follow-on state from a managed repair run using the generated runtime persistence contract.",
  args: {
    change_summary: tool.schema.string().describe("Summary of the repair-driven workflow change."),
    process_version: tool.schema.number().int().describe("Workflow process version after the deterministic refresh.").optional(),
    parallel_mode: tool.schema.enum(["parallel-lanes", "sequential"]).describe("Parallel execution mode after the deterministic refresh.").optional(),
    repair_follow_on_json: tool.schema.string().describe("Serialized repair_follow_on payload to persist through the runtime workflow contract."),
  },
  async execute(args: { change_summary: string; process_version?: number; parallel_mode?: "parallel-lanes" | "sequential"; repair_follow_on_json: string }) {
    const manifest = await loadManifest()
    const workflow = await loadWorkflowState()
    const repairFollowOn = parseObjectArg(args.repair_follow_on_json, "repair_follow_on_json")
    const changeSummary = args.change_summary.trim()
    if (!changeSummary) {
      throw new Error("change_summary must not be empty.")
    }
    const changedAt = new Date().toISOString()
    const processVersion = typeof args.process_version === "number" && args.process_version > 0
      ? Math.floor(args.process_version)
      : workflow.process_version

    syncWorkflowSelection(workflow, manifest)
    workflow.process_version = processVersion
    if (args.parallel_mode) {
      workflow.parallel_mode = args.parallel_mode
    }
    workflow.process_last_changed_at = changedAt
    workflow.process_last_change_summary = changeSummary
    workflow.pending_process_verification = true
    workflow.repair_follow_on = normalizeRepairFollowOnPayload(repairFollowOn, workflow.repair_follow_on, { processVersion, changedAt })
    const evaluatedBootstrap = await evaluateBootstrapState(workflow.bootstrap)
    workflow.bootstrap = evaluatedBootstrap.status === "ready"
      ? { ...evaluatedBootstrap, status: "stale" }
      : evaluatedBootstrap

    // Auto-resolve managed_blocked only when the cycle is fully clean.
    const rfo = workflow.repair_follow_on
    const requiredStages = Array.isArray(rfo.required_stages) ? rfo.required_stages : []
    const completedStages = Array.isArray(rfo.completed_stages) ? rfo.completed_stages : []
    if (
      rfo.outcome === "managed_blocked" &&
      requiredStages.every((stage: string) => completedStages.includes(stage)) &&
      Array.isArray(rfo.blocking_reasons) && rfo.blocking_reasons.length === 0 &&
      rfo.verification_passed === true &&
      rfo.handoff_allowed === true
    ) {
      rfo.outcome = "clean"
    }

    const expectedRevision = workflow.state_revision
    await saveWorkflowBundle({
      workflow,
      manifest,
      expectedRevision,
      skipGraphValidation: true,
    })

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
