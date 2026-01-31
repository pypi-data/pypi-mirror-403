https://www.mercurial-scm.org/wiki/TopicPlan#sub_branches.2C_namespacing_and_representation

  $ . "$TESTDIR/testlib/topic_setup.sh"

  $ hg init repo
  $ cd repo

Setting a topic namespace alone doesn't affect wdir()

  $ hg debug-topic-namespace space-name
  marked working directory as topic namespace: space-name
  $ hg debug-topic-namespaces
  space-name
  $ cat .hg/topic-namespace
  space-name (no-eol)

  $ hg log -r 'wdir()' -T '{topic_namespace}\n'
  none

  $ hg log -r 'wdir()' -T '{fqbn}\n'
  default

But after setting a topic the already-set namespace is visible on wdir()

  $ hg topic feature
  marked working directory as topic: feature
  $ hg topics
   * feature (0 changesets)

  $ hg log -r 'wdir()' -T '{topic_namespace}\n'
  space-name

  $ hg log -r 'wdir()' -T '{fqbn}\n'
  default//space-name/feature

Non-ascii topic namespace name

  $ hg debug-topic-namespace --clear
  $ test -f .hg/topic-namespace
  [1]
  $ hg --encoding utf-8 debug-topic-namespace æ
  marked working directory as topic namespace: \xc3\xa6 (esc)
  $ hg --encoding utf-8 debug-topic-namespaces
  æ (esc)
  $ hg --encoding ascii debug-topic-namespaces
  ? (esc)
  $ hg --encoding latin1 debug-topic-namespaces
  \xe6 (esc)
  $ cat .hg/topic-namespace
  \xc3\xa6 (no-eol) (esc)

  $ hg --encoding utf-8 debug-topic-namespace ©
  abort: invalid topic namespace name: '\xc2\xa9' (esc)
  (topic namespace names can only consist of alphanumeric, '-', '_' and '.' characters)
  [10]

  $ hg --encoding latin1 debug-topic-namespace æ
  abort: invalid topic namespace name: '\xc3\xa6' (esc)
  (topic namespace names can only consist of alphanumeric, '-', '_' and '.' characters)
  [10]

  $ hg branches

  $ hg debug-topic-namespace --clear
  $ hg debug-topic-namespaces

  $ hg topic --clear
  clearing empty topic "feature"
  $ hg topics

  $ hg debugtopicnamespace --clear nonsense
  abort: cannot use --clear when setting a topic namespace
  [255]

  $ hg branch stable
  marked working directory as branch stable
  (branches are permanent and global, did you want a bookmark?)
  $ hg debug-topic-namespace alice
  marked working directory as topic namespace: alice
  $ hg topic feature
  marked working directory as topic: feature
  $ echo a > a
  $ hg ci -qAm a

  $ hg debug-topic-namespaces
  alice

  $ hg log -r . -T '{rev}: {branch} {topic_namespace} {topic}\n'
  0: stable alice feature

  $ hg log -r . -T '{rev}: {fqbn}\n'
  0: stable//alice/feature

  $ hg log -r . -T '{rev}: {join(extras, " ")}\n'
  0: branch=stable topic=feature topic-namespace=alice

  $ hg branches
  stable//alice/feature          0:69c7dbf6acd1

Removing topic namespace file if it contains the default value

The default value changed from b'default' to b'none' in 11.1.0, this is a
safeguard against accidentally putting the new default tns value into commit
extras with an old version of topic extension

  $ printf 'none' > .hg/topic-namespace
  $ test -f .hg/topic-namespace
  $ hg ci -m ''
  nothing changed
  [1]
  $ test -f .hg/topic-namespace
  [1]

Updating to a revision with a namespace should activate it

  $ hg up null
  0 files updated, 0 files merged, 1 files removed, 0 files unresolved
  $ hg debug-topic-namespace
  none
  $ test -f .hg/topic-namespace
  [1]
  $ hg topics
     feature (1 changesets)
  $ test -f .hg/topic
  [1]
  $ hg up 0
  switching to topic-namespace alice
  switching to topic feature
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  $ hg debug-topic-namespace
  alice
  $ cat .hg/topic-namespace
  alice (no-eol)
  $ hg topics
   * feature (1 changesets)
  $ cat .hg/topic
  feature (no-eol)

Updating to a topic namespace is not supported

  $ hg up alice
  abort: unknown revision 'alice'
  [10]

Export/import of topic namespaces

  $ hg export
  # HG changeset patch
  # User test
  # Date 0 0
  #      Thu Jan 01 00:00:00 1970 +0000
  # Branch stable
  # Node ID 69c7dbf6acd180eeec055dd67933badd3601d45f
  # Parent  0000000000000000000000000000000000000000
  # EXP-Topic-Namespace alice
  # EXP-Topic feature
  a
  
  diff -r 000000000000 -r 69c7dbf6acd1 a
  --- /dev/null	Thu Jan 01 00:00:00 1970 +0000
  +++ b/a	Thu Jan 01 00:00:00 1970 +0000
  @@ -0,0 +1,1 @@
  +a

  $ hg import - << EOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Branch another-branch
  > # Node ID 1111111111111111111111111111111111111111
  > # Parent  2222222222222222222222222222222222222222
  > # EXP-Topic-Namespace mynamespace
  > # EXP-Topic mytopic
  > added z
  > 
  > diff --git a/z b/z
  > new file mode 100644
  > --- /dev/null
  > +++ b/z
  > @@ -0,0 +1,1 @@
  > +z
  > EOF
  applying patch from stdin

  $ hg log -r tip -T '{rev}: {branch} {topic_namespace} {topic}\n'
  1: stable mynamespace mytopic

  $ hg log -r tip -T '{rev}: {fqbn}\n'
  1: stable//mynamespace/mytopic

  $ hg log -r tip -T '{rev}: {join(extras, " ")}\n'
  1: branch=stable topic=mytopic topic-namespace=mynamespace

