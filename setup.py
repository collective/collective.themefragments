from setuptools import find_namespace_packages
from setuptools import setup

setup(
    name='collective.themefragments',
    version='3.0.0.dev0',
    description='Theme fragments for plone.app.theming',
    long_description=(open('README.md').read() + '\n' +
                      open('CHANGES.md').read()),
    long_description_content_type='text/markdown',
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Framework :: Plone',
        'Framework :: Plone :: 6.1',
        'Framework :: Plone :: 6.2',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    keywords='',
    author='Asko Soukka',
    author_email='asko.soukka@iki.fi',
    url='https://github.com/collective/collective.themefragments/',
    license='GPL',
    packages=find_namespace_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.10',
    install_requires=[
        'plone.app.theming',
        # Plone 4.3.x compatiblility
        'plone.app.widgets',
    ],
    extras_require={'test': [
        'plone.app.testing',
        'plone.app.textfield',
        'plone.app.blocks>=4.0.0',
        'plone.app.tiles',
    ]},
    entry_points="""
    # -*- Entry points: -*-
    [z3c.autoinclude.plugin]
    target = plone
    """
)
