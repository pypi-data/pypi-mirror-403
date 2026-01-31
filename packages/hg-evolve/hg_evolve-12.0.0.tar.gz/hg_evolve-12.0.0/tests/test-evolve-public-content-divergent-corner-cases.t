===============================================================
Tests the resolution of public content divergence: corner cases
===============================================================

This file intend to cover cases that are specific enough to not fit in the
other cases.

Setup
=====
  $ cat >> $HGRCPATH <<EOF
  > [alias]
  > glog = log -GT "{rev}:{node|short} {desc|firstline}\n {phase} {instabilities}\n\n"
  > [phases]
  > publish = False
  > [experimental]
  > evolution.allowdivergence = True
  > [extensions]
  > rebase =
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

Testing when divergence is not created by actual diff change, but because of rebasing:
--------------------------------------------------------------------------------------

Prepare the repo:

  $ hg init rebasediv
  $ cd rebasediv
  $ for ch in a b c; do
  >   echo $ch > $ch;
  >   hg ci -Am "added "$ch;
  > done;
  adding a
  adding b
  adding c

  $ hg glog
  @  2:155349b645be added c
  |   draft
  |
  o  1:5f6d8a4bf34a added b
  |   draft
  |
  o  0:9092f1db7931 added a
      draft
  

On server side: a new cset is added based on rev 1 and rev 2 is rebased on newly added cset:

  $ hg up .^ -q
  $ echo d > d
  $ hg ci -Am "added d"
  adding d
  created new head

  $ hg rebase -r 2 -d .
  rebasing 2:155349b645be "added c"

  $ hg glog
  o  4:c0d7ee6604ea added c
  |   draft
  |
  @  3:c9241b0f2d5b added d
  |   draft
  |
  o  1:5f6d8a4bf34a added b
  |   draft
  |
  o  0:9092f1db7931 added a
      draft
  

On user side: user has not pulled yet and amended the rev 2 which created the divergence after pull:
  $ hg up 2 --hidden -q
  updated to hidden changeset 155349b645be
  (hidden revision '155349b645be' was rewritten as: c0d7ee6604ea)
  working directory parent is obsolete! (155349b645be)

  $ echo cc >> c
  $ hg ci --amend -m "updated c"
  2 new content-divergent changesets

Lets change the phase to --public of branch which is pulled from server:
  $ hg phase --public -r 4
  $ hg glog -p
  @  5:f5f9b4fc8b77 updated c
  |   draft content-divergent
  |
  |  diff -r 5f6d8a4bf34a -r f5f9b4fc8b77 c
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,2 @@
  |  +c
  |  +cc
  |
  | o  4:c0d7ee6604ea added c
  | |   public
  | |
  | |  diff -r c9241b0f2d5b -r c0d7ee6604ea c
  | |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  | |  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  | |  @@ -0,0 +1,1 @@
  | |  +c
  | |
  | o  3:c9241b0f2d5b added d
  |/    public
  |
  |    diff -r 5f6d8a4bf34a -r c9241b0f2d5b d
  |    --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |    +++ b/d	Thu Jan 01 00:00:00 1970 +0000
  |    @@ -0,0 +1,1 @@
  |    +d
  |
  o  1:5f6d8a4bf34a added b
  |   public
  |
  |  diff -r 9092f1db7931 -r 5f6d8a4bf34a b
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +b
  |
  o  0:9092f1db7931 added a
      public
  
     diff -r 000000000000 -r 9092f1db7931 a
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/a	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +a
  

Evolve:
  $ hg evolve --content-divergent
  merge:[4] added c
  with: [5] updated c
  base: [2] added c
  rebasing "other" content-divergent changeset f5f9b4fc8b77 on c9241b0f2d5b
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  committed as a3019c73de83
  working directory is now at a3019c73de83

  $ hg glog -p
  @  8:a3019c73de83 phase-divergent update to c0d7ee6604ea:
  |   draft
  |
  |  diff -r c0d7ee6604ea -r a3019c73de83 c
  |  --- a/c	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -1,1 +1,2 @@
  |   c
  |  +cc
  |
  o  4:c0d7ee6604ea added c
  |   public
  |
  |  diff -r c9241b0f2d5b -r c0d7ee6604ea c
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +c
  |
  o  3:c9241b0f2d5b added d
  |   public
  |
  |  diff -r 5f6d8a4bf34a -r c9241b0f2d5b d
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/d	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +d
  |
  o  1:5f6d8a4bf34a added b
  |   public
  |
  |  diff -r 9092f1db7931 -r 5f6d8a4bf34a b
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +b
  |
  o  0:9092f1db7931 added a
      public
  
     diff -r 000000000000 -r 9092f1db7931 a
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/a	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +a
  
