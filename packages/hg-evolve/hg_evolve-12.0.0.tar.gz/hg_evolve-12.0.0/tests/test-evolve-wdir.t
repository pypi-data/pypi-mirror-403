===============================================
Testing evolution of obsolete working directory
===============================================

Pulling changes from other repos can make your working directory parent (wdir)
obsolete, most probably because now it has a new successor. But there are
other cases as well where it might be pruned with no successors or split
in multiple changesets etc.

This test file deals with all the possible cases for the evolution from an
obsolete working directory parent.

.. Case A: obsolete wdp with single successor
..     Resolution : simply update to the successor
..
.. Case B: obsolete wdp with no successor (simply pruned)
..     Resolution : update to a not-dead ancestor
..
.. Case C: obsolete wdp with multiple successor (divergence rewriting)
..     Resolution : suggest to check out one of the divergent cset and
..                  run `hg evolve --content-divergent`
..
.. Case D: obsolete wdp with multiple successor (split rewriting)
..     Resolution : if split over a single topological branch, update to
..                  tipmost, otherwise ask user to choose one

A. Obsolete wdp with single successor
-------------------------------------

Setup
  $ . $TESTDIR/testlib/common.sh
  $ cat >> $HGRCPATH <<EOF
  > [extensions]
  > evolve=
  > rebase=
  > [alias]
  > glog = log --graph --template "{rev}:{node|short} ({phase}): {desc|firstline} {if(troubles, '[{troubles}]')}\n"
  > EOF

#testcases inmemory ondisk
#if inmemory
  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution.in-memory = yes
  > EOF
#endif

  $ hg init repo
  $ cd repo
  $ mkcommit c_A
  $ mkcommit c_B
  $ hg amend -m "u_B"
  $ hg up -r 'desc(c_B)' --hidden
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 707ee88b2870
  (hidden revision '707ee88b2870' was rewritten as: 9bf151312dec)
  working directory parent is obsolete! (707ee88b2870)
  (use 'hg evolve' to update to its successor: 9bf151312dec)

  $ hg evolve
  update:[2] u_B
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 9bf151312dec
  $ hg glog
  @  2:9bf151312dec (draft): u_B
  |
  o  0:9f0188af4c58 (draft): c_A
  

B. Obsolete wdp with no successor
---------------------------------

  $ hg prune .
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at 9f0188af4c58
  1 changesets pruned
  $ hg up -r 'desc(c_B)' --hidden
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 707ee88b2870
  (hidden revision '707ee88b2870' is pruned)
  working directory parent is obsolete! (707ee88b2870)
  (use 'hg evolve' to update to its parent successor)

  $ hg evolve
  update:[0] c_A
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at 9f0188af4c58
  $ hg glog
  @  0:9f0188af4c58 (draft): c_A
  

C. Obsolete wdp with multiple successor (divergence rewriting)
---------------------------------------------------------------

  $ hg metaedit -r 'desc(u_B)' -d '0 1' --hidden
  $ hg metaedit -r 'desc(c_B)' -d '0 1' --hidden
  2 new content-divergent changesets
  $ hg up -r 'min(desc(c_B))' --hidden
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset 707ee88b2870
  (hidden revision '707ee88b2870' has diverged)
  working directory parent is obsolete! (707ee88b2870)
  (707ee88b2870 has diverged, use 'hg evolve --list --content-divergent' to resolve the issue)

  $ hg evolve
  parent is obsolete with multiple content-divergent successors:
  [3] u_B
  [4] c_B
  [2]

test that given hint works
  $ hg up -r 'desc(u_B)'
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg evolve --content-div
  merge:[3] u_B
  with: [4] c_B
  base: [1] c_B
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 767c654afe84
  $ hg glog
  @  5:767c654afe84 (draft): u_B
  |
  o  0:9f0188af4c58 (draft): c_A
  

