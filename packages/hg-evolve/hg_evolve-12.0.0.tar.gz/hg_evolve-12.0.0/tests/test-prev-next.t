  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > interactive = True
  > [extensions]
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

hg prev & next move to parent/child
  $ hg init test-repo
  $ cd test-repo
  $ touch a
  $ hg add a
  $ hg commit -m 'added a'
  $ touch b
  $ hg add b
  $ hg commit -m 'added b'
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [0] added a
  $ hg next
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [1] added b

hg prev & next respect --quiet
  $ hg prev -q
  $ hg next -q

hg prev -B should move active bookmark
  $ hg bookmark mark
  $ hg bookmarks
   * mark                      1:6e742c9127b3
  $ hg prev -B
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [0] added a
  $ hg bookmarks
   * mark                      0:a154386e50d1

hg next -B should move active bookmark
  $ hg next -B --dry-run
  hg update 6e742c9127b3;
  hg bookmark mark -r 6e742c9127b3;
  [1] added b
  $ hg next -B
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [1] added b
  $ hg bookmarks
   * mark                      1:6e742c9127b3

hg prev should unset active bookmark
  $ hg prev --dry-run
  hg update a154386e50d1;
  [0] added a
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [0] added a
  $ hg bookmarks
     mark                      1:6e742c9127b3

hg next should move active bookmark
  $ hg bookmark mark2
  $ hg bookmarks
     mark                      1:6e742c9127b3
   * mark2                     0:a154386e50d1
  $ hg next --dry-run --color=debug
  hg update 6e742c9127b3;
  [[evolve.rev|1]] added b
  $ hg next
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [1] added b
  $ hg bookmarks
     mark                      1:6e742c9127b3
     mark2                     0:a154386e50d1

  $ hg bookmark -d mark2
  $ hg bookmark mark

hg next/prev should not interfere with inactive bookmarks
  $ touch c
  $ hg add c
  $ hg commit -m 'added c'
  $ hg bookmark -r2 no-move
  $ hg prev -B
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [1] added b
  $ hg bookmarks
   * mark                      1:6e742c9127b3
     no-move                   2:4e26ef31f919
  $ hg next -B
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [2] added c
  $ hg bookmarks
   * mark                      2:4e26ef31f919
     no-move                   2:4e26ef31f919
  $ hg up 1
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  (leaving bookmark mark)
  $ hg next -B
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [2] added c
  $ hg bookmarks
     mark                      2:4e26ef31f919
     no-move                   2:4e26ef31f919
  $ hg prev -B
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [1] added b
  $ hg bookmarks
     mark                      2:4e26ef31f919
     no-move                   2:4e26ef31f919

test prev on root

  $ hg up null
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg prev
  already at repository root
  [1]
  $ hg up 1
  2 files updated, 0 files merged, 0 files removed, 0 files unresolved

Behavior with local modification
--------------------------------

  $ echo foo > modified-bar
  $ hg add modified-bar
  $ hg prev
  abort: uncommitted changes
  (do you want --merge?)
  [20]
  $ hg prev --merge
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [0] added a
  $ hg next
  abort: uncommitted changes
  (do you want --merge?)
  [20]
  $ hg next --merge
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [1] added b

Behavior with aspiring children
-------------------------------

  $ hg revert --all
  forgetting modified-bar
  $ hg log -G
  o  changeset:   2:4e26ef31f919
  |  bookmark:    mark
  |  bookmark:    no-move
  |  tag:         tip
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     added c
  |
  @  changeset:   1:6e742c9127b3
  |  user:        test
  |  date:        Thu Jan 01 00:00:00 1970 +0000
  |  summary:     added b
  |
  o  changeset:   0:a154386e50d1
     user:        test
     date:        Thu Jan 01 00:00:00 1970 +0000
     summary:     added a
  

no children of any kind

  $ hg next
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [2] added c
  $ hg next
  no children
  [1]
  $ hg next --evolve
  no children
  [1]
  $ hg prev --dry-run --color=debug
  hg update 6e742c9127b3;
  [[evolve.rev|1]] added b
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [1] added b

