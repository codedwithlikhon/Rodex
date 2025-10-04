# AI Elements Component Library Overview

[AI Elements](https://www.npmjs.com/package/ai-elements) is a component library and custom registry built on top of [shadcn/ui](https://ui.shadcn.com/) to help you build AI-native applications faster. It provides pre-built components like conversations, messages, and more. You can install it with the dedicated installer component: `<ElementsInstaller />`.

Here are some basic examples of what you can achieve using components from AI Elements: `<ElementsDemo />`.

## Components

Each component in the library ships with interactive previews. Use the `<Preview path="..." />` helper with the provided path names to explore them within your documentation site or Storybook.

- **Actions** (`<Preview path="actions" />`)
- **Artifact** (`<Preview path="artifact" />`)
- **Branch** (`<Preview path="branch" />`)
- **Chain of Thought** (`<Preview path="chain-of-thought" />`)
- **Code Block** (`<Preview path="code-block" />`)
- **Context** (`<Preview path="context" />`)
- **Conversation** (`<Preview path="conversation" className="p-0" />`)
- **Image** (`<Preview path="image" />`)
- **Loader** (`<Preview path="loader" />`)
- **Message** (`<Preview path="message" />`)
- **Open In Chat** (`<Preview path="open-in-chat" />`)
- **Prompt Input** (`<Preview path="prompt-input" />`)
- **Reasoning** (`<Preview path="reasoning" />`)
- **Response** (`<Preview path="response" />`)
- **Sources** (`<Preview path="sources" />`)
- **Suggestion** (`<Preview path="suggestion" />`)
- **Task** (`<Preview path="task" />`)
- **Tool** (`<Preview path="tool" />`)
- **Web Preview** (`<Preview path="web-preview" />`)
- **Inline Citation** (`<Preview path="inline-citation" />`)

View the [source code](https://github.com/vercel/ai-elements) for all components on GitHub.

## Setup

Installing AI Elements is straightforward and can be done in a couple of ways. You can use the dedicated CLI command for the fastest setup, or integrate via the standard shadcn/ui CLI if you have already adopted shadcn's workflow. Either approach invokes the installer component: `<ElementsInstaller />`.

### Prerequisites

Before installing AI Elements, make sure your environment meets the following requirements:

- [Node.js](https://nodejs.org/en/download/), version 18 or later.
- A [Next.js](https://nextjs.org/) project with the [AI SDK](https://ai-sdk.dev/) installed.
- [shadcn/ui](https://ui.shadcn.com/) installed in your project. If you do not have it installed, running any install command will automatically install it for you.
- Using the [AI Gateway](https://vercel.com/docs/ai-gateway) and adding `AI_GATEWAY_API_KEY` to your `env.local` is highly recommended so you can avoid juggling API keys for every provider. AI Gateway provides $5 in usage per month for experimentation.

### Installing Components

You can install AI Elements components using either the AI Elements CLI or the shadcn/ui CLI. Both achieve the same result: adding the selected component's code and any needed dependencies to your project.

The CLI downloads the component's code and integrates it into your project's directory (usually under your components folder). By default, AI Elements components are added to the `@/components/ai-elements/` directory (or whatever folder you have configured in your shadcn components settings).

After running the command, you should see a confirmation in your terminal that the files were added. You can then proceed to use the component in your code.

## Usage

Once an AI Elements component is installed, you can import it and use it in your application like any other React component. Because the source code is colocated with your application, the integration feels natural and transparent.

### Example Conversation Component

```tsx
'use client';

import {
  Message,
  MessageAvatar,
  MessageContent,
} from '@/components/ai-elements/message';
import { useChat } from '@ai-sdk/react';
import { Response } from '@/components/ai-elements/response';

const Example = () => {
  const { messages } = useChat();

  return (
    <>
      {messages.map(({ role, parts }, index) => (
        <Message from={role} key={index}>
          <MessageContent>
            {parts.map((part, i) => {
              switch (part.type) {
                case 'text':
                  return <Response key={`${role}-${i}`}>{part.text}</Response>;
              }
            })}
          </MessageContent>
        </Message>
      ))}
    </>
  );
};

export default Example;
```

In this example, the `Message` component is composed with `MessageContent` and `Response` subcomponents. You can style or configure each component as needed because they live inside your codebase. Explore the underlying files to understand the implementation or layer on custom behavior.

### Extensibility

All AI Elements components accept primitive HTML attributes. For example, the `Message` component extends `HTMLAttributes<HTMLDivElement>`, so you can pass any props that a `div` supports. This design keeps the components flexible while preserving predictable styling defaults.

### Customization

> **Note:** If you reinstall AI Elements by rerunning `npx ai-elements@latest`, the CLI will prompt before overwriting existing files. This safeguard helps you preserve custom changes.

After installation, no additional setup is needed. The component styles (Tailwind CSS classes) and scripts are already integrated. You can start interacting with each component immediately.

For example, to remove rounding on the `Message` component, update `components/ai-elements/message.tsx` and remove the `rounded-lg` class:

```tsx
export const MessageContent = ({
  children,
  className,
  ...props
}: MessageContentProps) => (
  <div
    className={cn(
      'flex flex-col gap-2 text-sm text-foreground',
      'group-[.is-user]:bg-primary group-[.is-user]:text-primary-foreground group-[.is-user]:px-4 group-[.is-user]:py-3',
      className,
    )}
    {...props}
  >
    <div className="is-user:dark">{children}</div>
  </div>
);
```

## Troubleshooting

### Why are my components not styled?

Ensure your project is configured correctly for shadcn/ui in Tailwind CSS. This means having a `globals.css` file that imports Tailwind and includes the shadcn/ui base styles.

### I ran the AI Elements CLI but nothing was added to my project

Double-check the following:

1. Your current working directory is the root of your project (where `package.json` lives).
2. Your `components.json` file (if using shadcn-style config) is set up correctly.
3. You are using the latest version of the AI Elements CLI:

   ```bash
   npx ai-elements@latest
   ```

If the issue persists, open an [issue on GitHub](https://github.com/vercel/ai-elements/issues).

### Theme switching does not work — the app stays in light mode

Ensure your app is using the same `data-theme` system that shadcn/ui and AI Elements expect. The default implementation toggles a `data-theme` attribute on the `<html>` element. Make sure your `tailwind.config.js` is configured with matching selectors.

### The component imports fail with “module not found”

Confirm that the referenced file exists. If it does, verify that your `tsconfig.json` defines the `@/*` path alias:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

### My AI coding assistant cannot access AI Elements components

1. Verify your config file syntax is valid JSON.
2. Confirm that the file path is correct for your AI tool.
3. Restart your coding assistant after making changes.
4. Ensure you have a stable internet connection.

### Still stuck?

If none of these steps resolve the issue, open an [issue on GitHub](https://github.com/vercel/ai-elements/issues) for support.
