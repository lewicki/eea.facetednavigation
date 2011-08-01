""" Upgrade scripts to version 4.1
"""
import logging
from zope.interface import noLongerProvides
from Products.CMFCore.utils import getToolByName
from zope.component import queryAdapter, getUtility
from zope.component.interface import interfaceToName
from zope.annotation.interfaces import IAnnotations

from eea.facetednavigation.interfaces import IFacetedNavigable
from eea.facetednavigation.interfaces import IFacetedLayout
from eea.facetednavigation.config import ANNO_FACETED_LAYOUT
logger = logging.getLogger("eea.facetednavigation.upgrades => 4.1")

def fix_default_layout(context):
    """ In eea.facetednavigation < 4.0 the default layout was
    folder_summary_view. As in Plone 4 folder_summary_view doesn't wrap the
    listing in a macro, the default layout for eea.facetednavigation > 4.0 is
    folder_listing. Still, we need to keep backward compatibility, at least when
    using with EEA site. Therefore this upgrade step is available only in
    EEA context, as folder_summary_view was customized in eea.design in order
    to define the 'content-core' macro.
    """
    ctool = getToolByName(context, 'portal_catalog')
    iface = interfaceToName(context, IFacetedNavigable)
    brains = ctool.unrestrictedSearchResults(object_provides=iface)
    for brain in brains:
        doc = brain.getObject()
        anno = queryAdapter(doc, IAnnotations)

        if not anno.get(ANNO_FACETED_LAYOUT, ''):
            layout = queryAdapter(doc, IFacetedLayout)
            logger.info(
                'Updating faceted layout to folder_summary_view for: %s',
                doc.absolute_url())

            err = layout.update_layout('folder_summary_view')
            if err:
                logger.exception('\t %s', err)

def cleanup_p4a(context):
    """ eea.facetednavigation > 4.0 doesn't depend on p4a.subtyper anymore,
    but your instance will crash if it's missing as there are persistent
    references to p4a.subtyper.interfaces.ISubtyped. After you run this script,
    you should be able to drop p4a.subtyper from your buildout.
    """
    try:
        from p4a.subtyper.interfaces import ISubtyper, ISubtyped
    except ImportError:
        logger.info('p4a.subtyper not installed. Aborting...')
        return


    ctool = getToolByName(context, 'portal_catalog')
    iface = interfaceToName(context, IFacetedNavigable)
    brains = ctool.unrestrictedSearchResults(object_provides=iface)
    for brain in brains:
        doc = brain.getObject()
        anno = queryAdapter(doc, IAnnotations)

        subtyper = getUtility(ISubtyper)
        name = subtyper.existing_type(doc).name
        if 'faceted' not in name.lower():
            continue

        logger.info(
            'Cleanup p4a.subtyper interface and descriptor info for: %s',
            doc.absolute_url())

        noLongerProvides(doc, ISubtyped)
        anno.pop('p4a.subtyper.DescriptorInfo', None)