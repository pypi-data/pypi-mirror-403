=================================================
Tests the resolution of content divergence: stack
=================================================

This file intend to cover case with stacks of divergent changesets

  $ cat >> $HGRCPATH <<EOF
  > [alias]
  > glog = log -GT "{rev}:{node|short} {desc|firstline}\n ({bookmarks}) [{branch}] {phase}"
  > [phases]
  > publish = False
  > [extensions]
  > strip =
  > rebase =
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

Resolving content-divergence of a stack with same parents
---------------------------------------------------------

  $ hg init stacktest
  $ cd stacktest
  $ echo ".*\.orig" > .hgignore
  $ hg add .hgignore
  $ hg ci -m "added hgignore"
  $ for ch in a b c d; do echo foo > $ch; hg add $ch; hg ci -qm "added "$ch; done;

  $ hg glog
  @  4:c41c793e0ef1 added d
  |   () [default] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ cd ..
  $ hg init stack2
  $ cd stack2
  $ hg pull ../stacktest
  pulling from ../stacktest
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 5 changesets with 5 changes to 5 files
  new changesets 8fa14d15e168:c41c793e0ef1 (5 drafts)
  (run 'hg update' to get a working copy)
  $ hg glog
  o  4:c41c793e0ef1 added d
  |   () [default] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg up c7586e2a9264
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo bar > a
  $ hg amend -m "watbar to a"
  3 new orphan changesets
  $ echo wat > a
  $ hg amend -m "watbar to a"
  $ hg evolve --all
  move:[2] added b
  atop:[6] watbar to a
  move:[3] added c
  move:[4] added d
  $ hg glog
  o  9:15c781f93cac added d
  |   () [default] draft
  o  8:9e5fb1d5b955 added c
  |   () [default] draft
  o  7:88516dccf68a added b
  |   () [default] draft
  @  6:82b74d5dc678 watbar to a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ cd ../stacktest
  $ hg up .^^^
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ echo wat > a
  $ hg amend -m "watbar to a"
  3 new orphan changesets
  $ hg evolve --all
  move:[2] added b
  atop:[5] watbar to a
  move:[3] added c
  move:[4] added d
  $ hg glog
  o  8:c72d2885eb51 added d
  |   () [default] draft
  o  7:3ce4be6d8e5e added c
  |   () [default] draft
  o  6:d5f148423c16 added b
  |   () [default] draft
  @  5:8e222f257bbf watbar to a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg pull ../stack2
  pulling from ../stack2
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 0 changes to 4 files (+1 heads)
  5 new obsolescence markers
  8 new content-divergent changesets
  new changesets 82b74d5dc678:15c781f93cac (4 drafts)
  (run 'hg heads' to see heads, 'hg merge' to merge)

  $ hg glog
  *  12:15c781f93cac added d
  |   () [default] draft
  *  11:9e5fb1d5b955 added c
  |   () [default] draft
  *  10:88516dccf68a added b
  |   () [default] draft
  *  9:82b74d5dc678 watbar to a
  |   () [default] draft
  | *  8:c72d2885eb51 added d
  | |   () [default] draft
  | *  7:3ce4be6d8e5e added c
  | |   () [default] draft
  | *  6:d5f148423c16 added b
  | |   () [default] draft
  | @  5:8e222f257bbf watbar to a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg evolve --all --content-divergent
  merge:[5] watbar to a
  with: [9] watbar to a
  base: [1] added a
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[6] added b
  with: [10] added b
  base: [2] added b
  rebasing "divergent" content-divergent changeset d5f148423c16 on df93a529fa42
  rebasing "other" content-divergent changeset 88516dccf68a on df93a529fa42
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[7] added c
  with: [11] added c
  base: [3] added c
  rebasing "divergent" content-divergent changeset 3ce4be6d8e5e on aca5a88a1692
  rebasing "other" content-divergent changeset 9e5fb1d5b955 on aca5a88a1692
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[8] added d
  with: [12] added d
  base: [4] added d
  rebasing "divergent" content-divergent changeset c72d2885eb51 on 67e04919c9a4
  rebasing "other" content-divergent changeset 15c781f93cac on 67e04919c9a4
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at df93a529fa42

  $ hg glog
  o  22:e72164a86fb4 added d
  |   () [default] draft
  o  19:67e04919c9a4 added c
  |   () [default] draft
  o  16:aca5a88a1692 added b
  |   () [default] draft
  @  13:df93a529fa42 watbar to a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

