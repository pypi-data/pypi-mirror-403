Testing retained_extras_on_rebase usage in evolve and modifying it in an extension

  $ . $TESTDIR/testlib/common.sh

  $ hg init repo
  $ cd repo
  $ cat > .hg/hgrc << EOF
  > [extensions]
  > evolve =
  > EOF

  $ echo apple > a
  $ hg ci -qAm 'apple'
  $ echo banana > b
  $ hg ci -qAm 'banana' --config extensions.commitextras= \
  > --extra useful=b-for-banana \
  > --extra useless=banana-peel

amending apple

  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [0] apple
  $ echo apricot > a
  $ hg amend -m 'apricot'
  1 new orphan changesets

the commit still has all extras that we added previously

  $ hg log -r 'desc("banana")' -T '{join(extras, " ")}\n'
  *useful=b-for-banana*useless=banana-peel* (glob)

let's run evolve with our extension

  $ hg --config extensions.retained_extras=${TESTDIR}/testlib/retain-extras-ext.py evolve
  move:[1] banana
  atop:[2] apricot

evolving banana retained "useful" and discarded "useless"

  $ hg log -r 'desc("banana")' -T '{join(extras, " ")}\n'
  *useful=b-for-banana* (glob)
