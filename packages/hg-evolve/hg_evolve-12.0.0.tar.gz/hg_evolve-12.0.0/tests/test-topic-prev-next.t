  $ . "$TESTDIR/testlib/topic_setup.sh"
  $ . "$TESTDIR/testlib/common.sh"

  $ cat << EOF >> $HGRCPATH
  > [extensions]
  > evolve =
  > [ui]
  > logtemplate = '{rev} [{topic}] {desc}\n'
  > EOF

Checking target ambiguity in hg next

  $ hg init ambiguous-next
  $ cd ambiguous-next

  $ mkcommit root
  $ hg topic A
  marked working directory as topic: A
  $ mkcommit A1
  active topic 'A' grew its first changeset
  (see 'hg help topics' for more information)
  $ mkcommit A2
  $ mkcommit A3
  $ mkcommit A4
  $ hg up 'desc("A3")'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ mkcommit A5
  $ hg up 'desc("A2")'
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg topic B
  $ mkcommit B1
  active topic 'B' grew its first changeset
  (see 'hg help topics' for more information)
  $ mkcommit B2

  $ hg log -G
  @  7 [B] B2
  |
  o  6 [B] B1
  |
  | o  5 [A] A5
  | |
  | | o  4 [A] A4
  | |/
  | o  3 [A] A3
  |/
  o  2 [A] A2
  |
  o  1 [A] A1
  |
  o  0 [] root
  

Quick sanity check

  $ hg up 'desc("A1")'
  switching to topic A
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ hg next
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [s2] A2
  $ hg stack
  ### topic: A (2 heads)
  ### target: default (branch)
  s5: A4
  s3^ A3 (base)
  s4: A5
  s3: A3
  s2@ A2 (current)
  s1: A1
  s0^ root (base)
  $ hg next
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [s3] A3
  $ hg log -G
  o  7 [B] B2
  |
  o  6 [B] B1
  |
  | o  5 [A] A5
  | |
  | | o  4 [A] A4
  | |/
  | @  3 [A] A3
  |/
  o  2 [A] A2
  |
  o  1 [A] A1
  |
  o  0 [] root
  
  $ hg next
  ambiguous next changeset:
  [s5] A4
  [s4] A5
  explicitly update to one of them
  [1]

Let's make some changesets unstable

  $ hg up 'desc("A2")'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo foo > A2
  $ hg amend
  5 new orphan changesets
  $ hg stack
  ### topic: A (2 heads)
  ### target: default (branch)
  s5$ A4 (orphan)
  s3^ A3 (base orphan)
  s4$ A5 (orphan)
  s3$ A3 (orphan)
  s2@ A2 (current)
  s1: A1
  s0^ root (base)
  $ hg log -G
  @  8 [A] A2
  |
  | *  7 [B] B2
  | |
  | *  6 [B] B1
  | |
  | | *  5 [A] A5
  | | |
  | | | *  4 [A] A4
  | | |/
  | | *  3 [A] A3
  | |/
  | x  2 [A] A2
  |/
  o  1 [A] A1
  |
  o  0 [] root
  

Simply walking on unstable changesets should work as expected

  $ hg up 'desc("B2")'
  switching to topic B
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [s1] B1
  $ hg next
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [s2] B2

B1 shouldn't be considered a target, orphan or not

  $ hg up 'desc("A2")'
  switching to topic A
  1 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg next
  move:[s3] A3
  atop:[s2] A2
  working directory is now at 2b67b6a6cae1

B1 is not considered a target when it's been stabilized

  $ hg up 'desc("A2")'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg evolve --rev 'desc("B1")'
  move:[6] B1
  atop:[8] A2
  switching to topic A
  $ hg next
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [s3] A3

A4 and A5 should be ambiguous for hg next even if A5 is an orphan and A4 is not

  $ hg evolve --rev 'desc("A3") + desc("A4")'
  move:[s5] A4
  atop:[s3] A3
  $ hg up 'desc("A3")'
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg stack
  ### topic: A (2 heads)
  ### target: default (branch)
  s5: A4
  s3^ A3 (base current)
  s4$ A5 (orphan)
  s3@ A3 (current)
  s2: A2
  s1: A1
  s0^ root (base)
  $ hg next --no-evolve --dry-run
  hg update 51d70e81d730;
  [s5] A4
  $ hg next
  ambiguous next changeset:
  [s5] A4
  [s4] A5
  explicitly update to one of them
  [1]

  $ cd ..

Making sure plain hg next sticks to topic when target is unstable

  $ hg init next-unstable-topic
  $ cd next-unstable-topic

  $ mkcommit ROOT
  $ hg topics topic-a
  marked working directory as topic: topic-a
  $ mkcommit A
  active topic 'topic-a' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg topics topic-b
  $ mkcommit B
  active topic 'topic-b' grew its first changeset
  (see 'hg help topics' for more information)
  $ hg up 'topic("topic-a")'
  switching to topic topic-a
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo foo > foo
  $ hg ci -A --amend
  adding foo
  1 new orphan changesets
  $ hg log -G
  @  3 [topic-a] A
  |
  | *  2 [topic-b] B
  | |
  | x  1 [topic-a] A
  |/
  o  0 [] ROOT
  

  $ hg next
  no children on topic "topic-a"
  do you want --no-topic
  [1]

  $ hg next --no-topic
  move:[2] B
  atop:[3] A
  working directory is now at 53f8332d648f

  $ cd ..
