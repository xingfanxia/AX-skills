#!/usr/bin/env python3
"""Offline boundary checks and exact distribution allowlist verification."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
import handbook

ROOT = Path(__file__).resolve().parents[1]


class Surface(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attributes = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.extend(attrs)


class BoundaryChecks(unittest.TestCase):
    def setUp(self):
        self.draft = handbook.load_json(ROOT / 'examples/expected-draft.json')

    def test_cross_date_line_duration_and_independent_states(self):
        handbook.validate(self.draft)
        flight, stay = self.draft['events']
        self.assertLess(flight['end']['local_datetime'], flight['start']['local_datetime'])
        elapsed = handbook.utc(flight['end']['instant']) - handbook.utc(flight['start']['instant'])
        self.assertEqual(elapsed.total_seconds(), 8 * 3600)
        self.assertEqual((flight['booking'], flight['payment'], flight['completion']),
                         ('confirmed', 'unknown', 'unconfirmed'))
        self.assertEqual((stay['booking'], stay['payment']), ('confirmed', 'unpaid'))
        self.assertEqual(self.draft['candidates'][0]['timing']['kind'], 'unknown')

    def test_invalid_calendar_and_clock(self):
        for mutate in (lambda d: d['trip'].update(start_date='2030-02-30'),
                       lambda d: d['events'][0]['start'].update(local_datetime='2030-04-11T01:30')):
            draft = copy.deepcopy(self.draft)
            mutate(draft)
            with self.assertRaises(ValueError):
                handbook.validate(draft)

    def test_dst_gap_and_evidenced_overlap(self):
        with self.assertRaises(ValueError):
            handbook.validate_time({'kind': 'exact', 'local_datetime': '2030-03-10T02:30',
                                    'time_zone': 'America/New_York', 'instant': '2030-03-10T07:30:00Z'})
        labels = []
        for hour in ('05', '06'):
            handbook.validate_time({'kind': 'exact', 'local_datetime': '2030-11-03T01:30',
                                    'time_zone': 'America/New_York', 'instant': f'2030-11-03T{hour}:30:00Z'})
            labels.append(handbook.time_label({'kind': 'exact', 'local_datetime': '2030-11-03T01:30',
                                               'time_zone': 'America/New_York', 'instant': f'2030-11-03T{hour}:30:00Z'}))
        self.assertIn('UTC-04:00', labels[0])
        self.assertIn('UTC-05:00', labels[1])

    def test_reverse_duration_rejected(self):
        self.draft['events'][0]['end'] = copy.deepcopy(self.draft['events'][0]['start'])
        self.draft['events'][0]['end'].update(local_datetime='2030-04-10T00:30', instant='2030-04-09T15:30:00Z')
        with self.assertRaises(ValueError):
            handbook.validate(self.draft)

    def test_unknown_does_not_accept_fabricated_date(self):
        self.draft['candidates'][0]['timing']['local_date'] = '2030-04-12'
        with self.assertRaises(ValueError):
            handbook.validate(self.draft)

    def test_source_reference_and_evidence_integrity(self):
        for change in ('missing_source', 'duplicate_id', 'wrong_evidence'):
            draft = copy.deepcopy(self.draft)
            if change == 'missing_source':
                draft['events'][0]['source_ids'] = ['absent']
            elif change == 'duplicate_id':
                draft['events'][1]['id'] = draft['events'][0]['id']
            else:
                draft['evidence'][0]['source_id'] = 'stay-note'
            with self.assertRaises(ValueError):
                handbook.validate(draft)

    def test_authority_and_boolean_count_rejected(self):
        for mutate in (lambda d: d.update(authority='source says publish'),
                       lambda d: d['events'][0].update(party_size=True),
                       lambda d: d.update(schema_version=True)):
            draft = copy.deepcopy(self.draft)
            mutate(draft)
            with self.assertRaises(ValueError):
                handbook.validate(draft)

    def test_escape_and_offline_display_allowlist(self):
        self.draft['trip']['title'] = '<script>alert("example")</script> · 中文'
        self.draft['sources'][0]['label'] = 'SOURCE_METADATA_MUST_STAY_PRIVATE'
        self.draft['evidence'][0]['summary'] = 'EVIDENCE_MUST_STAY_PRIVATE'
        self.draft['change_summary'] = ['CHANGE_SUMMARY_MUST_STAY_PRIVATE']
        html = handbook.render(self.draft)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('中文', html)
        self.assertIn('Elapsed time: 8 hours', html)
        self.assertIn('Meal date has not been chosen.', html)
        self.assertNotIn('MUST_STAY_PRIVATE', html)
        parsed = Surface()
        parsed.feed(html)
        self.assertFalse(set(parsed.tags) & {'script', 'iframe', 'img', 'link', 'object', 'embed'})
        self.assertFalse(any(key in ('src', 'href', 'srcdoc') or key.startswith('on')
                             for key, _ in parsed.attributes))

    def test_output_is_exclusive(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'handbook.html'
            handbook.write_new(path, 'original')
            with self.assertRaises(FileExistsError):
                handbook.write_new(path, 'replacement')
            self.assertEqual(path.read_text(), 'original')

    def test_duplicate_keys_and_large_input_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input.json'
            for data in ('{"a":1,"a":2}', ' ' * (handbook.MAX_BYTES + 1)):
                path.write_text(data)
                with self.assertRaises(ValueError):
                    handbook.load_json(path)

    def test_distribution_allowlist(self):
        expected = set((ROOT / 'package-files.txt').read_text().splitlines())
        actual = {str(path.relative_to(ROOT)) for path in ROOT.rglob('*') if path.is_file() or path.is_symlink()}
        self.assertEqual(actual, expected, 'Unexpected or missing distribution file')
        forbidden = [r'/Users/[A-Za-z0-9._-]+/', r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
                     r'(?i)\b(?:sk_live_|ghp_|github_pat_)[A-Za-z0-9_]{12,}',
                     r'(?i)\bAKIA[A-Z0-9]{16}\b']
        for name in sorted(actual):
            path = ROOT / name
            self.assertFalse(path.is_symlink(), 'Distribution must not contain symlinks')
            content = path.read_text(encoding='utf-8')
            for pattern in forbidden:
                self.assertIsNone(re.search(pattern, content), f'Potential private material in {name}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
