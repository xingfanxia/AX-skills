#!/usr/bin/env python3
"""Validate a portable draft and render an offline planning handbook (stdlib)."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 2 * 1024 * 1024


def reject(message):
    raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            reject('Duplicate JSON object key')
        result[key] = value
    return result


def load_json(path):
    with Path(path).open('rb') as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        reject('JSON exceeds 2 MiB')
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda _: reject('Non-finite JSON number'))


def validate_shape(value, schema, root, path='$'):
    """Evaluate the JSON Schema keywords used by the bundled v1 schema only."""
    if '$ref' in schema:
        return validate_shape(value, root['$defs'][schema['$ref'].split('/')[-1]], root, path)
    if 'oneOf' in schema:
        matches = 0
        for option in schema['oneOf']:
            try:
                validate_shape(value, option, root, path)
                matches += 1
            except ValueError:
                pass
        if matches != 1:
            reject(f'{path}: expected exactly one permitted shape')
        return
    if 'const' in schema and (type(value) is not type(schema['const']) or value != schema['const']):
        reject(f'{path}: wrong constant')
    if 'enum' in schema and value not in schema['enum']:
        reject(f'{path}: value outside allowed choices')
    kind = schema.get('type')
    types = {'object': dict, 'array': list, 'string': str, 'integer': int, 'null': type(None)}
    if kind and type(value) is not types[kind]:
        reject(f'{path}: wrong type')
    if kind == 'object':
        fields = schema['properties']
        if set(schema['required']) - value.keys():
            reject(f'{path}: required fields missing')
        if set(value) - fields.keys():
            reject(f'{path}: unexpected fields')
        for key, item in value.items():
            validate_shape(item, fields[key], root, f'{path}.{key}')
    elif kind == 'array':
        if len(value) > schema['maxItems']:
            reject(f'{path}: too many items')
        for index, item in enumerate(value):
            validate_shape(item, schema['items'], root, f'{path}[{index}]')
    elif kind == 'string':
        if len(value) < schema.get('minLength', 0) or len(value) > schema.get('maxLength', MAX_BYTES):
            reject(f'{path}: invalid text length')
        if 'minLength' in schema and not value.strip():
            reject(f'{path}: blank text')
        if 'pattern' in schema and not re.fullmatch(schema['pattern'], value):
            reject(f'{path}: invalid text format')
    elif kind == 'integer':
        if not schema.get('minimum', value) <= value <= schema.get('maximum', value):
            reject(f'{path}: integer out of range')


def utc(value):
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def validate_time(value):
    if value['kind'] == 'unknown':
        return
    zone = ZoneInfo(value['time_zone'])
    if value['kind'] == 'date':
        date.fromisoformat(value['local_date'])
    else:
        local = datetime.strptime(value['local_datetime'], '%Y-%m-%dT%H:%M')
        actual = utc(value['instant']).astimezone(zone)
        if actual.replace(tzinfo=None) != local:
            reject('Exact time: UTC instant does not match local clock and zone')


def validate(draft):
    schema = load_json(ROOT / 'schemas/draft.schema.json')
    validate_shape(draft, schema, schema)
    trip = draft['trip']
    ZoneInfo(trip['home_time_zone'])
    for key in ('start_date', 'end_date'):
        if trip[key] is not None:
            date.fromisoformat(trip[key])
    if trip['start_date'] and trip['end_date'] and trip['start_date'] > trip['end_date']:
        reject('Trip date window ends before it starts')
    source_ids = [source['id'] for source in draft['sources']]
    if len(set(source_ids)) != len(source_ids):
        reject('Duplicate source ID')
    for source in draft['sources']:
        if source['checked_at'] is not None:
            utc(source['checked_at'])
    subjects = [trip] + draft['events'] + draft['candidates']
    by_id = {item['id']: item for item in subjects}
    if len(by_id) != len(subjects):
        reject('Duplicate trip/event/candidate ID')
    for item in draft['events'] + draft['candidates']:
        ids = item['source_ids']
        if len(set(ids)) != len(ids) or not set(ids) <= set(source_ids):
            reject('Source references must be unique and declared')
    for event in draft['events']:
        start, end = event['start'], event['end']
        validate_time(start)
        validate_time(end)
        if start['kind'] == end['kind'] == 'exact' and utc(end['instant']) < utc(start['instant']):
            reject('Event ends before it starts')
        if start['kind'] == end['kind'] == 'date' and start['time_zone'] == end['time_zone']:
            if end['local_date'] < start['local_date']:
                reject('Event local date range is reversed')
    for candidate in draft['candidates']:
        validate_time(candidate['timing'])
    for evidence in draft['evidence']:
        subject = by_id.get(evidence['subject_id'])
        if subject is None or evidence['field'] not in subject or evidence['source_id'] not in source_ids:
            reject('Evidence refers to an unknown subject, field or source')
        if subject is not trip and evidence['source_id'] not in subject['source_ids']:
            reject('Evidence source is not linked to its subject')
    return draft


def e(value):
    return escape(str(value), quote=True)


def time_label(value):
    if value['kind'] == 'unknown':
        return 'Unknown — ' + value['reason']
    if value['kind'] == 'date':
        return value['local_date'] + ' · ' + value['time_zone'] + ' · time unknown'
    offset = utc(value['instant']).astimezone(ZoneInfo(value['time_zone'])).strftime('%z')
    offset = offset[:3] + ':' + offset[3:5] + (':' + offset[5:] if len(offset) > 5 else '')
    return value['local_datetime'].replace('T', ' ') + ' · ' + value['time_zone'] + ' (UTC' + offset + ')'


def state_label(value):
    return {'source_only': 'Based on source; not verified',
            'location_checked': 'Location checked; hours unverified',
            'live_checked': 'Checked against current information'}.get(value, value.replace('_', ' '))


def bullets(values):
    return '<ul>' + ''.join('<li>' + e(value) + '</li>' for value in values) + '</ul>' if values else ''


def render(draft):
    validate(draft)
    trip = draft['trip']
    blocks = []
    for event in draft['events']:
        start, end = event['start'], event['end']
        duration = ''
        if start['kind'] == end['kind'] == 'exact':
            hours = (utc(end['instant']) - utc(start['instant'])).total_seconds() / 3600
            duration = f'<p>Elapsed time: {hours:g} hours</p>'
        route = ' → '.join(value for value in (event['origin'], event['destination']) if value)
        party = f" · Party size: {event['party_size']}" if event['party_size'] is not None else ''
        blocks.append('<article><h3>' + e(event['title']) + '</h3><p>' + e(route) + '</p>'
                      + '<p><b>Start</b> ' + e(time_label(start)) + '<br><b>End</b> ' + e(time_label(end)) + '</p>'
                      + duration + '<p class="status">Booking: ' + e(state_label(event['booking']))
                      + ' · Payment: ' + e(state_label(event['payment'])) + ' · Completion: ' + e(state_label(event['completion']))
                      + e(party) + '</p>' + bullets(event['notes']) + '</article>')
    candidates = ''.join('<article><h3>' + e(item['title']) + '</h3><p>' + e(item['area'] or 'Area unknown')
                         + '</p><p>' + e(time_label(item['timing'])) + '</p><p class="status">'
                         + e(state_label(item['status'])) + ' · ' + e(state_label(item['verification'])) + '</p>'
                         + bullets(item['notes']) + '</article>' for item in draft['candidates'])
    window = trip['window'] or 'Travel window not chosen'
    dates = (trip['start_date'] or 'Start date unknown') + ' → ' + (trip['end_date'] or 'End date unknown')
    # Display allowlist: source labels, raw evidence and change summaries never enter HTML.
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="darkreader-lock" content="true"><meta name="color-scheme" content="light dark">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>''' + e(trip['title']) + '''</title><style>
*{box-sizing:border-box}body{margin:0;background:#f6f3ed;color:#26302d;font:17px/1.6 system-ui,sans-serif}
main{max-width:850px;margin:auto;padding:38px 22px}h1{font-size:clamp(28px,5vw,44px);line-height:1.2}
h2{margin-top:36px}h3{margin:0;font-size:21px}p{margin:10px 0}article{background:white;border:1px solid #d6ddd7;
border-radius:10px;padding:20px;margin:16px 0;break-inside:avoid;overflow-wrap:anywhere}
.tag,.status{font-size:14px;color:#445750}.tag{font-weight:700;letter-spacing:.06em}
ul{padding-left:24px}footer{margin-top:36px;font-size:14px}h1,p,li{overflow-wrap:anywhere}
@media(prefers-color-scheme:dark){body{background:#101820;color:#edf3f6}article{background:#1a252f;border-color:#31404d}.tag,.status{color:#adc0cd}}
@media print{body{background:white;color:#26302d;font-size:11pt}main{max-width:none;padding:0}article{background:white;color:#26302d;border-color:#d6ddd7;border-radius:0}.tag,.status{color:#445750}h2{break-after:avoid}}
</style></head><body><main><p class="tag">TRAVEL HANDBOOK · PLANNING DRAFT</p><h1>''' + e(trip['title']) + '</h1><p>' + e(window) + '</p><p>' + e(dates) + '</p><p>Home zone: ' + e(trip['home_time_zone']) + '</p>' + bullets(trip['notes']) + '<h2>Itinerary</h2>' + (''.join(blocks) or '<p>No scheduled events yet.</p>') + '<h2>Flexible candidates</h2>' + (candidates or '<p>No candidates recorded.</p>') + '<h2>Unresolved questions</h2>' + (bullets(draft['questions']) or '<p>No questions recorded.</p>') + '<footer>Offline planning copy. This file does not book, pay, publish or confirm actual travel. Source records are omitted. Review personal details before sharing.</footer></main></body></html>\n'


def write_new(path, content):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as handle:
        handle.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'render'):
        command = sub.add_parser(name)
        command.add_argument('draft', type=Path)
        if name == 'render':
            command.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    try:
        draft = validate(load_json(args.draft))
        if args.command == 'render':
            write_new(args.out, render(draft))
        print(json.dumps({'ok': True, 'result': 'draft_valid' if args.command == 'validate' else 'handbook_created',
                          'external_changes': False}))
        return 0
    except (ValueError, OSError, ZoneInfoNotFoundError, RecursionError):
        # Private filenames, source content and parser snippets never go to stdout/stderr.
        print(json.dumps({'ok': False, 'error': 'Invalid draft, unavailable time zone, or inaccessible/existing output. Inspect locally.'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
