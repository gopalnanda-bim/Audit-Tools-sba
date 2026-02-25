# GitHub Release Checklist

## One-time setup

1. Initialize repository (if needed):
   - `git init`
2. Add remote:
   - `git remote add origin <your-github-repo-url>`

## Create release package

1. Keep this folder layout in the release artifact:
   - `Audit and Test.extension/...`
2. Create zip from repository root containing `Audit and Test.extension`.

## Tag and publish

1. Commit:
   - `git add .`
   - `git commit -m "chore: prepare v0.1.0 release"`
2. Tag:
   - `git tag -a v0.1.0 -m "v0.1.0"`
3. Push:
   - `git push -u origin main`
   - `git push origin v0.1.0`
4. Create GitHub Release:
   - Tag: `v0.1.0`
   - Title: `v0.1.0`
   - Attach zip artifact if distributing a packaged extension.