Testing --continue case when relocating "divergent"
---------------------------------------------------
When no relocation is required for "other", but "divergent"
hit merge conflict in relocation. This test makes sure that
content of two divergent csets merged correctly after the
merge conflict.

  $ hg log -r "desc('added c')" -p
  changeset:   19:67e04919c9a4
  parent:      16:aca5a88a1692
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added c
  
  diff -r aca5a88a1692 -r 67e04919c9a4 c
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +foo
  
  $ hg strip -r 17: --hidden
  saved backup bundle to $TESTTMP/stacktest/.hg/strip-backup/f1cd8f167491-3817ebd7-backup.hg
  4 new orphan changesets
  4 new content-divergent changesets
  $ hg glog
  o  16:aca5a88a1692 added b
  |   () [default] draft
  @  13:df93a529fa42 watbar to a
  |   () [default] draft
  | *  12:15c781f93cac added d
  | |   () [default] draft
  | *  11:9e5fb1d5b955 added c
  | |   () [default] draft
  | x  10:88516dccf68a added b
  | |   () [default] draft
  | x  9:82b74d5dc678 watbar to a
  |/    () [default] draft
  | *  8:c72d2885eb51 added d
  | |   () [default] draft
  | *  7:3ce4be6d8e5e added c
  | |   () [default] draft
  | x  6:d5f148423c16 added b
  | |   () [default] draft
  | x  5:8e222f257bbf watbar to a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft
  $ hg next
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [16] added b
  $ echo conflict > c
  $ hg amend -A
  adding c

add some changes on "other" side, to check later that merging performed correctly
  $ hg up -r 11
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo new_file > newfile
  $ hg amend -Am "added c and newfile"
  adding newfile
  $ hg glog
  @  18:2ecfb60af48a added c and newfile
  |   () [default] draft
  | o  17:5907cbc074a0 added b
  | |   () [default] draft
  | o  13:df93a529fa42 watbar to a
  | |   () [default] draft
  | | *  12:15c781f93cac added d
  | | |   () [default] draft
  +---x  11:9e5fb1d5b955 added c
  | |     () [default] draft
  x |  10:88516dccf68a added b
  | |   () [default] draft
  x |  9:82b74d5dc678 watbar to a
  |/    () [default] draft
  | *  8:c72d2885eb51 added d
  | |   () [default] draft
  | *  7:3ce4be6d8e5e added c
  | |   () [default] draft
  | x  6:d5f148423c16 added b
  | |   () [default] draft
  | x  5:8e222f257bbf watbar to a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg evolve --content-divergent -r 7
  merge:[7] added c
  with: [18] added c and newfile
  base: [3] added c
  rebasing "divergent" content-divergent changeset 3ce4be6d8e5e on 5907cbc074a0
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ echo c > c
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue
  evolving 7:3ce4be6d8e5e "added c"
  rebasing "other" content-divergent changeset 2ecfb60af48a on 5907cbc074a0
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ hg diff
  diff -r 5907cbc074a0 c
  --- a/c	Thu Jan 01 00:00:00 1970 +0000
  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,5 @@
  +<<<<<<< destination: 5907cbc074a0 - test: added b
   conflict
  +=======
  +foo
  +>>>>>>> evolving:    2ecfb60af48a - test: added c and newfile
  diff -r 5907cbc074a0 newfile
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/newfile	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +new_file

  $ echo c > c
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve -c
  evolving 18:2ecfb60af48a "added c and newfile"
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at e7933de77142

  $ hg log -p -l1
  changeset:   21:e7933de77142
  tag:         tip
  parent:      17:5907cbc074a0
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added c and newfile
  
  diff -r 5907cbc074a0 -r e7933de77142 c
  --- a/c	Thu Jan 01 00:00:00 1970 +0000
  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -conflict
  +c
  diff -r 5907cbc074a0 -r e7933de77142 newfile
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/newfile	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +new_file
  

