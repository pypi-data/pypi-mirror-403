#testcases abortcontinuecommand abortcontinueflag
Test for the pick command

  $ cat >> $HGRCPATH <<EOF
  > [alias]
  > glog = log -G -T "{rev}:{node|short} {desc}\n"
  > glf = log -GT "{rev}: {desc} ({files})\n"
  > [extensions]
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

#if abortcontinueflag
  $ cat >> $HGRCPATH <<EOF
  > [alias]
  > abort = pick --abort
  > continue = pick --continue
  > EOF
#endif

  $ mkcommit() {
  >    echo "$1" > "$1"
  >    hg add "$1"
  >    hg ci -m "add $1"
  > }

  $ hg init repo
  $ cd repo
  $ hg help pick | sed 's/^    //'
  hg pick [OPTION]... [-r] REV
  
  aliases: grab
  
  move a commit onto the working directory parent and update to it.
  
  The resulting changeset will have the current active topic. If there's no
  active topic set, the resulting changeset will also not have any topic.
  
  options:
  
   -r --rev REV   revision to pick
   -c --continue  continue interrupted pick
   -a --abort     abort interrupted pick
   -t --tool TOOL specify merge tool
  
  (some details hidden, use --verbose to show complete help)

  $ mkcommit a
  $ mkcommit b
  $ mkcommit c

  $ hg glog
  @  2:4538525df7e2 add c
  |
  o  1:7c3bad9141dc add b
  |
  o  0:1f0dee641bb7 add a
  

Grabbing an ancestor

  $ hg pick -r 7c3bad9141dc
  abort: cannot pick an ancestor revision
  [255]

Grabbing the working directory parent

  $ hg pick -r .
  abort: cannot pick an ancestor revision
  [255]

Specifying multiple revisions to pick

  $ hg pick 1f0dee641bb7 -r 7c3bad9141dc
  abort: specify just one revision
  [255]

Specifying no revisions to pick

  $ hg pick
  abort: empty revision set
  [255]

Continuing without interrupted pick

  $ hg pick --continue
  abort: no interrupted pick state exists
  [20]
#if abortcontinuecommand
  $ hg continue
  abort: no operation in progress
  [20]
#endif

Aborting without interrupted pick

  $ hg pick --abort
  abort: no interrupted pick state exists
  [20]
#if abortcontinuecommand
  $ hg abort
  abort: no operation in progress
  [20]
#endif

Specifying both continue and revs

  $ hg up 1f0dee641bb7
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ hg pick -r 4538525df7e2 --continue
  abort: cannot specify both --continue and revision
  [255]

Making new branch heads

  $ mkcommit x
  created new head
  $ mkcommit y

  $ hg glog
  @  4:d46dc301d92f add y
  |
  o  3:8e224524cd09 add x
  |
  | o  2:4538525df7e2 add c
  | |
  | o  1:7c3bad9141dc add b
  |/
  o  0:1f0dee641bb7 add a
  
Grabbing a revision

  $ hg pick 7c3bad9141dc
  picking 1:7c3bad9141dc "add b"
  1 new orphan changesets
  $ hg glog
  @  5:7c15c05db6fa add b
  |
  o  4:d46dc301d92f add y
  |
  o  3:8e224524cd09 add x
  |
  | *  2:4538525df7e2 add c
  | |
  | x  1:7c3bad9141dc add b
  |/
  o  0:1f0dee641bb7 add a
  

When pick does not create any changes

  $ hg graft -r 4538525df7e2
  grafting 2:4538525df7e2 "add c"

  $ hg glog
  @  6:c4636a81ebeb add c
  |
  o  5:7c15c05db6fa add b
  |
  o  4:d46dc301d92f add y
  |
  o  3:8e224524cd09 add x
  |
  | *  2:4538525df7e2 add c
  | |
  | x  1:7c3bad9141dc add b
  |/
  o  0:1f0dee641bb7 add a
  
  $ hg pick -r 4538525df7e2
  picking 2:4538525df7e2 "add c"
  note: picking 2:4538525df7e2 created no changes to commit

  $ hg glog
  @  6:c4636a81ebeb add c
  |
  o  5:7c15c05db6fa add b
  |
  o  4:d46dc301d92f add y
  |
  o  3:8e224524cd09 add x
  |
  o  0:1f0dee641bb7 add a
  

