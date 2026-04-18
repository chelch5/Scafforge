import { type Plugin } from "@opencode-ai/plugin"

const DANGEROUS_BASH = /(rm\s+-|git\s+reset|git\s+clean|sudo\s+|chmod\s+777|dd\s+if=)/i
const BLENDER_MUTATING_TOOLS = new Set([
  "blender_agent_mesh_edit_batch",
  "blender_agent_modifier_stack_edit",
  "blender_agent_scene_batch_edit",
  "blender_agent_material_pbr_build",
  "blender_agent_node_graph_build",
  "blender_agent_uv_workflow",
  "blender_agent_bake_maps",
  "blender_agent_armature_animation",
])

function extractFilePath(args: Record<string, unknown>): string {
  const pathValue = args.filePath || args.path || args.target
  return typeof pathValue === "string" ? pathValue : ""
}

function isEnvPath(pathValue: string): boolean {
  return pathValue.includes(".env") && !pathValue.endsWith(".env.example")
}

function nonEmptyString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null
}

export const ToolGuard: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "read" || input.tool === "write" || input.tool === "edit") {
        const filePath = extractFilePath(output.args)
        if (filePath && isEnvPath(filePath)) {
          throw new Error("Do not read or modify sensitive .env files.")
        }
      }

      if (input.tool === "bash") {
        const command = typeof output.args.command === "string" ? output.args.command : ""
        if (DANGEROUS_BASH.test(command)) {
          throw new Error("Dangerous shell commands are blocked by the project tool guard.")
        }
      }

      if (input.tool === "blender_agent_project_initialize") {
        if (!nonEmptyString(output.args.output_blend)) {
          throw new Error(
            "Blender project_initialize must set a concrete output_blend so later mutating calls can reuse persistence.saved_blend.",
          )
        }
      }

      if (BLENDER_MUTATING_TOOLS.has(input.tool)) {
        if (!nonEmptyString(output.args.input_blend) || !nonEmptyString(output.args.output_blend)) {
          throw new Error(
            `Blender ${input.tool.replace("blender_agent_", "")} must include non-null input_blend and output_blend. Reuse persistence.saved_blend from the previous saved step instead of issuing a stateless mutation.`,
          )
        }
      }
    },
  }
}