Resolving content-divergence of a stack with different parents
---------------------------------------------------------

  $ cd ..
  $ hg init stackrepo1
  $ cd stackrepo1
  $ echo ".*\.orig" > .hgignore
  $ hg add .hgignore
  $ hg ci -m "added hgignore"

  $ for ch in a b c d;
  > do echo foo > $ch;
  > hg add $ch;
  > hg ci -qm "added "$ch;
  > done;

  $ hg glog
  @  4:c41c793e0ef1 added d
  |   () [default] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ cd ..
  $ hg init stackrepo2
  $ cd stackrepo2
  $ hg pull ../stackrepo1
  pulling from ../stackrepo1
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 5 changesets with 5 changes to 5 files
  new changesets 8fa14d15e168:c41c793e0ef1 (5 drafts)
  (run 'hg update' to get a working copy)

  $ hg glog
  o  4:c41c793e0ef1 added d
  |   () [default] draft
  o  3:ca1b80f7960a added c
  |   () [default] draft
  o  2:b1661037fa25 added b
  |   () [default] draft
  o  1:c7586e2a9264 added a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg up 8fa14d15e168
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo newfile > newfile
  $ hg ci -Am "add newfile"
  adding newfile
  created new head
  $ hg rebase -s c7586e2a9264 -d .
  rebasing 1:c7586e2a9264 "added a"
  rebasing 2:b1661037fa25 "added b"
  rebasing 3:ca1b80f7960a "added c"
  rebasing 4:c41c793e0ef1 "added d"

  $ hg glog
  o  9:d45f050514c2 added d
  |   () [default] draft
  o  8:8ed612937375 added c
  |   () [default] draft
  o  7:6eb54b5af3fb added b
  |   () [default] draft
  o  6:c04ff147ef79 added a
  |   () [default] draft
  @  5:2228e3b74514 add newfile
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ cd ../stackrepo1
  $ hg up .^^^
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ echo wat > a
  $ hg amend -m "watbar to a"
  3 new orphan changesets
  $ hg evolve --all
  move:[2] added b
  atop:[5] watbar to a
  move:[3] added c
  move:[4] added d

  $ hg glog
  o  8:c72d2885eb51 added d
  |   () [default] draft
  o  7:3ce4be6d8e5e added c
  |   () [default] draft
  o  6:d5f148423c16 added b
  |   () [default] draft
  @  5:8e222f257bbf watbar to a
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg pull ../stackrepo2
  pulling from ../stackrepo2
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 5 changesets with 1 changes to 5 files (+1 heads)
  4 new obsolescence markers
  8 new content-divergent changesets
  new changesets 2228e3b74514:d45f050514c2 (5 drafts)
  (run 'hg heads' to see heads, 'hg merge' to merge)

  $ hg glog
  *  13:d45f050514c2 added d
  |   () [default] draft
  *  12:8ed612937375 added c
  |   () [default] draft
  *  11:6eb54b5af3fb added b
  |   () [default] draft
  *  10:c04ff147ef79 added a
  |   () [default] draft
  o  9:2228e3b74514 add newfile
  |   () [default] draft
  | *  8:c72d2885eb51 added d
  | |   () [default] draft
  | *  7:3ce4be6d8e5e added c
  | |   () [default] draft
  | *  6:d5f148423c16 added b
  | |   () [default] draft
  | @  5:8e222f257bbf watbar to a
  |/    () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

  $ hg evolve --all --content-divergent
  merge:[5] watbar to a
  with: [10] added a
  base: [1] added a
  rebasing "divergent" content-divergent changeset 8e222f257bbf on 2228e3b74514
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[6] added b
  with: [11] added b
  base: [2] added b
  rebasing "divergent" content-divergent changeset d5f148423c16 on 4c0b67f978c2
  rebasing "other" content-divergent changeset 6eb54b5af3fb on 4c0b67f978c2
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[7] added c
  with: [12] added c
  base: [3] added c
  rebasing "divergent" content-divergent changeset 3ce4be6d8e5e on c2c8d7bb6505
  rebasing "other" content-divergent changeset 8ed612937375 on c2c8d7bb6505
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[8] added d
  with: [13] added d
  base: [4] added d
  rebasing "divergent" content-divergent changeset c72d2885eb51 on 2d29aa40ef18
  rebasing "other" content-divergent changeset d45f050514c2 on 2d29aa40ef18
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 4c0b67f978c2

  $ hg glog
  o  24:4a605b2a329e added d
  |   () [default] draft
  o  21:2d29aa40ef18 added c
  |   () [default] draft
  o  18:c2c8d7bb6505 added b
  |   () [default] draft
  @  15:4c0b67f978c2 watbar to a
  |   () [default] draft
  o  9:2228e3b74514 add newfile
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

