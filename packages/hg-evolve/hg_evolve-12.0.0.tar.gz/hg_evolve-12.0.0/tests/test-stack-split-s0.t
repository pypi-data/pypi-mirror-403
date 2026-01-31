Testing the case when s0 is obsolete, and has multiple successors that are
topological heads

  $ . "$TESTDIR/testlib/common.sh"

  $ cat << EOF >> "$HGRCPATH"
  > [extensions]
  > evolve =
  > topic =
  > EOF

  $ hg init split-s0
  $ cd split-s0

  $ mkcommit ROOT
  $ mkcommit A

creating a small stack for the experiment

  $ hg branch cool-stack
  marked working directory as branch cool-stack
  (branches are permanent and global, did you want a bookmark?)
  $ mkcommit J
  $ mkcommit K
  $ mkcommit L

right now everything is stable, including s0

  $ hg stack
  ### target: cool-stack (branch)
  s3@ L (current)
  s2: K
  s1: J
  s0^ A (base)

destabilize the stack by obsoleting s0 with 2 successors

  $ hg up 'desc(ROOT)' -q
  $ mkcommit X
  created new head
  (consider using topic for lightweight branches. See 'hg help topic')
  $ hg up 'desc(ROOT)' -q
  $ mkcommit Y
  created new head
  (consider using topic for lightweight branches. See 'hg help topic')

  $ hg prune --split --rev 'desc(A)' --successor 'desc(X)' --successor 'desc(Y)'
  1 changesets pruned
  3 new orphan changesets

the 2 successors are 2 different heads (the revset is taken from _singlesuccessor function)

  $ hg log -r 'heads((desc(X)+desc(Y))::(desc(X)+desc(Y)))' -GT '{desc}\n'
  @  Y
  |
  ~
  o  X
  |
  ~

we choose one of the successors for s0, this is better than failing to show the stack at all

  $ hg up 'desc(L)' -q
  $ hg stack
  ### target: cool-stack (branch)
  s3@ L (current orphan)
  s2$ K (orphan)
  s1$ J (orphan)
  s0^ Y (base)
