.. Copyright 2011 Pierre-Yves David <pierre-yves.david@ens-lyon.org>
..                Logilab SA        <contact@logilab.fr>

-----------------------------------
Terminology of the obsolete concept
-----------------------------------

Obsolete markers
----------------

The mutable concept is based on **obsolete markers**. Creating an obsolete
marker registers a relation between an old obsoleted changeset and its newer
version.

Old changesets are called **predecessors** while their new versions are called
**successors**. A marker always registers a single *predecessor* and:

- no *successor*: the *predecessor* is just discarded.
- one *successor*: the *predecessor* has been rewritten
- multiple *successors*: the *predecessor* were splits in multiple
  changesets.

.. The *predecessors* and *successors* terms can be used on changeset directly:

.. :predecessors: of a changeset `A` are changesets used as *predecessors* by
..              obsolete marker using changeset `A` as *successors*

.. :successors: of a changeset `B` are changesets used as *successors* by
..              obsolete marker using changeset `B` as *predecessors*

Chaining obsolete markers is allowed to rewrite a changeset that is already a
*successor*. This is a kind of *second order version control*.
To clarify ambiguous situations one can use **direct predecessors** or
**direct successors** to name changesets that are directly related.

The set of all *obsolete markers* forms a direct acyclic graph the same way
standard *parents*/*children* relation does. In this graph we have:

:any predecessors: are transitive predecessors of a changeset: *direct predecessors*
                 and *predecessors* of *predecessors*.

:any successors: are transitive successors of a changeset: *direct successors*
                 and *successors*  of *successors*)

Obsolete markers may refer changesets that are not known locally.
So, *direct predecessors* of a changeset may be unknown locally.
This is why we usually focus on the **first known predecessors**  of the rewritten
changeset. The same apply for *successors*.

Changeset in *any successors* which are not **obsolete** are called
**newest successors**..

.. note:: I'm not very happy with this naming scheme and I'm looking for a
          better distinction between *direct successors* and **any successors**.

Possible changesets "type"
--------------------------

The following table describes names and behaviors of changesets affected by
obsolete markers. The left column describes generic categories and the right
columns are about sub-categories.


+---------------------+--------------------------+-----------------------------+
| **mutable**         | **obsolete**             | **extinct**                 |
|                     |                          |                             |
| Changeset in either | Obsolete changeset is    | *extinct* changeset is      |
| *draft* or *secret* | *mutable* used as a      | *obsolete* which has only   |
| phase.              | *predecessor*.           | *obsolete* descendants.     |
|                     |                          |                             |
|                     | A changeset is used as   | They can safely be:         |
|                     | a *predecessor* when at  |                             |
|                     | least one obsolete       | - hidden in the UI,         |
|                     | marker refers to it      | - silently excluded from    |
|                     | as predecessors.         |   pull and push operations  |
|                     |                          | - mostly ignored            |
|                     |                          | - garbage collected         |
|                     |                          |                             |
|                     |                          +-----------------------------+
|                     |                          |                             |
|                     |                          | **suspended**               |
|                     |                          |                             |
|                     |                          | *suspended* changeset is    |
|                     |                          | *obsolete* with at least    |
|                     |                          | one non-obsolete descendant |
|                     |                          |                             |
|                     |                          | Those descendants prevent   |
|                     |                          | properties of extinct       |
|                     |                          | changesets to apply. But    |
|                     |                          | they will refuse to be      |
|                     |                          | pushed without --force.     |
|                     |                          |                             |
|                     +--------------------------+-----------------------------+
|                     |                          |                             |
|                     | **unstable**             | **orphan**                  |
|                     |                          |                             |
|                     | *unstable*    has        | *orphan* is a changeset     |
|                     | unresolved issue caused  | with obsolete ancestors.    |
|                     | by *obsolete* relations. |                             |
|                     |                          |                             |
|                     | Possible issues are      | It must be rebased on a     |
|                     | listed in the next       | non *unstable*    base to   |
|                     | column. It is possible   | solve the problem.          |
|                     | for *unstable*           |                             |
|                     | changeset to combine     | (possible alternative name: |
|                     | multiple issue at once.  | precarious)                 |
|                     | (a.k.a. content-divergent|                             |
|                     | and orphan)              +-----------------------------+
|                     |                          |                             |
|                     | (possible alternative    | **phase-divergent**         |
|                     | names: unsettled,        |                             |
|                     | troublesome              | *phase-divergent* is a      |
|                     |                          | changeset that tries to be  |
|                     |                          | successor of a public       |
|                     |                          | changeset.                  |
|                     |                          |                             |
|                     |                          | Public changeset can't      |
|                     |                          | be deleted and replace      |
|                     |                          | *phase-divergent*           |
|                     |                          | need to be converted into   |
|                     |                          | an overlay to this public   |
|                     |                          | changeset.                  |
|                     |                          |                             |
|                     |                          | (possible alternative names:|
|                     |                          | mislead, naive, unaware,    |
|                     |                          | mindless, disenchanting)    |
|                     |                          |                             |
|                     |                          +-----------------------------+
|                     |                          | **content-divergent**       |
|                     |                          |                             |
|                     |                          | *content-divergent*   is a  |
|                     |                          | changeset that appears when |
|                     |                          | multiple changesets are     |
|                     |                          | successors of the same      |
|                     |                          | predecessor.                |
|                     |                          |                             |
|                     |                          | *content-divergent*   are   |
|                     |                          | solved through a three way  |
|                     |                          | merge between the two       |
|                     |                          | *content-divergent*   ,     |
|                     |                          | using the last "obsolete-   |
|                     |                          | -common-ancestor" as the    |
|                     |                          | base.                       |
|                     |                          |                             |
|                     |                          | (*splitting* is             |
|                     |                          | properly not detected as a  |
|                     |                          | conflict)                   |
|                     |                          |                             |
|                     |                          | (possible alternative names:|
|                     |                          | clashing, rival, concurrent,|
|                     |                          | conflicting)                |
|                     |                          |                             |
|                     +--------------------------+-----------------------------+
|                     |                                                        |
|                     | Mutable changesets which are neither *obsolete* or     |
|                     | *unstable*    are *"ok"*.                              |
|                     |                                                        |
|                     | Do we really need a name for it ? *"ok"* is a pretty   |
|                     | crappy name :-/ other possibilities are:               |
|                     |                                                        |
|                     | - stable (confusing with stable branch)                |
|                     | - sane                                                 |
|                     | - healthy                                              |
|                     |                                                        |
+---------------------+--------------------------------------------------------+
|                                                                              |
|     **immutable**                                                            |
|                                                                              |
| Changesets in the *public* phases.                                           |
|                                                                              |
| Rewriting operation refuse to work on immutable changeset.                   |
|                                                                              |
| Obsolete markers that refer an immutable changeset as predecessors have      |
| no effect on the predecessors but may have effect on the successors.         |
|                                                                              |
| When a *mutable* changeset becomes *immutable* (changing its phase from draft|
| to public) it is just *immutable* and loose any property of it's former      |
| state.                                                                       |
|                                                                              |
| The phase properties says that public changesets stay as *immutable* forever.|
|                                                                              |
+------------------------------------------------------------------------------+



Command and operation name
--------------------------


Existing terms
``````````````

Mercurial core already uses the following terms:

:amend: to rewrite a changeset
:graft: to copy a changeset
:rebase: to move a changeset


Uncommit
````````

Remove files from a commit (and leave them as dirty in the working directory)

The *evolve* extension have an `uncommit` command that aims to replace most
`rollback` usage.

Fold
````

Collapse multiple changesets into a unique one.

The *evolve* extension will have a `fold` command.

Prune
`````

Make a changeset obsolete without successors.

This an important operation as it should mostly replace *strip*.

Alternative names:

- kill: shall has funny effects when you forget "hg" in front of ``hg kill``.
- obsolete: too vague, too long and too generic.

evolve
``````

Automatically resolve *troublesome* changesets
(*orphan*, *phase-divergent* and *content-divergent*)

This is an important name as hg pull/push will suggest it the same way it
suggest merging when you add heads.

Alternative names:

- solve (too generic ?)
- stabilize