when "divergent" and "other" both hit merge conflict in relocating
------------------------------------------------------------------

  $ hg strip 14: --hidden
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/stackrepo1/.hg/strip-backup/b0d57620c872-9e140417-backup.hg
  8 new content-divergent changesets

Prepare repo to have merge conflicts
  $ hg up -r "max(desc('added a'))"
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg evolve -r . --content-divergent
  merge:[5] watbar to a
  with: [10] added a
  base: [1] added a
  rebasing "divergent" content-divergent changeset 8e222f257bbf on 2228e3b74514
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  6 new orphan changesets
  working directory is now at 4c0b67f978c2
  $ echo b_conflict > b
  $ hg amend -A
  adding b

Let's try to evolve stack
  $ hg evolve --content-divergent
  merge:[6] added b
  with: [11] added b
  base: [2] added b
  rebasing "divergent" content-divergent changeset d5f148423c16 on 6b129ddb2c87
  merging b
  warning: conflicts while merging b! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo b > b
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 6:d5f148423c16 "added b"
  rebasing "other" content-divergent changeset 6eb54b5af3fb on 6b129ddb2c87
  merging b
  warning: conflicts while merging b! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo b > b
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 11:6eb54b5af3fb "added b"
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[7] added c
  with: [12] added c
  base: [3] added c
  rebasing "divergent" content-divergent changeset 3ce4be6d8e5e on e55b9e217879
  rebasing "other" content-divergent changeset 8ed612937375 on e55b9e217879
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[8] added d
  with: [13] added d
  base: [4] added d
  rebasing "divergent" content-divergent changeset c72d2885eb51 on 0e1902cb9cef
  rebasing "other" content-divergent changeset d45f050514c2 on 0e1902cb9cef
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg glog
  o  25:375c5a89ec21 added d
  |   () [default] draft
  o  22:0e1902cb9cef added c
  |   () [default] draft
  o  19:e55b9e217879 added b
  |   () [default] draft
  @  16:6b129ddb2c87 watbar to a
  |   () [default] draft
  o  9:2228e3b74514 add newfile
  |   () [default] draft
  o  0:8fa14d15e168 added hgignore
      () [default] draft

when relocating "other" hit merge conflict but not "divergent"
--------------------------------------------------------------
  $ hg strip 14: --hidden
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/stackrepo1/.hg/strip-backup/b0d57620c872-25c1f036-backup.hg
  8 new content-divergent changesets

