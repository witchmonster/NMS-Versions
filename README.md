# NMS Versions

Windows build-to-version mappings for No Man’s Sky, starting with Forsaken 7.10.

## Public endpoints

| File | Contents |
|---|---|
| [nms-versions.json](https://witchmonster.github.io/NMS-Versions/nms-versions.json) | Windows EXE build-to-version mappings |
| [ewa-nms-compatibility.json](https://witchmonster.github.io/NMS-Versions/ewa-compatibility/183877/ewa-nms-compatibility.json) | Reviewed assessments for exact game builds and admitted baselines |

## Sources

- **Version mappings:** [GOG’s public Windows build metadata](https://content-system.gog.com/products/1446213994/os/windows/builds?generation=2).
- **Release notes:** [Hello Games](https://www.nomanssky.com/release-log/).

For example, `7.13_Forsaken_184271` identifies version **7.13**, update **Forsaken** and inferred EXE build **184271**. This does not establish identical binaries across stores.

## Catalog contract

The schema 2 catalog preserves legacy two-component labels in `builds[]`. Three-component labels use the optional `exactBuilds` object, keyed by the full executable build string. Each exact entry carries the original `version`, `family` and `gogPublishedAt`, plus `notesUrl` when a retained source establishes it. For example, build `186923` maps to GOG version `7.15.1` and family `HolidayExpeditions2026`. Consumers can look up older two-component labels in `builds[]`.

## Maintenance

- The foreground collector refreshes the same Windows mappings and preserves historical entries. The NMS Jenkins Game Data job uses the maintained native scanner and catalog collector for the daily operation.
- The scanner generates assessments for exact game identities and admitted app baselines. Engineering resolves scanner, coverage and publication failures. The release reviewer independently verifies the reviewed source, recorded result and actual delivery.
- Unavailable or incomplete game files remain pending for later scheduled runs. Unchanged results preserve the public files and create no unnecessary assessment, commit or push.
- The maintained publisher verifies both actual Pages JSON endpoints after pushing. Authentication may require an explicit Pages build; a successful push alone does not prove public delivery.

## Limits

Windows only. Unknown builds remain unmapped. Version identity alone does not establish compatibility.