there were no changes to commit, so there shouldn't be any predecessors of 6,
and 2 should say it was pruned (issue6093)

  $ hg debugobsolete
  7c3bad9141dcb46ff89abf5f61856facd56e476c 7c15c05db6fa1458a8a745f977f4d2426abde6a0 0 (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '4', 'operation': 'pick', 'user': 'test'}
  4538525df7e2b9f09423636c61ef63a4cb872a2d 0 {7c3bad9141dcb46ff89abf5f61856facd56e476c} (Thu Jan 01 00:00:00 1970 +0000) {'ef1': '0', 'operation': 'pick', 'user': 'test'}
  $ hg olog --all --hidden -r 2+6
  x  4538525df7e2 (2) add c
       pruned using pick by test (Thu Jan 01 00:00:00 1970 +0000)
  
  @  c4636a81ebeb (6) add c
  

interrupted pick

  $ hg up d46dc301d92f
  0 files updated, 0 files merged, 2 files removed, 0 files unresolved
  $ echo foo > c
  $ hg ci -Aqm "foo to c"
  $ hg pick -r c4636a81ebeb
  picking 6:c4636a81ebeb "add c"
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts (see hg help resolve)
  [240]

  $ echo foobar > c
  $ hg resolve --all --mark
  (no more unresolved files)
  continue: hg pick --continue
#if abortcontinuecommand
  $ hg continue --dry-run
  pick in progress, will be resumed
#endif
  $ hg continue
  $ hg glog
  @  8:44e155eb95c7 add c
  |
  o  7:2ccc03d1d096 foo to c
  |
  | o  5:7c15c05db6fa add b
  |/
  o  4:d46dc301d92f add y
  |
  o  3:8e224524cd09 add x
  |
  o  0:1f0dee641bb7 add a
  

When interrupted pick results in no changes to commit

  $ hg up d46dc301d92f
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo bar > c
  $ hg add c
  $ hg ci -m "foo to c"
  created new head

  $ hg up 44e155eb95c7
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved

  $ hg pick 4e04628911f6
  picking 9:4e04628911f6 "foo to c"
  merging c
  warning: conflicts while merging c! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts (see hg help resolve)
  [240]
  $ echo foobar > c
  $ hg resolve -m
  (no more unresolved files)
  continue: hg pick --continue

  $ hg continue
  note: picking 9:4e04628911f6 created no changes to commit

Testing the abort functionality of hg pick

  $ echo foo > b
  $ hg ci -Aqm "foo to b"
  $ hg glog -r .^::
  @  10:c437988de89f foo to b
  |
  o  8:44e155eb95c7 add c
  |
  ~

  $ hg pick -r 7c15c05db6fa
  picking 5:7c15c05db6fa "add b"
  merging b
  warning: conflicts while merging b! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts (see hg help resolve)
  [240]

#if abortcontinuecommand
  $ hg abort --dry-run
  pick in progress, will be aborted
#endif
  $ hg abort
  pick aborted
  working directory is now at c437988de89f

  $ hg glog
  @  10:c437988de89f foo to b
  |
  o  8:44e155eb95c7 add c
  |
  o  7:2ccc03d1d096 foo to c
  |
  | o  5:7c15c05db6fa add b
  |/
  o  4:d46dc301d92f add y
  |
  o  3:8e224524cd09 add x
  |
  o  0:1f0dee641bb7 add a
  

Trying to pick a public changeset

  $ hg phase -r 7c15c05db6fa -p

  $ hg pick -r 7c15c05db6fa
  abort: cannot pick public changesets: 7c15c05db6fa
  (see 'hg help phases' for details)
  [10]

  $ hg glog
  @  10:c437988de89f foo to b
  |
  o  8:44e155eb95c7 add c
  |
  o  7:2ccc03d1d096 foo to c
  |
  | o  5:7c15c05db6fa add b
  |/
  o  4:d46dc301d92f add y
  |
  o  3:8e224524cd09 add x
  |
  o  0:1f0dee641bb7 add a
  
Checking phase preservation while picking secret changeset

In case of merge conflicts

  $ hg phase -r 7c15c05db6fa -s -f

  $ hg pick -r 7c15c05db6fa
  picking 5:7c15c05db6fa "add b"
  merging b
  warning: conflicts while merging b! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts (see hg help resolve)
  [240]

  $ echo bar > b
  $ hg resolve -m
  (no more unresolved files)
  continue: hg pick --continue

  $ hg continue
  $ hg phase -r .
  11: secret

