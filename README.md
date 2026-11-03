# NMS Versions

Windows build-to-version mappings for No Man’s Sky, starting with Forsaken 7.10.

## Public endpoints

| File | Contents |
|---|---|
| [nms-versions.json](https://witchmonster.github.io/NMS-Versions/nms-versions.json) | Version index; EXE mappings await publication |

## Sources

- **Version mappings:** [GOG’s public Windows build metadata](https://content-system.gog.com/products/1446213994/os/windows/builds?generation=2).
- **Release notes:** [Hello Games](https://www.nomanssky.com/release-log/).

For example, `7.13_Forsaken_184271` identifies version **7.13**, update **Forsaken** and inferred EXE build **184271**. This does not establish identical binaries across stores.

## Maintenance

- The collector adds public Windows mappings and preserves historical entries.
- Unchanged results preserve the existing file; failed refreshes preserve the last good index.
- GitHub Pages deploys automatically after each push.
- Daily refresh automation and reviewed compatibility assessments await publication.
- Compatibility assessments require separate review; automatic refreshes never generate them.

## Limits

Windows only. Unknown builds remain unmapped. Version identity alone does not establish compatibility.
