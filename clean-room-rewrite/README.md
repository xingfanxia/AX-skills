# clean-room-rewrite

Decide rewrite vs refactor with measurements, and when a rewrite wins, rebuild
the system clean-room: independent distillers turn the old code into an
executable spec package, a builder that never reads the old source implements
it, independent auditors check parity against the old code, and a shadow run
on real data gates the cutover.

Method inspired by the AIHOT 2.0 rewrite by 卡兹克
([KKKKhazix/AIHOT](https://github.com/KKKKhazix/AIHOT)); this version adds the
decision gate, ledger IDs, stop rules, a strangler variant, and a
cutover/rollback contract.

See [SKILL.md](SKILL.md).