Check that we don't have any unstable cset now:
  $ hg evolve -l
  $ cd ..

Different parent, simple conflict on relocate, deleted file on actual merge
---------------------------------------------------------------------------

Changeset "added c e" is also removing 'd'. This should conflict with the update
to 'd' in the successors of 'adding d' when solving the content divergence.

  $ hg init pubdiv-parent-deleted-file
  $ cd pubdiv-parent-deleted-file
  $ for ch in a b c d; do
  >   echo $ch > $ch;
  >   hg ci -Aqm "added "$ch;
  > done;

  $ hg up 'desc("added b")'
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo cfoo > c
  $ echo e > e
  $ hg add c e
  $ hg ci -m "added c e"
  created new head

  $ hg up 'desc("re:added c$")'
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo dd > d
  $ hg add d
  $ hg ci -m "added d"
  created new head

  $ hg glog --patch --rev 'sort(all(), "topo")'
  @  5:93cd84bbdaca added d
  |   draft
  |
  |  diff -r 155349b645be -r 93cd84bbdaca d
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/d	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +dd
  |
  | o  3:9150fe93bec6 added d
  |/    draft
  |
  |    diff -r 155349b645be -r 9150fe93bec6 d
  |    --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |    +++ b/d	Thu Jan 01 00:00:00 1970 +0000
  |    @@ -0,0 +1,1 @@
  |    +d
  |
  o  2:155349b645be added c
  |   draft
  |
  |  diff -r 5f6d8a4bf34a -r 155349b645be c
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +c
  |
  | o  4:e568fd1029bb added c e
  |/    draft
  |
  |    diff -r 5f6d8a4bf34a -r e568fd1029bb c
  |    --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |    +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  |    @@ -0,0 +1,1 @@
  |    +cfoo
  |    diff -r 5f6d8a4bf34a -r e568fd1029bb e
  |    --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |    +++ b/e	Thu Jan 01 00:00:00 1970 +0000
  |    @@ -0,0 +1,1 @@
  |    +e
  |
  o  1:5f6d8a4bf34a added b
  |   draft
  |
  |  diff -r 9092f1db7931 -r 5f6d8a4bf34a b
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +b
  |
  o  0:9092f1db7931 added a
      draft
  
     diff -r 000000000000 -r 9092f1db7931 a
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/a	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +a
  
  $ hg prune 'min(desc("added d"))' -s 'max(desc("added d"))'
  1 changesets pruned
  $ hg prune 'min(desc("added d"))' -s 'desc("added c e")' --hidden
  1 changesets pruned
  2 new content-divergent changesets

