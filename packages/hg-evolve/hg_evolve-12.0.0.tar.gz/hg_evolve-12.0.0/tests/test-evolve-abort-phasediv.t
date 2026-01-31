Tests for the --abort flag for `hg evolve` command while phase-divergence resolution
====================================================================================

The `--abort` flag aborts the interuppted evolve by undoing all the work which
was done during resolution i.e. stripping new changesets created, moving
bookmarks back, moving working directory back.

This test contains cases when `hg evolve` is doing phase-divergence resolution.

Setup
=====

  $ . $TESTDIR/testlib/common.sh

#testcases abortcommand abortflag
  $ cat >> $HGRCPATH <<EOF
  > [phases]
  > publish = False
  > [extensions]
  > evolve =
  > EOF

#if abortflag
  $ cat >> $HGRCPATH <<EOF
  > [alias]
  > abort = evolve --abort
  > EOF
#endif

#testcases inmemory ondisk
#if inmemory
  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution.in-memory = yes
  > EOF
#endif

  $ hg init abortrepo
  $ cd abortrepo
  $ echo ".*\.orig" > .hgignore
  $ hg add .hgignore
  $ hg ci -m "added hgignore"
  $ for ch in a b c d; do echo foo > $ch; hg add $ch; hg ci -qm "added "$ch; done;

  $ hg glog
  @  4:c41c793e0ef1 added d
  |   () draft
  o  3:ca1b80f7960a added c
  |   () draft
  o  2:b1661037fa25 added b
  |   () draft
  o  1:c7586e2a9264 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

Creating phase divergence, resolution of which will lead to conflicts
----------------------------------------------------------------------

  $ hg up .^^^
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ hg pick -r .~-3
  picking 4:c41c793e0ef1 "added d"
  $ echo foobar > c
  $ hg add c
  $ hg amend

  $ hg glog --hidden
  @  6:ddba58020bc0 added d
  |   () draft
  | x  5:cfe30edc6125 added d
  |/    () draft
  | x  4:c41c793e0ef1 added d
  | |   () draft
  | o  3:ca1b80f7960a added c
  | |   () draft
  | o  2:b1661037fa25 added b
  |/    () draft
  o  1:c7586e2a9264 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg phase -r c41c793e0ef1 --public --hidden
  1 new phase-divergent changesets

  $ hg glog
  @  6:ddba58020bc0 added d
  |   () draft phase-divergent
  | o  4:c41c793e0ef1 added d
  | |   () public
  | o  3:ca1b80f7960a added c
  | |   () public
  | o  2:b1661037fa25 added b
  |/    () public
  o  1:c7586e2a9264 added a
  |   () public
  o  0:8fa14d15e168 added hgignore
      () public
  $ hg evolve --phase-divergent
  recreate:[6] added d
  atop:[4] added d
  rebasing to destination parent: ca1b80f7960a
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

testing that interrupted evolve shows up in morestatus
  $ hg status -v
  M c
  A d
  # The repository is in an unfinished *evolve* state.
  
  # Unresolved merge conflicts:
  # 
  #     c
  # 
  # To mark files as resolved:  hg resolve --mark FILE
  
  # To continue:    hg evolve --continue
  # To abort:       hg evolve --abort
  # To stop:        hg evolve --stop
  # (also see `hg help evolve.interrupted`)
  

  $ hg parents
  changeset:   3:ca1b80f7960a
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added c
  

  $ hg abort
  evolve aborted
  working directory is now at ddba58020bc0

  $ hg glog
  @  6:ddba58020bc0 added d
  |   () draft phase-divergent
  | o  4:c41c793e0ef1 added d
  | |   () public
  | o  3:ca1b80f7960a added c
  | |   () public
  | o  2:b1661037fa25 added b
  |/    () public
  o  1:c7586e2a9264 added a
  |   () public
  o  0:8fa14d15e168 added hgignore
      () public

