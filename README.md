# Theme Fragments for [Plone Themes](https://pypi.org/project/plone.app.theming)

[![Tests](https://github.com/collective/collective.themefragments/actions/workflows/test-matrix.yml/badge.svg)](https://github.com/collective/collective.themefragments/actions/workflows/test-matrix.yml)
[![Meta](https://github.com/collective/collective.themefragments/actions/workflows/meta.yml/badge.svg)](https://github.com/collective/collective.themefragments/actions/workflows/meta.yml)

Diazo Rules may operate on content that is fetched from somewhere other than
the current page being rendered by Plone, by using the href attribute to
specify a path of a resource relative to the root of the Plone site:

```xml
<!-- Pull in extra navigation from a browser view on the Plone site root -->
<after
    css:theme-children="#leftnav"
    css:content=".navitem"
    href="/@@extra-nav"
    />
```

The `href` attribute can be used with any rule apart from `<drop />` and
`<strip />`, and can reference any URL, for example to an existing browser
view configured for your site. However, it is often desirable to generate some
dynamic content specifically for the purpose of constructing a particular theme.
In this scenario, you can use *fragments*.


## Fragment templates

Fragments are Zope Page Template files bundled with your theme. You can create
them by adding a folder called `fragments` to your theme resource directory
(i.e. the directory containing `rules.xml`), either through the web or on the
filesystem, and creating one or more files with a `.pt` extension in this
directory.

For example, you could create a file `fragments/customnav.pt` in your theme
directory, containing:

```html
<ul id="nav">
  <li tal:repeat="item context/@@folderListing">
    <img tal:replace="structure item/getIcon" />
    <span tal:replace="item/Title" tal:attributes="title item/Description">Title</span>
  </li>
</ul>
```

This uses Zope Page Template TAL syntax (the same syntax you might use to create
a template for a browser view if you are doing filesystem Python development,
say) to generate some markup based on the attributes and helper views available
relative to the current context.

The following variables are available to the page template used to build a
fragment:

`context`
: The context in which the fragment was looked up. This is usually either the
  portal root (when using an `href` with an absolute path, i.e. one starting
  with a `/`) or the current content object (when using an `href` with a
  relative path).

`request`
: The request used to render the fragment. When using a fragment from the
  `href` of a rule, this is a clone of the request used to render the page,
  but with the path to the fragment view, not the original content object.
  Note that form parameters from the original request are not available in this
  request.

`portal`
: The portal root object.

`portal_url`
: The URL to the portal root.

You can learn more about Zope Page Template syntax
[here](http://plone.org/documentation/tutorial/zpt/).


## Fragment modules

Fragment modules are Restricted Python Script modules bundled with your themes.
Availability of methods is limited to specific fragment by naming the module
after the fragment base name (with `.py` extension). Each module could
contain any number Python function definitions, which are then made available
as instance methods of the fragment view.

For example, you could create a file `fragments/customnav.py` in your
theme directory, containing:

```python
def getnav(self):
    return [{
        'Title': u'My title',
        'Description': u'My description',
        'getIcon': 'document_icon.png'
    }]
```

And call it in your fragment `fragments/customnav.pt` like a view method:

```html
<ul id="nav">
  <li tal:repeat="item view/getnav">
    <img tal:replace="structure item/getIcon" />
    <span tal:replace="item/Title" tal:attributes="title item/Description">Title</span>
  </li>
</ul>
```


## Fragment methods

> **Note:** Fragment methods preceded fragment modules and support for them
> may be removed in the future.

Fragment methods are Restricted Python Script files bundled with your themes.
Availability of methods is limited to specific fragment by prefixing the
method filename with the fragment name. Each script should contain code
for a single method and end by returning a value for the template.

For example, you could create a file `fragments/customnav.getnav.py` in your
theme directory, containing:

```python
return [{
    'Title': u'My title',
    'Description': u'My description',
    'getIcon': 'document_icon.png'
}]
```

And call it in your fragment `fragments/customnav.pt` like a view method:

```html
<ul id="nav">
  <li tal:repeat="item view/getnav">
    <img tal:replace="structure item/getIcon" />
    <span tal:replace="item/Title" tal:attributes="title item/Description">Title</span>
  </li>
</ul>
```

The following variables are available to the fragment method used to build a
fragment:

`self`
: The fragment view, which provides access to `self.context`,
  `self.request` and other available fragment methods similarly to
  filesystem browser views.

`args`
: List of positional arguments for the method call.
  *Fragment methods do not support Zope PythonScript's way of defining
  positional named arguments.*

`kwargs`
: Dictionary of keyword arguments for the method call.
  *Fragment methods do not support Zope PythonScript's way of defining
  named keyword arguments.*

`context`
: The context in which the fragment was looked up.
  *This is provided as tribute to Zope PythonScript.*

`container`
: The container for the context which the fragment was looked up.
  *This is provided as tribute to Zope PythonScript.*

`traverse_subpath`
: An empty string.
  *This is provided as tribute to Zope PythonScript.*


## Rendering fragments

The special `@@theme-fragment` view is used to render fragments. Before
using it in your theme, you can test it directly in your browser by going to
a URL like:

```
http://localhost:8080/Plone/@@theme-fragment/customnav
```

This will cause the fragment in `fragments/customnav.pt` to be rendered with
the Plone site `Plone` running on `localhost:8080` as its context. You can
render fragments relative to any content object, by adjusting the URL.

**Note:** Fragments are only available for the currently active theme. When
testing a fragment in the browser in this way, make sure the theme is enabled!

To use a fragment in a theme rule, use the `href` attribute with either an
absolute or relative path. For example:

```xml
<replace css:theme="#navlist" css:content="#nav" href="/@@theme-fragment/customnav" />
```

will replace the element with id `navlist` in the theme with the element with
id `nav` in the fragment generated by the `fragments/customnav.pt` template
in the theme, rendered with the portal root as its `context` always (since the
`href` is using an absolute path, i.e. one beginning with a `/`).

Similarly:

```xml
<replace css:theme="#navlist" css:content="#nav" href="@@theme-fragment/customnav" />
```

will do the same, but using the current content item as its `context` (i.e.
the `href` is using a relative path).


## Fragments as views

Fragments can also be used as content views, by setting the
`layout`-attribute of a content object to `++themefragment++name` where
*name* is the name of the fragment. Currently fragments cannot be configured to
be visible in the display menu.

**Note:** Fragments are only available for the currently active theme. When
using fragments in your content this way, make sure the theme is enabled!


## Fragment security

Fragments, like theme HTML mockup files, are publicly accessible by default.
Anyone with
access to the site can construct a URL containing `@@theme-fragment/<name>` to
render a given fragment.

Alternatively, more strict permissions can be defined per tile in theme
`manifest.cfg` with syntax:

```ini
[theme:themefragments:permissions]
basename = zope2.View
```

However, regardless of the defined permissions, the page templates used to build
fragments execute in a so-called
*Restricted Python* environment. This means that the are executed as the current
user (or *Anonymous*, if the current user is not logged in). Information (such
as content items or their attributes) not accessible to the current user cannot
be rendered, and may result in a `403 Forbidden` error when rendering the
fragment.


## Fragment tiles

With [plone.tiles](https://pypi.org/project/plone.tiles),
[plone.app.tiles](https://pypi.org/project/plone.app.tiles) and
[plone.app.blocks](https://pypi.org/project/plone.app.blocks) installed (the
`tiles` extra: `collective.themefragments[tiles]`) this
package provides an additional installation profile for *Theme fragment tile*,
which can be used to place theme fragments as tiles.

More readable titles for theme fragments can be defined in theme manifest.cfg
with:

```ini
[theme:themefragments:tiles]
basename = Display title
```

Where *basename* is the basename of fragment filename (the part before
`.pt`).

Tiles can define their configuration schema using
[plone.supermodel](https://pypi.org/project/plone.supermodel) XML in a
fragment specific file having its matching filename ending with `.xml`
instead of `.pt`.

It's also possible to specify fragment specific caching ruleset in
manifest.cfg with:

```ini
[theme:themefragments:caching]
basename = plone.content.feed
```


## Compatibility

Version 3.x supports Plone 6.1 on Python 3.10 to 3.13, and Plone 6.2 on Python
3.10 to 3.14.

For Plone 4.3 to 6.0 and Python 2.7, use collective.themefragments 2.12.


## Installation

Add `collective.themefragments` to the dependencies of your package, or to
your instance's eggs. Its ZCML is loaded by `plone.autoinclude`. There is
nothing to activate for fragments: they are rendered for the active theme.

For the fragment tile, install `collective.themefragments[tiles]` and the
*Theme fragment tile* profile (registered when plone.app.mosaic is installed).


## Development

Requires [uv](https://docs.astral.sh/uv/). This installs the package with Plone 6.2.3 in `.venv` (use `PLONE_VERSION=6.1.6 make install` for another version) and the prek git hook. The package doesn't depend on Products.CMFPlone: the Makefile adds it and plone.app.contenttypes for the development instance, which loads the package ZCML.

```shell
make install
make start          # Plone on http://localhost:8080 (admin / admin)
make console        # Python console with the Zope application as `app`
```

### Tests

Tests run through tox, as the CI does:

```shell
make test                                   # Plone 6.2.3
uvx --with tox-uv tox -e py312-plone61      # one Plone / Python combination
make test-all                               # lint, every combination, dependencies
```

Without tox:

```shell
.venv/bin/zope-testrunner --test-path=src -s collective.themefragments
```

### Lint

```shell
make check          # format then lint (pyupgrade, isort, black, flake8...)
```

`.editorconfig`, `.flake8`, `.gitignore`, `.pre-commit-config.yaml`, `tox.ini`,
`.github/` and the tool sections of `pyproject.toml` are generated by
[plone.meta](https://github.com/plone/meta): change `.meta.toml`, then run
`uvx --from plone.meta config-package --no-commit --branch current .`.

### Release

```shell
make release        # zest.releaser fullrelease, run through uvx
```


## Contribute

- Issue Tracker: https://github.com/collective/collective.themefragments/issues
- Source Code: https://github.com/collective/collective.themefragments


## License

The project is licensed under the GPLv2.
