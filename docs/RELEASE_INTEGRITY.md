# FinTrack Mac: release integrity checklist

The macOS build workflow compiles a pinned Mint Leaf v4.2 revision, applies the FinTrack patch, runs Python and XCTest checks, then produces unsigned arm64 ZIP and DMG artifacts.

## Before publishing

- Require a successful `push` run on `main`, not a manual or pull-request run.
- Confirm the tested source commit belongs to the current `main` history.
- Reject duplicate or older build numbers and retry on concurrent updates.
- Keep the build job's GitHub token read-only; reserve write access for the publisher.
- Check the ZIP includes a nonempty arm64 executable and retain the MIT license.
- Do not publish user financial records, local databases, credentials, or tokens.

## Current follow-up

The current publisher checks the successful workflow and app binary, but still needs source-commit verification, monotonic build-number enforcement, and push-conflict handling. These should be merged with CI validation before changing the default-branch release workflow.
