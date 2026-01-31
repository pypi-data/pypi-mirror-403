Test for issue 5832 present at https://bz.mercurial-scm.org/show_bug.cgi?id=5832
================================================================================

Setup
=====

  $ . $TESTDIR/testlib/common.sh

  $ cat >> $HGRCPATH <<EOF
  > [phases]
  > publish = False
  > [extensions]
  > evolve =
  > EOF

  $ hg init issue5832
  $ cd issue5832

  $ echo base > base
  $ hg ci -Aqm "added base"

  $ echo a > a
  $ hg ci -Aqm "added a"

  $ echo b > b
  $ hg ci -Aqm "added b"

  $ hg up .^^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo c > c
  $ echo d > d
  $ hg ci -Aqm "added c and d"

  $ hg merge
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "merge commit"

  $ hg glog
  @    4:b9b387427a53 merge commit
  |\    () draft
  | o  3:9402371b436e added c and d
  | |   () draft
  o |  2:a1da0651488c added b
  | |   () draft
  o |  1:1b24879c5c3c added a
  |/    () draft
  o  0:bde1d2b6b5e5 added base
      () draft

  $ hg up 1b24879c5c3c
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ echo foo > a
  $ hg amend
  2 new orphan changesets

  $ hg up bde1d2b6b5e5
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo c > c
  $ hg ci -Aqm "added c"
  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo d > d
  $ hg ci -Aqm "added d"
  $ hg glog
  @  7:5841d7cf9893 added d
  |   () draft
  | o  6:62fb70414f99 added c
  |/    () draft
  | o  5:7014ec2829cd added a
  |/    () draft
  | *    4:b9b387427a53 merge commit
  | |\    () draft orphan
  +---o  3:9402371b436e added c and d
  | |     () draft
  | *  2:a1da0651488c added b
  | |   () draft orphan
  | x  1:1b24879c5c3c added a
  |/    () draft
  o  0:bde1d2b6b5e5 added base
      () draft

  $ hg prune -r 9402371b436e --succ 62fb70414f99 --succ 5841d7cf9893 --split
  1 changesets pruned

  $ hg glog
  @  7:5841d7cf9893 added d
  |   () draft
  | o  6:62fb70414f99 added c
  |/    () draft
  | o  5:7014ec2829cd added a
  |/    () draft
  | *    4:b9b387427a53 merge commit
  | |\    () draft orphan
  +---x  3:9402371b436e added c and d
  | |     () draft
  | *  2:a1da0651488c added b
  | |   () draft orphan
  | x  1:1b24879c5c3c added a
  |/    () draft
  o  0:bde1d2b6b5e5 added base
      () draft

Checking what evolve is trying to do

  $ hg evolve --dry-run --any --all
  move:[2] added b
  atop:[5] added a
  hg rebase -r a1da0651488c -d 7014ec2829cd
  could not solve instability, ambiguous destination: parent split across two branches

Resolving instability using `hg evolve`

  $ hg evolve --any --all --config ui.interactive=True <<EOF
  > 1
  > EOF
  move:[2] added b
  atop:[5] added a
  move:[4] merge commit
  changeset 9402371b436e split over multiple topological branches, choose an evolve destination:
  1: [62fb70414f99] added c
  2: [5841d7cf9893] added d
  q: quit the prompt
  enter the index of the revision you want to select: 1
  move:[9] merge commit
  atop:[6] added c

  $ hg glog
  o    10:28a0775ac832 merge commit
  |\    () draft
  | o  8:2baf8bae7ea4 added b
  | |   () draft
  | | @  7:5841d7cf9893 added d
  | | |   () draft
  o---+  6:62fb70414f99 added c
   / /    () draft
  o /  5:7014ec2829cd added a
  |/    () draft
  o  0:bde1d2b6b5e5 added base
      () draft

  $ cd ..