Insert conflicting changes in between the stack of content-div csets
  $ hg up -r "max(desc('added b'))"
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo b_diverging_local > b
  $ hg amend
  2 new orphan changesets
  $ hg evolve
  move:[12] added c
  atop:[14] added b
  move:[13] added d
  $ hg up -r d5f148423c16
  2 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo b_diverging_other > b
  $ hg amend
  2 new orphan changesets
  $ hg evolve
  move:[7] added c
  atop:[17] added b
  move:[8] added d

  $ hg log -r tip
  changeset:   19:c351be27f199
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  instability: content-divergent
  summary:     added d
  
Now let's try to evolve stack
  $ hg evolve --content-divergent
  merge:[5] watbar to a
  with: [10] added a
  base: [1] added a
  rebasing "divergent" content-divergent changeset 8e222f257bbf on 2228e3b74514
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[14] added b
  with: [17] added b
  base: [2] added b
  rebasing "divergent" content-divergent changeset 2a955e808c53 on 4c0b67f978c2
  rebasing "other" content-divergent changeset 509103439e5e on 4c0b67f978c2
  merging b
  warning: conflicts while merging b! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  4 new orphan changesets
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

As now we have interrupted evolution of stack of content-divergent cset (when
relocation of "divergent" also included) let's test --abort and --stop 
test --abort:
  $ hg evolve --abort
  2 new content-divergent changesets
  evolve aborted
  working directory is now at 509103439e5e

confirm that tip is same as it was before we started --content-div resolution
  $ hg log -r tip
  changeset:   19:c351be27f199
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  instability: content-divergent
  summary:     added d
  
test --stop:
  $ hg log -G
  *  changeset:   19:c351be27f199
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: content-divergent
  |  summary:     added d
  |
  *  changeset:   18:eaf34afe4df3
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: content-divergent
  |  summary:     added c
  |
  @  changeset:   17:509103439e5e
  |  parent:      5:8e222f257bbf
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: content-divergent
  |  summary:     added b
  |
  | *  changeset:   16:91c8ccb9c241
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  instability: content-divergent
  | |  summary:     added d
  | |
  | *  changeset:   15:48b0f803817a
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  instability: content-divergent
  | |  summary:     added c
  | |
  | *  changeset:   14:2a955e808c53
  | |  parent:      10:c04ff147ef79
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  instability: content-divergent
  | |  summary:     added b
  | |
  | *  changeset:   10:c04ff147ef79
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  instability: content-divergent
  | |  summary:     added a
  | |
  | o  changeset:   9:2228e3b74514
  | |  parent:      0:8fa14d15e168
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     add newfile
  | |
  * |  changeset:   5:8e222f257bbf
  |/   parent:      0:8fa14d15e168
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    instability: content-divergent
  |    summary:     watbar to a
  |
  o  changeset:   0:8fa14d15e168
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     added hgignore
  
  $ hg evolve --content-divergent
  merge:[5] watbar to a
  with: [10] added a
  base: [1] added a
  rebasing "divergent" content-divergent changeset 8e222f257bbf on 2228e3b74514
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[14] added b
  with: [17] added b
  base: [2] added b
  rebasing "divergent" content-divergent changeset 2a955e808c53 on 4c0b67f978c2
  rebasing "other" content-divergent changeset 509103439e5e on 4c0b67f978c2
  merging b
  warning: conflicts while merging b! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  4 new orphan changesets
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg evolve --stop
  2 new orphan changesets
  stopped the interrupted evolve
  working directory is now at 509103439e5e
  $ hg log -G
  o  changeset:   21:4c0b67f978c2
  |  tag:         tip
  |  parent:      9:2228e3b74514
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     watbar to a
  |
  | *  changeset:   19:c351be27f199
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  instability: orphan, content-divergent
  | |  summary:     added d
  | |
  | *  changeset:   18:eaf34afe4df3
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  instability: orphan, content-divergent
  | |  summary:     added c
  | |
  | @  changeset:   17:509103439e5e
  | |  parent:      5:8e222f257bbf
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  instability: orphan, content-divergent
  | |  summary:     added b
  | |
  | | *  changeset:   16:91c8ccb9c241
  | | |  user:        test
  | | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | | |  instability: orphan, content-divergent
  | | |  summary:     added d
  | | |
  | | *  changeset:   15:48b0f803817a
  | | |  user:        test
  | | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | | |  instability: orphan, content-divergent
  | | |  summary:     added c
  | | |
  | | *  changeset:   14:2a955e808c53
  | | |  parent:      10:c04ff147ef79
  | | |  user:        test
  | | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | | |  instability: orphan, content-divergent
  | | |  summary:     added b
  | | |
  +---x  changeset:   10:c04ff147ef79
  | |    user:        test
  | |    date:        Thu Jan 01 00:00:00 1970 +0000
  | |    obsolete:    rewritten using evolve as 21:4c0b67f978c2
  | |    summary:     added a
  | |
  o |  changeset:   9:2228e3b74514
  | |  parent:      0:8fa14d15e168
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     add newfile
  | |
  | x  changeset:   5:8e222f257bbf
  |/   parent:      0:8fa14d15e168
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    obsolete:    rebased using evolve as 21:4c0b67f978c2
  |    summary:     watbar to a
  |
  o  changeset:   0:8fa14d15e168
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     added hgignore
  
  $ hg obslog -r 'desc("watbar to a")' --all
  o    4c0b67f978c2 (21) watbar to a
  |\     rewritten from b0d57620c872 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    rewritten(description, content) from c04ff147ef79 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  b0d57620c872 (20) watbar to a
  | |    rebased(parent) from 8e222f257bbf using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  c04ff147ef79 (10) added a
  | |    rebased(parent) from c7586e2a9264 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  8e222f257bbf (5) watbar to a
  |/     rewritten(description, content) from c7586e2a9264 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  c7586e2a9264 (1) added a
  
  $ hg obslog -r 'desc("added b")' --all
  *  2a955e808c53 (14) added b
  |    amended(content) from 6eb54b5af3fb using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  | @  509103439e5e (17) added b
  | |    amended(content) from d5f148423c16 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  6eb54b5af3fb (11) added b
  | |    rebased(parent) from b1661037fa25 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  d5f148423c16 (6) added b
  |/     rebased(parent) from b1661037fa25 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  b1661037fa25 (2) added b
  

