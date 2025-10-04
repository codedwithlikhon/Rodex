# AI SDK Overview

> **Note**
> This page offers a beginner-friendly summary of the high-level concepts behind the AI SDK. If you are ready to build, jump straight to the [quickstarts](/docs/getting-started) or browse the [supported models and providers](/docs/foundations/providers-and-models).

The AI SDK standardizes how you integrate artificial intelligence (AI) models across [supported providers](/docs/foundations/providers-and-models). By abstracting provider-specific details, the SDK lets teams focus on delivering great AI experiences instead of wrestling with glue code.

```ts
import { generateText } from "ai";
import { google } from "@ai-sdk/google";

const { text } = await generateText({
  model: google("gemini-2.5-flash"),
  prompt: "What is love?",
});
```

## Core AI Concepts

### Generative Artificial Intelligence

Generative models predict and produce outputs—text, images, or audio—based on the statistical patterns they learned during training. Example capabilities include:

- Generating a caption for a photo.
- Producing a transcription from an audio file.
- Creating an image that matches a text description.

### Large Language Models

Large language models (LLMs) specialize in text. Given an input sequence, an LLM predicts the most likely next tokens until a stopping condition is met. Training on massive text corpora makes them excellent at language-centric tasks, but it also means they can fabricate details when data is sparse—plan for this when designing user experiences.

### Embedding Models

Embedding models transform complex inputs into dense numerical vectors. Instead of generating new data, embeddings express semantic and syntactic relationships, powering search, clustering, recommendation, and retrieval-augmented generation workflows.

## Working with Tools

Although LLMs excel at free-form generation, they are less reliable at discrete reasoning or interacting with external systems. Tools extend an LLM’s abilities by letting it perform specific actions—query an API, retrieve data, or trigger side effects—and feed the results back into the conversation.

A tool definition includes three parts:

- **`description`** – Optional context that helps the model decide when to call the tool.
- **`inputSchema`** – A JSON Schema or [Zod](https://zod.dev/) schema describing required parameters. The SDK uses this schema both for the model prompt and for runtime validation.
- **`execute`** – An optional async function that runs when the model invokes the tool.

```ts
import { generateText, tool } from "ai";
import { z } from "zod";

const result = await generateText({
  model: "openai/gpt-4o",
  prompt: "What is the weather in San Francisco?",
  tools: {
    weather: tool({
      description: "Get the weather in a location",
      parameters: z.object({
        location: z.string().describe("The location to get the weather for"),
      }),
      execute: async ({ location }) => ({
        location,
        temperature: 72 + Math.floor(Math.random() * 21) - 10,
      }),
    }),
  },
});

console.log(result.toolResults);
```

### Schemas and Toolkits

Define tool parameters with either the built-in JSON Schema helper or Zod. Beyond application-specific tools, you can adopt prebuilt toolkits from providers such as Agentic, Browserbase, Browserless, Stripe, StackOne, Toolhouse, Agent Tools, AI Tool Maker, Composio, Interlify, and JigsawStack.

For deeper dives, see the AI SDK Core guidance on [tool calling](/docs/ai-sdk-core/tools-and-tool-calling) and [agents](/docs/foundations/agents).

## Streaming Experiences

LLM responses can take several seconds, so fully blocking UIs often feel sluggish. Streaming interfaces address this by displaying partial results as they arrive—ideal for chat or long-form generation. Consider streaming when you need responsive user feedback or when long outputs are common.

```ts
import { openai } from "@ai-sdk/openai";
import { streamText } from "ai";

const { textStream } = streamText({
  model: openai("gpt-4.1"),
  prompt: "Write a poem about embedding models.",
});

for await (const textPart of textStream) {
  console.log(textPart);
}
```

## Agent Patterns

Agents combine three ingredients in a loop: an LLM, tools, and control flow that governs how and when the model calls those tools. Start simple with single-shot text generation, then add tools for data retrieval or side effects, and finally orchestrate multi-step workflows when problems require iterative reasoning.

The SDK supports both a high-level `Agent` class and lower-level primitives such as `generateText`/`streamText` with explicit loop control. Use the managed loop when you want rapid iteration, or implement a manual loop for deterministic, auditable behavior.

When reliability is paramount, blend tool usage with conventional programming techniques—conditionals, reusable functions, and error handling—to keep complex flows predictable.

## Prompt Format for Referencing Documentation

When you need to cite this material in downstream prompts, use the following structure:

```
Documentation:
{paste documentation here}
---
Based on the above documentation, answer the following:
{your question}
```

This format keeps citations organized and ensures the model receives the necessary context alongside your question.

## Additional Resources

- [Agent Class](/docs/agents/agent-class)
- [Loop Control](/docs/agents/loop-control)
- [Workflow Patterns](/docs/agents/workflows)
- [Manual Loop Example](/cookbook/node/manual-agent-loop)

