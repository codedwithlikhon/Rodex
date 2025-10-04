# Codebase Analysis Playbook

This playbook provides a step-by-step methodology for investigating an unfamiliar codebase, with a focus on debugging and security analysis. It is designed so the process can be executed manually or automated through agents such as Rodex.

## 1. Preparation & Scoping
1. **Clarify objectives.** Capture the user goal (e.g., reproduce a bug, validate a fix, or perform a security sweep) and any constraints such as runtime limits or prohibited dependencies.
2. **Gather context.** Collect architecture diagrams, environment configs, AGENTS.md instructions, and recent commits. Note mandatory tooling or coding conventions.
3. **Set up the environment.**
   - Create an isolated virtual environment and install dependencies with lockfiles when available.
   - If the project defines `Makefile` or task runner scripts, run the bootstrap target to ensure parity with CI.
4. **Establish baselines.** Run the default lint/test suite to confirm the initial state and store logs for comparison.

## 2. Repository Reconnaissance
1. **Map the tree deliberately.** Use `fd`, `tree -L 2`, or repo-specific scripts to sketch the directory layout. Avoid expensive recursive globbing.
2. **Index entry points.** Identify binaries, CLI scripts, and service startup files. For polyglot repos, note language boundaries and shared libraries.
3. **Trace data flows.** Generate call graphs or dependency graphs using tools like `pydeps`, `madge`, or language servers. Record modules that orchestrate I/O, authentication, or network access.
4. **Document findings.** Maintain a running log (e.g., `docs/recon-notes.md`) capturing commands, insights, and open questions that can feed future automation prompts.

## 3. Static Analysis Matrix
Use the following matrix to choose the appropriate static analysis technique.

| Scenario | Goal | Recommended Tools | Execution Notes |
| --- | --- | --- | --- |
| Understand module responsibilities | High-level comprehension | `rg`, language server references, architecture docs | Start from entry points and follow imports downward. |
| Audit configuration/secret handling | Compliance & security | `detect-secrets`, `bandit`, custom regex scanners | Verify `.env` templates and secret managers are used consistently. |
| Validate type contracts | Correctness & refactoring safety | `mypy`, `pyright`, `tsc`, `go vet` | Run in strict mode when possible and capture suppressions that hide issues. |
| Inspect dependency risks | Supply-chain security | `pip-audit`, `npm audit`, `cargo audit` | Export SBOMs for long-running efforts. |
| Find dead or unused code | Maintainability | `vulture`, `ts-prune`, coverage reports | Combine with dynamic coverage for higher confidence. |

**Process:**
1. Prioritize matrix rows based on the objective captured in Section 1.
2. For each selected technique, script the command with deterministic flags (e.g., `--output json`) to aid automation.
3. Record findings with file paths, line numbers, and suggested remediations.

## 4. Dynamic Analysis & Reproduction
1. **Reproduce baseline behavior.** Execute the primary user journey or failing test case. Capture logs, screenshots, and HTTP traces when relevant.
2. **Instrument critical paths.** Add temporary logging, tracing, or feature flags to observe state transitions. Ensure instrumentation is feature-gated to avoid side effects.
3. **Isolate variables.** Toggle configurations, downgrade/upgrade dependencies, and replicate in clean containers to rule out environment skew.
4. **Collect artifacts.** Store failing outputs under `reports/` for reproducibility, noting the command, commit hash, and environment variables.

## 5. Security-Focused Deep Dive
Break the audit into specialized passes:
1. **Threat modeling.** Identify trust boundaries, data ingress/egress points, and attacker goals. Document assumptions and assets.
2. **Authentication & authorization.** Verify enforcement of identity, RBAC, and session management. Review middleware ordering and default-deny policies.
3. **Input validation & sanitization.** Check deserialization, file uploads, and external API calls for validation gaps. Ensure error handling avoids information leaks.
4. **Secrets & configuration.** Inspect key management, rotation policies, and logging redaction. Confirm secrets never land in version control.
5. **Dependency posture.** Run vulnerability scanners, cross-reference with known exploits, and stage patches in feature branches for regression testing.
6. **Observability & response.** Confirm logs, alerts, and dashboards surface anomalous activity. Ensure on-call runbooks exist for escalations.

For each pass, capture proof (file paths, diff snippets, or command outputs) to streamline ticket creation and follow-up automation.

## 6. Automation Hooks for Rodex
1. **Codify commands.** Store vetted commands in `configs/automation_tasks.yml` (or equivalent) with metadata describing prerequisites and expected artifacts.
2. **Define success heuristics.** Specify log patterns or exit codes that agents can assert against to determine pass/fail autonomously.
3. **Template prompts.** Maintain structured prompt templates covering reconnaissance, targeted static analysis, and regression verification. Include clarifying questions to reduce ambiguity.
4. **Feedback loop.** Instruct agents to append findings to a shared knowledge base, tagging by subsystem and severity. Review logs periodically for drift.

## 7. Reporting & Handoff
1. **Synthesize insights.** Summarize root causes, impacted components, and mitigation steps. Use tables for quick scanning.
2. **Recommend next actions.** Prioritize fixes, test additions, and monitoring enhancements. Highlight prerequisites and potential blockers.
3. **Share reproducibility data.** Provide the exact commands, environment info, and commit hashes used in the investigation.
4. **Archive artifacts.** Store reports, traces, and dashboards under version control or designated storage for future audits.

## 8. Continuous Improvement
1. After each engagement, conduct a retro to update this playbook with new heuristics or pitfalls.
2. Track time spent per activity to refine estimates and highlight opportunities for automation.
3. Encourage cross-team knowledge sharing through lunch-and-learns, documentation updates, and pairing sessions.

Adhering to this playbook enables repeatable, high-signal investigations that balance speed with thoroughness and create a solid foundation for autonomous execution by Rodex.
