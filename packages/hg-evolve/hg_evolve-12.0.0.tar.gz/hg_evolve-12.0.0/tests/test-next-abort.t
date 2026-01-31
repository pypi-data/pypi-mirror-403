Testing hg next with --abort flag and hg abort command handling an interrupted hg next

  $ . "$TESTDIR/testlib/common.sh"

  $ cat >> "$HGRCPATH" << EOF
  > [extensions]
  > evolve =
  > EOF

  $ hg init next-abort
  $ cd next-abort

  $ echo apple > a
  $ hg ci -qAm apple
  $ echo banana > b
  $ hg ci -qAm banana
  $ hg up 0
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo blueberry > b
  $ hg ci -qAm 'apple and blueberry' --amend
  1 new orphan changesets

  $ hg next
  move:[1] banana
  atop:[2] apple and blueberry
  merging b
  warning: conflicts while merging b! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]

#testcases abortcommand abortflag
#if abortflag
  $ hg next --abort
  next aborted
  working directory is now at 1c7f51cf0ef0
  $ hg next --abort
  abort: no interrupted next to abort
  [20]
  $ hg evolve --abort
  abort: no interrupted evolve to abort
  [20]

  $ hg next --abort --move-bookmark
  abort: cannot specify both --abort and --move-bookmark
  [10]
  $ hg next --abort --merge
  abort: cannot specify both --abort and --merge
  [10]
#else
  $ hg abort --dry-run
  evolve in progress, will be aborted
  $ hg abort
  evolve aborted
  working directory is now at 1c7f51cf0ef0
  $ hg abort
  abort: no operation in progress
  [20]
#endif

  $ cd ..