Change phase to public for one head:
  $ hg phase --public -r 'max(desc("added d"))'

  $ hg glog
  @  5:93cd84bbdaca added d
  |   public
  |
  | *  4:e568fd1029bb added c e
  | |   draft content-divergent
  | |
  o |  2:155349b645be added c
  |/    public
  |
  o  1:5f6d8a4bf34a added b
  |   public
  |
  o  0:9092f1db7931 added a
      public
  

  $ hg glog --patch --rev 'sort(all(), "topo")' --hidden
  @  5:93cd84bbdaca added d
  |   public
  |
  |  diff -r 155349b645be -r 93cd84bbdaca d
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/d	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +dd
  |
  | x  3:9150fe93bec6 added d
  |/    draft
  |
  |    diff -r 155349b645be -r 9150fe93bec6 d
  |    --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |    +++ b/d	Thu Jan 01 00:00:00 1970 +0000
  |    @@ -0,0 +1,1 @@
  |    +d
  |
  o  2:155349b645be added c
  |   public
  |
  |  diff -r 5f6d8a4bf34a -r 155349b645be c
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +c
  |
  | *  4:e568fd1029bb added c e
  |/    draft content-divergent
  |
  |    diff -r 5f6d8a4bf34a -r e568fd1029bb c
  |    --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |    +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  |    @@ -0,0 +1,1 @@
  |    +cfoo
  |    diff -r 5f6d8a4bf34a -r e568fd1029bb e
  |    --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |    +++ b/e	Thu Jan 01 00:00:00 1970 +0000
  |    @@ -0,0 +1,1 @@
  |    +e
  |
  o  1:5f6d8a4bf34a added b
  |   public
  |
  |  diff -r 9092f1db7931 -r 5f6d8a4bf34a b
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +b
  |
  o  0:9092f1db7931 added a
      public
  
     diff -r 000000000000 -r 9092f1db7931 a
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/a	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +a
  

  $ hg debugobsolete
  9150fe93bec603cd88d05cda9f6ff13420cb53e9 93cd84bbdacaeb8f881c29a609dbdd30c38cbc57 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'prune', 'user': 'test'}
  9150fe93bec603cd88d05cda9f6ff13420cb53e9 e568fd1029bbe9d506275bbb9a034a0509d80324 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'prune', 'user': 'test'}
  $ hg obslog --all --rev tip --patch
  @  93cd84bbdaca (5) added d
  |    amended(content) from 9150fe93bec6 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 9150fe93bec6 -r 93cd84bbdaca d
  |      --- a/d	Thu Jan 01 00:00:00 1970 +0000
  |      +++ b/d	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,1 +1,1 @@
  |      -d
  |      +dd
  |
  |
  | *  e568fd1029bb (4) added c e
  |/     rewritten(description, parent, content) from 9150fe93bec6 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |        diff -r 9150fe93bec6+ -r e568fd1029bb changeset-description
  |        --- a/changeset-description
  |        +++ b/changeset-description
  |        @@ -1,1 +1,1 @@
  |        -added d
  |        +added c e
  |
  |        diff -r e568fd1029bb c
  |        --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -0,0 +1,1 @@
  |        +cfoo
  |        diff -r e568fd1029bb d
  |        --- a/d	Thu Jan 01 00:00:00 1970 +0000
  |        +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -1,1 +0,0 @@
  |        -d
  |        diff -r e568fd1029bb e
  |        --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |        +++ b/e	Thu Jan 01 00:00:00 1970 +0000
  |        @@ -0,0 +1,1 @@
  |        +e
  |
  |
  x  9150fe93bec6 (3) added d
  

  $ hg evolve --content-divergent --any --update
  merge:[5] added d
  with: [4] added c e
  base: [3] added d
  rebasing "other" content-divergent changeset e568fd1029bb on 155349b645be
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg diff
  diff -r 155349b645be c
  --- a/c	Thu Jan 01 00:00:00 1970 +0000
  +++ b/c	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,5 @@
  +<<<<<<< destination: 155349b645be - test: added c
   c
  +=======
  +cfoo
  +>>>>>>> evolving:    e568fd1029bb - test: added c e
  diff -r 155349b645be e
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/e	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +e

  $ echo c > c
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue
  evolving 4:e568fd1029bb "added c e"
  file 'd' was deleted in other [other] but was modified in local [local].
  You can use (c)hanged version, (d)elete, or leave (u)nresolved.
  What do you want to do? u
  1 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg sum
  parent: 5:93cd84bbdaca 
   added d
  parent: 6:cf77846279b4 tip (content-divergent)
   added c e
  branch: default
  commit: 1 modified, 1 unknown, 1 unresolved (merge)
  update: (current)
  phases: 1 draft
  content-divergent: 1 changesets
  evolve: (evolve --continue)

  $ echo resolved > d
  $ hg resolve -m d
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue
  committed as 01169b149789
  working directory is now at 01169b149789

  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 01169b149789f09d81f86d5273e56671ab645590
  # Parent  93cd84bbdacaeb8f881c29a609dbdd30c38cbc57
  phase-divergent update to 93cd84bbdaca:
  
  added c e
  
  diff -r 93cd84bbdaca -r 01169b149789 d
  --- a/d	Thu Jan 01 00:00:00 1970 +0000
  +++ b/d	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -dd
  +resolved
  diff -r 93cd84bbdaca -r 01169b149789 e
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/e	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +e

  $ hg evolve -l
  $ cd ..