Importing a patch with default namespace and topic values

  $ hg import - << EOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Branch stable
  > # Node ID 1111111111111111111111111111111111111111
  > # Parent  2222222222222222222222222222222222222222
  > # EXP-Topic-Namespace none
  > # EXP-Topic 
  > more z
  > 
  > diff --git a/z b/z
  > --- a/z
  > +++ b/z
  > @@ -1,1 +1,1 @@
  > -z
  > +zebra
  > EOF
  applying patch from stdin

  $ hg log -r tip -T '{rev}: {branch} {topic_namespace} {topic}\n'
  2: stable none 

  $ hg log -r tip -T '{rev}: {fqbn}\n'
  2: stable

  $ hg log -r tip -T '{rev}: {join(extras, " ")}\n'
  2: branch=stable

Importing a patch with topic namespace set and topic unset

  $ hg import - << EOF
  > # HG changeset patch
  > # User test
  > # Date 0 0
  > #      Thu Jan 01 00:00:00 1970 +0000
  > # Branch stable
  > # Node ID 1111111111111111111111111111111111111111
  > # Parent  2222222222222222222222222222222222222222
  > # EXP-Topic-Namespace mynamespace
  > # EXP-Topic 
  > more z
  > 
  > diff --git a/z b/z
  > --- a/z
  > +++ b/z
  > @@ -1,1 +1,1 @@
  > -zebra
  > +z
  > EOF
  applying patch from stdin

  $ hg log -r tip -T '{rev}: {branch} {topic_namespace} {topic}\n'
  3: stable none 

  $ hg log -r tip -T '{rev}: {fqbn}\n'
  3: stable

  $ hg log -r tip -T '{rev}: {join(extras, " ")}\n'
  3: branch=stable

Revsets

  $ nslog() {
  >   hg log -T '{rev}: {topic_namespace}\n' -r "$1"
  > }

  $ nslog 'topicnamespace()'
  0: alice
  1: mynamespace
  $ nslog 'topicnamespace(:)'
  0: alice
  1: mynamespace
  $ nslog 'topicnamespace(all())'
  0: alice
  1: mynamespace
  $ nslog 'topicnamespace(topicnamespace("alice"))'
  0: alice
  $ nslog 'topicnamespace(wdir())'
  0: alice
  $ nslog 'topicnamespace("re:ice$")'
  0: alice
  $ nslog 'topicnamespace(nonsense)'
  abort: unknown revision 'nonsense'
  [10]

  $ nslog 'topicnamespace("re:nonsense")'
  $ nslog 'topicnamespace("literal:nonsense")'
  abort: topic namespace 'nonsense' does not exist
  [10]

Debug command related to the default/empty topic namespace

  $ hg debug-topic-namespace --clear

  $ echo none > none
  $ hg ci -qAm 'tns=none' \
  >    --config extensions.topic=! \
  >    --config extensions.commitextras= \
  >    --extra topic-namespace=none


  $ echo default > default
  $ hg ci -qAm 'tns=default' \
  >   --config extensions.topic=! \
  >   --config extensions.commitextras= \
  >   --extra topic-namespace=default

  $ hg debug-default-topic-namespace \
  >   --debug \
  >   | grep extra
  extra:       branch=stable
  extra:       topic-namespace=none

  $ hg debug-default-topic-namespace \
  >   --no-none \
  >   --default \
  >   --debug \
  >   | grep extra
  extra:       branch=stable
  extra:       topic-namespace=default

  $ hg debug-default-topic-namespace \
  >   --default \
  >   -T '{rev}:{node|short} {join(extras, " ")}\n'
  4:29a2d0acd473 branch=stable topic-namespace=none
  5:16d6061fce0c branch=stable topic-namespace=default

  $ hg debug-default-topic-namespace --none --default --clear

  $ hg debug-default-topic-namespace --none --default

  $ hg evolve --config extensions.evolve= --list

  $ hg evolve --config extensions.evolve= --any
  update:[7] tns=default
  0 files updated, 0 files merged, 0 files removed, 0 files unresolved
  working directory is now at 38c9ea9d27a7

  $ hg debug-default-topic-namespace --none --default

  $ hg verify --quiet

Parsing

  $ hg debugparsefqbn foo/bar//user26/feature -T '[{branch}] <{topic_namespace}> ({topic})\n'
  [foo/bar] <user26> (feature)

no double slashes means it's a named branch
  $ hg debug-parse-fqbn foo/bar
  branch:    foo/bar
  namespace: none
  topic:     

Formatting

  $ hg debugformatfqbn -b branch -n namespace -t topic
  branch//namespace/topic

  $ hg debug-format-fqbn -n namespace
  //namespace/

  $ hg debug-format-fqbn -b foo/bar -n user26 -t feature
  foo/bar//user26/feature

default values

  $ hg debug-format-fqbn -b default -n none -t '' --no-short
  default//none/
  $ hg debug-format-fqbn -b default -n none -t '' --short
  default

  $ hg debug-format-fqbn -b default -n namespace -t '' --no-short
  default//namespace/
  $ hg debug-format-fqbn -b default -n namespace -t '' --short
  default//namespace/

  $ hg debug-format-fqbn -b default -n none -t topic --no-short
  default//none/topic
  $ hg debug-format-fqbn -b default -n none -t topic --short
  default//topic

  $ cd ..