Again, let's evolve the stack
  $ hg evolve --content-divergent
  merge:[14] added b
  with: [17] added b
  base: [2] added b
  rebasing "divergent" content-divergent changeset 2a955e808c53 on 4c0b67f978c2
  rebasing "other" content-divergent changeset 509103439e5e on 4c0b67f978c2
  merging b
  warning: conflicts while merging b! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo foo > b
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  merge:[15] added c
  with: [18] added c
  base: [3] added c
  rebasing "divergent" content-divergent changeset 48b0f803817a on 59338f08e6ef
  rebasing "other" content-divergent changeset eaf34afe4df3 on 59338f08e6ef
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[16] added d
  with: [19] added d
  base: [4] added d
  rebasing "divergent" content-divergent changeset 91c8ccb9c241 on ef321c27d145
  rebasing "other" content-divergent changeset c351be27f199 on ef321c27d145
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 59338f08e6ef

  $ hg evolve -l

  $ cd ..

Make sure that content-divergent resolution doesn't undo a change (issue6203)
-----------------------------------------------------------------------------

  $ hg init issue6203
  $ cd issue6203
  $ echo a > a; hg add a; hg ci -m a
  $ echo 'b with typo' > b; hg add b; hg ci -m b
  $ echo c > c; hg add c; hg ci -m c

  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [1] b
  $ echo 'b without typo' > b
  $ hg amend
  1 new orphan changesets
  $ hg evolve
  move:[2] c
  atop:[3] b

  $ hg up 0
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo d > d; hg add d; hg ci -m d
  created new head
  $ hg rebase --hidden --config experimental.evolution.allowdivergence=True -s 1 -d 5
  rebasing 1:d420a663b65e "b"
  rebasing 2:49f182e7a6cc "c"
  4 new content-divergent changesets
  $ hg log -G -v --patch
  *  changeset:   7:ef4885dea3da
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: content-divergent
  |  files:       c
  |  description:
  |  c
  |
  |
  |  diff -r fe788ccf5416 -r ef4885dea3da c
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +c
  |
  *  changeset:   6:fe788ccf5416
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: content-divergent
  |  files:       b
  |  description:
  |  b
  |
  |
  |  diff -r 980f7dc84c29 -r fe788ccf5416 b
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +b with typo
  |
  @  changeset:   5:980f7dc84c29
  |  parent:      0:cb9a9f314b8b
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  files:       d
  |  description:
  |  d
  |
  |
  |  diff -r cb9a9f314b8b -r 980f7dc84c29 d
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/d	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +d
  |
  | *  changeset:   4:fef59171875e
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  instability: content-divergent
  | |  files:       c
  | |  description:
  | |  c
  | |
  | |
  | |  diff -r 5b2d00df9c4e -r fef59171875e c
  | |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  | |  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  | |  @@ -0,0 +1,1 @@
  | |  +c
  | |
  | *  changeset:   3:5b2d00df9c4e
  |/   parent:      0:cb9a9f314b8b
  |    user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    instability: content-divergent
  |    files:       b
  |    description:
  |    b
  |
  |
  |    diff -r cb9a9f314b8b -r 5b2d00df9c4e b
  |    --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |    +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  |    @@ -0,0 +1,1 @@
  |    +b without typo
  |
  o  changeset:   0:cb9a9f314b8b
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     files:       a
     description:
     a
  
  
     diff -r 000000000000 -r cb9a9f314b8b a
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/a	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +a
  

  $ hg evolve --content-divergent
  merge:[3] b
  with: [6] b
  base: [1] b
  rebasing "divergent" content-divergent changeset 5b2d00df9c4e on 980f7dc84c29
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[4] c
  with: [7] c
  base: [2] c
  rebasing "divergent" content-divergent changeset fef59171875e on 24bad874a3c7
  rebasing "other" content-divergent changeset ef4885dea3da on 24bad874a3c7
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

