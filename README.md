# NMS Versions

Windows build-to-version mappings for No Man’s Sky, starting with Forsaken 7.10.

## Public endpoints

| File | Contents |
|---|---|
| [nms-versions.json](https://witchmonster.github.io/NMS-Versions/nms-versions.json) | Windows EXE build-to-version mappings |
| [nms-compatibility.json](https://witchmonster.github.io/NMS-Versions/nms-compatibility.json) | Reviewed assessments for exact game builds and admitted baselines |

## Sources

- **Version mappings:** [GOG’s public Windows build metadata](https://content-system.gog.com/products/1446213994/os/windows/builds?generation=2).
- **Release notes:** [Hello Games](https://www.nomanssky.com/release-log/).

For example, `7.13_Forsaken_184271` identifies version **7.13**, update **Forsaken** and inferred EXE build **184271**. This does not establish identical binaries across stores.

## Maintenance

- The accepted collector refreshes public Windows mappings and preserves historical entries.
- The NMS Game Data owner maintains the existing daily run for discovery, scanner invocation and publication. The maintained NMSCompatibilityMaintenance.py command in the NMS repository composes that operation; its initial reviewed-Main and end-to-end adoption remain pending.
- The scanner generates assessments for exact game identities and admitted app baselines. Tech Lead independently reviews code and publication-rule changes before their initial adoption; NMS Game Data publishes routine compatible updates without a manually written verdict or per-build approval after adoption.
- Unavailable or incomplete game files remain pending for later scheduled runs. Unchanged results preserve the public files and create no unnecessary assessment, commit or push.
- The maintained publisher verifies both actual Pages JSON endpoints after pushing. Authentication may require an explicit Pages build; a successful push alone does not prove public delivery.

## Limits

Windows only. Unknown builds remain unmapped. Version identity alone does not establish compatibility.
