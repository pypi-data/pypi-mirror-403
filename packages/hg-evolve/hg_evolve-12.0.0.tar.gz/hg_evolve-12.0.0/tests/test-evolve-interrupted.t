Quitting an evolve in the middle (via ctrl-c or something) can leave things in a
weird intermediate state where hg thinks we're in the middle of an update
operation (or even just leave the 'merge' directory around without actually
indicating we're in the middle of *any* operation).

  $ . $TESTDIR/testlib/common.sh

  $ cat << EOF >> $HGRCPATH
  > [extensions]
  > rebase =
  > evolve =
  > [alias]
  > l = log -G -T'{rev} {desc}'
  > EOF

  $ hg init interrupted-orphan
  $ cd interrupted-orphan

  $ echo apricot > a
  $ hg ci -qAm apricot

  $ echo banana > b
  $ hg ci -qAm banana

Let's go back to amend 0 and make an orphan out of 1 (and a merge conflict to
test with)

  $ hg up -q 0
  $ echo blueberry > b
  $ hg l
  o  1 banana
  |
  @  0 apricot
  
  $ hg ci --amend -qAm 'apricot and blueberry'
  1 new orphan changesets
  $ hg l
  @  2 apricot and blueberry
  
  *  1 banana
  |
  x  0 apricot
  

  $ hg evolve --update --config hooks.precommit=false --config ui.merge=:other
  move:[1] banana
  atop:[2] apricot and blueberry
  transaction abort! (no-hg64 !)
  rollback completed (no-hg64 !)
  abort: precommit hook exited with status 1
  [40]
  $ hg l
  @  2 apricot and blueberry
  
  *  1 banana
  |
  x  0 apricot
  
  $ cat b
  banana

  $ hg status --config commands.status.verbose=True
  M b
  # The repository is in an unfinished *evolve* state.
  
  # No unresolved merge conflicts.
  
  # To continue:    hg evolve --continue
  # To abort:       hg evolve --abort
  # To stop:        hg evolve --stop
  # (also see `hg help evolve.interrupted`)
  

  $ ls .hg/evolvestate
  .hg/evolvestate

  $ cat b
  banana

  $ hg l
  @  2 apricot and blueberry
  
  *  1 banana
  |
  x  0 apricot
  

Test various methods of handling that unfinished state
  $ hg evolve --abort
  evolve aborted
  working directory is now at e1989e4b1526
  $ test -f .hg/evolvestate
  [1]
  $ cat b
  blueberry
  $ hg l
  @  2 apricot and blueberry
  
  *  1 banana
  |
  x  0 apricot
  

  $ hg evolve --update --config hooks.precommit=false --config ui.merge=:other
  move:[1] banana
  atop:[2] apricot and blueberry
  transaction abort! (no-hg64 !)
  rollback completed (no-hg64 !)
  abort: precommit hook exited with status 1
  [40]
  $ cat b
  banana
  $ hg evolve --stop
  stopped the interrupted evolve
  working directory is now at e1989e4b1526
  $ cat .hg/evolvestate
  cat: .hg/evolvestate: No such file or directory
  [1]
  $ cat b
  blueberry
  $ hg l
  @  2 apricot and blueberry
  
  *  1 banana
  |
  x  0 apricot
  

  $ hg evolve --update --config hooks.precommit=false --config ui.merge=:other
  move:[1] banana
  atop:[2] apricot and blueberry
  transaction abort! (no-hg64 !)
  rollback completed (no-hg64 !)
  abort: precommit hook exited with status 1
  [40]
  $ hg evolve --continue
  evolving 1:e0486f65907d "banana"
  working directory is now at b10ea0f329d2
  $ cat .hg/evolvestate
  cat: .hg/evolvestate: No such file or directory
  [1]
  $ cat b
  banana
  $ hg l
  @  3 banana
  |
  o  2 apricot and blueberry
  
