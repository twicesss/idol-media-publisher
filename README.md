# Idol Media Publisher

A cloud-run project for monitoring a configurable list of X accounts and preparing new post media for a YouTube publishing workflow.

## Zero-cost requirement

This project is being developed under a strict **no paid services / ₹0** constraint. Do not purchase X API credits, enable auto-recharge, or use a paid provider.

X's current official Developer Platform pricing is consumption-based. Public post reads and user lookups have per-resource charges, so the standard X API is **not considered a free data source** unless X explicitly confirms a free grant for your account. The current monitor is deliberately disabled to prevent accidental API requests.

Official X pricing: https://developer.x.com/

## Current status

**Phase 1: code scaffold only.** The repository currently contains:
- A configurable account list in `config/accounts.json`.
- An X API metadata-monitoring script, gated by `monitoring_enabled: false`.
- A manually triggered GitHub Actions workflow; there is no scheduled polling.
- Configuration tests and a README.

No X API requests are made while `monitoring_enabled` is false. No media is downloaded and nothing is published to YouTube.

## Monitored accounts

Edit `config/accounts.json` to add or remove handles. Use usernames only, without the `@` sign. No Python changes are needed.

- `WithPJihyo`
- `hyoluvsite`
- `zyo_0201`
- `parkjihyoo__`

## Free infrastructure notes

- Standard GitHub-hosted Actions runners are free for public repositories. Avoid larger runners and paid add-ons.
- YouTube Data API requests have a default quota allocation and generally do not incur per-call charges within quota. Quotas and API policies still apply.
- The standard YouTube Data API does not expose a general endpoint for creating Community image posts.
- Any external X monitoring service, proxy, downloader, hosted database, or media API must be checked for a real free tier before use. Do not assume an advertised trial or promotional credit is permanent free access.

GitHub Actions billing: https://docs.github.com/en/billing/concepts/product-billing/github-actions
YouTube Data API quota: https://developers.google.com/youtube/data/getting-started

## If a genuinely free X source becomes available

Only enable `monitoring_enabled` after verifying, in writing or in the official account console, that the X data access route available to this account has no charge and does not require paid credits. Then add `X_BEARER_TOKEN` as a GitHub repository secret, if that authorized route uses it.

Never commit API tokens or paste them into source files.

## Important operating notes

- This is not yet a functioning unattended publisher. The X monitor is intentionally disabled.
- Media retrieval must use an authorized source, and video/photo use must be appropriate for the destination platform.
- Scheduled GitHub Actions runs were removed to avoid unintended repeated API use.