D. Obsolete wdp with multiple successors (split rewriting)
----------------------------------------------------------

when split csets are on a single topological branch
  $ hg up -r 'desc(c_A)'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo X > X; echo Y > Y; echo Z > Z;
  $ hg ci -Am 'c_XYZ'
  adding X
  adding Y
  adding Z
  created new head
  $ hg split -r "desc(c_XYZ)" -d "0 0" --config ui.interactive=True << EOF
  > f
  > d
  > y
  > f
  > d
  > c
  > EOF
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  adding X
  adding Y
  adding Z
  diff --git a/X b/X
  new file mode 100644
  examine changes to 'X'?
  (enter ? for help) [Ynesfdaq?] f
  
  diff --git a/Y b/Y
  new file mode 100644
  examine changes to 'Y'?
  (enter ? for help) [Ynesfdaq?] d
  
  created new head
  continue splitting? [Ycdq?] y
  diff --git a/Y b/Y
  new file mode 100644
  examine changes to 'Y'?
  (enter ? for help) [Ynesfdaq?] f
  
  diff --git a/Z b/Z
  new file mode 100644
  examine changes to 'Z'?
  (enter ? for help) [Ynesfdaq?] d
  
  continue splitting? [Ycdq?] c

  $ hg up -r 'min(desc(c_XYZ))' --hidden
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  updated to hidden changeset c8b6cf6ce628
  (hidden revision 'c8b6cf6ce628' was split as: 1eb7dbbcecbd, b99a391251cc and 1 more)
  working directory parent is obsolete! (c8b6cf6ce628)
  (use 'hg evolve' to update to its tipmost successor: 1eb7dbbcecbd, b99a391251cc and 1 more)

  $ hg glog -l 3
  o  9:b7ec9e61ccbf (draft): c_XYZ
  |
  o  8:b99a391251cc (draft): c_XYZ
  |
  o  7:1eb7dbbcecbd (draft): c_XYZ
  |
  ~
test that given hint works
  $ hg evolve
  update:[9] c_XYZ
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at b7ec9e61ccbf

when split csets are on multiple topological branches
  $ hg rebase -r 'max(desc(c_XYZ))' -d 'desc(u_B)'
  rebasing 9:b7ec9e61ccbf tip "c_XYZ"
  $ hg glog
  @  10:cadaa9246c55 (draft): c_XYZ
  |
  | o  8:b99a391251cc (draft): c_XYZ
  | |
  | o  7:1eb7dbbcecbd (draft): c_XYZ
  | |
  o |  5:767c654afe84 (draft): u_B
  |/
  o  0:9f0188af4c58 (draft): c_A
  
  $ hg up -r 'min(desc(c_XYZ))' --hidden
  2 files updated, 0 files merged, 1 files removed, 0 files unresolved
  updated to hidden changeset c8b6cf6ce628
  (hidden revision 'c8b6cf6ce628' was split as: 1eb7dbbcecbd, b99a391251cc and 1 more)
  working directory parent is obsolete! (c8b6cf6ce628)
  (use 'hg evolve' to update to its tipmost successor: 1eb7dbbcecbd, b99a391251cc and 1 more)

  $ hg evolve --config ui.interactive=True << EOF
  > q
  > EOF
  changeset c8b6cf6ce628 split over multiple topological branches, choose an evolve destination:
  1: [b99a391251cc] c_XYZ
  2: [cadaa9246c55] c_XYZ
  q: quit the prompt
  enter the index of the revision you want to select: q
  abort: user quit
  [250]

  $ hg evolve --config ui.interactive=True << EOF
  > 1
  > EOF
  changeset c8b6cf6ce628 split over multiple topological branches, choose an evolve destination:
  1: [b99a391251cc] c_XYZ
  2: [cadaa9246c55] c_XYZ
  q: quit the prompt
  enter the index of the revision you want to select: 1
  update:[8] c_XYZ
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory is now at b99a391251cc
