# Vercel Framework and Build Settings Reference

This guide consolidates how Vercel configures and customizes build settings for Rodex deployments. Use it when you need to override the default behavior detected by Vercel or when you are preparing a new application directory for deployment.

## Framework Detection Workflow

Vercel performs a shallow clone (`git clone --depth=10`) of the repository at deploy time. It then inspects the project structure to auto-detect supported frameworks such as Next.js, Svelte, Nuxt, Vite, or FastAPI.

- When a framework is detected, Vercel pre-populates the **Framework Preset**, **Build Command**, **Output Directory**, **Install Command**, and **Development Command** with recommended defaults.
- If no framework is detected, Vercel selects **Other** and enables manual overrides.
- You can override defaults per project from the dashboard (`Project → Settings → Build & Development Settings`) or per deployment via `vercel.json`.

## Core Settings

### Framework Preset

Choose the framework that best matches your project:

- Selecting a preset adjusts the build, install, and output defaults.
- The **Override** toggle unlocks custom commands even when a preset is selected.
- To force a preset for a single deployment, set `"framework": "<preset-name>"` in `vercel.json`.

### Build Command

By default, Vercel maps to the framework-specific build script—e.g., `npm run build` for Vite, `next build` for Next.js.

- Enable **Override** to specify a custom build command for all deployments.
- To override per deployment, add `"buildCommand": "..."` to `vercel.json`.
- Leave the command empty (with **Other** selected) to skip the build entirely for static assets.

### Output Directory

Only artifacts in the configured output directory are served statically.

- Framework presets populate this automatically (e.g., `dist` for Vite).
- Setting **Other** defaults to `public/` if present, otherwise the project root.
- Override globally from the dashboard or per deployment via `"outputDirectory"` in `vercel.json`.

### Install Command

Vercel auto-detects the package manager (`npm`, `yarn`, `pnpm`, `bun`) and installs dependencies during the build.

- Customize the install command at the project level from the dashboard.
- Per-deployment overrides are supported through `vercel.json`.
- API routes continue to use framework-managed installers and cannot be customized.

### Development Command

`vercel dev` uses the detected framework command (e.g., `next dev`).

- Override the development command when you need custom behavior, ensuring your script passes the `$PORT` variable.
- If **Other** is selected and the command is left blank, `vercel dev` will fail.
- The project must be linked with `vercel` and have at least one deployment before `vercel dev` works correctly.

### Skip Build Step

For static sites that do not require compilation:

1. Select **Other** as the framework.
2. Enable **Override** on the Build Command.
3. Leave the command empty to bypass the build.

## Root Directory Management

Use the **Root Directory** setting when the deployable project lives in a subfolder (e.g., `frontend/`).

- Files outside the root cannot be accessed during the build, and `..` paths are blocked.
- Toggle **Include files outside of the Root Directory in the Build Step** if shared assets (e.g., workspace-wide configs) must be available.
- Enable **Skip builds with no changes** to avoid unnecessary deployments when the root and its dependencies are untouched.
- The setting applies to the dashboard and `vercel` CLI.
- Update the root directory and redeploy to apply changes.

## Node.js Version

Set the Node.js runtime used during builds and serverless execution.

- Changing the version requires a new deployment to take effect.
- Align the version with your local development environment to avoid mismatches.

## Corepack Support

To pin a specific package-manager version:

1. Add the environment variable `ENABLE_EXPERIMENTAL_COREPACK=1`.
2. Declare the manager in `package.json`:

   ```json
   {
     "packageManager": "pnpm@7.5.1"
   }
   ```

Corepack remains experimental and may change with future Node.js releases.

## Environment-Specific Guidance

### Prioritizing Production Builds

Enable **Prioritize Production Builds** when production deploys must jump the queue ahead of previews.

### On-Demand Concurrent Builds

Use this feature to unlock additional parallel build capacity when previews and hotfixes need to run simultaneously.

## Open Graph & Social Metadata Inspection

Every deployment exposes an **Open Graph** tab in the Vercel dashboard to preview OG and Twitter cards per route.

- Inspect metadata such as `og:title`, `og:description`, `og:image`, and `og:url`.
- Use the path filter to validate multiple routes within the same deployment.

### Example: Dynamic OG Image Metadata

```jsx
<div>
  <head>
    <meta name="og:title" content="Vercel CDN" />
    <meta name="og:description" content="Vercel CDN" />
    <meta
      name="og:image"
      content={`${
        process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : ""
      }/api/vercel`}
    />
    <meta name="og:url" content="https://vercel.com/docs/cdn" />
  </head>
  <h1>A page with Open Graph Image.</h1>
</div>
```

### Example: Twitter Card Metadata

```jsx
<div>
  <head>
    <meta name="twitter:title" content="Vercel CDN for Twitter" />
    <meta name="twitter:description" content="Vercel CDN for Twitter" />
    <meta
      name="twitter:image"
      content="https://og-examples.vercel.sh/api/static"
    />
    <meta name="twitter:card" content="summary_large_image" />
  </head>
  <h1>A page with Open Graph Image.</h1>
</div>
```

## Speed Insights

Enable **Speed Insights** from the project settings to collect metrics on loading speed, responsiveness, visual stability, and other Core Web Vitals for each deployment.

## Environments and Deployment Lifecycle

Vercel organizes deployments into **Production**, **Preview**, and **Development** environments.

- Use environments to stage changes safely while maintaining a stable production baseline.
- Environment protection rules ensure only authorized reviewers can promote builds.
- Combine environment scopes with **Deployment Protection** when you need gated access to sensitive routes.

## Deployment Checkpoints

1. Review or override framework settings as needed.
2. Confirm the root directory matches the intended app folder.
3. Align the Node.js version with local development.
4. Enable Corepack if you need deterministic package-manager versions.
5. Validate OG/Twitter metadata with the dashboard preview tools.
6. Monitor Speed Insights to verify the end-user experience.

Keep these checkpoints in your deployment runbook to ensure smooth Vercel builds across projects.