No merge conflicts

  $ hg up d46dc301d92f
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ echo foo > l
  $ hg add l
  $ hg ci -qm "added l" --secret

  $ hg phase -r .
  12: secret

  $ hg glog
  @  12:508d572e7053 added l
  |
  | o  11:10427de9e26e add b
  | |
  | o  10:c437988de89f foo to b
  | |
  | o  8:44e155eb95c7 add c
  | |
  | o  7:2ccc03d1d096 foo to c
  |/
  o  4:d46dc301d92f add y
  |
  o  3:8e224524cd09 add x
  |
  o  0:1f0dee641bb7 add a
  
  $ hg up 10427de9e26e
  3 files updated, 0 files merged, 1 files removed, 0 files unresolved

  $ hg pick -r 508d572e7053
  picking 12:508d572e7053 "added l"

  $ hg phase -r .
  13: secret

Pick rewrites node hashes in commit description

  $ echo 'hg pick rewrites hashes 1' > l
  $ hg ci -m '1705aa17bfed is my parent'
  $ echo 'hg pick rewrites hashes 2' > l
  $ hg ci -m 'f9ed1703aa00 is my parent'

  $ hg glog -r .^^::
  @  15:e3cb66090723 f9ed1703aa00 is my parent
  |
  o  14:f9ed1703aa00 1705aa17bfed is my parent
  |
  o  13:1705aa17bfed added l
  |
  ~

  $ hg up -q c437988de89f
  $ hg pick 13
  picking 13:1705aa17bfed "added l"
  2 new orphan changesets
  $ hg pick 14
  picking 14:f9ed1703aa00 "1705aa17bfed is my parent"
  $ hg pick 15
  picking 15:e3cb66090723 "f9ed1703aa00 is my parent"

  $ hg glog -r .^^::
  @  18:5825531d1322 7a6997f82fbe is my parent
  |
  o  17:7a6997f82fbe fb6281ea03e8 is my parent
  |
  o  16:fb6281ea03e8 added l
  |
  ~

  $ cd ..

Check pick behavior regarding working copy branch (issue6089)
-------------------------------------------------------------

The branch of the picked changeset should be preserved, and the working copy updated

  $ hg init issue6089
  $ cd issue6089

  $ touch a
  $ hg add a
  $ hg ci -m 'first commit on default'

  $ hg branch foo
  marked working directory as branch foo
  (branches are permanent and global, did you want a bookmark?)
  $ touch b
  $ hg add b
  $ hg ci -m 'first commit on foo'

  $ hg up default
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo test > a
  $ hg ci -m 'second commit on default'
  $ hg log -G --template '{node|short}: {branch}\n' --rev 'all()+wdir()'
  o  ffffffffffff: default
  |
  @  5f07cbf7d111: default
  |
  | o  96bb2057779e: foo
  |/
  o  d03a6bcc83cd: default
  

  $ hg pick 1
  picking 1:96bb2057779e "first commit on foo"
  $ hg log --template '{branch}\n' -r tip
  foo
  $ hg branch
  foo
  $ hg log -G --template '{node|short}: {branch}\n' --rev 'all()+wdir()'
  o  ffffffffffff: foo
  |
  @  5344a77549bd: foo
  |
  o  5f07cbf7d111: default
  |
  o  d03a6bcc83cd: default
  
  $ cd ..

Check that pick doesn't drop files after conflicts occur (issue6037)
--------------------------------------------------------------------

  $ hg init issue6037
  $ cd issue6037

  $ echo apple > a
  $ hg ci -qAm 'apple'

  $ echo apricot > a
  $ echo banana > b
  $ hg ci -qAm 'apricot and banana'

  $ echo avocado > a
  $ hg ci -m 'avocado'

  $ hg glf
  @  2: avocado (a)
  |
  o  1: apricot and banana (a b)
  |
  o  0: apple (a)
  
Now let's change order of 1 and 2 using pick command

  $ hg up -r 0
  1 files updated, 0 files merged, 1 files removed, 0 files unresolved

We avoid merge conflict here just to make the test shorter

  $ hg pick -r 2 --tool :other
  picking 2:f08a1e4a33c4 "avocado"

Now we pick revision 1 that touches two files (a and b), merge conflict is expected

  $ hg pick -r 1
  picking 1:892e123ebf62 "apricot and banana"
  merging a
  warning: conflicts while merging a! (edit, then use 'hg resolve --mark')
  unresolved merge conflicts (see hg help resolve)
  [240]
  $ hg resolve -t :other a
  (no more unresolved files)
  continue: hg pick --continue
  $ hg continue

Demonstrate that b was not forgotten and is definitely included in 4

  $ hg status b -A
  C b
  $ hg glf
  @  4: apricot and banana (a b)
  |
  o  3: avocado (a)
  |
  o  0: apple (a)
  
  $ cd ..
