Changelog
=========

2.0.0rc3 (2016-12-15)
---------------------

- Fix issue where fragments didn't render when traversed from a view context
  [Asko Soukka]

2.0.0rc2 (2016-12-14)
---------------------

- Fix issue where fragment was not properly decoded
  [datakurre]

2.0.0rc1 (2016-12-12)
---------------------

- Upgrade Theme fragment tiles with custom scheme to support layout aware
  tile data storage introduced in plone.app.blocks 4.0
  [datakurre]


1.1.0 (2016-12-12)
------------------

- Refactor fragment tile source into fragment tile vocabulary to
  fix compatibility issue with Plone 5.1
  [datakurre]


1.0.1 (2016-02-21)
------------------

- Fix issue where plone:tile -directive was not properly included
  [datakurre]


1.0.0 (2015-09-16)
------------------

- Add fragment tile for plone.app.mosaic
  [datakurre]


0.10.0 (2015-04-03)
-------------------

- Add support for restricted python view methods
  (with fragments/templatename.methodname.py)
  [datakurre]


0.9.0 (2015-04-01)
------------------

- First release based on Martin Aspeli's rejected pull for plone.app.theming.
