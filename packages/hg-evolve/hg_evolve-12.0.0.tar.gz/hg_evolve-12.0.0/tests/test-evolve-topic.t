
Check we can find the topic extensions

  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > logtemplate = {rev} - \{{get(namespaces, "topics")}} {node|short} {desc} ({phase})\n
  > [extensions]
  > rebase = 
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH
  $ echo "topic=$(echo $(dirname $TESTDIR))/hgext3rd/topic/" >> $HGRCPATH

  $ mkcommit() {
  >    echo "$1" > "$1"
  >    hg add "$1"
  >    hg ci -m "add $1"
  > }

Create a simple setup

  $ hg init repoa
  $ cd repoa
  $ mkcommit aaa
  $ mkcommit bbb
  $ hg topic foo
  marked working directory as topic: foo
  $ mkcommit ccc
  active topic 'foo' grew its first changeset
  (see 'hg help topics' for more information)
  $ mkcommit ddd
  $ mkcommit eee
  $ mkcommit fff
  $ hg topic bar
  $ mkcommit ggg
  active topic 'bar' grew its first changeset
  (see 'hg help topics' for more information)
  $ mkcommit hhh
  $ mkcommit iii
  $ mkcommit jjj

  $ hg log -G
  @  9 - {bar} 1d964213b023 add jjj (draft)
  |
  o  8 - {bar} fcab990f3261 add iii (draft)
  |
  o  7 - {bar} b0c2554835ac add hhh (draft)
  |
  o  6 - {bar} c748293f1c1a add ggg (draft)
  |
  o  5 - {foo} 6a6b7365c751 add fff (draft)
  |
  o  4 - {foo} 3969ab847d9c add eee (draft)
  |
  o  3 - {foo} 4e3a154f38c7 add ddd (draft)
  |
  o  2 - {foo} cced9bac76e3 add ccc (draft)
  |
  o  1 - {} a4dbed0837ea add bbb (draft)
  |
  o  0 - {} 199cc73e9a0b add aaa (draft)
  

Test that evolve --all evolve the current topic
-----------------------------------------------

make a mess

  $ hg up foo
  switching to topic foo
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  $ hg topic -l 
  ### topic: foo (?)
  ### branch: default (?)
  ### target: default (branch)
  s4@ add fff (current)
  s3: add eee
  s2: add ddd
  s1: add ccc
  s0^ add bbb (base)
  $ hg up 'desc(ddd)'
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo ddd >> ddd
  $ hg amend
  6 new orphan changesets
  $ hg up 'desc(fff)'
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo fff >> fff
  $ hg amend

  $ hg log -G
  @  11 - {foo} e104f49bab28 add fff (draft)
  |
  | o  10 - {foo} d9cacd156ffc add ddd (draft)
  | |
  | | *  9 - {bar} 1d964213b023 add jjj (draft)
  | | |
  | | *  8 - {bar} fcab990f3261 add iii (draft)
  | | |
  | | *  7 - {bar} b0c2554835ac add hhh (draft)
  | | |
  | | *  6 - {bar} c748293f1c1a add ggg (draft)
  | | |
  +---x  5 - {foo} 6a6b7365c751 add fff (draft)
  | |
  * |  4 - {foo} 3969ab847d9c add eee (draft)
  | |
  x |  3 - {foo} 4e3a154f38c7 add ddd (draft)
  |/
  o  2 - {foo} cced9bac76e3 add ccc (draft)
  |
  o  1 - {} a4dbed0837ea add bbb (draft)
  |
  o  0 - {} 199cc73e9a0b add aaa (draft)
  

Run evolve --all

  $ hg stack
  ### topic: foo
  ### target: default (branch)
  s4@ add fff (current orphan)
  s3$ add eee (orphan)
  s2: add ddd
  s1: add ccc
  s0^ add bbb (base)

  $ hg evolve --all --update
  move:[s3] add eee
  atop:[s2] add ddd
  move:[s4] add fff
  working directory is now at ad43ddbeead9
  $ hg log -G
  @  13 - {foo} ad43ddbeead9 add fff (draft)
  |
  o  12 - {foo} 42b49017ff90 add eee (draft)
  |
  o  10 - {foo} d9cacd156ffc add ddd (draft)
  |
  | *  9 - {bar} 1d964213b023 add jjj (draft)
  | |
  | *  8 - {bar} fcab990f3261 add iii (draft)
  | |
  | *  7 - {bar} b0c2554835ac add hhh (draft)
  | |
  | *  6 - {bar} c748293f1c1a add ggg (draft)
  | |
  | x  5 - {foo} 6a6b7365c751 add fff (draft)
  | |
  | x  4 - {foo} 3969ab847d9c add eee (draft)
  | |
  | x  3 - {foo} 4e3a154f38c7 add ddd (draft)
  |/
  o  2 - {foo} cced9bac76e3 add ccc (draft)
  |
  o  1 - {} a4dbed0837ea add bbb (draft)
  |
  o  0 - {} 199cc73e9a0b add aaa (draft)
  

