"""
Script to reindex selected content types and indexes.

Usage:
  $ PORTAL_TYPE=Contact INDEXES=Title,sortable_title \
    ./docker-entrypoint.sh run scripts/reindex_content.py

"""

from plone import api
from zope.component.hooks import setSite

import logging
import os
import transaction


logger = logging.getLogger("reindex_content")
logger.setLevel(logging.INFO)


def reindex_content(portal, portal_type: list[str], idxs: list):
    i = 0
    query = {"portal_type": portal_type} if portal_type != [""] else {"path": "/"}
    for brain in portal.portal_catalog.unrestrictedSearchResults(**query):
        try:
            obj = brain._unrestrictedGetObject()
        except Exception:  # noqa: S112
            continue
        # Note: update_metadata=1 updates all metadata columns
        # in ZCatalog, but not in solr unless they are also listed in idxs.
        obj.reindexObject(idxs=idxs, update_metadata=1)
        i += 1
        if not i % 100:
            logger.info(i)
            transaction.commit()
    logger.info(i)
    transaction.commit()


portal = app.Plone  # noqa: F821
setSite(portal)
with api.env.adopt_user("admin"):
    portal_type = os.environ.get("PORTAL_TYPE", "").split(",")
    idxs = os.environ["INDEXES"].split(",")
    reindex_content(portal, portal_type=portal_type, idxs=idxs)