Expected result:
Changeset with description "b" only adds file "b" with content "b without typo".
Changeset with description "c" only adds file "c" with content "c".

  $ hg glog -l2 -p
  o  12:8a66432f9036 c
  |   () [default] draftdiff -r 24bad874a3c7 -r 8a66432f9036 c
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +c
  |
  o  9:24bad874a3c7 b
  |   () [default] draftdiff -r 980f7dc84c29 -r 24bad874a3c7 b
  ~  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/b	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +b without typo
  
  $ cd ..

Testing case when resolution parent is ambiguous (MultipleSuccessorsError)
--------------------------------------------------------------------------

  $ hg init multiplesuccs1
  $ cd multiplesuccs1
  $ echo base > base
  $ hg ci -Aqm "added base"
  $ echo foo > foo
  $ hg ci -Aqm "added foo"
  $ echo bar > bar; echo car > car
  $ hg ci -Aqm "added bar and car"
  $ echo dar > dar
  $ hg ci -Aqm "added dar"

  $ cd ..
  $ hg clone multiplesuccs1 multiplesuccs2
  updating to branch default
  5 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd multiplesuccs2
  $ hg up -r "desc('added foo')"
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ echo newfoo > foo
  $ hg amend
  2 new orphan changesets
  $ hg evolve
  move:[2] added bar and car
  atop:[4] added foo
  move:[3] added dar

  $ cd ../multiplesuccs1
  $ hg up -r "desc('added base')"
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  $ echo tuna > tuna
  $ hg ci -Aqm "added tuna"
  $ hg rebase -s "desc('added foo')" -d .
  rebasing 1:8da7bbaea4f7 "added foo"
  rebasing 2:7f4b97b13607 "added bar and car"
  rebasing 3:9f12b2fcb3de "added dar"

  $ cd ../multiplesuccs2
  $ hg pull
  pulling from $TESTTMP/multiplesuccs1
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 4 changesets with 1 changes to 5 files (+1 heads)
  3 new obsolescence markers
  6 new content-divergent changesets
  new changesets 9703820a7d5b:9a1f460df8b5 (4 drafts)
  (run 'hg heads' to see heads, 'hg merge' to merge)
  $ hg glog
  *  10:9a1f460df8b5 added dar
  |   () [default] draft
  *  9:7dd5b9d42ef3 added bar and car
  |   () [default] draft
  *  8:afd8b2ea1b77 added foo
  |   () [default] draft
  o  7:9703820a7d5b added tuna
  |   () [default] draft
  | *  6:57a3f8edf065 added dar
  | |   () [default] draft
  | *  5:f4ed107810a7 added bar and car
  | |   () [default] draft
  | @  4:8a2d93492f59 added foo
  |/    () [default] draft
  o  0:bde1d2b6b5e5 added base
      () [default] draft

  $ hg evolve -r 4+5 --content-divergent
  merge:[4] added foo
  with: [8] added foo
  base: [1] added foo
  rebasing "divergent" content-divergent changeset 8a2d93492f59 on 9703820a7d5b
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  merge:[5] added bar and car
  with: [9] added bar and car
  base: [2] added bar and car
  rebasing "divergent" content-divergent changeset f4ed107810a7 on eb084588f69b
  rebasing "other" content-divergent changeset 7dd5b9d42ef3 on eb084588f69b
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  2 new orphan changesets
  working directory is now at eb084588f69b

  $ hg glog
  o  15:33947326df25 added bar and car
  |   () [default] draft
  @  12:eb084588f69b added foo
  |   () [default] draft
  | *  10:9a1f460df8b5 added dar
  | |   () [default] draft
  | x  9:7dd5b9d42ef3 added bar and car
  | |   () [default] draft
  | x  8:afd8b2ea1b77 added foo
  |/    () [default] draft
  o  7:9703820a7d5b added tuna
  |   () [default] draft
  | *  6:57a3f8edf065 added dar
  | |   () [default] draft
  | x  5:f4ed107810a7 added bar and car
  | |   () [default] draft
  | x  4:8a2d93492f59 added foo
  |/    () [default] draft
  o  0:bde1d2b6b5e5 added base
      () [default] draft

  $ hg rebase -r 10 -d 7
  rebasing 10:9a1f460df8b5 "added dar"
  $ hg up 0 -q
  $ echo alpha > alpha
  $ hg ci -Am "added alpha"
  adding alpha
  created new head
  $ hg rebase -r 6 -d 'desc("added alpha")'
  rebasing 6:57a3f8edf065 "added dar"
  $ hg evolve --content-divergent
  skipping 8b68d5104188: have a different parent than cf9a46e19942 (not handled yet)
  | 8b68d5104188, cf9a46e19942 are not based on the same changeset.
  | With the current state of its implementation,
  | evolve does not work in that case.
  | rebase one of them next to the other and run
  | this command again.
  | - either: hg rebase --dest 'p1(8b68d5104188)' -r cf9a46e19942
  | - or:     hg rebase --dest 'p1(cf9a46e19942)' -r 8b68d5104188

  $ hg strip -r 16:
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  saved backup bundle to $TESTTMP/multiplesuccs2/.hg/strip-backup/8b68d5104188-e72c2390-backup.hg
  2 new orphan changesets
  $ echo bar > bar; hg ci -Aqm "added bar"
  $ echo car > car; hg ci -Aqm "added car"
  $ hg prune --split -s 16+17 -r 15
  1 changesets pruned

  $ hg evolve --content-divergent
  skipping 57a3f8edf065: ambiguous orphan resolution parent for 57a3f8edf065