Test that evolve does not loose topic information
-------------------------------------------------

  $ hg evolve --rev 'topic(bar)' --update
  move:[6] add ggg
  atop:[13] add fff
  move:[7] add hhh
  move:[8] add iii
  move:[9] add jjj
  working directory is now at fed0f67a2171
  $ hg log -G
  @  17 - {bar} fed0f67a2171 add jjj (draft)
  |
  o  16 - {bar} 94e899639b23 add iii (draft)
  |
  o  15 - {bar} 55e5cd2b6cd6 add hhh (draft)
  |
  o  14 - {bar} 56107a7ddeaf add ggg (draft)
  |
  o  13 - {foo} ad43ddbeead9 add fff (draft)
  |
  o  12 - {foo} 42b49017ff90 add eee (draft)
  |
  o  10 - {foo} d9cacd156ffc add ddd (draft)
  |
  o  2 - {foo} cced9bac76e3 add ccc (draft)
  |
  o  1 - {} a4dbed0837ea add bbb (draft)
  |
  o  0 - {} 199cc73e9a0b add aaa (draft)
  

Tests next and prev behavior
============================

Basic move are restricted to the current topic

  $ hg up foo
  switching to topic foo
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [s3] add eee
  $ hg next
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [s4] add fff
  $ hg next
  no children on topic "foo"
  do you want --no-topic
  [1]
  $ hg next --no-topic
  switching to topic bar
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [14] add ggg
  $ hg prev
  preserving the current topic 'bar'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [s4] add fff
  $ hg prev
  no parent in topic "bar"
  (do you want --no-topic)
  [1]
  $ hg prev --no-topic
  switching to topic foo
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [12] add eee

Testing when instability is involved

  $ hg log -G
  o  17 - {bar} fed0f67a2171 add jjj (draft)
  |
  o  16 - {bar} 94e899639b23 add iii (draft)
  |
  o  15 - {bar} 55e5cd2b6cd6 add hhh (draft)
  |
  o  14 - {bar} 56107a7ddeaf add ggg (draft)
  |
  o  13 - {foo} ad43ddbeead9 add fff (draft)
  |
  @  12 - {foo} 42b49017ff90 add eee (draft)
  |
  o  10 - {foo} d9cacd156ffc add ddd (draft)
  |
  o  2 - {foo} cced9bac76e3 add ccc (draft)
  |
  o  1 - {} a4dbed0837ea add bbb (draft)
  |
  o  0 - {} 199cc73e9a0b add aaa (draft)
  
  $ hg topic -r ad43ddbeead9 bar
  4 new orphan changesets
  changed topic on 1 changesets to "bar"
  $ hg log -r 18 -T '{rev}: {join(extras, " ")}\n'
  18: _rewrite_noise=[0-9a-f]+ branch=default rebase_source=[0-9a-f]+ topic=bar (re)
  $ hg up 56107a7ddeaf
  switching to topic bar
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ hg stack
  ### topic: bar
  ### target: default (branch)
  s5$ add jjj (orphan)
  s4$ add iii (orphan)
  s3$ add hhh (orphan)
  s2@ add ggg (current orphan)
  s1: add fff
  s0^ add eee (base)

  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [s1] add fff

Testing issue 5708 when we are on obsolete changeset and there is active topic
------------------------------------------------------------------------------

  $ hg log --graph
  @  18 - {bar} 8dde0971132d add fff (draft)
  |
  | *  17 - {bar} fed0f67a2171 add jjj (draft)
  | |
  | *  16 - {bar} 94e899639b23 add iii (draft)
  | |
  | *  15 - {bar} 55e5cd2b6cd6 add hhh (draft)
  | |
  | *  14 - {bar} 56107a7ddeaf add ggg (draft)
  | |
  | x  13 - {foo} ad43ddbeead9 add fff (draft)
  |/
  o  12 - {foo} 42b49017ff90 add eee (draft)
  |
  o  10 - {foo} d9cacd156ffc add ddd (draft)
  |
  o  2 - {foo} cced9bac76e3 add ccc (draft)
  |
  o  1 - {} a4dbed0837ea add bbb (draft)
  |
  o  0 - {} 199cc73e9a0b add aaa (draft)
  

  $ hg topic
   * bar (5 changesets, 4 unstable)
     foo (3 changesets)