some aspiring children

  $ hg amend -m 'added b (2)'
  1 new orphan changesets
  $ hg next --no-evolve
  no children
  (1 unstable changesets to be evolved here, do you want --evolve?)
  [1]
  $ hg next --evolve --dry-run
  move:[2] added c
  atop:[3] added b (2)
  hg rebase -r 4e26ef31f919 -d 9ad178109a19

(add color output for smoke testing)

  $ hg next --evolve --color debug
  [evolve.operation|move:][[evolve.rev|2]] added c
  atop:[[evolve.rev|3]] added b (2)
  [ ui.status|working directory is now at [evolve.node|e3b6d5df389b]]

next with ambiguity

  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [3] added b (2)
  $ echo d > d
  $ hg add d
  $ hg commit -m 'added d'
  created new head
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [3] added b (2)
  $ hg next <<EOF
  > 2
  > EOF
  ambiguous next changeset, choose one to update:
  1: [e3b6d5df389b] added c
  2: [9df671ccd2c7] added d
  q: quit the prompt
  enter the index of the revision you want to select: 2
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [5] added d

  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [3] added b (2)

next with ambiguity in aspiring children

  $ hg amend -m 'added b (3)'
  2 new orphan changesets
  $ hg next --no-evolve
  no children
  (2 unstable changesets to be evolved here, do you want --evolve?)
  [1]
  $ hg next --evolve <<EOF
  > 1
  > EOF
  ambiguous next (unstable) changeset, choose one to evolve and update:
  1: [e3b6d5df389b] added c
  2: [9df671ccd2c7] added d
  q: quit the prompt
  enter the index of the revision you want to select: 1
  move:[4] added c
  atop:[6] added b (3)
  working directory is now at 5ce67c2407b0

  $ hg log -GT "{rev}:{node|short} {desc}\n"
  @  7:5ce67c2407b0 added c
  |
  o  6:d7f119adc759 added b (3)
  |
  | *  5:9df671ccd2c7 added d
  | |
  | x  3:9ad178109a19 added b (2)
  |/
  o  0:a154386e50d1 added a
  

  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [6] added b (3)
  $ hg next --evolve <<EOF
  > 2
  > EOF
  ambiguous next changeset, choose one to update:
  1: [5ce67c2407b0] added c
  2: [9df671ccd2c7] added d
  q: quit the prompt
  enter the index of the revision you want to select: 2
  move:[5] added d
  atop:[6] added b (3)
  working directory is now at 47ea25be8aea

prev with multiple parents

  $ hg log -GT "{rev}:{node|short} {desc}\n"
  @  8:47ea25be8aea added d
  |
  | o  7:5ce67c2407b0 added c
  |/
  o  6:d7f119adc759 added b (3)
  |
  o  0:a154386e50d1 added a
  
  $ hg merge -r 5ce67c2407b0
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "merge commit"

  $ hg prev <<EOF
  > q
  > EOF
  multiple parents, choose one to update:
  1: [47ea25be8aea] added d
  2: [5ce67c2407b0] added c
  q: quit the prompt
  enter the index of the revision you want to select: q
  [8] added d
  [7] added c
  multiple parents, explicitly update to one
  [1]

  $ hg prev --config ui.interactive=False
  [8] added d
  [7] added c
  multiple parents, explicitly update to one
  [1]

  $ hg prev <<EOF
  > 2
  > EOF
  multiple parents, choose one to update:
  1: [47ea25be8aea] added d
  2: [5ce67c2407b0] added c
  q: quit the prompt
  enter the index of the revision you want to select: 2
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [7] added c

  $ hg log -GT "{rev}:{node|short} {desc}\n"
  o    9:a4b8c25a87d3 merge commit
  |\
  | o  8:47ea25be8aea added d
  | |
  @ |  7:5ce67c2407b0 added c
  |/
  o  6:d7f119adc759 added b (3)
  |
  o  0:a154386e50d1 added a
  

  $ cd ..