Test a pratical "rebase" case
=============================

Initial setup

  $ hg init rebase-divergence
  $ cd rebase-divergence
  $ echo root >> root
  $ hg add root
  $ hg commit -m root
  $ for x in c_A c_B c_C c_D; do
  >     echo $x >> $x
  >     hg add $x
  >     hg commit -m $x
  > done

  $ hg up 'desc("c_A")'
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved

  $ for x in c_E c_F; do
  >     echo $x >> $x
  >     hg add $x
  >     hg commit -m $x
  > done
  created new head

(creating divergence locally for simplicity)

  $ node=`hg log --rev 'desc("c_E")' -T '{node}'`
  $ hg rebase -s $node -d 'desc("c_B")'
  rebasing 5:4ab2719bbab9 "c_E"
  rebasing 6:77ccbf8d837e tip "c_F"
  $ hg phase --public tip
  $ hg rebase --hidden -s $node -d 'desc("c_C")' --config experimental.evolution.allowdivergence=yes
  rebasing 5:4ab2719bbab9 "c_E"
  rebasing 6:77ccbf8d837e "c_F"
  2 new content-divergent changesets

  $ hg sum
  parent: 8:a52ac76b45f5 
   c_F
  branch: default
  commit: (clean)
  update: 4 new changesets, 3 branch heads (merge)
  phases: 4 draft
  content-divergent: 2 changesets
  $ hg evolve --list
  b4a584aea4bd: c_E
    content-divergent: c7d2d47c7240 (public) (precursor 4ab2719bbab9)
  
  8ae8db670b4a: c_F
    content-divergent: a52ac76b45f5 (public) (precursor 77ccbf8d837e)
  
  $ hg log -G --patch
  *  changeset:   10:8ae8db670b4a
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: content-divergent
  |  summary:     c_F
  |
  |  diff -r b4a584aea4bd -r 8ae8db670b4a c_F
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/c_F	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +c_F
  |
  *  changeset:   9:b4a584aea4bd
  |  parent:      3:abb77b893f28
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  instability: content-divergent
  |  summary:     c_E
  |
  |  diff -r abb77b893f28 -r b4a584aea4bd c_E
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/c_E	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +c_E
  |
  | @  changeset:   8:a52ac76b45f5
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     c_F
  | |
  | |  diff -r c7d2d47c7240 -r a52ac76b45f5 c_F
  | |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  | |  +++ b/c_F	Thu Jan 01 00:00:00 1970 +0000
  | |  @@ -0,0 +1,1 @@
  | |  +c_F
  | |
  | o  changeset:   7:c7d2d47c7240
  | |  parent:      2:eb1b4e1205b8
  | |  user:        test
  | |  date:        Thu Jan 01 00:00:00 1970 +0000
  | |  summary:     c_E
  | |
  | |  diff -r eb1b4e1205b8 -r c7d2d47c7240 c_E
  | |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  | |  +++ b/c_E	Thu Jan 01 00:00:00 1970 +0000
  | |  @@ -0,0 +1,1 @@
  | |  +c_E
  | |
  +---o  changeset:   4:dbb960d6c97c
  | |    user:        test
  | |    date:        Thu Jan 01 00:00:00 1970 +0000
  | |    summary:     c_D
  | |
  | |    diff -r abb77b893f28 -r dbb960d6c97c c_D
  | |    --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  | |    +++ b/c_D	Thu Jan 01 00:00:00 1970 +0000
  | |    @@ -0,0 +1,1 @@
  | |    +c_D
  | |
  o |  changeset:   3:abb77b893f28
  |/   user:        test
  |    date:        Thu Jan 01 00:00:00 1970 +0000
  |    summary:     c_C
  |
  |    diff -r eb1b4e1205b8 -r abb77b893f28 c_C
  |    --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |    +++ b/c_C	Thu Jan 01 00:00:00 1970 +0000
  |    @@ -0,0 +1,1 @@
  |    +c_C
  |
  o  changeset:   2:eb1b4e1205b8
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_B
  |
  |  diff -r e31751786014 -r eb1b4e1205b8 c_B
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/c_B	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +c_B
  |
  o  changeset:   1:e31751786014
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_A
  |
  |  diff -r 1e4be0697311 -r e31751786014 c_A
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/c_A	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +c_A
  |
  o  changeset:   0:1e4be0697311
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     root
  
     diff -r 000000000000 -r 1e4be0697311 root
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/root	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +root
  

