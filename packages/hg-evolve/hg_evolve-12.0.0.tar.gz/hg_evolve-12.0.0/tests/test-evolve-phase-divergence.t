** Test for handling of phase divergent changesets by `hg evolve` **
====================================================================

  $ . $TESTDIR/testlib/common.sh

  $ cat >> $HGRCPATH <<EOF
  > [alias]
  > glog = log -GT "{rev}:{node|short} {desc|firstline}\n ({bookmarks}) {phase}"
  > [extensions]
  > rebase =
  > evolve =
  > EOF

Setting up a public repo
------------------------

  $ hg init public
  $ cd public
  $ echo a > a
  $ hg commit -A -m init
  adding a
  $ cd ..

Setting up a private non-publishing repo
----------------------------------------

  $ hg clone public private
  updating to branch default
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ cd private
  $ cat >> .hg/hgrc <<EOF
  > [ui]
  > logtemplate = {rev}:{node|short}@{branch}({phase}) {desc|firstline}\n
  > [phases]
  > publish = false
  > EOF
  $ cd ..

Setting up couple of more instances of private repo
---------------------------------------------------

  $ cp -a private alice
  $ cp -a private bob
  $ cp -a private split
  $ cp -a private split-across-branches
  $ cp -a private split-and-amend
  $ cp -a private merge-no-conflict

Simple phase-divergence case
============================

Creating a phase-divergence changeset
-------------------------------------

Alice creating a draft changeset and pushing to main private repo

  $ cd alice
  $ echo a >> a
  $ hg commit -u alice -m 'modify a'
  $ hg push ../private
  pushing to ../private
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  $ hg glog
  @  1:4d1169d82e47 modify a
  |   () draft
  o  0:d3873e73d99e init
      () public

Bob pulling from private repo and pushing to the main public repo making the
changeset public

  $ cd ../bob
  $ hg pull ../private
  pulling from ../private
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets 4d1169d82e47 (1 drafts)
  (run 'hg update' to get a working copy)

  $ hg glog
  o  1:4d1169d82e47 modify a
  |   () draft
  @  0:d3873e73d99e init
      () public

  $ hg push ../public
  pushing to ../public
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

  $ hg glog
  o  1:4d1169d82e47 modify a
  |   () public
  @  0:d3873e73d99e init
      () public

*But* Alice decided to amend the changeset she had and then pulling from public
repo creating phase-divergent changeset locally

  $ cd ../alice
  $ hg amend -m 'tweak a'

XXX: pull should tell us how to see what is the new phase-divergent changeset
  $ hg pull ../public
  pulling from ../public
  searching for changes
  no changes found
  1 new phase-divergent changesets
  1 local changesets published

  $ hg glog
  @  2:98bb3a6cfe1a tweak a
  |   () draft
  | o  1:4d1169d82e47 modify a
  |/    () public
  o  0:d3873e73d99e init
      () public

Using evolve --list to list phase-divergent changesets
------------------------------------------------------

  $ hg evolve --list
  98bb3a6cfe1a: tweak a
    phase-divergent: 4d1169d82e47 (immutable precursor)
  


XXX-Pulkit: Trying to see instability on public changeset

XXX-Pulkit: this is not helpful

