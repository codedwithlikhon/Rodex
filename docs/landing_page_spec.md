# Landing Experience Specification

## Overview
This document defines the implementation contract for the Rodex landing experience so that the shipped UI matches the provided design ("What are we coding next?" workspace selector screen). It captures the user interface structure, focus management requirements, and the supporting backend APIs required to populate the view.

## Screen Structure
1. **Global Header**
   - Left: product logo.
   - Right: profile avatar with status indicator.
2. **Workspace Selector Row**
   - Pills for organization (e.g., `monorepo`) and branch (e.g., `main`).
   - Tabs for `Tasks` and `Archive` views with badge counts.
3. **Hero Panel**
   - Title: "What are we coding next?" (H1, 32px desktop).
   - Subtitle: short hint text (e.g., "Use / to focus the composer").
   - Prompt composer with placeholder "Start typing or paste context…".
   - Primary actions: `Ask` (secondary emphasis) and `Code` (primary emphasis) buttons.
   - Keyboard hint: `/` focuses the composer, `Cmd/Ctrl+Enter` submits.
4. **Task List**
   - Each task card includes title, relative timestamp, repo label, diff stats (+/-), and badge (Merged, In Review, etc.).
   - `Archive` tab reuses card layout but dims metadata.

## Focus Management
- The `Code` button receives default focus when the page loads to match the design highlight.
- Provide a skip link that jumps directly to the prompt composer.
- Use `:focus-visible` outlines on all interactive elements; align outlines with brand color `#9F6BFF` (per design palette) at 2px thickness.
- Implement roving `tabindex` inside the task list to keep focus within a single card while arrow keys move between cards.
- `/` keyboard shortcut invokes `focus()` on the prompt textarea without interfering with native typing.
- Restore focus to the last interacted element after modal or toast interactions, respecting `prefers-reduced-motion`.

## Responsive Behavior
- **≥1280px**: Content centered within 960px max width with the hero and task list in a vertical stack.
- **768–1279px**: Reduce hero padding by 16px, stack the Ask/Code buttons vertically with 12px gap.
- **<768px**: Convert workspace pills into a horizontally scrollable list; ensure 44px touch targets.

## API Contracts
The landing screen relies on three core endpoints served by the planner service.

### GET `/api/workspaces`
Returns the workspaces and branches available to the user.
```json
{
  "workspaces": [
    {
      "id": "monorepo",
      "name": "Monorepo",
      "branches": [
        { "id": "main", "label": "main", "is_default": true }
      ]
    }
  ]
}
```
- Cache for 5 minutes client-side.
- Include `etag` headers for optimistic concurrency.

### GET `/api/tasks?workspace=<id>&branch=<id>&status=<active|archived>`
Delivers task cards for the selected filters.
```json
{
  "tasks": [
    {
      "id": "task_123",
      "title": "Diagnose issues with status updates",
      "status": "merged",
      "repo": "monorepo",
      "branch": "main",
      "created_at": "2025-01-26T22:10:00Z",
      "merged_at": "2025-01-26T23:45:00Z",
      "diff": { "added": 76, "removed": 47 }
    }
  ]
}
```
- Support pagination via `cursor` query parameter.
- Provide `Cache-Control: no-store` to keep data fresh.
- Map `status` to badges (`merged`, `in_review`, `draft`).

### POST `/api/prompts`
Submits the composer content for processing.
```json
{
  "workspace_id": "monorepo",
  "branch_id": "main",
  "mode": "code",  // or "ask"
  "prompt": "Summarize the Gemini streaming outage workarounds."
}
```
Responses include a `job_id` for streaming progress updates.

Errors return problem+json payloads with actionable messages and field-level pointers for inline validation.

## State Management & Loading
- Use React Query (or equivalent) to manage caching, retries, and background refresh of task data.
- Display skeleton cards while fetching tasks; ensure skeletons retain focusable structure for screen readers using `aria-busy`.
- Maintain optimistic UI when creating prompts: append a placeholder task while awaiting backend confirmation.

## Analytics & Telemetry
- Track events for `landing.page_view`, `prompt.submitted`, `task.card_opened`, and `tab.changed` with workspace/branch metadata.
- Respect user consent settings stored in `localStorage` under `rodex:telemetry-consent`.

## Testing Checklist
- Keyboard-only walkthrough verifies default focus, skip links, and `/` shortcut.
- Cypress end-to-end test ensures API responses render correct counts and badges.
- Visual regression test compares hero section against design tokens with 0.1% tolerance.
- Contract tests for the three APIs using `pytest-httpx` mocks.

## Open Questions
- Confirm final palette tokens for badge colors and button gradients.
- Determine whether archived tasks require server-side filtering or client-side transformation.
