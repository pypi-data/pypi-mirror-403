KeyError: b'topic' on history-rewriting commands (issue6500)
https://bz.mercurial-scm.org/show_bug.cgi?id=6500

  $ . $TESTDIR/testlib/common.sh

Making sure we're not caching .topic() results for memctx or anything else that's not stored on-disk

  $ hg init issue6500-caching-memctx
  $ cd issue6500-caching-memctx

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > evolve =
  > topic =
  > EOF

for this test we need 2 changesets with amend_source, one with topic and one without

  $ hg topics foo
  marked working directory as topic: foo
  $ echo apple > a
  $ hg ci -qAm 'apple'
  $ echo apricot > a
  $ hg ci --amend -m 'apricot'

not using `hg topics --clear -r .` here because that would remove amend_source, see _changetopics()

  $ hg topics --clear
  $ hg ci --amend -m 'no foo apricot'

  $ hg log --hidden -r 1+2 -T '{rev}: {join(extras, " ")}\n'
  1: amend_source=* branch=default topic=foo (glob)
  2: amend_source=* branch=default (glob)

creating and handling 2 memctx instances (based on 1 and then 2) should work

  $ hg touch --hidden -r 1+2 --duplicate
  switching to topic foo

make sure extras stay the same

  $ hg log --hidden -r 3+4 -T '{rev}: {join(extras, " ")}\n'
  3: __touch-noise__=* amend_source=* branch=default topic=foo (glob)
  4: __touch-noise__=* amend_source=* branch=default (glob)
