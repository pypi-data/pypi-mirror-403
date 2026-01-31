==================================
Test for "orphan" type instability
==================================

This file gather test case around the "orphan" changeset instability. This
instability happens when a changesets has obsolete ancestors.

  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > logtemplate = {rev}:{node|short}@{branch}({phase}) {desc|firstline}\n
  > [extensions]
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH
  $ mkcommit() {
  >    echo "$1" > "$1"
  >    hg add "$1"
  >    hg ci -m "add $1"
  > }

  $ mkstack() {
  >    # Creates a stack of commit based on $1 with messages from $2, $3 ..
  >    hg update "$1" -C
  >    shift
  >    mkcommits $*
  > }

  $ mkcommits() {
  >   for i in $@; do mkcommit $i ; done
  > }

orphan parent is obsolete with a single successor
=================================================

Test orphan resolution for a changeset orphan because its parent is obsolete
with one successor.

  $ hg init test1
  $ cd test1
  $ mkcommits _a _b _c
  $ hg up "desc(_b)"
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg amend -m "bprime"
  1 new orphan changesets
  $ hg log -G
  @  3:36050226a9b9@default(draft) bprime
  |
  | *  2:102002290587@default(draft) add _c
  | |
  | x  1:37445b16603b@default(draft) add _b
  |/
  o  0:135f39f4bd78@default(draft) add _a
  

  $ hg evolve --all --any --orphan
  move:[2] add _c
  atop:[3] bprime
  $ hg log -G
  o  4:fdcf3523a74d@default(draft) add _c
  |
  @  3:36050226a9b9@default(draft) bprime
  |
  o  0:135f39f4bd78@default(draft) add _a
  

  $ cd ..


orphan parent is obsolete with a multiple successors (reversed order)
=====================================================================

Test orphan resolution for a changeset orphan because its parent is obsolete
with multiple successors on the same branch but in reverse order (cross-split).

  $ hg init test5
  $ cd test5
  $ mkcommits _a _b _c
  $ hg up "desc(_a)"
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ mkcommits bprimesplit1 bprimesplit2
  created new head
  $ hg prune "desc(_b)" -s "desc(bprimesplit1) + desc(bprimesplit2)" --split
  1 changesets pruned
  1 new orphan changesets
  $ hg up "desc(_a)"
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ mkcommits bsecondsplit1 bsecondsplit2
  created new head
  $ hg prune "desc(bprimesplit1)" -s "desc(bsecondsplit2)"
  1 changesets pruned
  1 new orphan changesets
  $ hg prune "desc(bprimesplit2)" -s "desc(bsecondsplit1)"
  1 changesets pruned
  $ hg log -G
  @  6:59b942dbda14@default(draft) add bsecondsplit2
  |
  o  5:8ffdae67d696@default(draft) add bsecondsplit1
  |
  | *  2:102002290587@default(draft) add _c
  | |
  | x  1:37445b16603b@default(draft) add _b
  |/
  o  0:135f39f4bd78@default(draft) add _a
  

  $ hg evolve --all --any --orphan
  move:[2] add _c
  atop:[6] add bsecondsplit2
  $ hg log -G
  o  7:98e3f21461ff@default(draft) add _c
  |
  @  6:59b942dbda14@default(draft) add bsecondsplit2
  |
  o  5:8ffdae67d696@default(draft) add bsecondsplit1
  |
  o  0:135f39f4bd78@default(draft) add _a
  

  $ cd ..
