# No Man's Sky releases

Official releases on all platforms since 7.10 inclusive. `nms-versions.json` contains
`schemaVersion` and `releases`: `version`, named `family`, actual official `platforms`, `notesUrl`,
and available UTC ISO 8601 timestamps. Unknown fields stay absent.

`rssPublishedAt` preserves Hello Games RSS `pubDate`; it does not prove the
original announcement or deployment time. `announcedAt` uses explicit official
publication metadata from retained notes/announcement HTML, never modified time.
Notes HTML is optional for RSS/platform facts; missing metadata stays absent.
`deployedAt` requires an actual
official Steam public Windows deployment record. `steamBuildId` requires an
explicit exact notes/build association and consistent deployment time within
24 hours before through 48 hours after the original announcement. Time alone
never joins identities; conflicting or insufficient bindings stay privately
unmapped while independent valid hotfix builds remain. No supported keyless
Steam history source currently supplies those records, so build fields remain
absent. No executable mapping or compatibility
qualification follows from a post, timestamp, or build identity. An optional
`builds` array retains each independently supported `steamBuildId`/`deployedAt`
pair with its actual `distribution` and `platform`; identical bindings deduplicate.

The collector uses the [Hello Games release log](https://www.nomanssky.com/release-log/)
for versions/families/platform lists and linked notes, and its
[RSS feed](https://www.nomanssky.com/feed/) for publisher dates. A major-update
date requires a release-log-identified major update and one exact-family blog
announcement linking to those notes. A patch never inherits that blog's date.
The documented [Steam news API](https://partner.steamgames.com/doc/webapi/ISteamNews)
supplies news dates, not deployment history; publisher-key build APIs are unavailable.
Console-only releases stay in the catalogue with their actual platform lists;
a Windows build never binds a release without PC support. Community/manual/AI
mappings never enter the output. A future app consumer filters its own platform.

Game Data refreshes with the accepted app tool:

```powershell
python -B src/tools/Collect-NMSPublicVersions.py --work-root target/versions-refresh
```

Use an installed Python 3 interpreter from the app checkout. The command requires
a fresh owned `target` path and writes `public/nms-versions.json`, `public/README.md`
and private captures/UNMAPPED diagnostics. Game Data checks current user/repo edits,
then adopts only those two public files after review. The tool never overwrites
this project or initializes Git. Game Data may maintain Git here only after the
user initializes an independent repo and its resolved Git root equals this folder.

The user creates a GitHub repository, initializes and pushes this folder, then
enables Settings > Pages > Deploy from a branch > main > /(root). The JSON URL
remains `<YOUR_PAGES_BASE_URL>/nms-versions.json` until the user supplies it.
No app network integration or Pages publication occurs during collection.
