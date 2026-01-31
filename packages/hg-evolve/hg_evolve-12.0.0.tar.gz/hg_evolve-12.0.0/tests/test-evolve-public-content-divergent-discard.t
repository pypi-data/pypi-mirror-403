===============================================================================
Tests the resolution of public content divergence: when merging leads to public
===============================================================================

This file intend to cover all the cases possible when merging the other
divergent cset into public cset leads to public cset itself.
Possible variants are:

parent: same/different
relocation: [no-]conflict
merging: [no-]conflict

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

Testing when same parent, no conflict:
--------------------------------------

  $ hg init pubdiv1
  $ cd pubdiv1
  $ for ch in a b c; do
  >   echo $ch > $ch;
  >   hg ci -Am "added "$ch;
  > done;
  adding a
  adding b
  adding c

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo ch > ch
  $ hg add ch
  $ hg ci -m "added ch"
  created new head

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo ch > ch
  $ hg add ch
  $ hg ci -m "added c"
  created new head

  $ hg glog
  @  4:f7c1071f1e7c added c
  |   draft
  |
  | o  3:90522bccf499 added ch
  |/    draft
  |
  | o  2:155349b645be added c
  |/    draft
  |
  o  1:5f6d8a4bf34a added b
  |   draft
  |
  o  0:9092f1db7931 added a
      draft
  

  $ hg prune 2 -s 3
  1 changesets pruned
  $ hg prune 2 -s 4 --hidden
  1 changesets pruned
  2 new content-divergent changesets
  $ hg phase --public -r 4

  $ hg glog
  @  4:f7c1071f1e7c added c
  |   public
  |
  | *  3:90522bccf499 added ch
  |/    draft content-divergent
  |
  o  1:5f6d8a4bf34a added b
  |   public
  |
  o  0:9092f1db7931 added a
      public
  
  $ hg evolve --content-divergent --any
  merge:[4] added c
  with: [3] added ch
  base: [2] added c
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  other divergent changeset 90522bccf499 has same content as local f7c1071f1e7c and differs by "description" only, discarding 90522bccf499
  content divergence resolution between f7c1071f1e7c (public) and 90522bccf499 has same content as f7c1071f1e7c, discarding 90522bccf499

  $ hg evolve -l

  $ hg parents
  changeset:   4:f7c1071f1e7c
  tag:         tip
  parent:      1:5f6d8a4bf34a
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added c
  
  $ cd ..

Testing when different parent, no conflict:
-------------------------------------------

  $ hg init pubdiv2
  $ cd pubdiv2
  $ for ch in a b c d; do
  >   echo $ch > $ch;
  >   hg ci -Am "added "$ch;
  > done;
  adding a
  adding b
  adding c
  adding d

  $ hg up 1
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo dh > dh
  $ hg add dh
  $ hg ci -m "added dh"
  created new head

  $ hg up 2
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo dh > dh
  $ hg add dh
  $ hg ci -m "added d"
  created new head

  $ hg glog
  @  5:e800202333a4 added d
  |   draft
  |
  | o  4:5acd58ef5066 added dh
  | |   draft
  | |
  +---o  3:9150fe93bec6 added d
  | |     draft
  | |
  o |  2:155349b645be added c
  |/    draft
  |
  o  1:5f6d8a4bf34a added b
  |   draft
  |
  o  0:9092f1db7931 added a
      draft
  

  $ hg prune 3 -s 4
  1 changesets pruned
  $ hg prune 3 -s 5 --hidden
  1 changesets pruned
  2 new content-divergent changesets
  $ hg phase --public -r 5

  $ hg glog
  @  5:e800202333a4 added d
  |   public
  |
  | *  4:5acd58ef5066 added dh
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
  
  $ hg evolve --content-divergent --any
  merge:[5] added d
  with: [4] added dh
  base: [3] added d
  rebasing "other" content-divergent changeset 5acd58ef5066 on 155349b645be
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  other divergent changeset ae3429430ef1 has same content as local e800202333a4 and differs by "description" only, discarding ae3429430ef1
  content divergence resolution between e800202333a4 (public) and ae3429430ef1 has same content as e800202333a4, discarding ae3429430ef1

  $ hg evolve -l

  $ hg parents
  changeset:   5:e800202333a4
  tag:         tip
  parent:      2:155349b645be
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added d
  
  $ cd ..