Test for issue5833 present at https://bz.mercurial-scm.org/show_bug.cgi?id=5833
===============================================================================

  $ hg init issue5833
  $ cd issue5833
  $ echo base > base
  $ hg ci -Aqm "added base"

  $ echo a > a
  $ hg ci -Aqm "added a"

  $ echo b > b
  $ hg ci -Aqm "added b"

  $ hg up .^^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo c > c
  $ echo d > d
  $ hg ci -Aqm "added c and d"

  $ hg merge
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "merge commit"

  $ hg glog
  @    4:b9b387427a53 merge commit
  |\    () draft
  | o  3:9402371b436e added c and d
  | |   () draft
  o |  2:a1da0651488c added b
  | |   () draft
  o |  1:1b24879c5c3c added a
  |/    () draft
  o  0:bde1d2b6b5e5 added base
      () draft
  $ hg log -r 'p1(.)'
  changeset:   3:9402371b436e
  parent:      0:bde1d2b6b5e5
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added c and d
  
  $ hg up bde1d2b6b5e5
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  $ echo l > l
  $ hg ci -Aqm "added l"
  $ hg pick -r 1b24879c5c3c
  picking 1:1b24879c5c3c "added a"
  2 new orphan changesets

  $ hg up bde1d2b6b5e5
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo c > c
  $ hg ci -Aqm "added c"
  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo d > d
  $ hg ci -Aqm "added d"

  $ hg glog
  @  8:5841d7cf9893 added d
  |   () draft
  | o  7:62fb70414f99 added c
  |/    () draft
  | o  6:5568b87b1491 added a
  | |   () draft
  | o  5:0a6281e212fe added l
  |/    () draft
  | *    4:b9b387427a53 merge commit
  | |\    () draft orphan
  +---o  3:9402371b436e added c and d
  | |     () draft
  | *  2:a1da0651488c added b
  | |   () draft orphan
  | x  1:1b24879c5c3c added a
  |/    () draft
  o  0:bde1d2b6b5e5 added base
      () draft

  $ hg prune -r 9402371b436e --succ 5841d7cf9893 --succ 62fb70414f99 --split
  1 changesets pruned

  $ hg glog
  @  8:5841d7cf9893 added d
  |   () draft
  | o  7:62fb70414f99 added c
  |/    () draft
  | o  6:5568b87b1491 added a
  | |   () draft
  | o  5:0a6281e212fe added l
  |/    () draft
  | *    4:b9b387427a53 merge commit
  | |\    () draft orphan
  +---x  3:9402371b436e added c and d
  | |     () draft
  | *  2:a1da0651488c added b
  | |   () draft orphan
  | x  1:1b24879c5c3c added a
  |/    () draft
  o  0:bde1d2b6b5e5 added base
      () draft

  $ hg evolve --any --all --dry-run
  move:[2] added b
  atop:[6] added a
  hg rebase -r a1da0651488c -d 5568b87b1491
  could not solve instability, ambiguous destination: parent split across two branches

  $ hg evolve --any --all --config ui.interactive=True <<EOF
  > 2
  > EOF
  move:[2] added b
  atop:[6] added a
  move:[4] merge commit
  changeset 9402371b436e split over multiple topological branches, choose an evolve destination:
  1: [62fb70414f99] added c
  2: [5841d7cf9893] added d
  q: quit the prompt
  enter the index of the revision you want to select: 2
  move:[10] merge commit
  atop:[8] added d

  $ hg glog
  o    11:460e6e72b7f9 merge commit
  |\    () draft
  | o  9:da76bb7cd904 added b
  | |   () draft
  @ |  8:5841d7cf9893 added d
  | |   () draft
  +---o  7:62fb70414f99 added c
  | |     () draft
  | o  6:5568b87b1491 added a
  | |   () draft
  | o  5:0a6281e212fe added l
  |/    () draft
  o  0:bde1d2b6b5e5 added base
      () draft

  $ cd ..

