  $ . $TESTDIR/testlib/pythonpath.sh
  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > evolve=
  > [experimental]
  > evolution.allowdivergence = True
  > EOF

This test file tests the case of content-divergence resolution of changesets
that have the null revision as the parent.

  $ hg init issue6201
  $ cd issue6201

  $ touch test
  $ hg add test
  $ hg commit -m test
  $ hg log -T '{node|short}\n'
  be090ea66256

  $ echo a >> test
  $ hg amend -m div1
  $ hg log -T '{node|short}\n'
  79fa0eb22d65

  $ hg up be090ea66256 --hidden --quiet
  updated to hidden changeset be090ea66256
  (hidden revision 'be090ea66256' was rewritten as: 79fa0eb22d65)
  working directory parent is obsolete! (be090ea66256)
  $ echo a >> test
  $ echo b >> test
  $ hg amend -m div2
  2 new content-divergent changesets
  $ hg log -T '{node|short}\n'
  4b2524b7508e
  79fa0eb22d65

  $ hg evolve --content-divergent --tool :other
  merge:[1] div1
  with: [2] div2
  base: [0] test
  0 files updated, 1 files merged, 0 files removed, 0 files unresolved
  working directory is now at 62fcb3488421

  $ hg evolve --list
