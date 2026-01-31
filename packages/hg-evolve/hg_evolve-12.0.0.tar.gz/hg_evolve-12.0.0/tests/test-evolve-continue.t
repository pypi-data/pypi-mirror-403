Testing the continue functionality of `hg evolve`

  $ . $TESTDIR/testlib/common.sh

  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > interactive = True
  > [extensions]
  > rebase =
  > evolve =
  > EOF

#testcases inmemory ondisk
#if inmemory
  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution.in-memory = yes
  > EOF
#endif

Setting up the repo

  $ hg init repo
  $ cd repo
  $ echo ".*\.orig" > .hgignore
  $ hg add .hgignore
  $ hg ci -m "added hgignore"
  $ for ch in a b c d; do echo foo>$ch; hg add $ch; hg ci -qm "added "$ch; done

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

Simple case of evolve --continue

  $ hg up 'desc("added c")'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
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

  $ echo foo > d
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue
  evolving 4:c41c793e0ef1 "added d"

  $ hg glog
  o  6:250d8c3c5ad9 added d
  |   () draft
  @  5:cb6a2ab625bb added c
  |   () draft
  o  2:b1661037fa25 added b
  |   () draft
  o  1:c7586e2a9264 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg up
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

Testing hg continue for evolve

  $ hg up 'desc("added b")'
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo bar > c
  $ hg add c
  $ hg amend
  2 new orphan changesets
  $ hg glog
  @  7:8591ebad2ee8 added b
  |   () draft
  | *  6:250d8c3c5ad9 added d
  | |   () draft orphan
  | *  5:cb6a2ab625bb added c
  | |   () draft orphan
  | x  2:b1661037fa25 added b
  |/    () draft
  o  1:c7586e2a9264 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg evolve --all
  move:[5] added c
  atop:[7] added b
  merging c (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo foo > c
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg continue
  evolving 5:cb6a2ab625bb "added c"
  move:[6] added d
  atop:[8] added c

  $ hg glog
  o  9:628919fc6772 added d
  |   () draft
  o  8:f8d5006085c0 added c
  |   () draft
  @  7:8591ebad2ee8 added b
  |   () draft
  o  1:c7586e2a9264 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg up
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved

Case when conflicts resolution lead to empty wdir in evolve --continue

  $ echo foo > e
  $ hg ci -Aqm "added e"
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [9] added d
  $ echo bar > e
  $ hg add e
  $ hg amend
  1 new orphan changesets

  $ hg glog
  @  11:7898e026e390 added d
  |   () draft
  | *  10:5610cf0a9e66 added e
  | |   () draft orphan
  | x  9:628919fc6772 added d
  |/    () draft
  o  8:f8d5006085c0 added c
  |   () draft
  o  7:8591ebad2ee8 added b
  |   () draft
  o  1:c7586e2a9264 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg evolve --update
  move:[10] added e
  atop:[11] added d
  merging e (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging e
  warning: conflicts while merging e! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo bar > e
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg diff

  $ hg evolve --continue
  evolving 10:5610cf0a9e66 "added e"
  evolution of 10:5610cf0a9e66 created no changes to commit

  $ hg glog
  @  11:7898e026e390 added d
  |   () draft
  o  8:f8d5006085c0 added c
  |   () draft
  o  7:8591ebad2ee8 added b
  |   () draft
  o  1:c7586e2a9264 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

Case when there are a lot of revision to continue

  $ hg up 'desc("added a")'
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  $ echo bar > b
  $ hg add b
  $ hg amend
  3 new orphan changesets

  $ hg evolve --all --update
  move:[7] added b
  atop:[12] added a
  merging b (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging b
  warning: conflicts while merging b! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo foo > b
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 7:8591ebad2ee8 "added b"
  move:[8] added c
  atop:[13] added b
  move:[11] added d
  working directory is now at 0fb68c8390f6

  $ hg glog
  @  15:0fb68c8390f6 added d
  |   () draft
  o  14:7bf9d72ff3bf added c
  |   () draft
  o  13:aaa724b65a25 added b
  |   () draft
  o  12:53b632d203d8 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

Conlicts -> resolve -> continue -> conflicts -> resolve -> continue
Test multiple conflicts in one evolve

  $ for ch in f g h; do echo foo > $ch; hg add $ch; hg ci -m "added "$ch; done;

  $ hg glog
  @  18:1519cf722575 added h
  |   () draft
  o  17:04c32ddd9b44 added g
  |   () draft
  o  16:29139ab665e3 added f
  |   () draft
  o  15:0fb68c8390f6 added d
  |   () draft
  o  14:7bf9d72ff3bf added c
  |   () draft
  o  13:aaa724b65a25 added b
  |   () draft
  o  12:53b632d203d8 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg up 'desc("added c")'
  1 files updated, 0 files merged, 4 files removed, 0 files unresolved

  $ echo bar > f
  $ echo bar > h
  $ hg add f h
  $ hg amend
  4 new orphan changesets

  $ hg glog
  @  19:ebc872a542e5 added c
  |   () draft
  | *  18:1519cf722575 added h
  | |   () draft orphan
  | *  17:04c32ddd9b44 added g
  | |   () draft orphan
  | *  16:29139ab665e3 added f
  | |   () draft orphan
  | *  15:0fb68c8390f6 added d
  | |   () draft orphan
  | x  14:7bf9d72ff3bf added c
  |/    () draft
  o  13:aaa724b65a25 added b
  |   () draft
  o  12:53b632d203d8 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg evolve --all --update
  move:[15] added d
  atop:[19] added c
  move:[16] added f
  merging f (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging f
  warning: conflicts while merging f! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo foo > f
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 16:29139ab665e3 "added f"
  move:[17] added g
  atop:[21] added f
  move:[18] added h
  merging h (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging h
  warning: conflicts while merging h! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo foo > h
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 18:1519cf722575 "added h"
  working directory is now at 0eb2b6434bd7

Make sure, confirmopt is respected while continue

  $ hg glog
  @  23:0eb2b6434bd7 added h
  |   () draft
  o  22:d4c17c25a1c7 added g
  |   () draft
  o  21:602e4bd1e5aa added f
  |   () draft
  o  20:5cf56d246d18 added d
  |   () draft
  o  19:ebc872a542e5 added c
  |   () draft
  o  13:aaa724b65a25 added b
  |   () draft
  o  12:53b632d203d8 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

  $ hg up 'desc("added f")'
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo bar > g
  $ hg add g
  $ hg amend
  2 new orphan changesets

  $ hg evolve --all --update --confirm << EOF
  > y
  > EOF
  move:[22] added g
  atop:[24] added f
  perform evolve? [Ny] y
  merging g (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging g
  warning: conflicts while merging g! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo foo > g
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue << EOF
  > y
  > EOF
  evolving 22:d4c17c25a1c7 "added g"
  move:[23] added h
  atop:[25] added g
  perform evolve? [Ny] y
  working directory is now at cc583f773dc4

  $ hg glog
  @  26:cc583f773dc4 added h
  |   () draft
  o  25:84772f0dfa79 added g
  |   () draft
  o  24:d074fc123610 added f
  |   () draft
  o  20:5cf56d246d18 added d
  |   () draft
  o  19:ebc872a542e5 added c
  |   () draft
  o  13:aaa724b65a25 added b
  |   () draft
  o  12:53b632d203d8 added a
  |   () draft
  o  0:8fa14d15e168 added hgignore
      () draft

Testing `evolve --continue` after `hg next --evolve`

  $ hg up .^^
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo foobar > g
  $ hg amend
  2 new orphan changesets

  $ hg next --evolve
  move:[25] added g
  atop:[27] added f
  merging g (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging g
  warning: conflicts while merging g! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ echo foo > g
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 25:84772f0dfa79 "added g"

Testing that interrupted evolve don't get confused about copies (issue5930):
----------------------------------------------------------------------------

  $ cd ..
  $ hg init issue5930
  $ cd issue5930
  $ echo a > a
  $ hg ci -Am "added a"
  adding a
  $ hg cp a b
  $ hg ci -m "rename a to b"

  $ hg up 0 -q
  $ echo c > c
  $ hg ci -Am "added c"
  adding c
  created new head

  $ echo d > c
  $ echo d > d
  $ hg ci -Am "added d, modified c"
  adding d
  $ hg up .^
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved

  $ hg log -G -T "{rev} {desc}\n"
  o  3 added d, modified c
  |
  @  2 added c
  |
  | o  1 rename a to b
  |/
  o  0 added a
  
  $ hg rebase -r . -d 1
  rebasing 2:29edef26570b "added c"
  1 new orphan changesets
  $ echo conflict > c
  $ hg amend

  $ hg log -G -T "{rev} {desc}\n"
  @  5 added c
  |
  | *  3 added d, modified c
  | |
  | x  2 added c
  | |
  o |  1 rename a to b
  |/
  o  0 added a
  

  $ hg evolve
  move:[3] added d, modified c
  atop:[5] added c
  merging c (inmemory !)
  hit merge conflicts; retrying merge in working copy (inmemory !)
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

Status mentions file 'b' (copied from 'a') here, even though it wasn't
affected by the evolved changeset (nor was 'a')

  $ hg st -C
  M c
  A d
  ? c.orig

  $ cd ..
  $ hg init transitive-renames
  $ cd transitive-renames
  $ echo 1 > a
  $ echo 1 > b
  $ hg ci -Aqm initial
  $ echo 2 > a
  $ hg mv b c
  $ hg ci -m 'rename b to c'
  $ echo 3 > a
  $ hg mv c d
  $ hg ci -m 'rename c to d'
  $ hg prev -q
  $ echo 2b > a
  $ hg amend -q
  1 new orphan changesets
  $ hg evolve -q
  warning: conflicts while merging a! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ hg st -C
  M a
  A d
    c
  R c
  ? a.orig
