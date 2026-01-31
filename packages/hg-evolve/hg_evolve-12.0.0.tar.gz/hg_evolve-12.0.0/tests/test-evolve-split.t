Check that evolve can handle split commits
------------------------------------------

  $ cat >> $HGRCPATH <<EOF
  > [ui]
  > logtemplate = {rev}:{node|short}@{branch}({phase}) {desc|firstline}\n
  > [extensions]
  > EOF
  $ echo "evolve=$(echo $(dirname $TESTDIR))/hgext3rd/evolve/" >> $HGRCPATH
  $ mkcommit() {
  >    echo "$1" > "$1"
  >    hg add "$1"
  >    hg ci -m "add $1"
  > }

  $ hg init split
  $ cd split
  $ mkcommit aa

Create a split commit
  $ printf "oo" > oo;
  $ printf "pp" > pp;
  $ hg add oo pp
  $ hg commit -m "oo+pp"
  $ mkcommit uu
  $ hg up 0
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ printf "oo" > oo;
  $ hg add oo
  $ hg commit -m "_oo"
  created new head
  $ printf "pp" > pp;
  $ hg add pp
  $ hg commit -m "_pp"
  $ hg prune --successor "desc(_oo) + desc(_pp)" -r "desc('oo+pp')" --split
  1 changesets pruned
  1 new orphan changesets
  $ hg log -G
  @  4:d0dcf24cddd3@default(draft) _pp
  |
  o  3:a7fdfda64c08@default(draft) _oo
  |
  | *  2:f52200b086ca@default(draft) add uu
  | |
  | x  1:d55647aaa0c6@default(draft) oo+pp
  |/
  o  0:58663bb03074@default(draft) add aa
  
  $ hg evolve --rev "0::"
  move:[2] add uu
  atop:[4] _pp

  $ cd ..
  $ hg init split-merged
  $ cd split-merged
  $ mkcommit aa

Split the changeset such that the successors don't have a single root and there's an unrelated changeset in between
  $ printf "oo" > oo;
  $ printf "pp" > pp;
  $ printf "qq" > qq;
  $ hg add oo pp qq
  $ hg commit -m "oo+pp+qq"
  $ mkcommit uu
  $ hg up 0
  0 files updated, 0 files merged, 4 files removed, 0 files unresolved
  $ printf "oo" > oo;
  $ hg add oo
  $ hg commit -m "_oo"
  created new head
  $ hg up 0
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ printf "pp" > pp;
  $ hg add pp
  $ hg commit -m "_pp"
  created new head
  $ hg merge 3
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg ci -m 'merge oo and pp'
  $ printf "qq" > qq;
  $ hg add qq
  $ hg commit -m "_qq"
  $ hg prune --successor "desc(_oo) + desc(_pp) + desc(_qq)" -r "desc('oo+pp+qq')" --split
  1 changesets pruned
  1 new orphan changesets
  $ hg log -G
  @  6:ea5b1e180c04@default(draft) _qq
  |
  o    5:bf7c32161b4b@default(draft) merge oo and pp
  |\
  | o  4:ece0aaa22eb7@default(draft) _pp
  | |
  o |  3:a7fdfda64c08@default(draft) _oo
  |/
  | *  2:cc56c47d84b3@default(draft) add uu
  | |
  | x  1:575a7380a87d@default(draft) oo+pp+qq
  |/
  o  0:58663bb03074@default(draft) add aa
  
  $ hg evolve --rev "0::"
  move:[2] add uu
  atop:[6] _qq