Run automatic evolution

  $ hg evolve --content-divergent --rev 'not public() and desc("c_E")::'
  merge:[7] c_E
  with: [9] c_E
  base: [5] c_E
  rebasing "other" content-divergent changeset b4a584aea4bd on eb1b4e1205b8
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  content divergence resolution between c7d2d47c7240 (public) and 0773642cfa95 has same content as c7d2d47c7240, discarding 0773642cfa95
  merge:[8] c_F
  with: [10] c_F
  base: [6] c_F
  rebasing "other" content-divergent changeset 8ae8db670b4a on c7d2d47c7240
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  content divergence resolution between a52ac76b45f5 (public) and 6a87ed4aa317 has same content as a52ac76b45f5, discarding 6a87ed4aa317
  $ hg sum
  parent: 8:a52ac76b45f5 tip
   c_F
  branch: default
  commit: (clean)
  update: 2 new changesets, 2 branch heads (merge)
  phases: 2 draft

  $ hg evolve --list

  $ hg log -G --patch -l2
  @  changeset:   8:a52ac76b45f5
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     c_F
  |
  |  diff -r c7d2d47c7240 -r a52ac76b45f5 c_F
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/c_F	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +c_F
  |
  o  changeset:   7:c7d2d47c7240
  |  parent:      2:eb1b4e1205b8
  ~  user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     c_E
  
     diff -r eb1b4e1205b8 -r c7d2d47c7240 c_E
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/c_E	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +c_E
  
  $ hg export tip
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID a52ac76b45f523a039fc4a938d79874f4bdb1a85
  # Parent  c7d2d47c7240562be5cbd1a24080dd0396178709
  c_F
  
  diff -r c7d2d47c7240 -r a52ac76b45f5 c_F
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/c_F	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +c_F

  $ hg debugobsolete
  4ab2719bbab9c0f4addf11ab7fa3cf3e1a832c2d c7d2d47c7240562be5cbd1a24080dd0396178709 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  77ccbf8d837e0eb67e09569335146263e7d61551 a52ac76b45f523a039fc4a938d79874f4bdb1a85 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  4ab2719bbab9c0f4addf11ab7fa3cf3e1a832c2d b4a584aea4bd8d771184530d445a582251275f37 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  77ccbf8d837e0eb67e09569335146263e7d61551 8ae8db670b4ad2385b9e008122af42ef6048a675 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  b4a584aea4bd8d771184530d445a582251275f37 0773642cfa95002f7937f44bec95dd208564c64e 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  0773642cfa95002f7937f44bec95dd208564c64e c7d2d47c7240562be5cbd1a24080dd0396178709 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  8ae8db670b4ad2385b9e008122af42ef6048a675 6a87ed4aa31771f9041ca1260a91f7185f38f15c 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  6a87ed4aa31771f9041ca1260a91f7185f38f15c a52ac76b45f523a039fc4a938d79874f4bdb1a85 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog --rev a52ac76b45f5
  @    a52ac76b45f5 (8) c_F
  |\     rewritten from 6a87ed4aa317 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |    rebased(parent) from 77ccbf8d837e using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  6a87ed4aa317 (12) c_F
  | |    rebased(parent) from 8ae8db670b4a using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  8ae8db670b4a (10) c_F
  |/     rebased(parent) from 77ccbf8d837e using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  77ccbf8d837e (6) c_F
  
