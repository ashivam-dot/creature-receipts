"""Focused fail-closed checks for the bounded source/art supply audit."""

import hashlib
import unittest
from unittest.mock import patch

from monitor import accident_intake as intake


class AccidentIntakeTest(unittest.TestCase):
    def test_live_source_must_keep_event_phrases(self):
        source = {"role": "primary", "url": "https://example.org/report"}
        with patch.object(intake, "fetch", return_value=(b"Mann Gulch Fire " * 150, "text/plain")):
            with self.assertRaisesRegex(intake.IntakeError, "lost a pinned event phrase"):
                intake.source_check(source, ["Mann Gulch Fire", "Board of Review"])

    def test_art_requires_live_rights_scene_and_exact_bytes(self):
        body = b"\xff\xd8\xff" + b"example image bytes"
        item = {"title": "File:MannGulchFire.jpg",
                "description_url": "https://commons.wikimedia.org/wiki/File:MannGulchFire.jpg",
                "download_url": "https://upload.wikimedia.org/wikipedia/commons/e/e1/MannGulchFire.jpg",
                "sha256": hashlib.sha256(body).hexdigest(),
                "description_canary": "Investigation party photo taken from the N slope of Mann Gulch",
                "scene": "Investigation party at the burned site; use only as aftermath context."}
        metadata = {"query": {"pages": {"1": {"title": item["title"], "imageinfo": [{
            "mime": "image/jpeg", "width": 629, "height": 650,
            "url": item["download_url"], "descriptionurl": item["description_url"],
            "extmetadata": {
                "LicenseShortName": {"value": "Public domain"},
                "UsageTerms": {"value": "Public domain"},
                "Copyrighted": {"value": "False"},
                "AttributionRequired": {"value": "false"},
                "Credit": {"value": "US Forest Service"},
                "ImageDescription": {"value": item["description_canary"]},
            }}]}}}}
        with patch.object(intake, "read_json", return_value=metadata), patch.object(
            intake, "fetch", return_value=(body, "image/jpeg")):
            self.assertEqual(intake.art_check(item)["sha256"], item["sha256"])
            with self.assertRaisesRegex(intake.IntakeError, "bytes differ"):
                intake.art_check({**item, "sha256": "0" * 64})
            metadata["query"]["pages"]["1"]["imageinfo"][0]["extmetadata"]["Copyrighted"]["value"] = "True"
            with self.assertRaisesRegex(intake.IntakeError, "rights metadata"):
                intake.art_check(item)

    def test_duplicate_is_skipped_and_technical_pass_never_selects(self):
        payload = {"intake": [
            {"id": "oppau-1921", "primary_kind": "retrospective_original_technical_study",
             "source_canaries": {"primary": ["one", "two"], "independent": ["three", "four"]},
             "art": [{"title": "one"}, {"title": "two"}]},
            {"id": "mann-gulch-1949", "primary_kind": "contemporaneous_board_report",
             "source_canaries": {"primary": ["one", "two"], "independent": ["three", "four"]},
             "art": [{"title": "three"}, {"title": "four"}]},
        ], "pool": [
            {"id": "oppau-1921", "aliases": ["Oppau"], "sources": []},
            {"id": "mann-gulch-1949", "aliases": ["Mann Gulch"],
             "sources": [{"role": "primary", "url": "https://source-one.org/report"},
                         {"role": "independent", "url": "https://source-two.org/account"}]},
        ], "used_ids": ["oppau-1921"], "known_titles": []}
        with patch.object(intake, "source_check", side_effect=lambda source, _: source), patch.object(
            intake, "art_check", side_effect=lambda art: art):
            report = intake.audit(payload)
        self.assertEqual(report["candidates"][0]["state"], "used_or_duplicate")
        self.assertEqual(report["candidates"][1]["state"], "technical_preflight_pass")
        self.assertEqual(report["eligible_for_selection"], 0)
        self.assertFalse(report["release_enabled"])

        payload["used_ids"] = []
        payload["known_titles"] = ["The Oppau disaster and Mann Gulch fire revisited"]
        with patch.object(intake, "source_check", side_effect=AssertionError("duplicate fetched")):
            duplicate_report = intake.audit(payload)
        self.assertTrue(all(item["state"] == "used_or_duplicate"
                            for item in duplicate_report["candidates"]))


if __name__ == "__main__":
    unittest.main()
