import { spawnSync } from "node:child_process";

const argv = process.argv.slice(2);

if (argv.length === 0) {
  console.error("usage: node scripts/run_python.mjs <script> [args...]");
  process.exit(1);
}

const candidates =
  process.platform === "win32"
    ? [
        ["py", ["-3"]],
        ["python", []],
        ["python3", []],
      ]
    : [
        ["python3", []],
        ["python", []],
        ["py", ["-3"]],
      ];

for (const [command, prefix] of candidates) {
  const result = spawnSync(command, [...prefix, ...argv], {
    stdio: "inherit",
  });

  if (result.error) {
    if (result.error.code === "ENOENT") {
      continue;
    }
    console.error(`failed to start ${command}: ${result.error.message}`);
    process.exit(1);
  }

  process.exit(result.status ?? 1);
}

console.error(
  "no usable Python launcher was found. Install python3/python or configure py -3."
);
process.exit(1);
