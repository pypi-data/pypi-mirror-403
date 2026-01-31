
  $ . "$TESTDIR/testlib/topic_setup.sh"

Initial setup

  $ cat << EOF >> $HGRCPATH
  > [ui]
  > logtemplate = {rev} {branch} \{{get(namespaces, "topics")}} {phase} {desc|firstline}\n
  > [experimental]
  > evolution=createmarkers,exchange,allowunstable
  > EOF

  $ hg init main
  $ cd main
  $ hg branch double//slash
  marked working directory as branch double//slash
  (branches are permanent and global, did you want a bookmark?)
  $ echo aaa > aaa
  $ hg add aaa
  $ hg commit -m c_a
  $ echo aaa > bbb
  $ hg add bbb
  $ hg commit -m c_b
  $ hg branch foo//bar
  marked working directory as branch foo//bar
  $ echo aaa > ccc
  $ hg add ccc
  $ hg commit -m c_c
  $ echo aaa > ddd
  $ hg add ddd
  $ hg commit -m c_d
  $ echo aaa > eee
  $ hg add eee
  $ hg commit -m c_e
  $ echo aaa > fff
  $ hg add fff
  $ hg commit -m c_f
  $ hg log -G
  @  5 foo//bar {} draft c_f
  |
  o  4 foo//bar {} draft c_e
  |
  o  3 foo//bar {} draft c_d
  |
  o  2 foo//bar {} draft c_c
  |
  o  1 double//slash {} draft c_b
  |
  o  0 double//slash {} draft c_a
  

Commit extras have branch name without formatting
-------------------------------------------------

  $ hg log -r 1 -T '{rev}: {join(extras, " ")}\n'
  1: branch=double//slash
  $ hg log -r 5 -T '{rev}: {join(extras, " ")}\n'
  5: branch=foo//bar

Check that branch without any parent does not crash stack
---------------------------------------------------------

  $ hg up double//slash//
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  $ hg stack
  ### target: double//slash (branch)
  s2@ c_b (current)
  s1: c_a
  $ hg phase --public 'branch("double//slash//")'
  $ hg up foo//bar//
  4 files updated, 0 files merged, 0 files removed, 0 files unresolved

Simple test
-----------

'hg stack' lists all changeset on the branch

  $ hg branch
  foo//bar
  $ hg stack
  ### target: foo//bar (branch)
  s4@ c_f (current)
  s3: c_e
  s2: c_d
  s1: c_c
  s0^ c_b (base)
  $ hg stack -v
  ### target: foo//bar (branch)
  s4(18b3ff044de9)@ c_f (current)
  s3(b1913e064ca1): c_e
  s2(8fad7e98adf6): c_d
  s1(da14ac95d156): c_c
  s0(2450a061c0f0)^ c_b (base)

Test "s#" reference
-------------------

  $ hg up s2
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg up foo//bar//
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg up s42
  abort: cannot resolve "s42": branch "foo//bar//" has only 4 non-public changesets
  [255]
  $ hg up s2
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg summary
  parent: 3:8fad7e98adf6 
   c_d
  branch: foo//bar//
  commit: (clean)
  update: 2 new changesets (update)
  phases: 4 draft

Case with some of the branch unstable
-------------------------------------

  $ echo bbb > ddd
  $ hg commit --amend
  2 new orphan changesets
  $ hg log -G
  @  6 foo//bar {} draft c_d
  |
  | *  5 foo//bar {} draft c_f
  | |
  | *  4 foo//bar {} draft c_e
  | |
  | x  3 foo//bar {} draft c_d
  |/
  o  2 foo//bar {} draft c_c
  |
  o  1 double//slash {} public c_b
  |
  o  0 double//slash {} public c_a
  
  $ hg stack
  ### target: foo//bar (branch)
  s4$ c_f (orphan)
  s3$ c_e (orphan)
  s2@ c_d (current)
  s1: c_c
  s0^ c_b (base)
  $ hg up s3
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg stack
  ### target: foo//bar (branch)
  s4$ c_f (orphan)
  s3@ c_e (current orphan)
  s2: c_d
  s1: c_c
  s0^ c_b (base)
  $ hg up s2
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved

Also test the revset:

  $ hg log -r 'stack()'
  2 foo//bar {} draft c_c
  6 foo//bar {} draft c_d
  4 foo//bar {} draft c_e
  5 foo//bar {} draft c_f