When the current topic, obsoleted changesets topic and successor topic are same

  $ hg up 55e5cd2b6cd6
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo foobar >> hhh
  $ hg amend
  $ hg up 55e5cd2b6cd6
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory parent is obsolete! (55e5cd2b6cd6)
  (use 'hg evolve' to update to its successor: 604c23b08613)
  $ hg log -Gr 14::
  *  19 - {bar} 604c23b08613 add hhh (draft)
  |
  | *  17 - {bar} fed0f67a2171 add jjj (draft)
  | |
  | *  16 - {bar} 94e899639b23 add iii (draft)
  | |
  | @  15 - {bar} 55e5cd2b6cd6 add hhh (draft)
  |/
  *  14 - {bar} 56107a7ddeaf add ggg (draft)
  |
  ~

  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [s2] add ggg

When the current topic and successors topic are same, but obsolete cset has
different topic

  $ hg rebase -s 94e899639b23 -d 604c23b08613 --config extensions.rebase=
  rebasing 16:94e899639b23 bar "add iii"
  1 new orphan changesets
  rebasing 17:fed0f67a2171 bar "add jjj"
  1 new orphan changesets
  $ hg log -Gr 42b49017ff90::
  *  21 - {bar} 573bbc059289 add jjj (draft)
  |
  *  20 - {bar} 8e94e3065186 add iii (draft)
  |
  *  19 - {bar} 604c23b08613 add hhh (draft)
  |
  | o  18 - {bar} 8dde0971132d add fff (draft)
  | |
  @ |  14 - {bar} 56107a7ddeaf add ggg (draft)
  | |
  x |  13 - {foo} ad43ddbeead9 add fff (draft)
  |/
  o  12 - {foo} 42b49017ff90 add eee (draft)
  |
  ~

  $ hg up ad43ddbeead9
  switching to topic foo
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  working directory parent is obsolete! (ad43ddbeead9)
  (use 'hg evolve' to update to its successor: 8dde0971132d)

  $ hg topic bar

  $ hg prev
  no parent in topic "bar"
  (do you want --no-topic)
  [1]

When current topic and obsolete cset topic are same but successor has different
one

  $ hg up ad43ddbeead9
  switching to topic foo
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [s3] add eee

Check stackaliases(s#) works with  --continue case also, while evolving:
------------------------------------------------------------------------
  $ hg up 18
  switching to topic bar
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg evolve --all
  move:[s2] add ggg
  atop:[s1] add fff
  move:[s3] add hhh
  move:[s4] add iii
  move:[s5] add jjj
  $ echo "changes in hhh" > hhh
  $ hg add hhh
  $ hg ci --amend
  4 new orphan changesets
  $ hg log -G
  @  26 - {bar} 235873f1950b add fff (draft)
  |
  | *  25 - {bar} ed0b505ff189 add jjj (draft)
  | |
  | *  24 - {bar} 50b1b9387d50 add iii (draft)
  | |
  | *  23 - {bar} 0d4bb3a72a5b add hhh (draft)
  | |
  | *  22 - {bar} 548702c1d91c add ggg (draft)
  | |
  | x  18 - {bar} 8dde0971132d add fff (draft)
  |/
  o  12 - {foo} 42b49017ff90 add eee (draft)
  |
  o  10 - {foo} d9cacd156ffc add ddd (draft)
  |
  o  2 - {foo} cced9bac76e3 add ccc (draft)
  |
  o  1 - {} a4dbed0837ea add bbb (draft)
  |
  o  0 - {} 199cc73e9a0b add aaa (draft)
  
  $ hg evolve --all
  move:[s2] add ggg
  atop:[s1] add fff
  move:[s3] add hhh
  merging hhh
  warning: conflicts while merging hhh! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ echo "resolved hhh" > hhh
  $ hg resolve --mark hhh
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg evolve --continue
  evolving 23:0d4bb3a72a5b "add hhh"
  move:[s4] add iii
  atop:[s3] add hhh
  move:[s5] add jjj

Test to make sure that evolve don't crash with FilteredRepoLookupError when obsolete revs are in play:
------------------------------------------------------------------------------------------------------

update to obsolete revision
  $ hg up -r 'min(desc("add fff"))' --hidden
  switching to topic foo
  2 files updated, 0 files merged, 1 files removed, 0 files unresolved
  updated to hidden changeset 6a6b7365c751
  (hidden revision '6a6b7365c751' was rewritten as: 235873f1950b)
  working directory parent is obsolete! (6a6b7365c751)
  (use 'hg evolve' to update to its successor: 235873f1950b)

Evolve:
  $ hg evolve
  update:[26] add fff
  switching to topic bar
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 235873f1950b