Testing when same parent, merging conflict:
-------------------------------------------

  $ hg init pubdiv3
  $ cd pubdiv3
  $ for ch in a b c; do
  >   echo $ch > $ch;
  >   hg ci -Am "added "$ch;
  > done;
  adding a
  adding b
  adding c

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo chconflict > ch
  $ hg add ch
  $ hg ci -m "added ch"
  created new head

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo ch > ch
  $ hg add ch
  $ hg ci -m "added c"
  created new head

  $ hg glog
  @  4:f7c1071f1e7c added c
  |   draft
  |
  | o  3:229da2719b19 added ch
  |/    draft
  |
  | o  2:155349b645be added c
  |/    draft
  |
  o  1:5f6d8a4bf34a added b
  |   draft
  |
  o  0:9092f1db7931 added a
      draft
  

  $ hg prune 2 -s 3
  1 changesets pruned
  $ hg prune 2 -s 4 --hidden
  1 changesets pruned
  2 new content-divergent changesets
  $ hg phase --public -r 4

  $ hg glog
  @  4:f7c1071f1e7c added c
  |   public
  |
  | *  3:229da2719b19 added ch
  |/    draft content-divergent
  |
  o  1:5f6d8a4bf34a added b
  |   public
  |
  o  0:9092f1db7931 added a
      public
  
  $ hg evolve --content-divergent --any
  merge:[4] added c
  with: [3] added ch
  base: [2] added c
  merging ch
  warning: conflicts while merging ch! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg diff
  diff -r f7c1071f1e7c ch
  --- a/ch	Thu Jan 01 00:00:00 1970 +0000
  +++ b/ch	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,5 @@
  +<<<<<<< local: f7c1071f1e7c - test: added c
   ch
  +=======
  +chconflict
  +>>>>>>> other: 229da2719b19 - test: added ch

  $ echo ch > ch
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue
  other divergent changeset 229da2719b19 has same content as local f7c1071f1e7c and differs by "description" only, discarding 229da2719b19

  $ hg evolve -l

  $ hg parents
  changeset:   4:f7c1071f1e7c
  tag:         tip
  parent:      1:5f6d8a4bf34a
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added c
  
  $ cd ..

Testing when different parent, relocation conflict:
---------------------------------------------------

  $ hg init pubdiv4
  $ cd pubdiv4
  $ for ch in a b c d; do
  >   echo $ch > $ch;
  >   hg ci -Am "added "$ch;
  > done;
  adding a
  adding b
  adding c
  adding d

  $ hg up 1
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo dh > dh
  $ echo cc > c
  $ hg add dh c
  $ hg ci -m "added dh"
  created new head

  $ hg up 2
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo dh > dh
  $ hg add dh
  $ hg ci -m "added d"
  created new head

  $ hg glog
  @  5:e800202333a4 added d
  |   draft
  |
  | o  4:f89a8e2f86ac added dh
  | |   draft
  | |
  +---o  3:9150fe93bec6 added d
  | |     draft
  | |
  o |  2:155349b645be added c
  |/    draft
  |
  o  1:5f6d8a4bf34a added b
  |   draft
  |
  o  0:9092f1db7931 added a
      draft
  

  $ hg prune 3 -s 4
  1 changesets pruned
  $ hg prune 3 -s 5 --hidden
  1 changesets pruned
  2 new content-divergent changesets
  $ hg phase --public -r 5

  $ hg glog
  @  5:e800202333a4 added d
  |   public
  |
  | *  4:f89a8e2f86ac added dh
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
  
  $ hg evolve --content-divergent --any
  merge:[5] added d
  with: [4] added dh
  base: [3] added d
  rebasing "other" content-divergent changeset f89a8e2f86ac on 155349b645be
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
  evolving 4:f89a8e2f86ac "added dh"
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  other divergent changeset 50a1c208f59e has same content as local e800202333a4 and differs by "description" only, discarding 50a1c208f59e

  $ hg evolve -l

  $ hg parents
  changeset:   5:e800202333a4
  tag:         tip
  parent:      2:155349b645be
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added d
  
  $ cd ..

Testing when different parent, merging conflict:
------------------------------------------------

  $ hg init pubdiv5
  $ cd pubdiv5
  $ for ch in a b c d; do
  >   echo $ch > $ch;
  >   hg ci -Am "added "$ch;
  > done;
  adding a
  adding b
  adding c
  adding d

  $ hg up 1
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo dhconflict > dh
  $ hg add dh
  $ hg ci -m "added dh"
  created new head

  $ hg up 2
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo dh > dh
  $ hg add dh
  $ hg ci -m "added d"
  created new head

  $ hg glog
  @  5:e800202333a4 added d
  |   draft
  |
  | o  4:db0b7bba0aae added dh
  | |   draft
  | |
  +---o  3:9150fe93bec6 added d
  | |     draft
  | |
  o |  2:155349b645be added c
  |/    draft
  |
  o  1:5f6d8a4bf34a added b
  |   draft
  |
  o  0:9092f1db7931 added a
      draft
  

  $ hg prune 3 -s 4
  1 changesets pruned
  $ hg prune 3 -s 5 --hidden
  1 changesets pruned
  2 new content-divergent changesets
  $ hg phase --public -r 5

  $ hg glog
  @  5:e800202333a4 added d
  |   public
  |
  | *  4:db0b7bba0aae added dh
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
  
  $ hg evolve --content-divergent --any
  merge:[5] added d
  with: [4] added dh
  base: [3] added d
  rebasing "other" content-divergent changeset db0b7bba0aae on 155349b645be
  merging dh
  warning: conflicts while merging dh! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo dh > dh
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue
  other divergent changeset a5bbf2042450 has same content as local e800202333a4 and differs by "description" only, discarding a5bbf2042450

  $ hg evolve -l

  $ hg parents
  changeset:   5:e800202333a4
  tag:         tip
  parent:      2:155349b645be
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added d
  
  $ cd ..