Case with multiple heads on the branch
--------------------------------------

Make things linear again

  $ hg rebase -s 'desc(c_e)' -d 'desc(c_d) - obsolete()'
  rebasing 4:b1913e064ca1 "c_e"
  rebasing 5:18b3ff044de9 "c_f"
  $ hg log -G
  o  8 foo//bar {} draft c_f
  |
  o  7 foo//bar {} draft c_e
  |
  @  6 foo//bar {} draft c_d
  |
  o  2 foo//bar {} draft c_c
  |
  o  1 double//slash {} public c_b
  |
  o  0 double//slash {} public c_a
  

Create the second head

  $ hg up 'desc(c_d)'
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ echo aaa > ggg
  $ hg add ggg
  $ hg commit -m c_g
  created new head
  (consider using topic for lightweight branches. See 'hg help topic')
  $ echo aaa > hhh
  $ hg add hhh
  $ hg commit -m c_h
  $ hg log -G
  @  10 foo//bar {} draft c_h
  |
  o  9 foo//bar {} draft c_g
  |
  | o  8 foo//bar {} draft c_f
  | |
  | o  7 foo//bar {} draft c_e
  |/
  o  6 foo//bar {} draft c_d
  |
  o  2 foo//bar {} draft c_c
  |
  o  1 double//slash {} public c_b
  |
  o  0 double//slash {} public c_a
  

Test output

  $ hg stack
  ### target: foo//bar (branch) (2 heads)
  s6@ c_h (current)
  s5: c_g
  s2^ c_d (base)
  s4: c_f
  s3: c_e
  s2: c_d
  s1: c_c
  s0^ c_b (base)

Case with multiple heads on the branch with instability involved
----------------------------------------------------------------

We amend the message to make sure the display base pick the right changeset

  $ hg up 'desc(c_d)'
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo ccc > ddd
  $ hg commit --amend -m 'c_D' 
  4 new orphan changesets
  $ hg rebase -d . -s 'desc(c_g)'
  rebasing 9:8c1819a4441f "c_g"
  rebasing 10:e255b784f0e9 "c_h"
  $ hg log -G
  o  13 foo//bar {} draft c_h
  |
  o  12 foo//bar {} draft c_g
  |
  @  11 foo//bar {} draft c_D
  |
  | *  8 foo//bar {} draft c_f
  | |
  | *  7 foo//bar {} draft c_e
  | |
  | x  6 foo//bar {} draft c_d
  |/
  o  2 foo//bar {} draft c_c
  |
  o  1 double//slash {} public c_b
  |
  o  0 double//slash {} public c_a
  

  $ hg stack
  ### target: foo//bar (branch) (2 heads)
  s6: c_h
  s5: c_g
  s2^ c_D (base current)
  s4$ c_f (orphan)
  s3$ c_e (orphan)
  s2@ c_D (current)
  s1: c_c
  s0^ c_b (base)

Check that stack doesn't show public changesets on a branch
-----------------------------------------------------------

  $ hg log --graph
  o  13 foo//bar {} draft c_h
  |
  o  12 foo//bar {} draft c_g
  |
  @  11 foo//bar {} draft c_D
  |
  | *  8 foo//bar {} draft c_f
  | |
  | *  7 foo//bar {} draft c_e
  | |
  | x  6 foo//bar {} draft c_d
  |/
  o  2 foo//bar {} draft c_c
  |
  o  1 double//slash {} public c_b
  |
  o  0 double//slash {} public c_a
  

  $ hg stack
  ### target: foo//bar (branch) (2 heads)
  s6: c_h
  s5: c_g
  s2^ c_D (base current)
  s4$ c_f (orphan)
  s3$ c_e (orphan)
  s2@ c_D (current)
  s1: c_c
  s0^ c_b (base)
  $ hg phase --public s1
  $ hg stack
  ### target: foo//bar (branch) (2 heads)
  s5: c_h
  s4: c_g
  s1^ c_D (base current)
  s3$ c_f (orphan)
  s2$ c_e (orphan)
  s1@ c_D (current)
  s0^ c_c (base)

Check that stack doesn't show changesets with a topic
-----------------------------------------------------

  $ hg topic --rev s4::s5 sometopic
  changed topic on 2 changesets to "sometopic"
  $ hg stack
  ### target: foo//bar (branch)
  s3$ c_f (orphan)
  s2$ c_e (orphan)
  s1@ c_D (current)
  s0^ c_c (base)
