Testing evolve --continue with unresolved conflicts (issue5966)
https://bz.mercurial-scm.org/show_bug.cgi?id=5966

  $ . $TESTDIR/testlib/common.sh

  $ hg init issue5966
  $ cd issue5966
  $ cat > .hg/hgrc << EOF
  > [phases]
  > publish = false
  > [alias]
  > glog = log -GT "{rev}: {desc}"
  > [extensions]
  > evolve=
  > EOF

  $ touch a
  $ hg ci -Aqm 'empty'

  $ echo apple > a
  $ hg ci -m 'apple'
  $ echo banana > a
  $ hg ci -m 'banana'
  $ echo coconut > a
  $ hg ci -m 'coconut'

  $ hg glog
  @  3: coconut
  |
  o  2: banana
  |
  o  1: apple
  |
  o  0: empty
  

  $ hg up -q 1

Amending revision 1 in a way that causes conflicts

  $ echo apricot > a
  $ hg amend -m 'apricot'
  2 new orphan changesets

  $ hg glog --hidden
  @  4: apricot
  |
  | *  3: coconut
  | |
  | *  2: banana
  | |
  | x  1: apple
  |/
  o  0: empty
  

  $ hg evolve -t :fail --rev 'first(orphan())'
  move:[2] banana
  atop:[4] apricot
  unresolved merge conflicts
  (see 'hg help evolve.interrupted')
  [240]
  $ hg evolve --list
  34a690fcf6ab: banana
    orphan: 7f59f18ca4a9 (obsolete parent)
  
  feb8c0bffa1f: coconut
    orphan: 34a690fcf6ab (orphan parent)
  
Evolve should detect unresolved conflict.

  $ hg resolve --list
  U a
  $ hg evolve --continue
  abort: unresolved merge conflicts (see 'hg help resolve')
  [20]

(even when ran twice)

  $ hg evolve --continue
  abort: unresolved merge conflicts (see 'hg help resolve')
  [20]

  $ cat a
  apricot
  $ hg resolve --list
  U a
  $ hg resolve a -t :other
  (no more unresolved files)
  continue: hg evolve --continue
  $ hg resolve --list
  R a
  $ hg evolve --continue
  evolving 2:34a690fcf6ab "banana"
  $ hg resolve --list

evolve the rest of the stack

  $ hg evolve
  move:[3] coconut
  atop:[5] banana
  merging a

All commit evolved

  $ hg glog
  o  6: coconut
  |
  o  5: banana
  |
  @  4: apricot
  |
  o  0: empty
  
