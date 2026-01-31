Tests for the --abort flag for `hg evolve` command while orphan resolution
==========================================================================

The `--abort` flag aborts the interrupted evolve by undoing all the work which
was done during resolution i.e. stripping new changesets created, moving
bookmarks back, moving working directory back.

This test contains cases when `hg evolve` is doing orphan resolution.

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

Testing --abort when no evolve is interrupted
=============================================

#if abortflag
  $ hg evolve --abort
  abort: no interrupted evolve to abort
  [20]
#else
  $ hg abort
  abort: no operation in progress
  [20]
#endif

Testing with wrong combination of flags
=======================================

  $ hg evolve --abort --continue
  abort: cannot specify both "--abort" and "--continue"
  [255]

  $ hg evolve --abort --stop
  abort: cannot specify both "--abort" and "--stop"
  [255]

  $ hg evolve --abort --rev 3
  abort: cannot specify both "--rev" and "--abort"
  [255]

  $ hg evolve --abort --any
  abort: cannot specify both "--any" and "--abort"
  [255]

  $ hg evolve --abort --all
  abort: cannot specify both "--all" and "--abort"
  [255]

Normal testingw when no rev was evolved
========================================

  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [3] added c

  $ echo babar > d
  $ hg add d
  $ hg amend
  1 new orphan changesets

  $ hg evolve --all
  move:[4] added d
  atop:[5] added c
  merging d (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging d
  warning: conflicts while merging d! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg parents
  changeset:   5:e93a9161a274
  tag:         tip
  parent:      2:b1661037fa25
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added c
  
#if abortcommand
when in dry-run mode
  $ hg abort --dry-run
  evolve in progress, will be aborted
#endif

  $ hg abort
  evolve aborted
  working directory is now at e93a9161a274

  $ hg glog
  @  5:e93a9161a274 added c
  |   () draft
  | *  4:c41c793e0ef1 added d
  | |   () draft orphan
  | x  3:ca1b80f7960a added c
  |/    () draft
  o  2:b1661037fa25 added b
  |   () draft
  o  1:c7586e2a9264 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg diff

  $ hg status

cleaning up things for next testing

  $ hg evolve --all --update
  move:[4] added d
  atop:[5] added c
  merging d (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging d
  warning: conflicts while merging d! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ echo foo > d
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 4:c41c793e0ef1 "added d"
  working directory is now at 69c43da639bb

  $ hg up .^^^
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved

When there are evolved revisions but on a single branch
=======================================================

  $ echo bar > c
  $ hg add c
  $ hg amend
  3 new orphan changesets

  $ hg evolve --all
  move:[2] added b
  atop:[7] added a
  move:[5] added c
  merging c (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
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
  

  $ hg glog
  @  8:0c41ec482070 added b
  |   () draft
  o  7:125af0ed8cae added a
  |   () draft
  | *  6:69c43da639bb added d
  | |   () draft orphan
  | %  5:e93a9161a274 added c
  | |   () draft orphan
  | x  2:b1661037fa25 added b
  | |   () draft
  | x  1:c7586e2a9264 added a
  |/    () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg abort
  1 new orphan changesets
  evolve aborted
  working directory is now at 125af0ed8cae

  $ hg glog
  @  7:125af0ed8cae added a
  |   () draft
  | *  6:69c43da639bb added d
  | |   () draft orphan
  | *  5:e93a9161a274 added c
  | |   () draft orphan
  | *  2:b1661037fa25 added b
  | |   () draft orphan
  | x  1:c7586e2a9264 added a
  |/    () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ cd ..

Testing when evolved revs are on multiple branches
==================================================

  $ hg init repotwo
  $ cd repotwo
  $ echo ".*\.orig" > .hgignore
  $ hg add .hgignore
  $ hg ci -m "added hgignore"
  $ echo a > a
  $ hg ci -Aqm "added a"
  $ for ch in b c; do echo $ch > $ch; hg add $ch; hg ci -m "added "$ch; done;
  $ hg up .^^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ for ch in c d; do echo $ ch > $ch; hg add $ch; hg ci -m "added "$ch; done;
  created new head
  $ hg up .^^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo foo > a
  $ hg ci -m "foo to a"
  created new head

  $ hg glog
  @  6:8f20d4390c21 foo to a
  |   () draft
  | o  5:bcb1c47f8520 added d
  | |   () draft
  | o  4:86d2603075a3 added c
  |/    () draft
  | o  3:17509928e5bf added c
  | |   () draft
  | o  2:9f0c80a55ddc added b
  |/    () draft
  o  1:2f913b0c9220 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg prev
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [1] added a
  $ echo aa > a
  $ hg amend
  5 new orphan changesets

  $ hg evolve --all
  move:[2] added b
  atop:[7] added a
  move:[4] added c
  atop:[7] added a
  move:[6] foo to a
  atop:[7] added a
  merging a (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging a
  warning: conflicts while merging a! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg glog
  o  9:7f8e8bd9f0b6 added c
  |   () draft
  | o  8:db3b42ef4da7 added b
  |/    () draft
  @  7:807e8e2ca559 added a
  |   () draft
  | %  6:8f20d4390c21 foo to a
  | |   () draft orphan
  | | *  5:bcb1c47f8520 added d
  | | |   () draft orphan
  | | x  4:86d2603075a3 added c
  | |/    () draft
  | | *  3:17509928e5bf added c
  | | |   () draft orphan
  | | x  2:9f0c80a55ddc added b
  | |/    () draft
  | x  1:2f913b0c9220 added a
  |/    () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg abort
  2 new orphan changesets
  evolve aborted
  working directory is now at 807e8e2ca559

  $ hg glog
  @  7:807e8e2ca559 added a
  |   () draft
  | *  6:8f20d4390c21 foo to a
  | |   () draft orphan
  | | *  5:bcb1c47f8520 added d
  | | |   () draft orphan
  | | *  4:86d2603075a3 added c
  | |/    () draft orphan
  | | *  3:17509928e5bf added c
  | | |   () draft orphan
  | | *  2:9f0c80a55ddc added b
  | |/    () draft orphan
  | x  1:2f913b0c9220 added a
  |/    () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg status

  $ hg diff

Testing when user created a new changesets on top of evolved revisions
======================================================================

  $ hg evolve --all
  move:[2] added b
  atop:[7] added a
  move:[4] added c
  atop:[7] added a
  move:[6] foo to a
  atop:[7] added a
  merging a (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging a
  warning: conflicts while merging a! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ hg glog
  o  9:7f8e8bd9f0b6 added c
  |   () draft
  | o  8:db3b42ef4da7 added b
  |/    () draft
  @  7:807e8e2ca559 added a
  |   () draft
  | %  6:8f20d4390c21 foo to a
  | |   () draft orphan
  | | *  5:bcb1c47f8520 added d
  | | |   () draft orphan
  | | x  4:86d2603075a3 added c
  | |/    () draft
  | | *  3:17509928e5bf added c
  | | |   () draft orphan
  | | x  2:9f0c80a55ddc added b
  | |/    () draft
  | x  1:2f913b0c9220 added a
  |/    () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ echo foo > a
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ cd ..
  $ hg init clonerepo
  $ cd repotwo
  $ hg push ../clonerepo --force
  pushing to ../clonerepo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 10 changesets with 8 changes to 5 files (+4 heads)
  3 new obsolescence markers
  3 new orphan changesets
  $ cd ../clonerepo
  $ hg up 7f8e8bd9f0b6
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo bar > bar
  $ hg add bar
  $ hg ci -m "made an new commit on evolved rev"

  $ hg push ../repotwo --force
  pushing to ../repotwo
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  $ cd ../repotwo
  $ hg abort
  warning: new changesets detected on destination branch
  abort: unable to abort interrupted evolve, use 'hg evolve --stop' to stop evolve
  [255]

  $ hg evolve --stop
  stopped the interrupted evolve
  working directory is now at 807e8e2ca559

Testing when the evolved revision turned public due to some other user actions
==============================================================================

  $ hg evolve --all
  move:[3] added c
  atop:[8] added b
  move:[5] added d
  atop:[9] added c
  move:[6] foo to a
  atop:[7] added a
  merging a (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging a
  warning: conflicts while merging a! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg glog
  o  12:1c476940790a added d
  |   () draft
  | o  11:c10a55eb0cc6 added c
  | |   () draft
  +---o  10:48eca1ed5478 made an new commit on evolved rev
  | |     () draft
  o |  9:7f8e8bd9f0b6 added c
  | |   () draft
  | o  8:db3b42ef4da7 added b
  |/    () draft
  @  7:807e8e2ca559 added a
  |   () draft
  | %  6:8f20d4390c21 foo to a
  | |   () draft orphan
  | x  1:2f913b0c9220 added a
  |/    () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg phase -r 1c476940790a --public

  $ hg abort
  cannot clean up public changesets: 1c476940790a
  abort: unable to abort interrupted evolve, use 'hg evolve --stop' to stop evolve
  [255]

  $ hg evolve --stop
  stopped the interrupted evolve
  working directory is now at 807e8e2ca559

  $ cd ..

Testing that bookmark should be moved back when doing `hg evolve --abort`
=========================================================================

  $ hg init repothree
  $ cd repothree
  $ echo ".*\.orig" > .hgignore
  $ hg add .hgignore
  $ hg ci -m "added hgignore"
  $ for ch in a b c; do echo $ch > $ch; hg add $ch; hg ci -m "added "$ch; done;

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg bookmark bm1
  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  (leaving bookmark bm1)
  $ echo foo > c
  $ hg add c
  $ hg amend
  2 new orphan changesets

  $ hg glog
  @  4:a0086c17bfc7 added a
  |   () draft
  | *  3:17509928e5bf added c
  | |   () draft orphan
  | *  2:9f0c80a55ddc added b
  | |   (bm1) draft orphan
  | x  1:2f913b0c9220 added a
  |/    () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg evolve --all
  move:[2] added b
  atop:[4] added a
  move:[3] added c
  merging c (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg glog
  @  5:c1f4718020e3 added b
  |   (bm1) draft
  o  4:a0086c17bfc7 added a
  |   () draft
  | %  3:17509928e5bf added c
  | |   () draft orphan
  | x  2:9f0c80a55ddc added b
  | |   () draft
  | x  1:2f913b0c9220 added a
  |/    () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg abort
  1 new orphan changesets
  evolve aborted
  working directory is now at a0086c17bfc7

  $ hg glog
  @  4:a0086c17bfc7 added a
  |   () draft
  | *  3:17509928e5bf added c
  | |   () draft orphan
  | *  2:9f0c80a55ddc added b
  | |   (bm1) draft orphan
  | x  1:2f913b0c9220 added a
  |/    () draft
  o  0:8fa14d15e168 added hgignore
      () draft

Testing `--abort` when conflicts are caused due to `hg next --evolve`
=====================================================================

  $ hg next --evolve
  move:[2] added b
  atop:[4] added a
  working directory is now at c1f4718020e3
  $ hg next --evolve
  move:[3] added c
  atop:[5] added b
  merging c (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

We do have state files for evolve and merge before abort

  $ find .hg/ -name '*state' | grep -v dirstate | sort
  .hg/evolvestate
  .hg/merge/state

The files are gone after abort

  $ hg abort
  evolve aborted
  working directory is now at c1f4718020e3
  $ find .hg/ -name '*state' | grep -v dirstate
  [1]