XXX-Marmoute: public changeset "instable themself"
XXX-Marmoute: I'm not sure if we store this information and it is useful to show it.
XXX-Marmoute: We should maybe point the user toward `hg obslog` instead`
  $ hg evolve -r 4d1169d8 --list
  4d1169d82e47: modify a
  

Understanding phasedivergence using obslog
------------------------------------------

XXX: There must be mention of phase-divergence here
  $ hg obslog -r . --all
  @  98bb3a6cfe1a (2) tweak a
  |    reworded(description) from 4d1169d82e47 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  o  4d1169d82e47 (1) modify a
  
Solving the phase divergence using evolve command
--------------------------------------------------

(We do not solve evolution other than orphan by default because it turned out
it was too confusing for users. We used to behave this way, but having multiple
possible outcome to evolve end up scaring people)

  $ hg evolve
  nothing to evolve on current working copy parent
  (do you want to use --phase-divergent)
  [2]

testing the --confirm option
  $ hg evolve --phase-divergent --confirm <<EOF
  > n
  > EOF
  recreate:[2] tweak a
  atop:[1] modify a
  perform evolve? [Ny] n
  abort: evolve aborted by user
  [255]

testing the --dry-run option

  $ hg evolve --phase-divergent --dry-run
  recreate:[2] tweak a
  atop:[1] modify a
  hg rebase --rev 98bb3a6cfe1a --dest d3873e73d99e;
  hg update 4d1169d82e47;
  hg revert --all --rev 98bb3a6cfe1a;
  hg commit --message "phase-divergent update to 98bb3a6cfe1a"

XXX: evolve should have mentioned that draft commit is just obsoleted in favour
of public one. From the message it looks like a new commit is created.

  $ hg evolve --phase-divergent --update
  recreate:[2] tweak a
  atop:[1] modify a
  no changes to commit
  working directory is now at 4d1169d82e47

  $ hg glog
  @  1:4d1169d82e47 modify a
  |   () public
  o  0:d3873e73d99e init
      () public

Syncying every repo with the new state
--------------------------------------

  $ hg push ../public
  pushing to ../public
  searching for changes
  no changes found
  2 new obsolescence markers
  [1]
  $ hg push ../private
  pushing to ../private
  searching for changes
  no changes found
  2 new obsolescence markers
  [1]
  $ hg push ../bob
  pushing to ../bob
  searching for changes
  no changes found
  2 new obsolescence markers
  [1]

phase-divergence that lead to new commit and bookmark movement
==============================================================

Creating more phase-divergence where a new resolution commit will be formed and
also testing bookmark movement

Alice created a commit and push to private non-publishing repo

  $ echo foo > foo
  $ hg add foo
  $ hg ci -m "added foo to foo"
  $ hg glog
  @  3:aa071e5554e3 added foo to foo
  |   () draft
  o  1:4d1169d82e47 modify a
  |   () public
  o  0:d3873e73d99e init
      () public

  $ hg push ../private
  pushing to ../private
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Bob pulled from the private repo and pushed that to publishing repo

  $ cd ../bob
  $ hg pull ../private
  pulling from ../private
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets aa071e5554e3 (1 drafts)
  (run 'hg update' to get a working copy)

  $ hg push ../public
  pushing to ../public
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Alice amended that changeset and then pulled from publishing repo creating
phase-divergence

  $ cd ../alice
  $ echo bar >> foo
  $ hg amend -m "added bar to foo"
  $ hg bookmark bm

  $ hg pull ../public
  pulling from ../public
  searching for changes
  no changes found
  1 new phase-divergent changesets
  1 local changesets published

  $ hg glog
  @  4:d47f2b37ed82 added bar to foo
  |   (bm) draft
  | o  3:aa071e5554e3 added foo to foo
  |/    () public
  o  1:4d1169d82e47 modify a
  |   () public
  o  0:d3873e73d99e init
      () public

Resolving the new phase-divergence changeset using `hg evolve`
--------------------------------------------------------------

XXX: this should have popped up for a new commit message of the changeset or an
option should be there

XXX: we should document what should user expect where running this, writing this
test I have to go through code base to understand what will be the behavior

  $ hg evolve --phase-divergent --update
  recreate:[4] added bar to foo
  atop:[3] added foo to foo
  committed as 3d62500c673d
  working directory is now at 3d62500c673d

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 3d62500c673dd1c88bb09a73e86d0210aed6fcb6
  # Parent  aa071e5554e36080a36cfd24accd5a71e3320f1e
  phase-divergent update to aa071e5554e3:
  
  added bar to foo
  
  diff -r aa071e5554e3 -r 3d62500c673d foo
  --- a/foo	Thu Jan 01 00:00:00 1970 +0000
  +++ b/foo	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,2 @@
   foo
  +bar

XXX: the commit message is not best one, we should give option to user to modify
the commit message

  $ hg glog
  @  5:3d62500c673d phase-divergent update to aa071e5554e3:
  |   (bm) draft
  o  3:aa071e5554e3 added foo to foo
  |   () public
  o  1:4d1169d82e47 modify a
  |   () public
  o  0:d3873e73d99e init
      () public

  $ hg debugobsolete
  4d1169d82e47b11570c7f380790da5f89f7cabc2 98bb3a6cfe1a3d98d0959e9d42322f38313a08f3 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'operation': 'amend', 'user': 'test'}
  98bb3a6cfe1a3d98d0959e9d42322f38313a08f3 0 {d3873e73d99ef67873dac33fbcc66268d5d2b6f4} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  aa071e5554e36080a36cfd24accd5a71e3320f1e d47f2b37ed8216234c503b3a2657989958754a59 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  d47f2b37ed8216234c503b3a2657989958754a59 3d62500c673dd1c88bb09a73e86d0210aed6fcb6 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog -r . --all
  @  3d62500c673d (5) phase-divergent update to aa071e5554e3:
  |    rewritten(description, parent, content) from d47f2b37ed82 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  d47f2b37ed82 (4) added bar to foo
  |    rewritten(description, content) from aa071e5554e3 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  o  aa071e5554e3 (3) added foo to foo
  

Syncing all other repositories
------------------------------

These pushed should not be turned to quiet mode as the output is very helpful to
make sure everything is working fine

  $ hg push ../bob
  pushing to ../bob
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  2 new obsolescence markers

  $ hg push ../private
  pushing to ../private
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  2 new obsolescence markers

  $ hg push ../public
  pushing to ../public
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  2 new obsolescence markers


phase divergence rebasing back to old changeset - with (unrelated?) conflict
============================================================================

Creating a phasedivergence changeset where the divergent changeset changed in a
way that we rebase that on old public changeset, there will be conflicts, but
the `hg evolve` command handles it very well and uses `hg revert` logic to
prevent any conflicts

Alice creates one more changeset and pushes to private repo

  $ echo bar > bar
  $ hg ci -Aqm "added bar to bar"
  $ hg push ../private
  pushing to ../private
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Bob pulls from private and pushes to public repo
  $ cd ../bob

  $ hg pull ../private
  pulling from ../private
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  new changesets b756eb10ea73 (1 drafts)
  1 local changesets published
  (run 'hg update' to get a working copy)

  $ hg push ../public
  pushing to ../public
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Alice amends the changeset and then pull from public creating phase-divergence

  $ cd ../alice
  $ echo foo > bar
  $ hg amend -m "foo to bar"

  $ hg pull ../public
  pulling from ../public
  searching for changes
  no changes found
  1 new phase-divergent changesets
  1 local changesets published

  $ hg glog
  @  7:2c3560aedead foo to bar
  |   (bm) draft
  | o  6:b756eb10ea73 added bar to bar
  |/    () public
  o  5:3d62500c673d phase-divergent update to aa071e5554e3:
  |   () public
  o  3:aa071e5554e3 added foo to foo
  |   () public
  o  1:4d1169d82e47 modify a
  |   () public
  o  0:d3873e73d99e init
      () public

Resolving the new phase-divergence changeset using `hg evolve`
---------------------------------------------------------------

  $ hg evolve --phase-divergent --update
  recreate:[7] foo to bar
  atop:[6] added bar to bar
  committed as 502e73736632
  working directory is now at 502e73736632

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 502e737366322886cf628276aa0a2796904453b4
  # Parent  b756eb10ea73ee4ba69c998e64a5c6e1005d74b5
  phase-divergent update to b756eb10ea73:
  
  foo to bar
  
  diff -r b756eb10ea73 -r 502e73736632 bar
  --- a/bar	Thu Jan 01 00:00:00 1970 +0000
  +++ b/bar	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -bar
  +foo

  $ hg glog
  @  8:502e73736632 phase-divergent update to b756eb10ea73:
  |   (bm) draft
  o  6:b756eb10ea73 added bar to bar
  |   () public
  o  5:3d62500c673d phase-divergent update to aa071e5554e3:
  |   () public
  o  3:aa071e5554e3 added foo to foo
  |   () public
  o  1:4d1169d82e47 modify a
  |   () public
  o  0:d3873e73d99e init
      () public

Syncing all the repositories
----------------------------

  $ hg push ../private
  pushing to ../private
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  2 new obsolescence markers
  $ hg push ../public
  pushing to ../public
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  2 new obsolescence markers

different parents for successors and predecessors
=================================================

Creating phase-divergence with divergent changeset and precursor having
different parents

Alice creates a changeset and pushes to private repo

  $ echo x > x
  $ hg ci -Am "added x to x"
  adding x

  $ hg push ../private
  pushing to ../private
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Bob does what he always does, pull from private and push to public, he is acting
as a CI service

  $ cd ../bob
  $ hg pull ../private
  pulling from ../private
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 2 changes to 2 files
  2 new obsolescence markers
  new changesets 502e73736632:2352021b3785 (1 drafts)
  (run 'hg update' to get a working copy)
  $ hg push ../public
  pushing to ../public
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files

Alice like always dont care about Bob existence and rebases her changeset and
then pull from public repo creating phase divergence

  $ cd ../alice
  $ hg rebase -r . -d .^^^
  rebasing 9:2352021b3785 bm tip "added x to x"

  $ hg pull ../public
  pulling from ../public
  searching for changes
  no changes found
  1 new phase-divergent changesets
  1 local changesets published

  $ hg debugobsolete
  4d1169d82e47b11570c7f380790da5f89f7cabc2 98bb3a6cfe1a3d98d0959e9d42322f38313a08f3 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'operation': 'amend', 'user': 'test'}
  98bb3a6cfe1a3d98d0959e9d42322f38313a08f3 0 {d3873e73d99ef67873dac33fbcc66268d5d2b6f4} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  aa071e5554e36080a36cfd24accd5a71e3320f1e d47f2b37ed8216234c503b3a2657989958754a59 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  d47f2b37ed8216234c503b3a2657989958754a59 3d62500c673dd1c88bb09a73e86d0210aed6fcb6 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  b756eb10ea73ee4ba69c998e64a5c6e1005d74b5 2c3560aedeadb452d517b6c5a93fd3af91b3b8cd 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  2c3560aedeadb452d517b6c5a93fd3af91b3b8cd 502e737366322886cf628276aa0a2796904453b4 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  2352021b37851be226ebed109b0eb6eada918566 334e300d6db500489d842240cbdc40c203d385c7 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  $ hg obslog -r .
  @  334e300d6db5 (10) added x to x
  |    rebased(parent) from 2352021b3785 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  o  2352021b3785 (9) added x to x
  
  $ hg glog -r .^::
  @  10:334e300d6db5 added x to x
  |   (bm) draft
  | o  9:2352021b3785 added x to x
  | |   () public
  | o  8:502e73736632 phase-divergent update to b756eb10ea73:
  | |   () public
  | o  6:b756eb10ea73 added bar to bar
  |/    () public
  o  5:3d62500c673d phase-divergent update to aa071e5554e3:
  |   () public
  ~

Using `hg evolve` to resolve phase-divergence
---------------------------------------------

  $ hg evolve --phase-divergent --update
  recreate:[10] added x to x
  atop:[9] added x to x
  rebasing to destination parent: 502e73736632
  (leaving bookmark bm)
  no changes to commit
  working directory is now at 2352021b3785

XXX: we should move bookmark here
  $ hg glog
  @  9:2352021b3785 added x to x
  |   (bm) public
  o  8:502e73736632 phase-divergent update to b756eb10ea73:
  |   () public
  o  6:b756eb10ea73 added bar to bar
  |   () public
  o  5:3d62500c673d phase-divergent update to aa071e5554e3:
  |   () public
  o  3:aa071e5554e3 added foo to foo
  |   () public
  o  1:4d1169d82e47 modify a
  |   () public
  o  0:d3873e73d99e init
      () public

  $ hg debugobsolete
  4d1169d82e47b11570c7f380790da5f89f7cabc2 98bb3a6cfe1a3d98d0959e9d42322f38313a08f3 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'operation': 'amend', 'user': 'test'}
  98bb3a6cfe1a3d98d0959e9d42322f38313a08f3 0 {d3873e73d99ef67873dac33fbcc66268d5d2b6f4} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  aa071e5554e36080a36cfd24accd5a71e3320f1e d47f2b37ed8216234c503b3a2657989958754a59 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  d47f2b37ed8216234c503b3a2657989958754a59 3d62500c673dd1c88bb09a73e86d0210aed6fcb6 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  b756eb10ea73ee4ba69c998e64a5c6e1005d74b5 2c3560aedeadb452d517b6c5a93fd3af91b3b8cd 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  2c3560aedeadb452d517b6c5a93fd3af91b3b8cd 502e737366322886cf628276aa0a2796904453b4 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  2352021b37851be226ebed109b0eb6eada918566 334e300d6db500489d842240cbdc40c203d385c7 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  334e300d6db500489d842240cbdc40c203d385c7 b1a0e143e32be800ff6a5c2cd6c77823652c901b 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  b1a0e143e32be800ff6a5c2cd6c77823652c901b 0 {502e737366322886cf628276aa0a2796904453b4} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog -r . b1a0e143e32b --all --hidden
  x  b1a0e143e32b (11) added x to x
  |    rebased(parent) from 334e300d6db5 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  |    pruned using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  334e300d6db5 (10) added x to x
  |    rebased(parent) from 2352021b3785 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  @  2352021b3785 (9) added x to x
  

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 2352021b37851be226ebed109b0eb6eada918566
  # Parent  502e737366322886cf628276aa0a2796904453b4
  added x to x
  
  diff -r 502e73736632 -r 2352021b3785 x
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/x	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +x

divergence with parent+content change both, no conflict
=======================================================

Creating divergence with parent cand content change both but not resulting in
conflicts

Alice is tired of pushing and pulling and will create phase-divergence locally

  $ hg glog
  @  9:2352021b3785 added x to x
  |   (bm) public
  o  8:502e73736632 phase-divergent update to b756eb10ea73:
  |   () public
  o  6:b756eb10ea73 added bar to bar
  |   () public
  o  5:3d62500c673d phase-divergent update to aa071e5554e3:
  |   () public
  o  3:aa071e5554e3 added foo to foo
  |   () public
  o  1:4d1169d82e47 modify a
  |   () public
  o  0:d3873e73d99e init
      () public

  $ echo y > y
  $ echo foobar >> foo
  $ hg add y
  $ hg ci -m "y to y and foobar to foo"
  $ hg rebase -r . -d .^^^
  rebasing 12:dc88f5aa9bc9 tip "y to y and foobar to foo"

  $ echo foo > y
  $ hg amend

Alice making the old changeset public to have content-divergence

  $ hg phase -r dc88f5aa9bc9 --public --hidden
  1 new phase-divergent changesets
  $ hg glog
  @  14:13015a180eee y to y and foobar to foo
  |   () draft
  | o  12:dc88f5aa9bc9 y to y and foobar to foo
  | |   () public
  | o  9:2352021b3785 added x to x
  | |   (bm) public
  | o  8:502e73736632 phase-divergent update to b756eb10ea73:
  |/    () public
  o  6:b756eb10ea73 added bar to bar
  |   () public
  o  5:3d62500c673d phase-divergent update to aa071e5554e3:
  |   () public
  o  3:aa071e5554e3 added foo to foo
  |   () public
  o  1:4d1169d82e47 modify a
  |   () public
  o  0:d3873e73d99e init
      () public

  $ hg debugobsolete
  4d1169d82e47b11570c7f380790da5f89f7cabc2 98bb3a6cfe1a3d98d0959e9d42322f38313a08f3 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'operation': 'amend', 'user': 'test'}
  98bb3a6cfe1a3d98d0959e9d42322f38313a08f3 0 {d3873e73d99ef67873dac33fbcc66268d5d2b6f4} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  aa071e5554e36080a36cfd24accd5a71e3320f1e d47f2b37ed8216234c503b3a2657989958754a59 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  d47f2b37ed8216234c503b3a2657989958754a59 3d62500c673dd1c88bb09a73e86d0210aed6fcb6 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  b756eb10ea73ee4ba69c998e64a5c6e1005d74b5 2c3560aedeadb452d517b6c5a93fd3af91b3b8cd 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  2c3560aedeadb452d517b6c5a93fd3af91b3b8cd 502e737366322886cf628276aa0a2796904453b4 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  2352021b37851be226ebed109b0eb6eada918566 334e300d6db500489d842240cbdc40c203d385c7 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  334e300d6db500489d842240cbdc40c203d385c7 b1a0e143e32be800ff6a5c2cd6c77823652c901b 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  b1a0e143e32be800ff6a5c2cd6c77823652c901b 0 {502e737366322886cf628276aa0a2796904453b4} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  dc88f5aa9bc90a6418899d267d9524205dfb429b 211ab84d1689507465ecf708fea540e9867d5fda 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  211ab84d1689507465ecf708fea540e9867d5fda 13015a180eee523ba9950f18683762a77f560f3d 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  $ hg obslog -r .
  @  13015a180eee (14) y to y and foobar to foo
  |    amended(content) from 211ab84d1689 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  211ab84d1689 (13) y to y and foobar to foo
  |    rebased(parent) from dc88f5aa9bc9 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  o  dc88f5aa9bc9 (12) y to y and foobar to foo
  
Resolving divergence using `hg evolve`
-------------------------------------

  $ hg evolve --phase-divergent --update
  recreate:[14] y to y and foobar to foo
  atop:[12] y to y and foobar to foo
  rebasing to destination parent: 2352021b3785
  committed as ec66af49a1a6
  working directory is now at ec66af49a1a6

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID ec66af49a1a643ef308fe11697c59c4920d2bd9e
  # Parent  dc88f5aa9bc90a6418899d267d9524205dfb429b
  phase-divergent update to dc88f5aa9bc9:
  
  y to y and foobar to foo
  
  diff -r dc88f5aa9bc9 -r ec66af49a1a6 y
  --- a/y	Thu Jan 01 00:00:00 1970 +0000
  +++ b/y	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -y
  +foo

  $ hg glog
  @  16:ec66af49a1a6 phase-divergent update to dc88f5aa9bc9:
  |   () draft
  o  12:dc88f5aa9bc9 y to y and foobar to foo
  |   () public
  o  9:2352021b3785 added x to x
  |   (bm) public
  o  8:502e73736632 phase-divergent update to b756eb10ea73:
  |   () public
  o  6:b756eb10ea73 added bar to bar
  |   () public
  o  5:3d62500c673d phase-divergent update to aa071e5554e3:
  |   () public
  o  3:aa071e5554e3 added foo to foo
  |   () public
  o  1:4d1169d82e47 modify a
  |   () public
  o  0:d3873e73d99e init
      () public

divergence with parent+content change both, with conflict
=========================================================

Creating divergence with parent and content change both which results in
conflicts while rebasing on parent

  $ echo l > l
  $ hg ci -Aqm "added l to l"
  $ hg rebase -r . -d .^^^^
  rebasing 17:c7c3e834e653 tip "added l to l"
  $ echo kl > l
  $ echo foo > x
  $ hg add x
  $ hg amend

  $ hg debugobsolete
  4d1169d82e47b11570c7f380790da5f89f7cabc2 98bb3a6cfe1a3d98d0959e9d42322f38313a08f3 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '1', 'operation': 'amend', 'user': 'test'}
  98bb3a6cfe1a3d98d0959e9d42322f38313a08f3 0 {d3873e73d99ef67873dac33fbcc66268d5d2b6f4} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  aa071e5554e36080a36cfd24accd5a71e3320f1e d47f2b37ed8216234c503b3a2657989958754a59 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  d47f2b37ed8216234c503b3a2657989958754a59 3d62500c673dd1c88bb09a73e86d0210aed6fcb6 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  b756eb10ea73ee4ba69c998e64a5c6e1005d74b5 2c3560aedeadb452d517b6c5a93fd3af91b3b8cd 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  2c3560aedeadb452d517b6c5a93fd3af91b3b8cd 502e737366322886cf628276aa0a2796904453b4 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  2352021b37851be226ebed109b0eb6eada918566 334e300d6db500489d842240cbdc40c203d385c7 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  334e300d6db500489d842240cbdc40c203d385c7 b1a0e143e32be800ff6a5c2cd6c77823652c901b 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  b1a0e143e32be800ff6a5c2cd6c77823652c901b 0 {502e737366322886cf628276aa0a2796904453b4} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'evolve', 'user': 'test'}
  dc88f5aa9bc90a6418899d267d9524205dfb429b 211ab84d1689507465ecf708fea540e9867d5fda 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  211ab84d1689507465ecf708fea540e9867d5fda 13015a180eee523ba9950f18683762a77f560f3d 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  13015a180eee523ba9950f18683762a77f560f3d 7c9c658a311a5194f4826f91ae667b151263d192 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  7c9c658a311a5194f4826f91ae667b151263d192 ec66af49a1a643ef308fe11697c59c4920d2bd9e 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  c7c3e834e6538706672e2b5387a27efda6e0f00f 5c0ff97e7b93a7510a08eaf8ae3821448255963d 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'rebase', 'user': 'test'}
  5c0ff97e7b93a7510a08eaf8ae3821448255963d 4c2ba1e0fc47842138814c7e5dc64392bdf2d70e 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  $ hg obslog -r .
  @  4c2ba1e0fc47 (19) added l to l
  |    amended(content) from 5c0ff97e7b93 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  5c0ff97e7b93 (18) added l to l
  |    rebased(parent) from c7c3e834e653 using rebase by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  x  c7c3e834e653 (17) added l to l
  

  $ hg phase -r c7c3e834e653 --public --hidden
  1 new phase-divergent changesets

Resolution using `hg evolve --phase-divergent`
----------------------------------------------

  $ hg evolve --phase-divergent --update
  recreate:[19] added l to l
  atop:[17] added l to l
  rebasing to destination parent: ec66af49a1a6
  merging x
  warning: conflicts while merging x! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

  $ hg diff
  diff -r ec66af49a1a6 l
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/l	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +kl
  diff -r ec66af49a1a6 x
  --- a/x	Thu Jan 01 00:00:00 1970 +0000
  +++ b/x	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,5 @@
  +<<<<<<< destination: ec66af49a1a6 - test: phase-divergent update to dc88f5aa9...
   x
  +=======
  +foo
  +>>>>>>> evolving:    4c2ba1e0fc47 - test: added l to l

  $ echo foo > x

  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue

  $ hg evolve --continue
  evolving 19:4c2ba1e0fc47 "added l to l"
  committed as 4a3e0e3f88ca
  working directory is now at 4a3e0e3f88ca

  $ hg glog
  @  21:4a3e0e3f88ca phase-divergent update to c7c3e834e653:
  |   () draft
  o  17:c7c3e834e653 added l to l
  |   () public
  o  16:ec66af49a1a6 phase-divergent update to dc88f5aa9bc9:
  |   () public
  o  12:dc88f5aa9bc9 y to y and foobar to foo
  |   () public
  o  9:2352021b3785 added x to x
  |   (bm) public
  o  8:502e73736632 phase-divergent update to b756eb10ea73:
  |   () public
  o  6:b756eb10ea73 added bar to bar
  |   () public
  o  5:3d62500c673d phase-divergent update to aa071e5554e3:
  |   () public
  o  3:aa071e5554e3 added foo to foo
  |   () public
  o  1:4d1169d82e47 modify a
  |   () public
  o  0:d3873e73d99e init
      () public

  $ hg exp
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 4a3e0e3f88ca7c24f3b9f54abfbb49a314fe4c0b
  # Parent  c7c3e834e6538706672e2b5387a27efda6e0f00f
  phase-divergent update to c7c3e834e653:
  
  added l to l
  
  diff -r c7c3e834e653 -r 4a3e0e3f88ca l
  --- a/l	Thu Jan 01 00:00:00 1970 +0000
  +++ b/l	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -l
  +kl
  diff -r c7c3e834e653 -r 4a3e0e3f88ca x
  --- a/x	Thu Jan 01 00:00:00 1970 +0000
  +++ b/x	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -x
  +foo

Creating phase divergence when couple of changesets are folded into one
------------------------------------------------------------------------

  $ hg glog -r .
  @  21:4a3e0e3f88ca phase-divergent update to c7c3e834e653:
  |   () draft
  ~
  $ echo f > f
  $ hg ci -Aqm "added f"
  $ echo g > g
  $ hg ci -Aqm "added g"

  $ hg fold -r . -r .^ --exact
  2 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ hg evolve --list

  $ hg phase -r 898734e41932 --public --hidden
  1 new phase-divergent changesets

  $ hg glog -r c7c3e834e653::
  @  24:5dfcf4a7c095 added f
  |   () draft
  | o  23:898734e41932 added g
  | |   () public
  | o  22:54c60ee8ecb8 added f
  |/    () public
  o  21:4a3e0e3f88ca phase-divergent update to c7c3e834e653:
  |   () public
  o  17:c7c3e834e653 added l to l
  |   () public
  ~

  $ hg evolve --list
  5dfcf4a7c095: added f
    phase-divergent: 54c60ee8ecb8 (immutable precursor)
    phase-divergent: 898734e41932 (immutable precursor)
  
Resolving phase divergence using `hg evolve`

  $ hg evolve --phase-divergent --all
  recreate:[24] added f
  atop:[23] added g
  rebasing to destination parent: 54c60ee8ecb8
  no changes to commit
  working directory is now at 4a3e0e3f88ca

  $ hg glog -r c7c3e834e653::
  o  23:898734e41932 added g
  |   () public
  o  22:54c60ee8ecb8 added f
  |   () public
  @  21:4a3e0e3f88ca phase-divergent update to c7c3e834e653:
  |   () public
  o  17:c7c3e834e653 added l to l
  |   () public
  ~

When the public changesets is split causing phase-divergence
------------------------------------------------------------

  $ cd ../split

  $ echo m > m
  $ echo n > n
  $ hg ci -Aqm "added m and n"

  $ hg glog
  @  1:a51bce62c219 added m and n
  |   () draft
  o  0:d3873e73d99e init
      () public

  $ hg prev
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  [0] init
  $ echo m > m
  $ hg ci -Aqm "added m"
  $ echo n > n
  $ hg ci -Aqm "added n"

  $ hg glog
  @  3:e1154ec0206a added n
  |   () draft
  o  2:4f25cd9cd2bf added m
  |   () draft
  | o  1:a51bce62c219 added m and n
  |/    () draft
  o  0:d3873e73d99e init
      () public

  $ hg prune -r a51bce62c219 --succ 4f25cd9cd2bf --succ e1154ec0206a --split
  1 changesets pruned

  $ hg phase -r a51bce62c219 --hidden --public
  2 new phase-divergent changesets

  $ hg glog
  @  3:e1154ec0206a added n
  |   () draft
  *  2:4f25cd9cd2bf added m
  |   () draft
  | o  1:a51bce62c219 added m and n
  |/    () public
  o  0:d3873e73d99e init
      () public

  $ hg evolve --all --phase-divergent
  recreate:[2] added m
  atop:[1] added m and n
  committed as 86419909e017
  recreate:[3] added n
  atop:[1] added m and n
  rebasing to destination parent: d3873e73d99e
  committed as 89ba615ea1ec
  working directory is now at 89ba615ea1ec

XXX: this is messy, we should solve things in better way
  $ hg glog --hidden
  @  6:89ba615ea1ec phase-divergent update to a51bce62c219:
  |   () draft
  | x  5:ee4af146c5cf added n
  | |   () draft
  +---o  4:86419909e017 phase-divergent update to a51bce62c219:
  | |     () draft
  | | x  3:e1154ec0206a added n
  | | |   () draft
  | | x  2:4f25cd9cd2bf added m
  | |/    () draft
  o |  1:a51bce62c219 added m and n
  |/    () public
  o  0:d3873e73d99e init
      () public

  $ hg debugobsolete
  a51bce62c219f024bc0ae0cc0e3957ee77d7cb46 4f25cd9cd2bf15bc83316e91fbcb93489ea15a75 e1154ec0206ac05c3765f7bd1337e3b96db2974f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'prune', 'user': 'test'}
  4f25cd9cd2bf15bc83316e91fbcb93489ea15a75 86419909e01787959aa6471aee605c6d604a3e0d 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  e1154ec0206ac05c3765f7bd1337e3b96db2974f ee4af146c5cfe0b1bf7665243dd89f9bfe604f59 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  ee4af146c5cfe0b1bf7665243dd89f9bfe604f59 89ba615ea1ec3ba5b25db9f7897eb29712d7e5d6 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog -r a51bce62c219 --all
  o  86419909e017 (4) phase-divergent update to a51bce62c219:
  |    rewritten(description, parent, content) from 4f25cd9cd2bf using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  | @  89ba615ea1ec (6) phase-divergent update to a51bce62c219:
  | |    rewritten(description, parent, content) from ee4af146c5cf using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  4f25cd9cd2bf (2) added m
  | |    split(description, parent, content) from a51bce62c219 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  ee4af146c5cf (5) added n
  | |    rebased(parent) from e1154ec0206a using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  e1154ec0206a (3) added n
  |/     split(description, parent, content) from a51bce62c219 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  o  a51bce62c219 (1) added m and n
  

XXX: not sure this is the correct
  $ hg exp 89ba615ea1ec
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 89ba615ea1ec3ba5b25db9f7897eb29712d7e5d6
  # Parent  a51bce62c219f024bc0ae0cc0e3957ee77d7cb46
  phase-divergent update to a51bce62c219:
  
  added n
  
  diff -r a51bce62c219 -r 89ba615ea1ec m
  --- a/m	Thu Jan 01 00:00:00 1970 +0000
  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +0,0 @@
  -m

XXX: not sure this is correct
  $ hg exp 86419909e017
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 86419909e01787959aa6471aee605c6d604a3e0d
  # Parent  a51bce62c219f024bc0ae0cc0e3957ee77d7cb46
  phase-divergent update to a51bce62c219:
  
  added m
  
  diff -r a51bce62c219 -r 86419909e017 n
  --- a/n	Thu Jan 01 00:00:00 1970 +0000
  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +0,0 @@
  -n

When the public changeset is split across various topological branches
======================================================================

  $ cd ../split-across-branches

  $ echo p > p
  $ echo q > q
  $ hg ci -Aqm "added p and q"

  $ hg prev
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  [0] init
  $ echo p > p
  $ hg ci -Aqm "added p"
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [0] init
  $ echo q > q
  $ hg ci -Aqm "added q"

  $ hg glog
  @  3:bb87595f9a77 added q
  |   () draft
  | o  2:a47263294745 added p
  |/    () draft
  | o  1:90859808ece6 added p and q
  |/    () draft
  o  0:d3873e73d99e init
      () public

  $ hg prune -r 90859808ece6 --succ a47263294745 --succ bb87595f9a77 --split
  1 changesets pruned

  $ hg phase -r 90859808ece6 --public --hidden
  2 new phase-divergent changesets

  $ hg glog
  @  3:bb87595f9a77 added q
  |   () draft
  | *  2:a47263294745 added p
  |/    () draft
  | o  1:90859808ece6 added p and q
  |/    () public
  o  0:d3873e73d99e init
      () public

  $ hg evolve --list
  a47263294745: added p
    phase-divergent: 90859808ece6 (immutable precursor)
  
  bb87595f9a77: added q
    phase-divergent: 90859808ece6 (immutable precursor)
  
  $ hg evolve --all --phase-divergent
  recreate:[2] added p
  atop:[1] added p and q
  committed as 25875a9cb640
  recreate:[3] added q
  atop:[1] added p and q
  committed as 26f564f94bcc
  working directory is now at 26f564f94bcc

  $ hg glog --hidden
  @  5:26f564f94bcc phase-divergent update to 90859808ece6:
  |   () draft
  | o  4:25875a9cb640 phase-divergent update to 90859808ece6:
  |/    () draft
  | x  3:bb87595f9a77 added q
  | |   () draft
  | | x  2:a47263294745 added p
  | |/    () draft
  o |  1:90859808ece6 added p and q
  |/    () public
  o  0:d3873e73d99e init
      () public

  $ hg debugobsolete
  90859808ece64c9ca64dd29992db42353c70f164 a472632947451d2e52659aec3088c98ddf920f2b bb87595f9a77d7d1e4a8726beef266a1636f63d5 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'prune', 'user': 'test'}
  a472632947451d2e52659aec3088c98ddf920f2b 25875a9cb6400973b846c94f6a80410067c2cb1f 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  bb87595f9a77d7d1e4a8726beef266a1636f63d5 26f564f94bcc34e049eb112fd14ab1e5286f2325 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog -r 90859808ece6 --all
  o  25875a9cb640 (4) phase-divergent update to 90859808ece6:
  |    rewritten(description, parent, content) from a47263294745 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  | @  26f564f94bcc (5) phase-divergent update to 90859808ece6:
  | |    rewritten(description, parent, content) from bb87595f9a77 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  a47263294745 (2) added p
  | |    split(description, content) from 90859808ece6 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  bb87595f9a77 (3) added q
  |/     split(description, content) from 90859808ece6 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  o  90859808ece6 (1) added p and q
  

XXX: not sure this is correct
  $ hg exp 26f564f94bcc
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 26f564f94bcc34e049eb112fd14ab1e5286f2325
  # Parent  90859808ece64c9ca64dd29992db42353c70f164
  phase-divergent update to 90859808ece6:
  
  added q
  
  diff -r 90859808ece6 -r 26f564f94bcc p
  --- a/p	Thu Jan 01 00:00:00 1970 +0000
  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +0,0 @@
  -p

XXX: not sure this is correct
  $ hg exp 25875a9cb640
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 25875a9cb6400973b846c94f6a80410067c2cb1f
  # Parent  90859808ece64c9ca64dd29992db42353c70f164
  phase-divergent update to 90859808ece6:
  
  added p
  
  diff -r 90859808ece6 -r 25875a9cb640 q
  --- a/q	Thu Jan 01 00:00:00 1970 +0000
  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +0,0 @@
  -q

When the public changeset is split and amended
==============================================

  $ cd ../split-and-amend

  $ echo m > m
  $ echo n > n
  $ hg ci -Aqm "added m and n"
  $ hg prev
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  [0] init
  $ echo m > m
  $ hg ci -Aqm "added m"
  $ echo n > n
  $ hg ci -Aqm "added n"

  $ hg glog
  @  3:e1154ec0206a added n
  |   () draft
  o  2:4f25cd9cd2bf added m
  |   () draft
  | o  1:a51bce62c219 added m and n
  |/    () draft
  o  0:d3873e73d99e init
      () public

  $ hg prune -r a51bce62c219 --succ 4f25cd9cd2bf --succ e1154ec0206a --split
  1 changesets pruned

  $ echo n2 > n
  $ hg amend

  $ hg phase -r a51bce62c219 --public --hidden
  2 new phase-divergent changesets

  $ hg glog
  @  4:52ca78bb98c7 added n
  |   () draft
  *  2:4f25cd9cd2bf added m
  |   () draft
  | o  1:a51bce62c219 added m and n
  |/    () public
  o  0:d3873e73d99e init
      () public

  $ hg evolve --list
  4f25cd9cd2bf: added m
    phase-divergent: a51bce62c219 (immutable precursor)
  
  52ca78bb98c7: added n
    phase-divergent: a51bce62c219 (immutable precursor)
  
  $ hg evolve --all --phase-divergent
  recreate:[2] added m
  atop:[1] added m and n
  committed as 86419909e017
  recreate:[4] added n
  atop:[1] added m and n
  rebasing to destination parent: d3873e73d99e
  committed as 0f21d47fe960
  working directory is now at 0f21d47fe960

  $ hg glog --hidden
  @  7:0f21d47fe960 phase-divergent update to a51bce62c219:
  |   () draft
  | x  6:302a3ecef922 added n
  | |   () draft
  +---o  5:86419909e017 phase-divergent update to a51bce62c219:
  | |     () draft
  | | x  4:52ca78bb98c7 added n
  | | |   () draft
  | | | x  3:e1154ec0206a added n
  | | |/    () draft
  | | x  2:4f25cd9cd2bf added m
  | |/    () draft
  o |  1:a51bce62c219 added m and n
  |/    () public
  o  0:d3873e73d99e init
      () public

  $ hg debugobsolete
  a51bce62c219f024bc0ae0cc0e3957ee77d7cb46 4f25cd9cd2bf15bc83316e91fbcb93489ea15a75 e1154ec0206ac05c3765f7bd1337e3b96db2974f 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'prune', 'user': 'test'}
  e1154ec0206ac05c3765f7bd1337e3b96db2974f 52ca78bb98c71222f8afae28d48ae6cfd44a60c9 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '8', 'operation': 'amend', 'user': 'test'}
  4f25cd9cd2bf15bc83316e91fbcb93489ea15a75 86419909e01787959aa6471aee605c6d604a3e0d 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  52ca78bb98c71222f8afae28d48ae6cfd44a60c9 302a3ecef922d617073b8e96d3e0f15ab7a6d30d 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'evolve', 'user': 'test'}
  302a3ecef922d617073b8e96d3e0f15ab7a6d30d 0f21d47fe96059e134fd230d6d1623ff1d541963 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog -r a51bce62c219 --all
  @  0f21d47fe960 (7) phase-divergent update to a51bce62c219:
  |    rewritten(description, parent, content) from 302a3ecef922 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  | o  86419909e017 (5) phase-divergent update to a51bce62c219:
  | |    rewritten(description, parent, content) from 4f25cd9cd2bf using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  302a3ecef922 (6) added n
  | |    rebased(parent) from 52ca78bb98c7 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  | x  4f25cd9cd2bf (2) added m
  | |    split(description, parent, content) from a51bce62c219 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  52ca78bb98c7 (4) added n
  | |    amended(content) from e1154ec0206a using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  | |
  x |  e1154ec0206a (3) added n
  |/     split(description, parent, content) from a51bce62c219 using prune by test (Thu Jan 01 00:00:00 1970 +0000)
  |
  o  a51bce62c219 (1) added m and n
  

XXX: not sure this is correct
  $ hg exp 86419909e017
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 86419909e01787959aa6471aee605c6d604a3e0d
  # Parent  a51bce62c219f024bc0ae0cc0e3957ee77d7cb46
  phase-divergent update to a51bce62c219:
  
  added m
  
  diff -r a51bce62c219 -r 86419909e017 n
  --- a/n	Thu Jan 01 00:00:00 1970 +0000
  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +0,0 @@
  -n

XXX: not sure this is correct
  $ hg exp 0f21d47fe960
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 0f21d47fe96059e134fd230d6d1623ff1d541963
  # Parent  a51bce62c219f024bc0ae0cc0e3957ee77d7cb46
  phase-divergent update to a51bce62c219:
  
  added n
  
  diff -r a51bce62c219 -r 0f21d47fe960 m
  --- a/m	Thu Jan 01 00:00:00 1970 +0000
  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +0,0 @@
  -m
  diff -r a51bce62c219 -r 0f21d47fe960 n
  --- a/n	Thu Jan 01 00:00:00 1970 +0000
  +++ b/n	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -n
  +n2

Testing the evolution of a phase-divergent merge with no conflicts
==================================================================

  $ cd ../merge-no-conflict

  $ echo h > h
  $ hg ci -Aqm "added h"
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [0] init
  $ echo i > i
  $ hg ci -Aqm "added i"
  $ hg merge -r a53d182199c1
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "merge h and i"

  $ hg glog
  @    3:205b2f5ecb7b merge h and i
  |\    () draft
  | o  2:f0be5e638ecf added i
  | |   () draft
  o |  1:a53d182199c1 added h
  |/    () draft
  o  0:d3873e73d99e init
      () public

  $ hg up a53d182199c1
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg merge -r f0be5e638ecf
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "merge h and i successor"
  created new head
  $ hg glog
  @    4:8d4acf488ab5 merge h and i successor
  |\    () draft
  +---o  3:205b2f5ecb7b merge h and i
  | |/    () draft
  | o  2:f0be5e638ecf added i
  | |   () draft
  o |  1:a53d182199c1 added h
  |/    () draft
  o  0:d3873e73d99e init
      () public

  $ hg prune -r 205b2f5ecb7b --succ .
  1 changesets pruned

  $ hg phase 205b2f5ecb7b --hidden --public
  1 new phase-divergent changesets

Resolution of phase-divergent merge commit using `hg evolve`

XXX: we should handle phase-divergent merges
  $ hg evolve --phase-divergent
  skipping 8d4acf488ab5 : we do not handle merge yet

Check we preserve "cancelation" of changes
==========================================

This tests case where the phase divergence changesets cancelled some of the
change made by the public predecessors. The cancellation of these changes need
to be preserved.

  $ hg init cancelled-changes
  $ cd cancelled-changes
  $ cat << EOF > .hg/hgrc
  > [diff]
  > word-diff = yes
  > EOF
  $ cat << EOF > numbers
  > 1
  > 2
  > 3
  > 4
  > 5
  > 6
  > 7
  > 8
  > 9
  > EOF
  $ cat << EOF > letters
  > a
  > b
  > c
  > d
  > e
  > f
  > g
  > h
  > i
  > EOF
  $ cat << EOF > romans
  > I
  > II
  > III
  > IV
  > V
  > VI
  > VII
  > VIII
  > IX
  > EOF
  $ hg add numbers letters romans
  $ hg commit -m root
  $ cat << EOF > numbers
  > 1
  > 2
  > 3
  > four
  > 5
  > 6
  > 7
  > 8
  > nine
  > EOF
  $ cat << EOF > letters
  > a
  > b
  > c
  > D
  > e
  > f
  > g
  > h
  > i
  > EOF
  $ hg commit -m E1
  $ cat << EOF > numbers
  > 1
  > 2
  > 3
  > 4
  > 5
  > 6
  > seven
  > 8
  > nine
  > EOF
  $ cat << EOF > letters
  > a
  > b
  > c
  > d
  > e
  > f
  > g
  > h
  > i
  > EOF
  $ cat << EOF > romans
  > I
  > ii
  > III
  > IV
  > V
  > VI
  > VII
  > VIII
  > IX
  > EOF
  $ hg commit --amend -m E2
  $ hg --hidden phase --public --rev 'desc(E1)'
  1 new phase-divergent changesets
  $ hg log -G --patch --hidden --rev 'not desc("root")'
  @  changeset:   2:599454370881
  |  tag:         tip
  ~  parent:      0:6d1fdf6de7e2
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     instability: phase-divergent
     summary:     E2
  
     diff -r 6d1fdf6de7e2 -r 599454370881 numbers
     --- a/numbers	Thu Jan 01 00:00:00 1970 +0000
     +++ b/numbers	Thu Jan 01 00:00:00 1970 +0000
     @@ -4,6 +4,6 @@
      4
      5
      6
     -7
     +seven
      8
     -9
     +nine
     diff -r 6d1fdf6de7e2 -r 599454370881 romans
     --- a/romans	Thu Jan 01 00:00:00 1970 +0000
     +++ b/romans	Thu Jan 01 00:00:00 1970 +0000
     @@ -1,5 +1,5 @@
      I
     -II
     +ii
      III
      IV
      V
  
  o  changeset:   1:3074c7249d20
  |  user:        test
  ~  date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     E1
  
     diff -r 6d1fdf6de7e2 -r 3074c7249d20 letters
     --- a/letters	Thu Jan 01 00:00:00 1970 +0000
     +++ b/letters	Thu Jan 01 00:00:00 1970 +0000
     @@ -1,7 +1,7 @@
      a
      b
      c
     -d
     +D
      e
      f
      g
     diff -r 6d1fdf6de7e2 -r 3074c7249d20 numbers
     --- a/numbers	Thu Jan 01 00:00:00 1970 +0000
     +++ b/numbers	Thu Jan 01 00:00:00 1970 +0000
     @@ -1,9 +1,9 @@
      1
      2
      3
     -4
     +four
      5
      6
      7
      8
     -9
     +nine
  
  $ hg evolve --list
  599454370881: E2
    phase-divergent: 3074c7249d20 (immutable precursor)
  
  $ hg debugobsolete
  3074c7249d2023b1fff891591d7e609695cd09c2 59945437088136c5fa2f9bb8573d5d02623fe7cb 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  $ hg obslog --all --patch
  @  599454370881 (2) E2
  |    rewritten(description, content) from 3074c7249d20 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 3074c7249d20 -r 599454370881 changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -E1
  |      +E2
  |
  |      diff -r 3074c7249d20 -r 599454370881 letters
  |      --- a/letters	Thu Jan 01 00:00:00 1970 +0000
  |      +++ b/letters	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,7 +1,7 @@
  |       a
  |       b
  |       c
  |      -D
  |      +d
  |       e
  |       f
  |       g
  |      diff -r 3074c7249d20 -r 599454370881 numbers
  |      --- a/numbers	Thu Jan 01 00:00:00 1970 +0000
  |      +++ b/numbers	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,9 +1,9 @@
  |       1
  |       2
  |       3
  |      -four
  |      +4
  |       5
  |       6
  |      -7
  |      +seven
  |       8
  |       nine
  |      diff -r 3074c7249d20 -r 599454370881 romans
  |      --- a/romans	Thu Jan 01 00:00:00 1970 +0000
  |      +++ b/romans	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,5 +1,5 @@
  |       I
  |      -II
  |      +ii
  |       III
  |       IV
  |       V
  |
  |
  o  3074c7249d20 (1) E1
  

  $ hg evolve --phase-divergent --rev 'desc("E2")'
  recreate:[2] E2
  atop:[1] E1
  committed as 9eebcb77a7e2
  working directory is now at 9eebcb77a7e2
  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Node ID 9eebcb77a7e2b240cb7dce095bbe608b5de91cc8
  # Parent  3074c7249d2023b1fff891591d7e609695cd09c2
  phase-divergent update to 3074c7249d20:
  
  E2
  
  diff -r 3074c7249d20 -r 9eebcb77a7e2 letters
  --- a/letters	Thu Jan 01 00:00:00 1970 +0000
  +++ b/letters	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,7 +1,7 @@
   a
   b
   c
  -D
  +d
   e
   f
   g
  diff -r 3074c7249d20 -r 9eebcb77a7e2 numbers
  --- a/numbers	Thu Jan 01 00:00:00 1970 +0000
  +++ b/numbers	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,9 +1,9 @@
   1
   2
   3
  -four
  +4
   5
   6
  -7
  +seven
   8
   nine
  diff -r 3074c7249d20 -r 9eebcb77a7e2 romans
  --- a/romans	Thu Jan 01 00:00:00 1970 +0000
  +++ b/romans	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,5 +1,5 @@
   I
  -II
  +ii
   III
   IV
   V
  $ hg log -G --patch --rev 'not desc("root")'
  @  changeset:   3:9eebcb77a7e2
  |  tag:         tip
  |  parent:      1:3074c7249d20
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     phase-divergent update to 3074c7249d20:
  |
  |  diff -r 3074c7249d20 -r 9eebcb77a7e2 letters
  |  --- a/letters	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/letters	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -1,7 +1,7 @@
  |   a
  |   b
  |   c
  |  -D
  |  +d
  |   e
  |   f
  |   g
  |  diff -r 3074c7249d20 -r 9eebcb77a7e2 numbers
  |  --- a/numbers	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/numbers	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -1,9 +1,9 @@
  |   1
  |   2
  |   3
  |  -four
  |  +4
  |   5
  |   6
  |  -7
  |  +seven
  |   8
  |   nine
  |  diff -r 3074c7249d20 -r 9eebcb77a7e2 romans
  |  --- a/romans	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/romans	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -1,5 +1,5 @@
  |   I
  |  -II
  |  +ii
  |   III
  |   IV
  |   V
  |
  o  changeset:   1:3074c7249d20
  |  user:        test
  ~  date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     E1
  
     diff -r 6d1fdf6de7e2 -r 3074c7249d20 letters
     --- a/letters	Thu Jan 01 00:00:00 1970 +0000
     +++ b/letters	Thu Jan 01 00:00:00 1970 +0000
     @@ -1,7 +1,7 @@
      a
      b
      c
     -d
     +D
      e
      f
      g
     diff -r 6d1fdf6de7e2 -r 3074c7249d20 numbers
     --- a/numbers	Thu Jan 01 00:00:00 1970 +0000
     +++ b/numbers	Thu Jan 01 00:00:00 1970 +0000
     @@ -1,9 +1,9 @@
      1
      2
      3
     -4
     +four
      5
      6
      7
      8
     -9
     +nine
  
  $ hg debugobsolete
  3074c7249d2023b1fff891591d7e609695cd09c2 59945437088136c5fa2f9bb8573d5d02623fe7cb 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '9', 'operation': 'amend', 'user': 'test'}
  59945437088136c5fa2f9bb8573d5d02623fe7cb 9eebcb77a7e2b240cb7dce095bbe608b5de91cc8 1 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '13', 'operation': 'evolve', 'user': 'test'}
  $ hg obslog --patch
  @  9eebcb77a7e2 (3) phase-divergent update to 3074c7249d20:
  |    rewritten(description, parent, content) from 599454370881 using evolve by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 599454370881+ -r 9eebcb77a7e2 changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,3 @@
  |      +phase-divergent update to 3074c7249d20:
  |      +
  |       E2
  |
  |      diff -r 9eebcb77a7e2 letters
  |      --- a/letters	Thu Jan 01 00:00:00 1970 +0000
  |      +++ b/letters	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,7 +1,7 @@
  |       a
  |       b
  |       c
  |      -D
  |      +d
  |       e
  |       f
  |       g
  |      diff -r 9eebcb77a7e2 numbers
  |      --- a/numbers	Thu Jan 01 00:00:00 1970 +0000
  |      +++ b/numbers	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,7 +1,7 @@
  |       1
  |       2
  |       3
  |      -four
  |      +4
  |       5
  |       6
  |       seven
  |
  |
  x  599454370881 (2) E2
  |    rewritten(description, content) from 3074c7249d20 using amend by test (Thu Jan 01 00:00:00 1970 +0000)
  |      diff -r 3074c7249d20 -r 599454370881 changeset-description
  |      --- a/changeset-description
  |      +++ b/changeset-description
  |      @@ -1,1 +1,1 @@
  |      -E1
  |      +E2
  |
  |      diff -r 3074c7249d20 -r 599454370881 letters
  |      --- a/letters	Thu Jan 01 00:00:00 1970 +0000
  |      +++ b/letters	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,7 +1,7 @@
  |       a
  |       b
  |       c
  |      -D
  |      +d
  |       e
  |       f
  |       g
  |      diff -r 3074c7249d20 -r 599454370881 numbers
  |      --- a/numbers	Thu Jan 01 00:00:00 1970 +0000
  |      +++ b/numbers	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,9 +1,9 @@
  |       1
  |       2
  |       3
  |      -four
  |      +4
  |       5
  |       6
  |      -7
  |      +seven
  |       8
  |       nine
  |      diff -r 3074c7249d20 -r 599454370881 romans
  |      --- a/romans	Thu Jan 01 00:00:00 1970 +0000
  |      +++ b/romans	Thu Jan 01 00:00:00 1970 +0000
  |      @@ -1,5 +1,5 @@
  |       I
  |      -II
  |      +ii
  |       III
  |       IV
  |       V
  |
  |
  o  3074c7249d20 (1) E1
  
  $ cd ..

Phase divergence with file removal cancelation
==============================================

  $ hg init cancel-removal
  $ cd cancel-removal
  $ echo a > a
  $ echo b > b
  $ echo c > c
  $ echo d > d
  $ hg ci -Aqm initial

Oops, we meant to delete just 'a', but we deleted 'b' and 'c' too

  $ hg rm a b c
  $ hg ci -m 'delete a'
  $ hg revert -r .^ b
  $ hg amend
  $ hg glog --hidden --patch
  @  2:0825dcee2670 delete a
  |   () draftdiff -r 75d2b02c4a5c -r 0825dcee2670 a
  |  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  |  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -1,1 +0,0 @@
  |  -a
  |  diff -r 75d2b02c4a5c -r 0825dcee2670 c
  |  --- a/c	Thu Jan 01 00:00:00 1970 +0000
  |  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -1,1 +0,0 @@
  |  -c
  |
  | x  1:dff6e52f5e41 delete a
  |/    () draftdiff -r 75d2b02c4a5c -r dff6e52f5e41 a
  |    --- a/a	Thu Jan 01 00:00:00 1970 +0000
  |    +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |    @@ -1,1 +0,0 @@
  |    -a
  |    diff -r 75d2b02c4a5c -r dff6e52f5e41 b
  |    --- a/b	Thu Jan 01 00:00:00 1970 +0000
  |    +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |    @@ -1,1 +0,0 @@
  |    -b
  |    diff -r 75d2b02c4a5c -r dff6e52f5e41 c
  |    --- a/c	Thu Jan 01 00:00:00 1970 +0000
  |    +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |    @@ -1,1 +0,0 @@
  |    -c
  |
  o  0:75d2b02c4a5c initial
      () draftdiff -r 000000000000 -r 75d2b02c4a5c a
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/a	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +a
     diff -r 000000000000 -r 75d2b02c4a5c b
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/b	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +b
     diff -r 000000000000 -r 75d2b02c4a5c c
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/c	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +c
     diff -r 000000000000 -r 75d2b02c4a5c d
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/d	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +d
  

The public predecessors deletes'a', 'b' and 'c',
If was amended to only delete 'a', and 'c'
so the fixup should add back 'b'.

  $ hg phase -p -r dff6e52f5e41 --hidden
  1 new phase-divergent changesets
  $ hg evolve --phase-divergent
  recreate:[2] delete a
  atop:[1] delete a
  committed as 84aa492b3c37
  working directory is now at 84aa492b3c37
  $ hg glog --patch
  @  3:84aa492b3c37 phase-divergent update to dff6e52f5e41:
  |   () draftdiff -r dff6e52f5e41 -r 84aa492b3c37 b
  |  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -0,0 +1,1 @@
  |  +b
  |
  o  1:dff6e52f5e41 delete a
  |   () publicdiff -r 75d2b02c4a5c -r dff6e52f5e41 a
  |  --- a/a	Thu Jan 01 00:00:00 1970 +0000
  |  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -1,1 +0,0 @@
  |  -a
  |  diff -r 75d2b02c4a5c -r dff6e52f5e41 b
  |  --- a/b	Thu Jan 01 00:00:00 1970 +0000
  |  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -1,1 +0,0 @@
  |  -b
  |  diff -r 75d2b02c4a5c -r dff6e52f5e41 c
  |  --- a/c	Thu Jan 01 00:00:00 1970 +0000
  |  +++ /dev/null	Thu Jan 01 00:00:00 1970 +0000
  |  @@ -1,1 +0,0 @@
  |  -c
  |
  o  0:75d2b02c4a5c initial
      () publicdiff -r 000000000000 -r 75d2b02c4a5c a
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/a	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +a
     diff -r 000000000000 -r 75d2b02c4a5c b
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/b	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +b
     diff -r 000000000000 -r 75d2b02c4a5c c
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/c	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +c
     diff -r 000000000000 -r 75d2b02c4a5c d
     --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
     +++ b/d	Thu Jan 01 00:00:00 1970 +0000
     @@ -0,0 +1,1 @@
     +d
  

  $ hg diff --change .
  diff -r dff6e52f5e41 -r 84aa492b3c37 b
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/b	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +b

