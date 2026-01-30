"""
Script to move/rename a content object.

Usage:
  $ OLD_ID=/Plone/foo/bar NEW_ID=/Plone/foo/bas \
    ./docker-entrypoint.sh run scripts/move_rename_object.py

Implementation notes: This applies a monkey patch to the handleContentishEvent function from CMFCore.
The goal is to optimize performance by transfering existing catalog data to a new path rather than doing a full unindex + reindex.
See also https://github.com/plone/Products.CMFPlone/pull/3834
(but that stalled due to some test issues that need to be debugged).
"""

from Acquisition import aq_base
from OFS.interfaces import IObjectWillBeMovedEvent
from plone import api
from Products.CMFCore.CMFCatalogAware import handleContentishEvent as orig
from Products.CMFCore.indexing import getQueue
from Products.CMFCore.interfaces import ICatalogTool
from zope.component import ComponentLookupError
from zope.component import queryUtility
from zope.component.hooks import setSite
from zope.container.interfaces import IObjectAddedEvent
from zope.container.interfaces import IObjectMovedEvent
from zope.lifecycleevent.interfaces import IObjectCopiedEvent
from zope.lifecycleevent.interfaces import IObjectCreatedEvent

import inspect
import os
import transaction


def handleContentishEvent(ob, event):
    """Event subscriber for (IContentish, IObjectEvent) events."""
    if IObjectAddedEvent.providedBy(event):
        ob.notifyWorkflowCreated()
        ob.indexObject()

    elif IObjectWillBeMovedEvent.providedBy(event):
        # Move/Rename
        if event.oldParent is not None and event.newParent is not None:
            try:
                catalog = queryUtility(ICatalogTool)
            except ComponentLookupError:
                # Happens when renaming a Plone Site in the ZMI.
                # Then it is best to manually clear and rebuild
                # the catalog later anyway.
                # But for now do what would happen without our patch.
                ob.unindexObject()
            else:
                ob_path = "/".join(ob.getPhysicalPath())
                rid = catalog._catalog.uids.get(ob_path)
                if rid is not None:
                    setattr(ob, "__rid", rid)
                else:
                    # This may happen if deferred indexing is active and an
                    # object is added and renamed/moved in the same transaction
                    # (e.g. moved in an IObjectAddedEvent handler)
                    return
        elif event.oldParent is not None:
            # Delete
            ob.unindexObject()

    elif IObjectMovedEvent.providedBy(event):
        if event.newParent is not None:
            rid = getattr(ob, "__rid", None)
            if rid:
                catalog = queryUtility(ICatalogTool)
                _catalog = catalog._catalog

                new_path = "/".join(ob.getPhysicalPath())
                old_path = _catalog.paths[rid]

                # Make sure the queue is empty before we update catalog internals
                getQueue().process()

                del _catalog.uids[old_path]
                _catalog.uids[new_path] = rid
                _catalog.paths[rid] = new_path

                ob.reindexObject(idxs=["allowedRolesAndUsers", "path", "getId", "id"])

                delattr(ob, "__rid")
            else:
                # This may happen if deferred indexing is active and an
                # object is added and renamed/moved in the same transaction
                # (e.g. moved in an IObjectAddedEvent handler)
                ob.indexObject()

    elif IObjectCopiedEvent.providedBy(event):
        if hasattr(aq_base(ob), "workflow_history"):
            del ob.workflow_history

    elif IObjectCreatedEvent.providedBy(event):
        if hasattr(aq_base(ob), "addCreator"):
            ob.addCreator()


def apply_patch():
    _globals = orig.__globals__
    _globals.update({"getQueue": getQueue})
    source = "\n" * (
        handleContentishEvent.__code__.co_firstlineno - 1
    ) + inspect.getsource(handleContentishEvent)
    code = compile(source, handleContentishEvent.__code__.co_filename, "exec")
    exec(code, _globals)  # noqa: S102
    orig.__code__ = _globals["handleContentishEvent"].__code__


portal = app.Plone  # noqa: F821
setSite(portal)
with api.env.adopt_user("admin"):
    old_id = os.environ.get("OLD_ID", "").lstrip("/")
    new_id = os.environ.get("NEW_ID", "").lstrip("/")

    if old_id == new_id:
        raise ValueError(
            f"OLD_ID and NEW_ID are identical ({old_id!r}); rename would be a no-op."
        )

    obj = portal.unrestrictedTraverse(old_id)
    parent = obj.__parent__
    target = portal.unrestrictedTraverse("/".join(new_id.split("/")[:-1]))

    # parent.manage_renameObject(old_id, new_id)
    # print("Naive rename", len(app._p_jar._registered_objects))
    # transaction.abort()

    apply_patch()
    if parent.getId() == target.getId():
        parent.manage_renameObject(obj.getId(), new_id.split("/")[-1])
        transaction.commit()
    else:
        cut = parent.manage_cutObjects(obj.getId())
        target.manage_pasteObjects(cut)
        target.manage_renameObject(obj.getId(), new_id.split("/")[-1])
        transaction.commit()
