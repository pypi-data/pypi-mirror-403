test of the fold command
------------------------

  $ . $TESTDIR/testlib/common.sh
  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > interactive = true
  > [extensions]
  > evolve =
  > topic =
  > EOF

  $ logtopic() {
  >    hg log -G -T "{rev}:{node}\ntopics: {topics}" 
  > }

Check that fold keep the topic if all revisions have the topic
--------------------------------------------------------------

  $ hg init testfold
  $ cd testfold
  $ mkcommit ROOT
  $ hg topic myfeature
  marked working directory as topic: myfeature
  $ mkcommit feature1
  active topic 'myfeature' grew its first changeset
  (see 'hg help topics' for more information)
  $ mkcommit feature2
  $ logtopic
  @  2:6e0fb07fa151928b633485a01b6d815b27f5a26d
  |  topics: myfeature
  o  1:95b29fc10be4e6343c8d344ad4354d6ff4098df1
  |  topics: myfeature
  o  0:ea207398892eb49e06441f10dda2a731f0450f20
     topics:
  $ hg fold --exact -r "(tip~1)::" -m "folded"
  2 changesets folded
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg stack
  ### topic: myfeature
  ### target: default (branch)
  s1@ folded (current)
  s0^ ROOT (base)
  $ logtopic
  @  3:ba602426356f35854a83b02183d999749142443c
  |  topics: myfeature
  o  0:ea207398892eb49e06441f10dda2a731f0450f20
     topics:
  $ hg summary
  parent: 3:ba602426356f tip
   folded
  branch: default//myfeature
  commit: (clean)
  update: (current)
  phases: 2 draft
  topic:  myfeature

Check that fold dismis the topic if not all revisions have the topic
--------------------------------------------------------------------

(I'm not sure this behavior make senses, but now it is tested)

  $ hg topic --clear
  $ mkcommit feature3
  created new head
  (consider using topic for lightweight branches. See 'hg help topic')
  $ hg topic myotherfeature
  marked working directory as topic: myotherfeature
  $ mkcommit feature4
  active topic 'myotherfeature' grew its first changeset
  (see 'hg help topics' for more information)
  $ logtopic
  @  5:85e76d22bde1cb5ce44b00fc91a88cb805c93b1b
  |  topics: myotherfeature
  o  4:6508e0bfb6a188bb94d77c107f4e969291010b42
  |  topics:
  o  3:ba602426356f35854a83b02183d999749142443c
  |  topics: myfeature
  o  0:ea207398892eb49e06441f10dda2a731f0450f20
     topics:
  $ hg fold --exact -r "(tip~1)::" -m "folded 2"
  active topic 'myotherfeature' is now empty
  2 changesets folded
  clearing empty topic "myotherfeature"
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ logtopic
  @  6:9fa327ea84f90ba000b75b90446680c993972df0
  |  topics:
  o  3:ba602426356f35854a83b02183d999749142443c
  |  topics: myfeature
  o  0:ea207398892eb49e06441f10dda2a731f0450f20
     topics:
  $ hg summary
  parent: 6:9fa327ea84f9 tip
   folded 2
  branch: default
  commit: (clean)
  update: (current)
  phases: 3 draft