prev and next should lock properly against other commands

  $ hg init repo
  $ cd repo
  $ cat >> .hg/hgrc << EOF
  > [ui]
  > timeout.warn = 0
  > EOF
  $ HGEDITOR="sh ${TESTDIR}/fake-editor.sh"
  $ echo hi > foo
  $ hg ci -Am 'one'
  adding foo
  $ echo bye > foo
  $ hg ci -Am 'two'

  $ hg amend --edit &
  $ sleep 1
  $ hg prev
  waiting for lock on working directory of $TESTTMP/repo held by process '*' on host '*' (glob)
  got lock after (\d+) seconds (re)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [0] one
  $ wait

  $ hg amend --edit &
  $ sleep 1
  $ hg next --evolve
  waiting for lock on working directory of $TESTTMP/repo held by process '*' on host '*' (glob)
  1 new orphan changesets
  got lock after (\d+) seconds (re)
  move:[2] two
  atop:[3] one
  working directory is now at ab3a85718ec9
  $ wait

testing next --evolve when working directory is dirty

  $ hg log -GT "{rev}:{node|short} {desc|firstline}"
  @  4:ab3a85718ec9 two
  |
  o  3:c741983992fc one
  

  $ hg up .^
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ echo foobar > bar
  $ hg add bar
  $ hg amend
  1 new orphan changesets

  $ echo babar > bar

  $ hg next --evolve
  abort: uncommitted changes
  (use `hg amend`, `hg revert` or `hg shelve`)
  [20]

  $ cd ..

Testing that `next` and `prev` respects `commands.update.check=noconflict`

  $ hg init noconflict
  $ cd noconflict
  $ echo "[commands]" >> .hg/hgrc
  $ echo "update.check=noconflict" >> .hg/hgrc

  $ echo hi > wat
  $ hg ci -Aqm "added wat"
  $ echo hi > foo
  $ hg ci -Aqm "added foo"
  $ echo hi > bar
  $ hg ci -Aqm "added bar"

testing for `hg prev`

  $ echo bar > wat
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [1] added foo
  $ hg diff
  diff -r cf959ce4e1ff wat
  --- a/wat	Thu Jan 01 00:00:00 1970 +0000
  +++ b/wat	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -hi
  +bar

testing for `hg next`

  $ hg next
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  [2] added bar
  $ hg diff
  diff -r ac3de1218820 wat
  --- a/wat	Thu Jan 01 00:00:00 1970 +0000
  +++ b/wat	Thu Jan 01 00:00:00 1970 +0000
  @@ -1,1 +1,1 @@
  -hi
  +bar

test that we dont end up in merge conflicts

  $ echo bar > bar
  $ hg prev
  abort: conflicting changes
  (do you want --merge?)
  [20]

  $ echo hi > bar
  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [1] added foo
  $ echo bar > bar
  $ hg add bar

  $ hg next
  abort: conflicting changes
  (do you want --merge?)
  [20]

Test that --merge still works fine with commands.update.check set

  $ hg config commands.update.check
  noconflict
  $ echo hi > bar
  $ echo bar >> bar
  $ hg next
  abort: conflicting changes
  (do you want --merge?)
  [20]
  $ hg next --merge
  merging bar
  warning: conflicts while merging bar! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  use 'hg resolve' to retry unresolved file merges
  [2] added bar

  $ echo babar > bar
  $ hg resolve -m
  (no more unresolved files)

Testing --merge works with other values of commands.update.check also

  $ hg prev --config commands.update.check=abort
  abort: uncommitted changes
  (do you want --merge?)
  [20]
  $ hg prev --merge --config commands.update.check=abort
  file 'bar' was deleted in other [destination] but was modified in local [working copy].
  You can use (c)hanged version, (d)elete, or leave (u)nresolved.
  What do you want to do? 
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  use 'hg resolve' to retry unresolved file merges
  [1] added foo

  $ hg revert --all
  forgetting bar
  reverting wat
  $ hg resolve -m
  (no more unresolved files)

  $ echo bar > bar
  $ hg add bar

  $ hg next --config commands.update.check=abort
  abort: uncommitted changes
  (do you want --merge?)
  [20]
  $ hg next --merge --config commands.update.check=abort
  merging bar
  warning: conflicts while merging bar! (edit, then use 'hg resolve --mark')
  0 files updated, 0 files merged, 0 files removed, 1 files unresolved
  use 'hg resolve' to retry unresolved file merges
  [2] added bar

