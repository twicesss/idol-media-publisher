# Idol Media Publisher

A cloud-run project for monitoring a configurable list of X accounts and preparing new post media for a YouTube publishing workflow.

## Current status

**Phase 1: X post metadata monitoring scaffold.** The current workflow:
- Reads account handles from `config/accounts.json`.
- Runs every 30 minutes through GitHub Actions (or manually via workflow dispatch).
- Uses the official X API to read post metadata and media attachment metadata.
- Records discovered post IDs and a report in `data/`.
- Does not download media or publish anything to YouTube yet.

Media retrieval and publishing are separate implementation stages. X media metadata is not itself a guaranteed downloadable video file.

## Monitored accounts

Edit `config/accounts.json` to add or remove handles. Use usernames only, without the `@` sign. No Python changes are needed.

- `WithPJihyo`
- `hyoluvsite`
- `zyo_0201`
- `parkjihyoo__`

## Setup

1. Create an X Developer project/app and obtain an API Bearer Token with permission to read the posts this app needs.
2. In this GitHub repository, open **Settings → Secrets and variables → Actions**.
3. Add a repository secret named `X_BEARER_TOKEN` with the Bearer Token value.
4. Open **Actions → Monitor X Accounts → Run workflow** to perform a test run.
5. Scheduled checks run every 30 minutes. If the secret is not configured, live monitoring is skipped safely.

Never commit API tokens or paste them into source files.

## X API cost note

X currently uses pay-per-usage credits. Its official pricing page lists post reads at **US$0.005 per returned post** and user reads at **US$0.010 per returned user**. Repeated resources are generally deduplicated within a 24-hour UTC window, but X describes this as a soft guarantee. Check the Developer Console for current rates and set a spending limit before enabling monitoring.

Official pricing: https://docs.x.com/x-api/getting-started/pricing

## YouTube integration

Video uploads will use the YouTube Data API after OAuth setup. Google's current documentation describes a default daily allowance of 100 video uploads in its dedicated upload quota bucket. Actual access remains subject to account, project, and policy requirements.

- Upload endpoint: https://developers.google.com/youtube/data/reference/rest/v3/videos/insert
- API overview: https://developers.google.com/youtube/data/getting-started

The standard YouTube Data API does not expose a general endpoint for creating Community image posts. Photo publishing needs a separately verified supported route before it can be automated.

## Local checks

Run `python -m unittest discover -s tests -v`.

## Important operating notes

- GitHub Actions scheduled jobs run on GitHub-hosted runners and can be delayed during high load.
- This project is not yet a fully unattended publisher; current code discovers metadata only.
- Media retrieval must use an authorized source, and video/photo use must be appropriate for the destination platform.
