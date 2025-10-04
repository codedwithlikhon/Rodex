# Railway Templates Overview

Railway templates package one or more services into a reusable scaffold so that new projects can be provisioned in just a few clicks. They are the preferred way to distribute Rodex (and other multi-service applications) because they bundle infrastructure defaults, environment variables, and build commands into a single, repeatable definition.

## Key Benefits

### Bootstrap Projects Quickly
Templates make it simple to stand up a working stack without copy-pasting configuration between repositories. Consumers pick a template from the marketplace (or their personal scaffold), deploy it, and Railway takes care of building every service that the template defines.

### Encode Best Practices
Well-crafted templates capture opinions about service composition, environment variables, health checks, and deployment commands. By shipping these defaults, you help every consumer of the template align with the conventions that keep the project healthy.

### Build Community Clout
When you publish a template it appears in Railway's public marketplace, making it discoverable by the broader community. Great templates showcase your project, bring in new users, and serve as executable documentation for how it should be deployed.

### Participate in the Kickback Program
Railway shares 50% of the usage revenue incurred by deployments created from marketplace templates. Publishing and maintaining high-quality templates is therefore both a service to the community and a way to offset your own infrastructure costs.

## Affiliate Program Requirements

If you plan to promote your template through Railway's affiliate program, make sure you satisfy the following guardrails before you start sharing your referral link:

- **Valid Railway account** – Sign up for a Railway account (free) so referral activity can be attributed correctly.
- **Compliance with Terms of Service** – Ensure your project and promotional material respect Railway's Fair Use Policy and the broader Terms of Service.
- **High-quality, relevant content** – Keep your template and marketing materials aligned with Railway's mission. Commissions are only paid when referrals become successful customers.
- **Use the official referral link** – Only signups originating from your unique link qualify for the 15% revenue share, so include it prominently in your outreach.

Adhering to these requirements keeps your affiliate efforts eligible for commissions and signals to Railway that your template is worth featuring in the marketplace.

## Updatable Templates

Templates that pull source code directly from a GitHub repository can be kept up to date after the initial deployment:

1. **Automatic branch creation** – When the upstream repository changes, Railway creates a new branch in the consumer's forked repo to track the update.
2. **Preview via PR deploys** – The branch appears as a pull request so maintainers can validate the update with ephemeral environments before merging.
3. **One-click promotion** – Merging the pull request triggers a fresh deployment, promoting the changes to production without manual reconfiguration.

This workflow only applies to services sourced from GitHub repositories. Railway does not yet track updates for Docker-image-based services, so those must be upgraded manually.

## Best Practices for Authors

- **Document assumptions** – Explain required secrets, resource plans, and external dependencies so deployers are never surprised.
- **Keep repos template-friendly** – Store infrastructure files (such as `railway.json`, `nixpacks.toml`, and `Procfile`) at the repository root so Railway can detect them automatically.
- **Test upgrades** – Use the updatable templates flow yourself to ensure that downstream projects receive safe, reversible updates.
- **Version consciously** – Tag releases in GitHub and reference them in template definitions when you need deterministic builds.

## Additional Resources

- [Railway Templates Documentation](https://docs.railway.app/deploy/your-own-template)
- [Updatable Templates Blog Post](https://blog.railway.app/p/updatable-templates)
- [`docs/deployments/railway-template.md`](./railway-template.md) for Rodex-specific deployment details.
