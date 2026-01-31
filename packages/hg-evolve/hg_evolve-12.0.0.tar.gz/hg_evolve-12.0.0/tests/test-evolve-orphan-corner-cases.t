=======================================================
Tests the resolution of orphan changesets: corner cases
=======================================================

Setup
=====
  $ cat >> $HGRCPATH <<EOF
  > [alias]
  > glog = log -GT "{rev}:{node|short} {desc|firstline}\n {phase} {troubles}\n\n"
  > [phases]
  > publish = False
  > [extensions]
  > rebase =
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH

  $ glog() {
  >   hg log -G --template '{rev}:{node|short}@{branch}({phase}) {desc|firstline}\n' "$@"
  > }

Test to make sure that `lastsolved` always has correct value and things don't break:
------------------------------------------------------------------------------------
(before we were not updating it in case of orphan merge)

Prepare the repo:
  $ hg init orphanmergerepo
  $ cd orphanmergerepo
  $ for fn in a b c; do echo foo > $fn; hg ci -Am "added "$fn; done;
  adding a
  adding b
  adding c
Let's create a merge commit so that we can create orphan merge later:
  $ hg up 1 -q
  $ echo feature > f
  $ hg ci -Am "added feature f"
  adding f
  created new head
  $ hg merge
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m "merge feature branch"
  $ glog
  @    4:2c0a98d38026@default(draft) merge feature branch
  |\
  | o  3:4c33e511041e@default(draft) added feature f
  | |
  o |  2:8be98ac1a569@default(draft) added c
  |/
  o  1:80e6d2c47cfe@default(draft) added b
  |
  o  0:f7ad41964313@default(draft) added a
  

Now make the parents of merge commit obsolete to get a orphan merge:
  $ hg up 2 -q
  $ echo "fixit" > c
  $ hg ci --amend -m "updated c"
  1 new orphan changesets
  $ hg up 3 -q
  $ echo "fixit" > c
  $ hg ci --amend -m "updated f"
  $ glog
  @  6:086d9bedcd75@default(draft) updated f
  |
  | o  5:f84f2c548fbc@default(draft) updated c
  |/
  | *    4:2c0a98d38026@default(draft) merge feature branch
  | |\
  +---x  3:4c33e511041e@default(draft) added feature f
  | |
  | x  2:8be98ac1a569@default(draft) added c
  |/
  o  1:80e6d2c47cfe@default(draft) added b
  |
  o  0:f7ad41964313@default(draft) added a
  

To check `lastsolved` contain right value after completion of orphan-merge
resolution there should be one more instability to be evolved; lets create one:
  $ hg up 1 -q
  $ echo d > d
  $ hg ci -Am "added d"
  adding c
  adding d
  created new head
  $ echo e > e
  $ hg ci -Am "added e"
  adding e
  $ hg up .^
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ echo "updated d" >> d
  $ hg ci --amend -m "updated d"
  1 new orphan changesets
  $ glog
  @  9:7c4d1834c346@default(draft) updated d
  |
  | *  8:421f7614462a@default(draft) added e
  | |
  | x  7:afe5acea1990@default(draft) added d
  |/
  | o  6:086d9bedcd75@default(draft) updated f
  |/
  | o  5:f84f2c548fbc@default(draft) updated c
  |/
  | *    4:2c0a98d38026@default(draft) merge feature branch
  | |\
  +---x  3:4c33e511041e@default(draft) added feature f
  | |
  | x  2:8be98ac1a569@default(draft) added c
  |/
  o  1:80e6d2c47cfe@default(draft) added b
  |
  o  0:f7ad41964313@default(draft) added a
  
Now we have one orphan merge and one more orphan cset that we just created.
Lets evolve:
  $ hg evolve --all --any
  move:[4] merge feature branch
  atop:[5] updated c
  move:[10] merge feature branch
  atop:[6] updated f
  move:[8] added e
  atop:[9] updated d