When there are multiple phase-divergent changes, resolution of last one resulted
in conflicts
---------------------------------------------------------------------------------

  $ echo foo > c
  $ hg amend
  $ hg phase -r ca1b80f --draft --force
  $ hg prev
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  [1] added a
  $ hg pick -r ca1b80f
  picking 3:ca1b80f7960a "added c"
  $ echo foobar > b
  $ hg add b
  $ hg amend
  $ hg phase -r c41c793e0ef1 --public --hidden
  2 new phase-divergent changesets

  $ hg evolve --list
  e44ebefe4f54: added d
    phase-divergent: c41c793e0ef1 (immutable precursor)
  
  28cd06b3f801: added c
    phase-divergent: ca1b80f7960a (immutable precursor)
  

  $ hg evolve --dry-run --all --phase-divergent
  recreate:[7] added d
  atop:[4] added d
  hg rebase --rev e44ebefe4f54 --dest ca1b80f7960a;
  hg update c41c793e0ef1;
  hg revert --all --rev e44ebefe4f54;
  hg commit --message "phase-divergent update to e44ebefe4f54"
  recreate:[9] added c
  atop:[3] added c
  hg rebase --rev 28cd06b3f801 --dest b1661037fa25;
  hg update ca1b80f7960a;
  hg revert --all --rev 28cd06b3f801;
  hg commit --message "phase-divergent update to 28cd06b3f801"

  $ hg glog --hidden
  @  9:28cd06b3f801 added c
  |   () draft phase-divergent
  | x  8:9ff8adbe8a24 added c
  |/    () draft
  | *  7:e44ebefe4f54 added d
  |/    () draft phase-divergent
  | x  6:ddba58020bc0 added d
  |/    () draft
  | x  5:cfe30edc6125 added d
  |/    () draft
  | o  4:c41c793e0ef1 added d
  | |   () public
  | o  3:ca1b80f7960a added c
  | |   () public
  | o  2:b1661037fa25 added b
  |/    () public
  o  1:c7586e2a9264 added a
  |   () public
  o  0:8fa14d15e168 added hgignore
      () public

  $ hg evolve --phase-divergent --all
  recreate:[7] added d
  atop:[4] added d
  rebasing to destination parent: ca1b80f7960a
  no changes to commit
  recreate:[9] added c
  atop:[3] added c
  rebasing to destination parent: b1661037fa25
  merging b
  warning: conflicts while merging b! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg abort
  1 new phase-divergent changesets
  evolve aborted
  working directory is now at 28cd06b3f801

  $ hg glog --hidden
  @  9:28cd06b3f801 added c
  |   () draft phase-divergent
  | x  8:9ff8adbe8a24 added c
  |/    () draft
  | *  7:e44ebefe4f54 added d
  |/    () draft phase-divergent
  | x  6:ddba58020bc0 added d
  |/    () draft
  | x  5:cfe30edc6125 added d
  |/    () draft
  | o  4:c41c793e0ef1 added d
  | |   () public
  | o  3:ca1b80f7960a added c
  | |   () public
  | o  2:b1661037fa25 added b
  |/    () public
  o  1:c7586e2a9264 added a
  |   () public
  o  0:8fa14d15e168 added hgignore
      () public

When there are multiple conflicted phase-divergence resolution and we abort
after resolving one of them
----------------------------------------------------------------------------

  $ hg up e44ebefe4f54
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo foobar > c
  $ hg amend

  $ hg glog --hidden
  @  10:ef9b72b9b42c added d
  |   () draft phase-divergent
  | *  9:28cd06b3f801 added c
  |/    () draft phase-divergent
  | x  8:9ff8adbe8a24 added c
  |/    () draft
  | x  7:e44ebefe4f54 added d
  |/    () draft
  | x  6:ddba58020bc0 added d
  |/    () draft
  | x  5:cfe30edc6125 added d
  |/    () draft
  | o  4:c41c793e0ef1 added d
  | |   () public
  | o  3:ca1b80f7960a added c
  | |   () public
  | o  2:b1661037fa25 added b
  |/    () public
  o  1:c7586e2a9264 added a
  |   () public
  o  0:8fa14d15e168 added hgignore
      () public

  $ hg evolve --phase-divergent --all
  recreate:[9] added c
  atop:[3] added c
  rebasing to destination parent: b1661037fa25
  merging b
  warning: conflicts while merging b! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo watwat > c
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 9:28cd06b3f801 "added c"
  committed as 92acf49069a4
  recreate:[10] added d
  atop:[4] added d
  rebasing to destination parent: ca1b80f7960a
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg abort
  1 new phase-divergent changesets
  evolve aborted
  working directory is now at ef9b72b9b42c

  $ hg glog --hidden
  @  10:ef9b72b9b42c added d
  |   () draft phase-divergent
  | *  9:28cd06b3f801 added c
  |/    () draft phase-divergent
  | x  8:9ff8adbe8a24 added c
  |/    () draft
  | x  7:e44ebefe4f54 added d
  |/    () draft
  | x  6:ddba58020bc0 added d
  |/    () draft
  | x  5:cfe30edc6125 added d
  |/    () draft
  | o  4:c41c793e0ef1 added d
  | |   () public
  | o  3:ca1b80f7960a added c
  | |   () public
  | o  2:b1661037fa25 added b
  |/    () public
  o  1:c7586e2a9264 added a
  |   () public
  o  0:8fa14d15e168 added hgignore
      () public
