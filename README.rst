Theme Fragments for `Plone Themes`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. image:: https://secure.travis-ci.org/datakurre/collective.themefragments.png
   :target: https://travis-ci.org/datakurre/collective.themefragments

.. _Plone Themes: https://pypi.python.org/pypi/plone.app.theming

Diazo Rules may operate on content that is fetched from somewhere other than
the current page being rendered by Plone, by using the href attribute to
specify a path of a resource relative to the root of the Plone site::

  <!-- Pull in extra navigation from a browser view on the Plone site root -->
  <after
      css:theme-children="#leftnav"
      css:content=".navitem"
      href="/@@extra-nav"
      />

The ``href`` attribute can be used with any rule apart from ``<drop />`` and
``<strip />``, and can reference any URL, for example to an existing browser
view configured for your site. However, it is often desirable to generate some
dynamic content specifically for the purpose of constructing a particular theme.
In this scenario, you can use *fragments*.

Fragment templates
++++++++++++++++++

Fragments are Zope Page Template files bundled with your theme. You can create
them by adding a folder called ``fragments`` to your theme resource directory
(i.e. the directory containing ``rules.xml``), either through the web or on the
filesystem, and creating one or more files with a ``.pt`` extension in this
directory.

For example, you could create a file ``fragments/customnav.pt`` in your theme
directory, containing::

  <ul id="nav">
    <li tal:repeat="item context/@@folderListing">
      <img tal:replace="structure item/getIcon" />
      <span tal:replace="item/Title" tal:attributes="titile item/Description">Title</span>
    </li>
  </ul>

This uses Zope Page Template TAL syntax (the same syntax you might use to create
a template for a browser view if you are doing filesystem Python development,
say) to generate some markup based on the attributes and helper views available
relative to the current context.

The following variables are available to the page template used to build a
fragment:

``context``
  The context in which the fragment was looked up. This is usually either the
  portal root (when using an ``href`` with an absolute path, i.e. one starting
  with a ``/``) or the current content object (when using an ``href`` with a
  relative path).
``request``
  The request used to render the fragment. When using a fragment from the
  ``href`` of a rule, this is a clone of the request used to render the page,
  but with the path to the fragment view, not the original content object.
  Note that form parameters from the original request are not available in this
  request.
``portal``
  The portal root object.
``portal_url``
  The URL to the portal root.

You can learn more about Zope Page Template syntax
`here <http://plone.org/documentation/tutorial/zpt/>`_.

Fragment methods
++++++++++++++++

Fragment methods are Restricted Python Script files bundled with your themes.
Availability of methods is limited to specific fragment by prefixing the
method filename with the fragment name. Each script should contain code
for a single method and end by returning a value for the template.

For example, you could create a file ``fragments/customnav.getnav.py`` in your
theme directory, containing::

   return [{
       'Title': u'My title',
       'Description': u'My description',
       'getIcon': 'document_icon.png'
   }]

And call it in your fragment ``fragments/customnav.pt`` like a view method::

  <ul id="nav">
    <li tal:repeat="item view/getnav">
      <img tal:replace="structure item/getIcon" />
      <span tal:replace="item/Title" tal:attributes="titile item/Description">Title</span>
    </li>
  </ul>

The following variables are available to the fragment method kkkkkkkused to build a
fragment:

``self``
  The fragment view, which provides access to ``self.context``,
  ``self.request`` and other available fragment methods similarly to
  filesystem browser views.

``args``
  List of positional arguments for the method call.
  *Fragment methods do not support Zope PythonScript's way of defining
  positional named arguments.*

``kwargs``
  Dictionary of keyword arguments for the method call.
  *Fragment methods do not support Zope PythonScript's way of defining
  named keyword arguments.*

``context``
  The context in which the fragment was looked up.
  *This is provided as tribute to Zope PythonScript.*

``container``
  The container for the context which the fragment was looked up.
  *This is provided as tribute to Zope PythonScript.*

``traverse_subpath``
  An empty string.
  *This is provided as tribute to Zope PythonScript.*

Rendering fragments
+++++++++++++++++++

The special ``@@theme-fragment`` view is used to render fragments. Before
using it in your theme, you can test it directly in your browser by going to
a URL like::

  http://localhost:8080/Plone/@@theme-fragment/customnav

This will cause the fragment in ``fragments/customnav.pt`` to be rendered with
the Plone site ``Plone`` running on ``localhost:8080`` as its context. You can
render fragments relative to any content object, by adjusting the URL.

**Note:** Fragments are only available for the currently active theme. When
testing a fragment in the browser in this way, make sure the theme is enabled!

To use a fragment in a theme rule, use the ``href`` attribute with either an
absolute or relative path. For example::

  <replace css:theme="#navlist" css:content="#nav" href="/@@theme-fragment/customnav" />

will replace the element with id ``navlist`` in the theme with the element with
id ``nav`` in the fragment generated by the ``fragments/customnav.pt`` template
in the theme, rendered with the portal root as its ``context`` always (since the
``href`` is using an absolute path, i.e. one beginning with a ``/``).

Similarly::

  <replace css:theme="#navlist" css:content="#nav" href="@@theme-fragment/customnav" />

will do the same, but using the current content item as its ``context`` (i.e.
the ``href`` is using a relative path).

Fragment security
+++++++++++++++++

Fragments, like theme HTML mockup files, are publicly accessible. Anyone with
access to the site can construct a URL containing ``@@theme-fragment/<name>`` to
render a given fragment.

However, the page templates used to build fragments execute in a so-called
*Restricted Python* environment. This means that the are executed as the current
user (or *Anonymous*, if the current user is not logged in). Information (such
as content items or their attributes) not accessible to the current user cannot
be rendered, and may result in a ``403 Forbidden`` error when rendering the
fragment.

Fragment tiles
++++++++++++++

With `plone.tiles`_, `plone.app.tiles`_ and `plone.app.blocks`_ installed this
package provides an additional installation profile for *Theme fragment tile*,
which can be used to place theme fragments as tiles.

More readable titles for theme fragments can be defined in theme manifest.cfg
with:

.. code:: ini

   [theme:themefragments:tiles]
   basename = Display title

Where *basename* is the basename of fragment filename (the part before
``.pt``).

Tiles can define their configuration schema using `plone.supermodel`_ XML in a
fragment specific file having its matching filename ending with ``.xml``
instaead of ``.pt``.

.. _plone.tiles: https://pypi.python.org/pypi/plone.tiles
.. _plone.supermodel: https://pypi.python.org/pypi/plone.supermodel
.. _plone.app.tiles: https://pypi.python.org/pypi/plone.app.tiles
.. _plone.app.blocks: https://pypi.python.org/pypi/plone.app.blocks
