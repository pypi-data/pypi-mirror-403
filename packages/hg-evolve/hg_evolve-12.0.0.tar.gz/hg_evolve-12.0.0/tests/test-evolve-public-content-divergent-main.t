=============================================================
Tests the resolution of public content divergence: main cases
=============================================================

This file intend to cover all the common cases of public content divergence.
That is all the variant of:
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

Prepare the repository:

  $ hg init pubdiv1
  $ cd pubdiv1
  $ for ch in a b; do
  >   echo $ch > $ch;
  >   hg ci -Aqm "added "$ch;
  > done;
  $ hg glog
  @  1:5f6d8a4bf34a added b
  |   draft
  |
  o  0:9092f1db7931 added a
      draft
  

Make an amend and change phase to public:

  $ printf "I am first\nb\n" > b
  $ hg amend
  $ hg phase --public

Amend again to create a cset divergent to public one:

  $ hg up 1 --hidden -q
  updated to hidden changeset 5f6d8a4bf34a
  (hidden revision '5f6d8a4bf34a' was rewritten as: 44f360db368f)
  working directory parent is obsolete! (5f6d8a4bf34a)

  $ echo "I am second" >> b
  $ hg ci --amend -m "updated b"
  1 new content-divergent changesets

  $ hg glog
  @  3:dcdaf152280a updated b
  |   draft content-divergent
  |
  | o  2:44f360db368f added b
  |/    public
  |
  o  0:9092f1db7931 added a
      public
  

Lets resolve the public content-divergence:

  $ hg evolve --content-divergent
  merge:[2] added b
  with: [3] updated b
  base: [1] added b
  merging b
  0 files updated, 1 files merged, 0 files removed, 0 files unresolved
  committed as b11d193ede1d
  working directory is now at b11d193ede1d

Following graph log shows that it correctly merged the two divergent csets:

  $ hg glog -p
  @  5:b11d193ede1d phase-divergent update to 44f360db368f:
  |   draft
  |
  |  diff -r 44f360db368f -r b11d193ede1d b
  |  --- a/b	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -1,2 +1,3 @@
  |   I am first
  |   b
  |  +I am second
  |
  o  2:44f360db368f added b
  |   public
  |
  |  diff -r 9092f1db7931 -r 44f360db368f b
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,2 @@
  |  +I am first
  |  +b
  |
  o  0:9092f1db7931 added a
      public
  
     diff -r 000000000000 -r 9092f1db7931 a
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/a	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +a
  
  $ hg evolve -l
  $ cd ..

Testing when same parent, merging conflict:
-------------------------------------------

Prepare the repository:

  $ hg init pubdiv2
  $ cd pubdiv2
  $ for ch in a b; do
  >   echo $ch > $ch;
  >   hg ci -Aqm "added "$ch;
  > done;
  $ hg glog
  @  1:5f6d8a4bf34a added b
  |   draft
  |
  o  0:9092f1db7931 added a
      draft
  

Make an amend and change phase to public:

  $ echo "I am foo" > b
  $ hg amend
  $ hg phase --public

Amend again to create a cset divergent to public one:

  $ hg up 1 --hidden -q
  updated to hidden changeset 5f6d8a4bf34a
  (hidden revision '5f6d8a4bf34a' was rewritten as: 580f2d01e52c)
  working directory parent is obsolete! (5f6d8a4bf34a)

  $ echo "I am bar" > b
  $ hg ci --amend -m "updated b"
  1 new content-divergent changesets

  $ hg glog
  @  3:0e805383168e updated b
  |   draft content-divergent
  |
  | o  2:580f2d01e52c added b
  |/    public
  |
  o  0:9092f1db7931 added a
      public
  

Lets resolve the divergence:

  $ hg evolve --content-divergent
  merge:[2] added b
  with: [3] updated b
  base: [1] added b
  merging b
  warning: conflicts while merging b! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo "I am foobar" > b
  $ hg resolve -m --tool union
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  committed as 4ae447c511d3
  working directory is now at 4ae447c511d3

  $ hg glog
  @  5:4ae447c511d3 phase-divergent update to 580f2d01e52c:
  |   draft
  |
  o  2:580f2d01e52c added b
  |   public
  |
  o  0:9092f1db7931 added a
      public
  
Testing when different parent, no conflict:
-------------------------------------------

  $ hg init pubdiv3
  $ cd pubdiv3
  $ for ch in a b c d; do
  >   echo $ch > $ch;
  >   hg ci -Aqm "added "$ch;
  > done;

  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo dd > d
  $ hg add d
  $ hg ci -m "added d"
  created new head

  $ hg up 1
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo dd > d
  $ echo e > e
  $ hg add d e
  $ hg ci -m "added d e"
  created new head

  $ hg glog
  @  5:4291d72ee19a added d e
  |   draft
  |
  | o  4:93cd84bbdaca added d
  | |   draft
  | |
  | | o  3:9150fe93bec6 added d
  | |/    draft
  | |
  | o  2:155349b645be added c
  |/    draft
  |
  o  1:5f6d8a4bf34a added b
  |   draft
  |
  o  0:9092f1db7931 added a
      draft
  

  $ hg prune 3 -s 5
  1 changesets pruned
  $ hg prune 3 -s 4 --hidden
  1 changesets pruned
  2 new content-divergent changesets

