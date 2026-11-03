"""Focused collector tests. All generated fixtures stay under this repo's target."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import collect


def item(label="7.11_Forsaken_183877", **changes):
    value = {"product_id": "1446213994", "public": True, "os": "windows", "branch": None,
             "generation": 2, "build_id": "60170037734095994", "version_name": label,
             "date_published": "2026-10-29T17:16:02+0000"}
    value.update(changes)
    return value


def raw(*items):
    return json.dumps({"count": len(items), "total_count": 500, "has_private_branches": True, "items": list(items)}).encode()


def encoded(index):
    return json.dumps(index).encode()


class Collector(unittest.TestCase):
    def setUp(self):
        target = collect.ROOT / "target" / "tests"
        target.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix=self._testMethodName + "-", dir=target))
        self.output = self.root / "nms-versions.json"

    def test_label_lookup_uses_full_exe_not_gog_or_steam_namespace(self):
        index = collect.produce(raw(item()))
        self.assertEqual(collect.lookup(index, "183877")["version"], "7.11")
        self.assertEqual(collect.lookup(index, "183877")["family"], "Forsaken")
        for unknown in ["26295378", "60170037734095994", "52805", "999999", "183877.0", 183877]:
            self.assertIsNone(collect.lookup(index, unknown))
        with self.assertRaises(ValueError):
            collect.lookup({**index, "namespace": "steam-build"}, "183877")

    def test_actual_publication_semantics_and_timezone(self):
        row = collect.produce(raw(item()))["builds"][0]
        self.assertEqual(row["gogPublishedAt"], "2026-10-29T17:16:02Z")
        self.assertNotIn("deployedAt", row)
        self.assertNotIn("steamBuildId", row)
        with self.assertRaises(ValueError):
            collect.produce(raw(item(date_published="2026-10-29T17:16:02")))

    def test_windows_public_default_branch_only(self):
        for changes in [{"public": False}, {"os": "osx"}, {"branch": "experimental"}]:
            index = collect.produce(raw(item(), item("7.13_Forsaken_184271", **changes)))
            self.assertEqual(len(index["builds"]), 1)
        for changes in [{"product_id": "other"}, {"public": 1}, {"generation": 1}]:
            with self.assertRaises(ValueError):
                collect.produce(raw(item(**changes)))
        missing = item()
        del missing["branch"]
        with self.assertRaises(ValueError):
            collect.produce(raw(missing))

    def test_label_format_and_family_conflicts_refuse(self):
        for label in ["7.11_Forsaken", "7.11_Forsaken_183877_extra", "7.11__183877", "7.11_ Forsaken_183877"]:
            with self.subTest(label=label), self.assertRaises(ValueError):
                collect.produce(raw(item(label)))
        for other in [item("7.13_Forsaken_183877"), item("7.11_Other_183877"), item(date_published="2026-10-30T17:16:02Z")]:
            with self.assertRaises(ValueError):
                collect.produce(raw(item(), other))

    def test_duplicate_identical_source_deduplicates(self):
        self.assertEqual(len(collect.produce(raw(item(), item()))["builds"]), 1)

    def test_rolling_history_preserves_earlier_rows(self):
        old = collect.produce(raw(item("7.10_Forsaken_183791"), item()))
        current = collect.produce(raw(item("7.13_Forsaken_184271")), encoded(old))
        self.assertEqual([r["executableBuild"] for r in current["builds"]], ["183791", "183877", "184271"])
        with self.assertRaises(ValueError):
            collect.produce(raw(item("7.13_Forsaken_183877")), encoded(old))

    def test_legacy_catalogue_supplies_notes_only_not_console_or_rss_dates(self):
        legacy = {"schemaVersion": 1, "releases": [
            {"version": v, "family": "Forsaken", "platforms": platforms,
             "notesUrl": f"https://www.nomanssky.com/{v}/", "rssPublishedAt": "2026-10-30T12:00:00Z"}
            for v, platforms in [("7.11", ["PC"]), ("7.12", ["PS5"])]]}
        index = collect.produce(raw(item()), encoded(legacy))
        self.assertEqual(len(index["builds"]), 1)
        self.assertEqual(index["builds"][0]["notesUrl"], "https://www.nomanssky.com/7.11/")
        self.assertEqual(index["builds"][0]["gogPublishedAt"], "2026-10-29T17:16:02Z")

    def test_old_versions_excluded_count_is_not_complete_history(self):
        index = collect.produce(raw(item(), item("7.06_Cosmos_180836")))
        self.assertEqual(len(index["builds"]), 1)
        with self.assertRaises(ValueError):
            collect.produce(raw())
        bad = json.loads(raw(item()))
        bad["count"] = 500
        with self.assertRaises(ValueError):
            collect.produce(encoded(bad))

    def test_stable_refresh_preserves_exact_bytes_and_mtime(self):
        with patch.object(collect, "fetch", return_value=raw(item())):
            changed, _ = collect.refresh(self.output)
            self.assertTrue(changed)
            before = self.output.read_bytes(), self.output.stat().st_mtime_ns
            changed, _ = collect.refresh(self.output)
            self.assertFalse(changed)
            self.assertEqual((self.output.read_bytes(), self.output.stat().st_mtime_ns), before)

    def test_request_and_schema_failure_preserve_last_good(self):
        last_good = encoded(collect.produce(raw(item())))
        self.output.write_bytes(last_good)
        for response in [OSError("offline"), b"not JSON", raw(item("bad-label")), raw(item(product_id="275850"))]:
            with patch.object(collect, "fetch", side_effect=response if isinstance(response, Exception) else None,
                              return_value=response):
                with self.assertRaises((OSError, ValueError)):
                    collect.refresh(self.output)
            self.assertEqual(self.output.read_bytes(), last_good)

    def test_conflicting_or_foreign_history_preserved(self):
        good = collect.produce(raw(item()))
        for change in [{"namespace": "steam"}, {"schemaVersion": 3}, {"builds": good["builds"] * 2}]:
            bad = {**good, **change}
            self.output.write_bytes(encoded(bad))
            before = self.output.read_bytes()
            with patch.object(collect, "fetch", return_value=raw(item())), self.assertRaises(ValueError):
                collect.refresh(self.output)
            self.assertEqual(self.output.read_bytes(), before)

    def test_concurrent_owner_edit_survives_refresh(self):
        self.output.write_bytes(encoded(collect.produce(raw(item()))))
        def source():
            self.output.write_bytes(b"owner edit")
            return raw(item("7.13_Forsaken_184271"))
        with patch.object(collect, "fetch", side_effect=source), self.assertRaises(ValueError):
            collect.refresh(self.output)
        self.assertEqual(self.output.read_bytes(), b"owner edit")

    def test_order_does_not_change_content(self):
        first, second = item(), item("7.13_Forsaken_184271")
        self.assertEqual(collect.produce(raw(first, second)), collect.produce(raw(second, first)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
