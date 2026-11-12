# Idol Media Publisher

A zero-paid-service experiment for monitoring public X profile video feeds and preparing a later YouTube publishing workflow.

## Current status

**Phase 1: optional FxEmbed RSS metadata monitor.** Monitoring is disabled by default. The workflow is manual-only and performs no network requests while disabled.

### Candidate free feed source

FxEmbed documents public RSS media feeds in this format:

- `https://fxtwitter.com/{handle}/media.xml`

The documentation says media-only feeds include posts with videos and that RSS entries can expose an progressive MP4 enclosure when available. The public FxTwitter API documentation says its status API does not require an API key and is free, with fair-use limits.

References:
- RSS feed documentation: https://docs.fxembed.com/guide/advanced/rss-atom-feeds/
- API overview and rate limits: https://docs.fxembed.com/api/introduction/
- X media direct links: https://docs.fxembed.com/guide/url-modifiers/direct-media/

**Important policy uncertainty:** FxEmbed is an independent third-party service, not an X-operated API. Its documentation does not establish that X has authorized it to collect or redistribute X data. X's Terms prohibit scraping without express written permission, and X's automation rules warn against scripting the X website. This feed-based experiment avoids buying X API credits, but we cannot represent it as approved by X or guarantee it is compliant with X's terms. Do not scale or enable unattended reposting without resolving this issue.

X references:
- Terms of Service: https://x.com/en/tos
- Automation rules: https://help.x.com/en/rules-and-policies/x-automation

## Monitored accounts

Edit `config/accounts.json` to add or remove handles. Use usernames without `@`; no code change is needed.

- `WithPJihyo`
- `hyoluvsite`
- `zyo_0201`
- `parkjihyoo__`

## Enable a manual metadata test

1. Open `config/accounts.json`.
2. Change `monitoring_enabled` from `false` to `true`.
3. Commit the change.
4. Open **Actions → Check X Media Feeds → Run workflow**.
5. Inspect `data/latest_report.json` and the action logs.

The first run establishes a baseline and does not mark existing feed entries as new. Later runs report newly observed video posts. The workflow has no automatic schedule at this stage.

## Zero-cost constraints

- No X Developer API token is required by this feed reader.
- Do not purchase X API credits or use paid RSS providers.
- GitHub Actions is configured for the public repository's standard hosted runner and manual checks only.
- The feed provider is a third party; availability, rate limits, and feed completeness may change.

## Publishing stages not implemented

- No MP4 files are downloaded yet; photo-only posts are ignored.
- No YouTube uploads are performed yet.
- YouTube video uploads can be implemented with the free YouTube Data API quota and OAuth, subject to quota and policy requirements.
- Photo posts are intentionally out of scope and ignored.
- The first-stage feed parser records enclosure URLs for metadata inspection only.

Never put API tokens or browser cookies in source files or commit them to GitHub.
