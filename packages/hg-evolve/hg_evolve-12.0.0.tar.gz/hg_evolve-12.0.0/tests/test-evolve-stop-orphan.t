Tests for the --stop flag for `hg evolve` command while resolving orphans
=========================================================================

The `--stop` flag stops the interrupted evolution and delete the state file so
user can do other things and comeback and do evolution later on

This is testing cases when `hg evolve` command is doing orphan resolution.

Setup
=====

  $ . $TESTDIR/testlib/common.sh

  $ cat >> $HGRCPATH <<EOF
  > [extensions]
  > evolve =
  > EOF

#testcases inmemory ondisk
#if inmemory
  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution.in-memory = yes
  > EOF
#endif

  $ hg init stoprepo
  $ cd stoprepo
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

Testing `--stop` when no evolve is interrupted
==============================================

  $ hg evolve --stop
  abort: no interrupted evolve to stop
  [20]

Testing with wrong combinations of flags
========================================

  $ hg evolve --stop --rev 1
  abort: cannot specify both "--rev" and "--stop"
  [255]

  $ hg evolve --stop --continue
  abort: cannot specify both "--stop" and "--continue"
  [255]

  $ hg evolve --stop --all
  abort: cannot specify both "--all" and "--stop"
  [255]

  $ hg evolve --stop --any
  abort: cannot specify both "--any" and "--stop"
  [255]

Testing when only one revision is to evolve
===========================================

  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [3] added c
  $ echo bar > d
  $ hg add d
  $ hg amend
  1 new orphan changesets
  $ hg glog
  @  5:cb6a2ab625bb added c
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

  $ hg evolve
  move:[4] added d
  atop:[5] added c
  merging d (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging d
  warning: conflicts while merging d! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg evolve --stop
  stopped the interrupted evolve
  working directory is now at cb6a2ab625bb

Checking whether evolvestate file exists or not
  $ cat .hg/evolvestate
  cat: .hg/evolvestate: No such file or directory
  [1]

Checking where we are
  $ hg id
  cb6a2ab625bb tip

Checking working dir
  $ hg status
Checking for incomplete mergestate
  $ ls .hg/ | grep merge
  [1]

Checking graph
  $ hg glog
  @  5:cb6a2ab625bb added c
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

Testing the stop flag in case conflicts are caused by `hg next --evolve`
========================================================================

  $ hg next --evolve
  move:[4] added d
  atop:[5] added c
  merging d (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging d
  warning: conflicts while merging d! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg diff
  diff -r cb6a2ab625bb d
  --- a/d	Thu Jan 01 00:00:00 1970 +0000
  +++ b/d	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,5 @@
  +<<<<<<< destination: cb6a2ab625bb - test: added c
   bar
  +=======
  +foo
  +>>>>>>> evolving:    c41c793e0ef1 - test: added d

We do have state files for evolve and merge before the --stop
  $ find .hg/ -name '*state' | grep -v dirstate | sort
  .hg/evolvestate
  .hg/merge/state

  $ hg evolve --stop
  stopped the interrupted evolve

  $ hg glog
  @  5:cb6a2ab625bb added c
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

  $ hg status

The state files are gone after the --stop
  $ find .hg/ -name '*state' | grep -v dirstate
  [1]

Checking when multiple revs need to be evolved, some revs evolve without
conflicts
=========================================================================

Making sure obsmarkers should be on evolved changeset and not rest of them once
we do `evolve --stop`
--------------------------------------------------------------------------------

  $ hg evolve --update
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
  working directory is now at 250d8c3c5ad9
  $ hg glog
  @  6:250d8c3c5ad9 added d
  |   () draft
  o  5:cb6a2ab625bb added c
  |   () draft
  o  2:b1661037fa25 added b
  |   () draft
  o  1:c7586e2a9264 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg up .^^^^
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  $ echo bar > c
  $ hg add c
  $ hg amend
  4 new orphan changesets

  $ hg glog
  @  7:21817cd42526 added hgignore
      () draft
  *  6:250d8c3c5ad9 added d
  |   () draft orphan
  *  5:cb6a2ab625bb added c
  |   () draft orphan
  *  2:b1661037fa25 added b
  |   () draft orphan
  *  1:c7586e2a9264 added a
  |   () draft orphan
  x  0:8fa14d15e168 added hgignore
      () draft

  $ hg evolve --all
  move:[1] added a
  atop:[7] added hgignore
  move:[2] added b
  move:[5] added c
  merging c (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg status
  M c
  A d

  $ hg evolve --stop
  stopped the interrupted evolve
  working directory is now at 21817cd42526

Only changeset which has a successor now are obsoleted
  $ hg glog
  o  9:aec285328e90 added b
  |   () draft
  o  8:fd00db71edca added a
  |   () draft
  @  7:21817cd42526 added hgignore
      () draft
  *  6:250d8c3c5ad9 added d
  |   () draft orphan
  *  5:cb6a2ab625bb added c
  |   () draft orphan
  x  2:b1661037fa25 added b
  |   () draft
  x  1:c7586e2a9264 added a
  |   () draft
  x  0:8fa14d15e168 added hgignore
      () draft

Making sure doing evolve again resumes from right place and does the right thing

  $ hg evolve --all
  move:[5] added c
  atop:[9] added b
  merging c (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo foobar > c
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 5:cb6a2ab625bb "added c"
  move:[6] added d
  atop:[10] added c
  $ hg glog
  o  11:4b77e6973234 added d
  |   () draft
  o  10:b4e2f43191a0 added c
  |   () draft
  o  9:aec285328e90 added b
  |   () draft
  o  8:fd00db71edca added a
  |   () draft
  @  7:21817cd42526 added hgignore
      () draft

Bookmarks should only be moved of the changesets which have been evolved,
bookmarks of rest of them should stay where they are are
-------------------------------------------------------------------------

  $ hg up tip^
  4 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg bookmark b1
  $ hg up .^
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  (leaving bookmark b1)
  $ hg bookmark b2

  $ hg glog
  o  11:4b77e6973234 added d
  |   () draft
  o  10:b4e2f43191a0 added c
  |   (b1) draft
  @  9:aec285328e90 added b
  |   (b2) draft
  o  8:fd00db71edca added a
  |   () draft
  o  7:21817cd42526 added hgignore
      () draft

  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [8] added a
  $ echo tom > c
  $ hg amend
  3 new orphan changesets

  $ hg glog
  @  12:a3cc2042492f added a
  |   () draft
  | *  11:4b77e6973234 added d
  | |   () draft orphan
  | *  10:b4e2f43191a0 added c
  | |   (b1) draft orphan
  | *  9:aec285328e90 added b
  | |   (b2) draft orphan
  | x  8:fd00db71edca added a
  |/    () draft
  o  7:21817cd42526 added hgignore
      () draft

  $ hg evolve --all
  move:[9] added b
  atop:[12] added a
  move:[10] added c
  merging c (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg evolve --stop
  stopped the interrupted evolve
  working directory is now at a3cc2042492f

Bookmarks of only the changeset which are evolved is moved
  $ hg glog
  o  13:a3f4b95da934 added b
  |   (b2) draft
  @  12:a3cc2042492f added a
  |   () draft
  | *  11:4b77e6973234 added d
  | |   () draft orphan
  | *  10:b4e2f43191a0 added c
  | |   (b1) draft orphan
  | x  9:aec285328e90 added b
  | |   () draft
  | x  8:fd00db71edca added a
  |/    () draft
  o  7:21817cd42526 added hgignore
      () draft