Testing when different parent, conflict in relocation and merging:
------------------------------------------------------------------

  $ hg init pubdiv6
  $ cd pubdiv6
  $ for ch in a b c d; do
  >   echo $ch > $ch;
  >   hg ci -Am "added "$ch;
  > done;
  adding a
  adding b
  adding c
  adding d

  $ hg up 1
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo dhconflict > dh
  $ echo cc > c
  $ hg add dh c
  $ hg ci -m "added dh"
  created new head

  $ hg up 2
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo dh > dh
  $ hg add dh
  $ hg ci -m "added d"
  created new head

  $ hg glog
  @  5:e800202333a4 added d
  |   draft
  |
  | o  4:67b19bbd770f added dh
  | |   draft
  | |
  +---o  3:9150fe93bec6 added d
  | |     draft
  | |
  o |  2:155349b645be added c
  |/    draft
  |
  o  1:5f6d8a4bf34a added b
  |   draft
  |
  o  0:9092f1db7931 added a
      draft
  

  $ hg prune 3 -s 4
  1 changesets pruned
  $ hg prune 3 -s 5 --hidden
  1 changesets pruned
  2 new content-divergent changesets
  $ hg phase --public -r 5

  $ hg glog
  @  5:e800202333a4 added d
  |   public
  |
  | *  4:67b19bbd770f added dh
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
  
  $ hg evolve --content-divergent --any
  merge:[5] added d
  with: [4] added dh
  base: [3] added d
  rebasing "other" content-divergent changeset 67b19bbd770f on 155349b645be
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
  evolving 4:67b19bbd770f "added dh"
  merging dh
  warning: conflicts while merging dh! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo dh > dh
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue
  other divergent changeset 573a0455bb00 has same content as local e800202333a4 and differs by "description" only, discarding 573a0455bb00

  $ hg evolve -l

  $ hg parents
  changeset:   5:e800202333a4
  tag:         tip
  parent:      2:155349b645be
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added d
  
  $ cd ..

Testing that we warn the user for the metadata being lost in divergence resolution:
-----------------------------------------------------------------------------------

  $ hg init pubdiv7
  $ cd pubdiv7
  $ echo '[extensions]' > .hg/hgrc
  $ echo "topic=$(echo $(dirname $TESTDIR))/hgext3rd/topic/" >> .hg/hgrc
  $ for ch in a b c d; do
  >   echo $ch > $ch;
  >   hg ci -Am "added "$ch;
  > done;
  adding a
  adding b
  adding c
  adding d

  $ echo dada > d
  $ hg amend
  $ hg up -r "desc('added c')"
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg branch double//slash
  marked working directory as branch double//slash
  (branches are permanent and global, did you want a bookmark?)
  $ hg debug-topic-namespace tns-1
  marked working directory as topic namespace: tns-1
  $ hg topics topic-1
  marked working directory as topic: topic-1
  $ echo dada > d
  $ hg ci -Am "added d"
  adding d
  active topic 'topic-1' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg prune -r "min(desc('added d'))" -s . --hidden
  1 changesets pruned
  2 new content-divergent changesets

(publish one side)
  $ hg phase --public
  active topic 'topic-1' is now empty
  (use 'hg topic --clear' to clear it if needed)
  $ hg up -r "draft()"
  clearing empty topic "topic-1"
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ hg debug-topic-namespace tns-2
  marked working directory as topic namespace: tns-2
  $ hg topics topic-2
  marked working directory as topic: topic-2

(make other divergent a closed branch head)
  $ hg ci --amend -m "closing branch double//slash" --close-branch
  active topic 'topic-2' grew its first changeset
  (see 'hg help topics' for more information)

  $ hg glog
  @  6:fe5d55b4e488 closing branch double//slash
  |   draft content-divergent
  |
  | o  5:bde8ac1c636a added d
  |/    public
  |
  o  2:155349b645be added c
  |   public
  |
  o  1:5f6d8a4bf34a added b
  |   public
  |
  o  0:9092f1db7931 added a
      public
  

Run automatic evolution:

  $ hg evolve --content-divergent
  merge:[5] added d
  with: [6] closing branch double//slash
  base: [3] added d
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  other divergent changeset fe5d55b4e488 is a closed branch head and differs from local bde8ac1c636a by "branch, description" only, discarding fe5d55b4e488
  content divergence resolution between bde8ac1c636a (public) and fe5d55b4e488 has same content as bde8ac1c636a, discarding fe5d55b4e488
  active topic 'topic-2' is now empty
  working directory is now at bde8ac1c636a

