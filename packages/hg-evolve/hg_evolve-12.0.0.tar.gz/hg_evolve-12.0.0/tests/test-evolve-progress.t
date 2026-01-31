Test Evolve progress output
===========================

  $ . "$TESTDIR/testlib/common.sh"
  $ cat >> $HGRCPATH <<EOF
  > [extensions]
  > evolve=
  > EOF

  $ hg init progress
  $ cd progress
  $ echo a > a
  $ hg ci -Aqm first
  $ echo a2 > a
  $ hg ci -m second
  $ echo b > b
  $ hg ci -Aqm third
  $ echo b2 > b
  $ hg ci -m fourth

Test progress with --all
  $ hg co -q 'desc("first")'
  $ hg amend -m 'first v2'
  3 new orphan changesets
  $ hg evolve --config progress.debug=yes --debug
  evolve: 1/3 changesets (33.33%)
  move:[1] second
  atop:[4] first v2
  hg rebase -r 4f60c78b6d58 -d fd0a2402f834
  evolve: 1/3 changesets (33.33%)
  resolving manifests
   branchmerge: True, force: True, partial: False
   ancestor: a87874c6ec31, local: fd0a2402f834+, remote: 4f60c78b6d58
   a: remote is newer -> g
  getting a
  updating: a 1/1 files (100.00%)
  committing files:
  a
  committing manifest
  committing changelog
  evolve: 2/3 changesets (66.67%)
  move:[2] third
  hg rebase -r 769574b07a96 -d 5f16d91ecde0
  evolve: 2/3 changesets (66.67%)
  resolving manifests
   branchmerge: True, force: True, partial: False
   ancestor: 4f60c78b6d58, local: 5f16d91ecde0+, remote: 769574b07a96
   b: remote created -> g
  getting b
  updating: b 1/1 files (100.00%)
  committing files:
  b
  committing manifest
  committing changelog
  evolve: 3/3 changesets (100.00%)
  move:[3] fourth
  hg rebase -r 22782fddc0ab -d 53c0008d98a0
  evolve: 3/3 changesets (100.00%)
  resolving manifests
   branchmerge: True, force: True, partial: False
   ancestor: 769574b07a96, local: 53c0008d98a0+, remote: 22782fddc0ab
   b: remote is newer -> g
  getting b
  updating: b 1/1 files (100.00%)
  committing files:
  b
  committing manifest
  committing changelog
  updating the branch cache
  obscache is out of date
  invalid branch cache (served): tip differs
  resolving manifests
   branchmerge: False, force: False, partial: False
   ancestor: 385376d04062, local: 385376d04062+, remote: fd0a2402f834
   b: other deleted -> r
  removing b
  updating: b 1/2 files (50.00%)
   a: remote is newer -> g
  getting a
  updating: a 2/2 files (100.00%)

Test progress with -r
  $ hg co -q 'desc("first")'
  $ hg amend -m 'first v3'
  3 new orphan changesets
  $ hg evolve -r 'desc("second")' --config progress.debug=yes --debug
  evolve: 1/1 changesets (100.00%)
  move:[5] second
  atop:[8] first v3
  hg rebase -r 5f16d91ecde0 -d 152c368c622b
  evolve: 1/1 changesets (100.00%)
  resolving manifests
   branchmerge: True, force: True, partial: False
   ancestor: fd0a2402f834, local: 152c368c622b+, remote: 5f16d91ecde0
   a: remote is newer -> g
  getting a
  updating: a 1/1 files (100.00%)
  committing files:
  a
  committing manifest
  committing changelog
  updating the branch cache
  obscache is out of date
  invalid branch cache (served): tip differs
  invalid branch cache (served.hidden): tip differs
  resolving manifests
   branchmerge: False, force: False, partial: False
   ancestor: df5d742141b0, local: df5d742141b0+, remote: 152c368c622b
   a: remote is newer -> g
  getting a
  updating: a 1/1 files (100.00%)

Test progress with --continue
  $ hg co -q 'desc("first")'
  $ echo conflict > a
  $ hg amend -m 'first v4'
  1 new orphan changesets
  $ hg evolve --all --config progress.debug=yes --debug
  evolve: 1/3 changesets (33.33%)
  move:[9] second
  atop:[10] first v4
  hg rebase -r df5d742141b0 -d f8d7d38c0a88
  evolve: 1/3 changesets (33.33%)
  resolving manifests
   branchmerge: True, force: True, partial: False
   ancestor: 152c368c622b, local: f8d7d38c0a88+, remote: df5d742141b0
  starting 4 threads for background file closing (?)
   preserving a for resolve of a
   a: versions differ -> m
  updating: a 1/1 files (100.00%)
  picked tool ':merge' for a (binary False symlink False changedelete False)
  merging a
  my a@f8d7d38c0a88+ other a@df5d742141b0 ancestor a@152c368c622b
  warning: conflicts while merging a! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ echo resolved > a
  $ hg resolve -m a
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue --config progress.debug=yes --debug
  evolving 9:df5d742141b0 "second"
  committing files:
  a
  committing manifest
  committing changelog
  updating the branch cache
  obscache is out of date
  move:[6] third
  atop:[11] second
  hg rebase -r 53c0008d98a0 -d c8caf623f57b
  evolve: 2/3 changesets (66.67%)
  resolving manifests
   branchmerge: True, force: True, partial: False
   ancestor: 5f16d91ecde0, local: c8caf623f57b+, remote: 53c0008d98a0
   b: remote created -> g
  getting b
  updating: b 1/1 files (100.00%)
  committing files:
  b
  committing manifest
  committing changelog
  move:[7] fourth
  hg rebase -r 385376d04062 -d 55f7ff45dec4
  evolve: 3/3 changesets (100.00%)
  resolving manifests
   branchmerge: True, force: True, partial: False
   ancestor: 53c0008d98a0, local: 55f7ff45dec4+, remote: 385376d04062
   b: remote is newer -> g
  getting b
  updating: b 1/1 files (100.00%)
  committing files:
  b
  committing manifest
  committing changelog
  updating the branch cache
  obscache is out of date
  invalid branch cache (served): tip differs
  invalid branch cache (served.hidden): tip differs
  resolving manifests
   branchmerge: False, force: False, partial: False
   ancestor: 1edc3bac9e3c, local: 1edc3bac9e3c+, remote: f8d7d38c0a88
   b: other deleted -> r
  removing b
  updating: b 1/2 files (50.00%)
   a: remote is newer -> g
  getting a
  updating: a 2/2 files (100.00%)

  $ cd ..