Change phase to public for one head:
  $ hg phase -r 4 --public

  $ hg glog
  @  5:4291d72ee19a added d e
  |   draft content-divergent
  |
  | o  4:93cd84bbdaca added d
  | |   public
  | |
  | o  2:155349b645be added c
  |/    public
  |
  o  1:5f6d8a4bf34a added b
  |   public
  |
  o  0:9092f1db7931 added a
      public
  

  $ hg evolve --content-divergent --any
  merge:[4] added d
  with: [5] added d e
  base: [3] added d
  rebasing "other" content-divergent changeset 4291d72ee19a on 155349b645be
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  committed as 07aa587dcd2b
  working directory is now at 07aa587dcd2b

  $ hg glog -l 1
  @  8:07aa587dcd2b phase-divergent update to 93cd84bbdaca:
  |   draft
  ~

  $ hg evolve -l
  $ cd ..

Testing when different parents, relocation conflict:
----------------------------------------------------

  $ hg init pubdiv4
  $ cd pubdiv4
  $ for ch in a b c d; do
  >   echo $ch > $ch;
  >   hg ci -Aqm "added "$ch;
  > done;

  $ hg up .^^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo d > d
  $ echo cfoo > c
  $ echo e > e
  $ hg add d c e
  $ hg ci -m "added d c e"
  created new head

  $ hg up 'desc("added c")'
  1 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo dd > d
  $ hg add d
  $ hg ci -m "added d"
  created new head

  $ hg glog
  @  5:93cd84bbdaca added d
  |   draft
  |
  | o  4:f31bcc378766 added d c e
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
  
  $ hg prune 'min(desc("re:added d$"))' -s 'max(desc("re:added d$"))'
  1 changesets pruned
  $ hg prune 'min(desc("re:added d$"))' -s 'desc("added d c e")' --hidden
  1 changesets pruned
  2 new content-divergent changesets

Change phase to public for one head:
  $ hg phase --public -r 'max(desc("re:added d$"))'

  $ hg glog
  @  5:93cd84bbdaca added d
  |   public
  |
  | *  4:f31bcc378766 added d c e
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
  
  $ hg evolve --content-divergent --any --update
  merge:[5] added d
  with: [4] added d c e
  base: [3] added d
  rebasing "other" content-divergent changeset f31bcc378766 on 155349b645be
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
  +>>>>>>> evolving:    f31bcc378766 - test: added d c e
  diff -r 155349b645be d
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/d	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +d
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
  evolving 4:f31bcc378766 "added d c e"
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  committed as e247c56b4c01
  working directory is now at e247c56b4c01
  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID e247c56b4c0103b53448551b3e5ff9a8173be791
  # Parent  93cd84bbdacaeb8f881c29a609dbdd30c38cbc57
  phase-divergent update to 93cd84bbdaca:
  
  added d c e
  
  diff -r 93cd84bbdaca -r e247c56b4c01 e
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/e	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +e

  $ hg evolve -l
  $ cd ..

Testing when merging conflicts, relocation don't:
-------------------------------------------------

  $ hg init pubdiv5
  $ cd pubdiv5
  $ for ch in a b c d; do
  >   echo $ch > $ch;
  >   hg ci -Aqm "added "$ch;
  > done;

  $ hg up .^^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo dconflict > d
  $ hg add d
  $ hg ci -m "added d"
  created new head

  $ hg up 2
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo dd > d
  $ hg add d
  $ hg ci -m "added d"
  created new head

  $ hg glog
  @  5:93cd84bbdaca added d
  |   draft
  |
  | o  4:9411ad1fe615 added d
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
  
  $ hg prune 3 -s 5
  1 changesets pruned
  $ hg prune 3 -s 4 --hidden
  1 changesets pruned
  2 new content-divergent changesets

Change phase to public for one head:
  $ hg phase --public -r 5

  $ hg glog
  @  5:93cd84bbdaca added d
  |   public
  |
  | *  4:9411ad1fe615 added d
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
  with: [4] added d
  base: [3] added d
  rebasing "other" content-divergent changeset 9411ad1fe615 on 155349b645be
  merging d
  warning: conflicts while merging d! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo d > d
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue
  committed as d87a8f56f14a

  $ hg evolve -l
  $ cd ..

Testing when relocation, merging both conflict:
-----------------------------------------------

  $ hg init pubdiv6
  $ cd pubdiv6
  $ for ch in a b c d; do
  >   echo $ch > $ch;
  >   hg ci -Aqm "added "$ch;
  > done;

  $ hg up .^^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo cfoo > c
  $ echo e > e
  $ echo dconflict > d
  $ hg add c e d
  $ hg ci -m "added c e"
  created new head

  $ hg up 2
  1 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo dd > d
  $ hg add d
  $ hg ci -m "added d"
  created new head

  $ hg glog
  @  5:93cd84bbdaca added d
  |   draft
  |
  | o  4:3c17c7afaf6e added c e
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
  
  $ hg prune 3 -s 5
  1 changesets pruned
  $ hg prune 3 -s 4 --hidden
  1 changesets pruned
  2 new content-divergent changesets

Change phase to public for one head:
  $ hg phase --public -r 5

  $ hg glog
  @  5:93cd84bbdaca added d
  |   public
  |
  | *  4:3c17c7afaf6e added c e
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
  with: [4] added c e
  base: [3] added d
  rebasing "other" content-divergent changeset 3c17c7afaf6e on 155349b645be
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
  +>>>>>>> evolving:    3c17c7afaf6e - test: added c e
  diff -r 155349b645be d
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/d	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +dconflict
  diff -r 155349b645be e
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/e	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +e

  $ echo cfoo > c
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue
  evolving 4:3c17c7afaf6e "added c e"
  merging d
  warning: conflicts while merging d! (edit, then use 'hg resolve --mark')
  2 files updated, 0 files merged, 0 files removed, 1 files unresolved
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ echo d > d
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue
  committed as 704cf6f2d22f

  $ hg evolve -l
  $ cd ..
