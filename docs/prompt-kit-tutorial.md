# Build AI-Native Interfaces with prompt-kit

## Introduction
prompt-kit is an open-source component system for building AI-native
applications with React. It ships ready-to-use interface primitives—chat
threads, agent dashboards, prompt editors, and evaluation tools—designed to
work seamlessly with modern model providers. Instead of wiring together
low-level UI building blocks, prompt-kit packages sensible defaults and
observability patterns so teams can launch production-ready AI experiences
faster.

This tutorial walks through a complete prompt-kit integration in a new React
application. Along the way you will learn:

- What "AI-native" means in practice and how prompt-kit accelerates those
  workflows.
- How prompt-kit aligns with [shadcn/ui](https://ui.shadcn.com) to deliver a
  cohesive design system.
- How to scaffold core AI interfaces—chat conversations, agent handoffs,
  prompt editors, and analytics dashboards.
- Techniques for customization, theming, and troubleshooting.

The guide assumes you are comfortable with JavaScript or TypeScript and that
you have previously built a React application. Each step includes the rationale
for the action, concrete commands, and pointers to additional documentation so
that both newcomers and experienced developers can follow along.

## What Is an AI-Native Application?
An AI-native application places large language models (LLMs) or other
foundation models at the center of the product experience. Instead of adding
"AI features" as an afterthought, AI-native apps expose capabilities such as
natural-language chat, autonomous agent orchestration, inline evaluation, or
prompt experimentation as first-class workflows. These requirements introduce
unique UI challenges: managing streaming responses, surfacing model metadata,
collecting user feedback, and handling fallbacks when automation fails.

prompt-kit addresses these needs with opinionated React components that
coordinate UI state, accessibility, and network lifecycles, letting you focus
on your product logic rather than rebuilding interface plumbing from scratch.

## Relationship to shadcn/ui
prompt-kit builds on top of the design tokens and primitives published by
[shadcn/ui](https://ui.shadcn.com), a popular component toolkit for Tailwind
CSS and Radix UI. Because of this relationship, prompt-kit components inherit
accessible keyboard interactions, consistent theming, and a Tailwind-friendly
class structure. You will install shadcn/ui alongside prompt-kit to ensure the
components share typography, spacing, and motion patterns. If you already use
shadcn/ui in your project, prompt-kit will feel familiar and require minimal
styling changes.

## Prerequisites
Before you begin, make sure your environment satisfies the following
requirements:

- **Node.js 18.17+** – prompt-kit targets modern Node runtimes with native
  fetch and Web Streams. Install via [Node.js downloads](https://nodejs.org/en)
  or your preferred version manager.
- **Package manager** – examples use `pnpm` 8.15.1, but `npm` or `yarn` also
  work.
- **React 18.2+** – prompt-kit expects concurrent rendering features and the
  latest context APIs. See the [React documentation](https://react.dev/learn)
  for upgrade guidance.
- **Tailwind CSS 3.4+** – required for shadcn/ui theming.

If you are retrofitting an existing codebase, verify these versions before
proceeding. Upgrading first prevents subtle runtime incompatibilities later.

## Step 1 – Scaffold a React Application
Start by creating a new Next.js application, which offers server components and
API routes ideal for AI workloads. If you prefer Vite or Remix, adjust the
commands accordingly; the prompt-kit usage patterns remain identical.

```bash
pnpm create next-app@14.1.0 ai-native-app \
  --typescript \
  --eslint \
  --tailwind \
  --src-dir \
  --app \
  --import-alias "@/*"
cd ai-native-app
```

This step creates a TypeScript-ready project with Tailwind configured, matching
the requirements listed above. Inspect `package.json` to confirm `next@14.1.0`
and `react@18.2.0` are installed.

## Step 2 – Install prompt-kit and shadcn/ui
With the project scaffolded, install prompt-kit, shadcn/ui, and supporting
packages. Installing together ensures consistent peer dependencies.

```bash
pnpm add @promptkit/react@0.9.2 @promptkit/core@0.9.2
pnpm dlx shadcn-ui@0.8.0 init
```

- `@promptkit/core` bundles shared state machines, utilities, and model
  adapters.
- `@promptkit/react` contains the component wrappers that render UI elements.
- The `shadcn-ui` CLI seeds a `components/` directory with foundational UI
  primitives used throughout prompt-kit.

After running the CLI, follow the interactive prompts to confirm the Tailwind
config path (`tailwind.config.js`), CSS entry point (`src/app/globals.css`), and
component directory (`src/components`). The CLI prints a success message
outlining generated files.

## Step 3 – Configure Tailwind and Theme Tokens
prompt-kit expects Tailwind to expose shadcn/ui tokens. Update your
configuration to include the library paths so that Tailwind processes prompt-kit
styles.

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";
import baseConfig from "./tailwind-shadcn.config";

const config: Config = {
  presets: [baseConfig],
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./node_modules/@promptkit/react/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
};

export default config;
```

The preset import (`tailwind-shadcn.config`) is added by the shadcn/ui CLI. By
including prompt-kit in the `content` array, Tailwind generates the necessary
utility classes for each component.

Next, initialize the global styles. The snippet below merges Tailwind base
styles with prompt-kit theme variables.

```css
/* src/app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --promptkit-font-sans: var(--font-sans);
  --promptkit-radius-md: 0.75rem;
}
```

Adding these variables lets you tweak fonts and radii across all prompt-kit
components from a single location.

## Step 4 – Set Up the PromptKitProvider
prompt-kit exposes context providers for session management, model selection,
and telemetry. Wrap your app with `PromptKitProvider` so components can access
the configuration.

```tsx
// src/app/layout.tsx
import "./globals.css";
import { Inter } from "next/font/google";
import { PromptKitProvider } from "@promptkit/react";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        <PromptKitProvider
          apiBaseUrl="/api/promptkit"
          defaultModel="gpt-4o-mini"
          appearance={{
            colorMode: "system",
            accentColor: "violet",
          }}
        >
          {children}
        </PromptKitProvider>
      </body>
    </html>
  );
}
```

This provider establishes a default model and API endpoint that the React
components use when issuing requests. Adjust `apiBaseUrl` to match your server
implementation or proxy configuration.

## Step 5 – Implement a Chat Interface
Chat is the most common AI pattern. prompt-kit ships a `Chat` component that
supports streaming tokens, system messages, and quick replies.

```tsx
// src/app/chat/page.tsx
import { Chat, ChatComposer } from "@promptkit/react/chat";
import { Card } from "@/components/ui/card";

export default function ChatPage() {
  return (
    <main className="container py-10 space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold">Research Assistant</h1>
        <p className="text-muted-foreground">
          Ask domain questions and receive grounded answers with citations.
        </p>
      </header>

      <Card className="p-0">
        <Chat
          sessionId="research-assistant"
          instructions="You are a focused research assistant. Answer with bullet points and cite sources."
          emptyState={{
            title: "Start a conversation",
            description:
              "Share a research question or paste a paragraph to summarize.",
            ctaLabel: "Ask a question",
          }}
        />
        <ChatComposer
          className="border-t"
          placeholder="Ask a follow-up..."
          shortcuts={[{
            label: "Summarize",
            prompt: "Summarize the previous response in three bullet points.",
          }]}
        />
      </Card>
    </main>
  );
}
```

The `Chat` component consumes the provider configuration and automatically
synchronizes conversation state with your backend. Pairing it with
`ChatComposer` delivers an accessible input experience with multi-line editing
and slash commands. When the page loads, users see an empty state guiding them
through the interaction.

### Server Route Example
To complete the loop, create an API route that proxies requests to your LLM.
This example uses the OpenAI SDK, but any provider can work.

```ts
// src/app/api/promptkit/route.ts
import { NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";
import { streamChatCompletions } from "@promptkit/core/server";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function POST(req: NextRequest) {
  const body = await req.json();

  const stream = await streamChatCompletions({
    client: openai,
    model: body.model,
    messages: body.messages,
  });

  return new NextResponse(stream);
}
```

`streamChatCompletions` abstracts away chunking and backpressure management,
providing a `ReadableStream` that Next.js can send to the browser.

## Step 6 – Explore Additional Components
prompt-kit includes specialized components tailored for AI workflows. Install
and register each one with the shadcn/ui CLI to ensure style parity.

```bash
pnpm dlx shadcn-ui@0.8.0 add chart card tabs tooltip progress
```

The command above adds supporting primitives used by prompt-kit dashboards and
inspectors. With these in place, you can render additional AI interface pieces:

### PromptPlayground
Use `PromptPlayground` to experiment with system prompts, model parameters, and
input variables in real time.

```tsx
import { PromptPlayground } from "@promptkit/react/playground";

<PromptPlayground
  template={`You are a travel planner. Draft a 3-day itinerary for {{city}}.`}
  variables={{ city: "Lisbon" }}
  parameters={{ temperature: 0.4, maxTokens: 600 }}
  onRun={(result) => console.log(result)}
/>
```

Developers can bind `onRun` to persist experiments or populate regression tests.

### AgentTimeline
`AgentTimeline` visualizes agent tasks, tool executions, and handoffs to human
operators.

```tsx
import { AgentTimeline } from "@promptkit/react/agents";

<AgentTimeline
  runs={[
    {
      id: "1",
      name: "Ingest knowledge base",
      status: "completed",
      durationMs: 15400,
      toolCalls: [
        { id: "web-scraper", label: "Web Scraper", status: "completed" },
        { id: "vector-store", label: "Vector Store", status: "completed" },
      ],
    },
    {
      id: "2",
      name: "Draft summary",
      status: "requires_action",
      message: "Need clarification on target audience.",
    },
  ]}
  onResolveRun={(runId) => console.log("Resolve run", runId)}
/>
```

This component helps support teams triage automation gaps and audit decision
history.

### EvalBoard
`EvalBoard` presents aggregated evaluation scores across prompts or model
versions.

```tsx
import { EvalBoard } from "@promptkit/react/evals";

<EvalBoard
  metrics={[
    { id: "accuracy", label: "Accuracy", value: 0.87 },
    { id: "toxicity", label: "Toxicity", value: 0.02 },
  ]}
  runs={[
    {
      id: "weekly-run",
      label: "Weekly Regression",
      createdAt: "2024-03-01T08:00:00Z",
      metrics: { accuracy: 0.87, toxicity: 0.02 },
    },
  ]}
/>
```

Evaluators can track model quality over time without building bespoke charts.

## Component Catalog and Use Cases
| Component | Use Case | Notes |
|-----------|----------|-------|
| `Chat`, `ChatComposer` | Conversational interfaces, support copilots | Handles streaming, attachments, slash commands |
| `PromptPlayground` | Prompt engineering workflows | Compare prompts and parameter sweeps |
| `AgentTimeline` | Agentic automation and human-in-the-loop | Visualizes tool calls, supports resolution actions |
| `EvalBoard` | Model evaluation dashboards | Aggregates test runs and quality metrics |
| `InlineFeedback` | Collecting thumbs-up/down, free-form notes | Persists signals to analytics pipelines |
| `KnowledgePanel` | Presenting retrieved documents | Displays citations, highlights, and confidence |

Each component ships with TypeScript types and sensible fallbacks for loading
and error states.

## Customization and Theming
prompt-kit embraces Tailwind utility classes, making customization straightforward.

1. **Override CSS variables** – Update values in `globals.css` to tweak fonts,
   radii, or color accents globally.
2. **Use the `appearance` prop** – Most components accept `appearance` props for
   per-instance theming, such as dark mode overrides.
3. **Extend shadcn/ui primitives** – Because prompt-kit composes shadcn/ui
   components, you can wrap primitives (e.g., `Button`, `Card`) to introduce
   brand-specific styles.

Example: customizing the chat composer button.

```tsx
import { ChatComposer } from "@promptkit/react/chat";
import { Button } from "@/components/ui/button";

<ChatComposer
  actions={(state) => (
    <Button
      type="submit"
      disabled={state.isSending}
      className="bg-emerald-500 hover:bg-emerald-600"
    >
      {state.isSending ? "Sending..." : "Send"}
    </Button>
  )}
/>
```

This override keeps the accessible behavior while matching your brand colors.

## Best Practices for Integration
- **Isolate model logic** – Keep prompt-kit components declarative by pushing
  API calls into dedicated services. This approach simplifies testing and lets
  you swap providers without touching the UI.
- **Stream responses** – Use `streamChatCompletions` or the equivalent for your
  provider to minimize latency and improve perceived performance.
- **Log interactions** – prompt-kit surfaces events like `onMessageSent` and
  `onFeedback` for analytics. Connect these to your observability stack.
- **Write integration tests** – Employ React Testing Library to ensure custom
  theming and error states render as expected.
- **Guard secrets** – Never expose API keys in the browser. Route all model
  calls through server-side functions or edge handlers.

## Troubleshooting
| Symptom | Cause | Resolution |
|---------|-------|------------|
| Tailwind classes missing on prompt-kit components | Tailwind `content` array excludes node module paths | Add `"./node_modules/@promptkit/react/**/*.{js,ts,jsx,tsx}"` to `tailwind.config.ts` and restart the dev server |
| Dark mode tokens not applied | Missing CSS variables for shadcn/ui theme | Verify `PromptKitProvider` `appearance` prop and ensure `className={inter.variable}` is set on `<html>` |
| Chat not streaming responses | API route returns JSON instead of stream | Return the `ReadableStream` from `streamChatCompletions` without buffering |
| `PromptKitProvider` throws missing API key error | Environment variable not loaded | Configure `.env.local` and restart `next dev` |

When in doubt, inspect the browser console for warnings emitted by prompt-kit;
they often link to detailed remediation guides.

## Next Steps and Additional Resources
You now have a fully functioning AI-native interface built with prompt-kit.
Extend the tutorial by:

1. Connecting telemetry events to your analytics pipeline to track usage.
2. Adding `InlineFeedback` to capture user sentiment per response.
3. Building multi-agent workflows with `AgentTimeline` and server-side task
   orchestration.

For deeper exploration, consult the following references:

- [prompt-kit Documentation](https://github.com/prompt-kit) – component API
  reference and roadmap.
- [shadcn/ui Docs](https://ui.shadcn.com) – theming, CLI commands, and component
  primitives.
- [React Official Documentation](https://react.dev) – concurrent rendering
  patterns and hooks.
- [Node.js Guides](https://nodejs.org/docs/latest/api/) – runtime APIs and
  deployment best practices.

With these resources and prompt-kit components, you can deliver responsive,
accessible, and maintainable AI-native experiences without rebuilding the UI
stack from scratch.
