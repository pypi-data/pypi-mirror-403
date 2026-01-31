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
"""Django markdowns extensions for markdown.

DjangoLinkInlineProcessor based on
https://gist.github.com/hakib/73fccc340e855bb65f42197e298c0c7d
"""

import re
import markdown

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.urls import reverse, resolve, Resolver404, NoReverseMatch
from django.utils.translation import gettext_lazy as _
from markdown.inlinepatterns import (
    IMAGE_LINK_RE,
    ImageInlineProcessor,
    LINK_RE,
    LinkInlineProcessor,
    SimpleTagInlineProcessor,
)
from urllib.parse import urlparse
from xml.etree.ElementTree import Element

from .settings import IMG_CLASS


class DjangoLinkInlineProcessor(LinkInlineProcessor):
    """Django link inline processor."""

    def getLink(  # noqa, N802
        self, data: str, index: int
    ) -> tuple[str, str | None, int, bool]:
        """Get link, with django specifix stuff."""
        href, title, index, handled = super().getLink(data, index)
        return self._clean_link(href), title, index, handled

    def _clean_link(self, href: str) -> str:
        if href == "":
            return ""
        elif href.startswith("mailto:"):
            email_match = re.match("^(mailto:)?([^?]*)", href)
            if not email_match:
                raise ValueError(f"Invalid mailto link: {href}.")

            email = email_match.group(2)
            if email:
                try:
                    EmailValidator()(email)
                except ValidationError:
                    raise ValueError(f"Invalid email address: {email}.")

            return href
        elif href.startswith("#") or href.startswith("/"):
            return href

        # Remove fragments or query params before trying to match the url name
        href_parts = re.search(r"#|\?", href)
        if href_parts:
            start_ix = href_parts.start()
            url_name, url_extra = href[:start_ix], href[start_ix:]
        else:
            url_name, url_extra = href, ""

        try:
            if "|" in url_name:
                url_name, args = url_name.split("|")
                url = reverse(url_name, args=args.split(","))
            else:
                url = reverse(url_name)
        except NoReverseMatch:
            pass
        else:
            return url + url_extra

        parsed_url = urlparse(href)

        if parsed_url.netloc in settings.ALLOWED_HOSTS:
            try:
                resolver_match = resolve(parsed_url.path)
            except Resolver404:
                raise ValueError(
                    "Should not use absolute links to the current site.\n"
                    "We couldn't find a match to this URL. Are you sure it exists?"
                    f"{href}"
                )
            else:
                raise ValueError(
                    "Should not use absolute links to the current site.\n"
                    f'Try using the url name "{resolver_match.url_name}", given: '
                    + "{href}."
                )

        if parsed_url.scheme not in ("http", "https", "ftp"):
            raise ValueError(
                "Must provide an absolute URL (be sure to include https://, http:// or "
                + f"ftp://) or a proper Django URL-pattern name: {href}."
            )

        return href


class DjangoImageInlineProcessor(DjangoLinkInlineProcessor, ImageInlineProcessor):
    """Django link inline processor."""

    def handleMatch(  # noqa, N802
        self, m: re.Match[str], data: str
    ) -> tuple[Element | None, int | None, int | None]:
        """Handle Match."""
        el, start, end = super().handleMatch(m, data)

        if el is not None and el.get("src").endswith(".pdf"):
            obj = Element("object")
            obj.set("data", el.get("src"))
            obj.set("type", "application/pdf")
            obj.set("width", "100%")
            obj.set("height", f'{el.get("title", "600")}px')
            obj.set("title", el.get("alt"))

            iframe = Element("iframe")
            iframe.set("src", el.get("src"))
            iframe.set("width", "100%")
            iframe.set("height", f'{el.get("title", "600")}px')
            iframe.set("style", "border: none;")
            iframe.set("title", el.get("alt"))
            obj.append(iframe)

            p = Element("p")
            p.text = str(_("Your browser does not support PDFs."))
            iframe.append(p)

            a = Element("a")
            a.set("href", el.get("src"))
            a.text = str(_("Download the PDF"))
            p.append(a)
            el = obj
        elif el is not None and IMG_CLASS is not None:
            el.set("class", IMG_CLASS)
        return el, start, end


class ExtendedFormatExtension(markdown.Extension):
    """Extendend format markdown extension.

    * subscript with ~
    * superscript with ^
    * underline with __
    """

    def extendMarkdown(self, md: markdown.Markdown):  # noqa, N802
        """Extend markdown."""
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(r"()~(.*?)~", "sub"), "sub", 65
        )
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(r"()\^(.*?)\^", "sup"), "sup", 65
        )
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(r"()__(.*?)__", "u"), "u", 65
        )


class DjangoExtension(markdown.Extension):
    """Django markdown extension."""

    def extendMarkdown(self, md: markdown.Markdown):  # noqa, N802
        """Extend markdown."""
        md.inlinePatterns.register(DjangoLinkInlineProcessor(LINK_RE, md), "link", 160)
        md.inlinePatterns.register(
            DjangoImageInlineProcessor(IMAGE_LINK_RE, md), "image_link", 150
        )