Test for issue5946 present at https://bz.mercurial-scm.org/show_bug.cgi?id=5946
===============================================================================
issue with computing dependency with split and merge

  $ hg init issue5946
  $ cd issue5946
  $ echo base > base
  $ hg ci -Aqm "added base"

  $ echo a > a
  $ hg ci -Aqm "added a"

  $ echo b > b
  $ hg ci -Aqm "added b"

  $ hg up .^^
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo c > c
  $ echo d > d
  $ hg ci -Aqm "added c and d"
The next line is the only difference from issue5833 above, i.e. the order of
the parents is reversed
  $ hg co 2
  2 files updated, 0 files merged, 2 files removed, 0 files unresolved

  $ hg merge
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "merge commit"

  $ hg glog
  @    4:b9b387427a53 merge commit
  |\    () draft
  | o  3:9402371b436e added c and d
  | |   () draft
  o |  2:a1da0651488c added b
  | |   () draft
  o |  1:1b24879c5c3c added a
  |/    () draft
  o  0:bde1d2b6b5e5 added base
      () draft
  $ hg log -r 'p1(.)'
  changeset:   2:a1da0651488c
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     added b
  
  $ hg up bde1d2b6b5e5
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  $ echo l > l
  $ hg ci -Aqm "added l"
  $ hg pick -r 1b24879c5c3c
  picking 1:1b24879c5c3c "added a"
  2 new orphan changesets

  $ hg up bde1d2b6b5e5
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo c > c
  $ hg ci -Aqm "added c"
  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo d > d
  $ hg ci -Aqm "added d"

  $ hg glog
  @  8:5841d7cf9893 added d
  |   () draft
  | o  7:62fb70414f99 added c
  |/    () draft
  | o  6:5568b87b1491 added a
  | |   () draft
  | o  5:0a6281e212fe added l
  |/    () draft
  | *    4:b9b387427a53 merge commit
  | |\    () draft orphan
  +---o  3:9402371b436e added c and d
  | |     () draft
  | *  2:a1da0651488c added b
  | |   () draft orphan
  | x  1:1b24879c5c3c added a
  |/    () draft
  o  0:bde1d2b6b5e5 added base
      () draft

  $ hg prune -r 9402371b436e --succ 5841d7cf9893 --succ 62fb70414f99 --split
  1 changesets pruned

  $ hg glog
  @  8:5841d7cf9893 added d
  |   () draft
  | o  7:62fb70414f99 added c
  |/    () draft
  | o  6:5568b87b1491 added a
  | |   () draft
  | o  5:0a6281e212fe added l
  |/    () draft
  | *    4:b9b387427a53 merge commit
  | |\    () draft orphan
  +---x  3:9402371b436e added c and d
  | |     () draft
  | *  2:a1da0651488c added b
  | |   () draft orphan
  | x  1:1b24879c5c3c added a
  |/    () draft
  o  0:bde1d2b6b5e5 added base
      () draft

  $ hg evolve --any --all --dry-run
  move:[2] added b
  atop:[6] added a
  hg rebase -r a1da0651488c -d 5568b87b1491
  could not solve instability, ambiguous destination: parent split across two branches

  $ hg evolve --any --all --config ui.interactive=True <<EOF
  > 2
  > EOF
  move:[2] added b
  atop:[6] added a
  changeset 9402371b436e split over multiple topological branches, choose an evolve destination:
  1: [62fb70414f99] added c
  2: [5841d7cf9893] added d
  q: quit the prompt
  enter the index of the revision you want to select: 2
  move:[4] merge commit
  atop:[8] added d
  move:[10] merge commit
  atop:[9] added b

  $ hg glog
  o    11:578c938ebd2e merge commit
  |\    () draft
  | o  9:da76bb7cd904 added b
  | |   () draft
  @ |  8:5841d7cf9893 added d
  | |   () draft
  +---o  7:62fb70414f99 added c
  | |     () draft
  | o  6:5568b87b1491 added a
  | |   () draft
  | o  5:0a6281e212fe added l
  |/    () draft
  o  0:bde1d2b6b5e5 added base
      () draft