Add test which shows that now `next` command does not get confused by split:
----------------------------------------------------------------------------
  $ cd ..
  $ mkdir nextconfused
  $ cd nextconfused
  $ hg init
  $ echo firstline > a
  $ hg add a
  $ hg ci -qm A
  $ echo bbbbb > b
  $ echo secondline >> a
  $ hg add b
  $ hg ci -qm B
  $ echo ccccc > c
  $ hg add c
  $ hg ci -qm C
  $ hg log -GT "{rev}:{node|short} {desc}\n"
  @  2:fdc998261dcb C
  |
  o  1:cc0edb0cc2b1 B
  |
  o  0:cae96ff49c84 A
  
  $ hg up 1
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg split << EOF
  > y
  > y
  > n
  > Y
  > y
  > y
  > EOF
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved
  reverting a
  adding b
  diff --git a/a b/a
  1 hunks, 1 lines changed
  examine changes to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -1,1 +1,2 @@
   firstline
  +secondline
  record change 1/2 to 'a'?
  (enter ? for help) [Ynesfdaq?] y
  
  diff --git a/b b/b
  new file mode 100644
  examine changes to 'b'?
  (enter ? for help) [Ynesfdaq?] n
  
  created new head
  continue splitting? [Ycdq?] Y
  diff --git a/b b/b
  new file mode 100644
  examine changes to 'b'?
  (enter ? for help) [Ynesfdaq?] y
  
  @@ -0,0 +1,1 @@
  +bbbbb
  record this change to 'b'?
  (enter ? for help) [Ynesfdaq?] y
  
  no more changes to split
  1 new orphan changesets

  $ hg up 3 -q
  $ hg log -GT "{rev}:{node|short} {desc}\n"
  o  4:279f6cab32b5 B
  |
  |
  |  new desc
  @  3:a9f74d07e45c B
  |
  |
  |  new desc
  | *  2:fdc998261dcb C
  | |
  | x  1:cc0edb0cc2b1 B
  |/
  o  0:cae96ff49c84 A
  
  $ hg ci --amend -m "B modified"
  1 new orphan changesets
  $ hg log -GT "{rev}:{node|short} {desc}\n"
  @  5:64ab03d3110c B modified
  |
  | *  4:279f6cab32b5 B
  | |
  | |
  | |  new desc
  | x  3:a9f74d07e45c B
  |/
  |
  |    new desc
  | *  2:fdc998261dcb C
  | |
  | x  1:cc0edb0cc2b1 B
  |/
  o  0:cae96ff49c84 A
  
  $ hg next --evolve << EOF
  > q
  > EOF
  move:[4] B
  atop:[5] B modified
  working directory is now at 1b434459c7e7

  $ cd ..

Testing --merge and --evolve flags: 1 child, 1 aspchild, dirty working copy

  $ hg init next-dirty-evolve
  $ cd next-dirty-evolve

  $ echo apple > a
  $ hg ci -qAm apple
  $ echo banana > b
  $ hg ci -qAm banana
  $ echo coconut > c
  $ hg ci -qAm coconut

  $ hg prev
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  [1] banana
  $ echo blueberry > b
  $ hg ci --amend -m blueberry
  1 new orphan changesets

  $ echo durian > d
  $ hg ci -qAm durian
  $ hg log -GT "{rev} {desc}\n"
  @  4 durian
  |
  o  3 blueberry
  |
  | *  2 coconut
  | |
  | x  1 banana
  |/
  o  0 apple
  

  $ hg up 'desc("blueberry")'
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo avocado > a

  $ hg next --no-merge --evolve --dry-run
  abort: uncommitted changes
  (use `hg amend`, `hg revert` or `hg shelve`)
  [20]
  $ hg next --no-merge --no-evolve --dry-run
  abort: uncommitted changes
  (do you want --merge?)
  [20]
  $ hg next --merge --no-evolve --dry-run
  hg update db0dc1f00682;
  [4] durian
  $ hg next --merge --evolve --dry-run
  abort: uncommitted changes
  (use `hg amend`, `hg revert` or `hg shelve`)
  [20]
