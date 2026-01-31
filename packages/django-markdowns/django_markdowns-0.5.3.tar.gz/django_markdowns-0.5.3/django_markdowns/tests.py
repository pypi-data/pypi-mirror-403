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
"""Markdowns Django app tests."""

from django.test import TestCase

from .templatetags import markdowns


class MarkdownsTestCase(TestCase):
    """Markdown test case."""

    def test_templatefilter(self):
        """Simple test for template filter."""
        html = markdowns.md("This is a simple paragraph.")
        self.assertEqual(html, "<p>This is a simple paragraph.</p>")

        html = markdowns.md("* this\n* is\n* a\n* list")
        self.assertEqual(
            html,
            "<ul>\n<li>this</li>\n<li>is</li>\n<li>a</li>\n<li>list</li>\n</ul>",
        )

        self.assertEqual(
            markdowns.md("This is ^superscript^ and ~subscript~ and __underline__."),
            "<p>This is <sup>superscript</sup> and <sub>subscript</sub> and "
            + "<u>underline</u>.</p>",
        )

    def test_djangoimageinlineprocessor(self):
        """Test the pdf functionality of the django image inline processor."""
        html = markdowns.md(
            "![PDF Title](https://example.com/test/test.pdf)",
        )
        self.assertEqual(
            html,
            '<p>\n<object data="https://example.com/test/test.pdf" height="600px" '
            + 'title="PDF Title" type="application/pdf" width="100%">\n<iframe '
            'height="600px" src="https://example.com/test/test.pdf" style="border: '
            + 'none;" title="PDF Title" width="100%">\n<p>Your browser does not '
            + 'support PDFs.<a href="https://example.com/test/test.pdf">Download the '
            + "PDF</a></p>\n</iframe>\n</object>\n</p>",
        )

        html = markdowns.md(
            '![PDF Title](https://example.com/test/test.pdf "850")',
        )
        self.assertEqual(
            html,
            '<p>\n<object data="https://example.com/test/test.pdf" height="850px" '
            + 'title="PDF Title" type="application/pdf" width="100%">\n<iframe '
            + 'height="850px" src="https://example.com/test/test.pdf" style="border: '
            + 'none;" title="PDF Title" width="100%">\n<p>Your browser does not '
            + 'support PDFs.<a href="https://example.com/test/test.pdf">Download the '
            + "PDF</a></p>\n</iframe>\n</object>\n</p>",
        )
