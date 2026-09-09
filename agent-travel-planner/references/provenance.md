# Origin and license

Workflow authorship: Xingfan Xia (AX), distilled from the author's privately
operated Travel Vault workflow. The reusable lessons are conversational
brainstorm/plan/update, separate evidence and authority, a replayable draft,
preview/read-back, explicit local-time uncertainty and independent booking,
payment and completion states.

The private workflow has been exercised with real travel updates and food
planning, including application read-back and portable exports. That operational
experience motivates the guidance; it is not evidence that this standalone
package has a production API or identical export capabilities.

The public schema, Python helpers, HTML layout and fictional fixture were newly
written for this package. No private project implementation, real itinerary,
booking source, traveler media, credentials, or third-party application code is
included. No code or media from Flighty, Settle, or PolyForm is incorporated.
This package does not assert a license to redistribute those products.

All files in this package are covered by the included MIT LICENSE, matching the
AX-skills repository license. Preserve that notice when redistributing the
standalone folder. Python's standard library is an environment dependency;
no third-party library, font, image, script or time-zone database is vendored.

The intended distribution contains only the files listed in package-files.txt.
Run `python3 scripts/check.py` before packaging; inspect the actual file list and
text diff as well. Automated pattern checks help catch common accidental
material, but cannot prove that arbitrary text is non-personal.
