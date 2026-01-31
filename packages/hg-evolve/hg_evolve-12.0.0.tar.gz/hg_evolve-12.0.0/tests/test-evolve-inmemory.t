Tests running `hg evolve` with in-memory merge.

  $ . $TESTDIR/testlib/common.sh

  $ cat >> $HGRCPATH <<EOF
  > [extensions]
  > evolve =
  > drawdag=$RUNTESTDIR/drawdag.py
  > [alias]
  > glog = log -G -T '{rev}:{node|short} {separate(" ", phase, tags)}\n{desc|firstline}'
  > [experimental]
  > evolution.in-memory = yes
  > EOF

Test evolving a single orphan

  $ hg init single-orphan
  $ cd single-orphan
  $ hg debugdrawdag <<'EOS'
  >     C  # C/C = C\n
  > B2  |  # B2/B = B2\n
  > |   B  # B/B = B\n
  >  \ /   # replace: B -> B2
  >   A
  > EOS
  1 new orphan changesets
  $ hg evolve
  move:[3] C
  atop:[2] B2
  $ hg glog
  o  4:a2a0434af50b draft tip
  |  C
  | x  3:46f17045c5ee draft C
  | |  C
  o |  2:3d6c495db414 draft B2
  | |  B2
  | x  1:caf23a7900cb draft B
  |/   B
  o  0:426bada5c675 draft A
     A
  $ hg cat -r tip B C
  B2
  C
  $ cd ..

Test that in-memory evolve works when there are conflicts
and after continuing.

  $ hg init conflicts
  $ cd conflicts
  $ hg debugdrawdag <<'EOS'
  >     E  # E/E = E\n
  >     |
  >     D  # D/B = D\n
  >     |
  >     C  # C/C = C\n
  > B2  |  # B2/B = B2\n
  > |   B  # B/B = B\n
  >  \ /   # replace: B -> B2
  >   A
  > EOS
  3 new orphan changesets
  $ hg evolve
  move:[3] C
  atop:[2] B2
  move:[4] D
  merging B
  hit merge conflicts; retrying merge in working copy
  merging B
  warning: conflicts while merging B! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ hg glog
  @  6:a2a0434af50b draft tip
  |  C
  | *  5:844900596917 draft E
  | |  E
  | %  4:a75d38413966 draft D
  | |  D
  | x  3:46f17045c5ee draft C
  | |  C
  o |  2:3d6c495db414 draft B2
  | |  B2
  | x  1:caf23a7900cb draft B
  |/   B
  o  0:426bada5c675 draft A
     A
  $ cat C
  C
  $ cat B
  <<<<<<< destination: a2a0434af50b - test: C
  B2
  =======
  D
  >>>>>>> evolving:    a75d38413966 D - test: D
  $ echo D2 > B
  $ hg resolve -m
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 4:a75d38413966 "D"
  move:[5] E
  atop:[7] D
  $ hg glog
  o  8:918ab8de4edf draft tip
  |  E
  o  7:c9677354e977 draft
  |  D
  o  6:a2a0434af50b draft
  |  C
  | x  5:844900596917 draft E
  | |  E
  | x  4:a75d38413966 draft D
  | |  D
  | x  3:46f17045c5ee draft C
  | |  C
  o |  2:3d6c495db414 draft B2
  | |  B2
  | x  1:caf23a7900cb draft B
  |/   B
  o  0:426bada5c675 draft A
     A
  $ hg cat -r tip B C E
  D2
  C
  E
  $ cd ..

Test that in-memory merge is disabled if there's a precommit hook

  $ hg init precommit-hook
  $ cd precommit-hook
  $ hg debugdrawdag <<'EOS'
  >     C  # C/C = C\n
  > B2  |  # B2/B = B2\n
  > |   B  # B/B = B\n
  >  \ /   # replace: B -> B2
  >   A
  > EOS
  1 new orphan changesets
  $ cat >> .hg/hgrc <<EOF
  > [hooks]
  > precommit = sh -c "echo 'running precommit hook'"
  > EOF
The hook is not run with in-memory=force
  $ hg co B2
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg evolve --config experimental.evolution.in-memory=force --update
  move:[3] C
  atop:[2] B2
  working directory is now at a2a0434af50b
  $ hg glog
  @  4:a2a0434af50b draft tip
  |  C
  | x  3:46f17045c5ee draft C
  | |  C
  o |  2:3d6c495db414 draft B2
  | |  B2
  | x  1:caf23a7900cb draft B
  |/   B
  o  0:426bada5c675 draft A
     A
  $ hg co tip^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg amend -m B3
  1 new orphan changesets
The hook is run with in-memory=yes
  $ hg next --config experimental.evolution.in-memory=yes
  move:[4] C
  atop:[5] B3
  running precommit hook
  working directory is now at 24f38f1ca271
  $ hg glog
  @  6:24f38f1ca271 draft tip
  |  C
  o  5:b43c30321752 draft
  |  B3
  | x  3:46f17045c5ee draft C
  | |  C
  +---x  2:3d6c495db414 draft B2
  | |    B2
  | x  1:caf23a7900cb draft B
  |/   B
  o  0:426bada5c675 draft A
     A
