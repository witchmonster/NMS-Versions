# NMS Windows build index

[Public JSON](https://witchmonster.github.io/NMS-Versions/nms-versions.json) maps full
NMS EXE build numbers to public versions and named update families since 7.10.
The collector reads official GOG public Windows default-branch metadata. The
approved NMS-specific rule treats the final decimal component of a developer
label such as `7.11_Forsaken_183877` as EXE build `183877`. This interpretation
establishes a version label; it grants no decoder qualification or cross-store
binary compatibility and supplies no Steam build ID.

## JSON

Schema 2 uses namespace `nms.gog.windows.exe` and a `builds` array. Each row has
`executableBuild` (full decimal string), `version`, `family`, `gogPublishedAt`
(UTC ISO 8601), and optional official Hello Games `notesUrl`. GOG publication
time describes that GOG build record, not an original announcement or Steam
deployment. Unknown keys remain unknown; callers must use exact EXE numbers,
never GOG IDs, Steam IDs, truncated values or version ranges.

## Refresh

Python 3.12 or newer and its standard library suffice. Run from this repository:

```powershell
python -B collect.py --output nms-versions.json
python -B test_collect.py
```

The collector verifies product 1446213994, public Windows default branch,
generation 2, complete developer labels and explicit publication timezones. It
retains accepted mappings that disappear from GOG's rolling public response;
`total_count` does not describe the returned public history. Conflicts, malformed
responses and request failures preserve the last good file. Unchanged facts
preserve its exact bytes and modification time. Atomic staging stays under
`target`. The collector performs no Git operation.

The former schema-1 release catalogue contributes existing official notes links
only during migration; it supplies no EXE mappings, console rows or GOG dates.
Later records without known notes links omit that optional field. The collector
does not guess notes URLs or associate builds by nearby dates.

For retained-source replay, place the captured official response under `target`:

```powershell
python -B collect.py --output target/proposed.json --history nms-versions.json --source-file target/gog-builds.json
```

## Daily maintenance and publication

Game Data reuses its existing daily automation and accepted collector. Before
refresh, Game Data verifies this exact resolved independent repository root,
`main`, a clean worktree/index, no linked root or output paths, and origin
`https://github.com/witchmonster/NMS-Versions.git`. Game Data preserves unexpected
changes and reports an actionable refusal through CTO/CAO; Game Data never
initializes a repository, resets user work, replaces a remote or edits engineering
source/tests. Engineering delivers collector changes through independent review
and main integration before Game Data runs them.

Game Data runs the refresh command above. `changed: false` requires no commit or
push and stays quiet. After `changed: true`, Game Data verifies the generated JSON
and confirms that only `nms-versions.json` and, when necessary, `README.md` changed.
Game Data rejects any unexpected staged or unstaged path before these commands:

```powershell
git add -- nms-versions.json README.md
git diff --cached --check
git commit -m "Refresh NMS Windows build mappings"
git push origin main
```

The existing GitHub Pages main/root configuration rebuilds automatically after a
push. Initial publication requires an ordinary HTTP check of the public JSON and
its numeric mappings. Daily index maintenance preserves converter-only alert
rules and grants no extraction, converter execution, game-data adoption or app
source authority. The app consumes this index through its separate asynchronous
validated provider, cache and bundled offline fallback; it makes no GOG request.
