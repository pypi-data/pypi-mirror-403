hg pick with no active topic and with a different active topic (issue6406)
https://bz.mercurial-scm.org/show_bug.cgi?id=6406
For prior discussions on this behavior see also
https://foss.heptapod.net/mercurial/evolve/-/merge_requests/313
https://foss.heptapod.net/mercurial/evolve/-/merge_requests/390

  $ . "$TESTDIR/testlib/common.sh"

  $ cat << EOF >> "$HGRCPATH"
  > [phases]
  > publish = no
  > [extensions]
  > evolve =
  > topic =
  > EOF

#testcases inmemory ondisk
#if inmemory
  $ cat >> $HGRCPATH <<EOF
  > [experimental]
  > evolution.in-memory = yes
  > EOF
#endif

  $ hg init issue6406
  $ cd issue6406

  $ mkcommit ROOT

  $ hg debug-topic-namespace aaa
  marked working directory as topic namespace: aaa
  $ hg topic a-things
  marked working directory as topic: a-things
  $ mkcommit apple
  active topic 'a-things' grew its first changeset
  (see 'hg help topics' for more information)

  $ hg up 'desc("ROOT")'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg debug-topic-namespace bbb
  marked working directory as topic namespace: bbb
  $ hg topic b-things
  marked working directory as topic: b-things
  $ mkcommit banana
  active topic 'b-things' grew its first changeset
  (see 'hg help topics' for more information)
  $ mkcommit blackberry

  $ hg up 'desc("apple")'
  switching to topic-namespace aaa
  switching to topic a-things
  1 files updated, 0 files merged, 2 files removed, 0 files unresolved

This is what the help text says about this issue

  $ hg help pick | grep 'active topic' | sed 's/^    //'
  The resulting changeset will have the current active topic. If there's no
  active topic set, the resulting changeset will also not have any topic.

wdir has no active topic: pick should clear topic of the resulting cset

  $ hg debug-topic-namespace --clear
  $ hg topic --clear
  $ hg pick 'desc("banana")'
  picking 2:fcda3d8dafd2 "banana"
  1 new orphan changesets
  $ hg log -r . -T '{rev}: {desc} ({fqbn})\n'
  4: banana (default)
  $ hg debug-topic-namespace
  none
  $ hg topic --current
  no active topic
  [1]

wdir has active topic: pick should use the active topic for the resulting cset

  $ hg debug-topic-namespace everything
  marked working directory as topic namespace: everything
  $ hg topic all-things
  marked working directory as topic: all-things
  $ hg pick 'desc("blackberry")'
  picking 3:48bbfbece8fa "blackberry"
  active topic 'all-things' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg log -r . -T '{rev}: {desc} ({fqbn})\n'
  5: blackberry (default//everything/all-things)
  $ hg debug-topic-namespace
  everything
  $ hg topic --current
  all-things

  $ hg log -GT '{rev}: {desc} ({fqbn})\n{join(extras, " ")}\n\n'
  @  5: blackberry (default//everything/all-things)
  |  branch=default topic=all-things topic-namespace=everything
  |
  o  4: banana (default)
  |  branch=default
  |
  o  1: apple (default//aaa/a-things)
  |  branch=default topic=a-things topic-namespace=aaa
  |
  o  0: ROOT (default)
     branch=default
  
