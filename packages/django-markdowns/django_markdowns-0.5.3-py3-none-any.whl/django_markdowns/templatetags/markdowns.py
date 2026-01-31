# Copyright (C) 2021-2026 J. Nathanael Philipp (jnphilipp) <nathanael@philipp.land>
#
# This file is part of django_markdowns.
#
# django_markdowns is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# django_markdowns is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with django_markdowns.  If not, see <http://www.gnu.org/licenses/>.
"""Django markdowns markdown templatetags."""

import markdown

from django.template import Library
from django.utils.safestring import mark_safe
from django.template.defaultfilters import stringfilter

from ..extensions import DjangoExtension, ExtendedFormatExtension
from ..settings import EXTENSIONS

register = Library()


@register.filter()
@stringfilter
def md(text: str) -> str:
    """Convert markdown to html."""
    return mark_safe(
        markdown.markdown(
            text,
            extensions=[
                "markdown.extensions.fenced_code",
                DjangoExtension(),
                ExtendedFormatExtension(),
            ]
            + EXTENSIONS,
        )
    )
