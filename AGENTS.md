# Agent Guidance

## Purpose of This File

The `AGENTS.md` file complements `README.md` by focusing on workflow details that are especially important for coding agents. While the README stays oriented toward human contributors, this document captures the conventions and guardrails that help automated contributors operate effectively without cluttering contributor-facing docs.

## Working Agreements

- **Communication**
  - Use clear, concise commit messages that describe the "why" behind changes.
  - When raising a PR, summarize both the functional change and the validation steps that were run locally.

- **Development Workflow**
  - Prefer small, reviewable commits. Keep the main branch deployable.
  - When adding dependencies, ensure they are declared in `pyproject.toml` and update any lockfiles if present.

- **Testing Expectations**
  - Run `pytest` before pushing Python changes.
  - Capture and document any deviations from green test runs along with remediation plans.

- **Documentation**
  - Update relevant docs in `docs/` when behavior or workflows change.
  - Add docstrings and inline comments for complex logic.

## UI Guidance

Follow these baseline principles when working on frontend assets to ensure accessible, fast, and delightful experiences:

### Interactions
- MUST: Provide full keyboard support in line with WAI-ARIA Authoring Practices.
- MUST: Maintain visible focus indicators using `:focus-visible` and `:focus-within` where appropriate.
- MUST: Manage focus programmatically (trap, move, and restore) per relevant APG patterns.

### Targets & Input
- MUST: Ensure tap/click targets are at least 24px (44px on mobile). If the visual affordance is smaller, expand the hit area.
- MUST: Keep mobile input font sizes ≥16px or define the proper viewport meta tag.
- NEVER: Disable browser zoom.
- MUST: Set `touch-action: manipulation` to avoid double-tap zoom and align `-webkit-tap-highlight-color` with the design system.

### Forms & Validation
- MUST: Preserve focus and input values during hydration.
- NEVER: Block paste actions in inputs or textareas.
- MUST: Show spinners on loading buttons while retaining the original label.
- MUST: Trigger form submission with Enter on text inputs and Ctrl/Cmd+Enter within textareas (with Enter adding a newline).
- MUST: Keep submit buttons enabled until a request is initiated, then disable and use idempotency safeguards.
- MUST: Accept user input optimistically and validate after submission, surfacing inline errors and focusing the first one.
- MUST: Configure `autocomplete`, semantic input types, and `inputmode` appropriately.
- SHOULD: Disable spellcheck for emails, codes, and usernames.
- SHOULD: Use placeholder text with ellipses that demonstrate expected formatting.
- MUST: Warn before navigating away when unsaved changes exist.
- MUST: Support password managers and 2FA flows, including paste for one-time codes.
- MUST: Trim values to mitigate text expansion issues.
- MUST: Ensure checkbox and radio labels share the interactive hit target.

### State & Navigation
- MUST: Reflect navigation state in the URL for deep links.
- MUST: Restore scroll position when navigating back/forward.
- MUST: Use `<a>` or router link components for navigational elements to support standard browser behaviors.

### Feedback & Messaging
- SHOULD: Employ optimistic UI updates with reconciliation on response.
- MUST: Confirm destructive actions or provide an undo option.
- MUST: Use polite `aria-live` regions for toasts and validation feedback.
- SHOULD: Use ellipsis characters (…) to hint at follow-up actions.

### Touch, Drag & Scroll
- MUST: Provide generous targets and avoid finicky gestures.
- MUST: Stagger tooltip delays within groups to avoid overwhelming the user.
- MUST: Contain overscroll in modals and drawers.
- MUST: Disable text selection during drags and set `inert` where appropriate.
- MUST: Avoid inactive interactive-looking UI elements.

### Autofocus & Animation
- SHOULD: Autofocus primary inputs on desktop when appropriate; avoid on mobile to prevent layout shifts.
- MUST: Respect `prefers-reduced-motion` and stick to compositor-friendly properties (transform, opacity).
- SHOULD: Use animation to clarify cause and effect, ensuring interactions are interruptible and context-aware.

### Layout & Content
- SHOULD: Favor optical alignment and consistent spacing.
- MUST: Validate designs across breakpoints, including ultra-wide displays.
- MUST: Respect safe-area insets and prevent unwanted scrollbars.
- MUST: Provide resilient layouts for varying content densities.
- MUST: Supply semantic headings, `scroll-margin-top`, and skip links for accessibility.
- MUST: Ensure accessible names, redundant status cues, and appropriate use of native semantics.

### Performance & Design Quality
- MUST: Test under constrained CPU/network conditions and minimize reflows.
- MUST: Keep mutation latency under 500 ms and virtualize large lists.
- MUST: Prevent layout shifts by reserving space for images and preload only above-the-fold assets.
- SHOULD: Compose layered shadows and hue-consistent palettes with appropriate contrast per APCA.

These guidelines are additive to the primary documentation and help ensure agent contributions remain accessible, performant, and user-friendly.
