# django-markdowns

Provides markdown functionality for Django via a template filter.

![Tests](https://github.com/jnphilipp/django-markdowns/actions/workflows/tests.yml/badge.svg)
[![pypi Version](https://img.shields.io/pypi/v/django-markdowns.svg?logo=pypi&logoColor=white)](https://pypi.org/project/django-markdowns/)

## Features:
 * Adding `md` Django template filter.
   * Add `django_markdowns` to `INSTALLED_APPS` in `settings.py`.
   * Load in template with `{% load markdowns %}`.
 * Adding `DjangoExtension` extension for markdown package.
   * use of Django URL syntax.
     ```
     [Some link](APP_NAME:VIEW_NAME|PARAMS,COMMA,SEPARATED)
     ```
 * Adding `SubSupExtension` extionsion for markdown package.
   * use `~subscript~` to get `<sub>subscript</sub>`
   * use `^superscript^` to get `<sup>superscript</sup>`
