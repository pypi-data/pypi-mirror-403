"""
Nolite HTML Components

This module provides a comprehensive collection of Python classes that represent
standard HTML5 elements. Each class inherits from the base `Component` class and
sets a specific HTML tag, allowing for a Pythonic representation of the entire
HTML vocabulary.

Styling is handled via Pythonic keyword arguments (e.g., `bg_color`, `font_size`).
"""

from typing import List, Optional, Any

from ..core.component import Component


# Document Metadata


class Head(Component):
    """Represents the <head> element. Usually managed by the Page class."""

    tag: str = "head"


class Title(Component):
    """Represents the <title> element. Usually managed by the Page class."""

    tag: str = "title"


class Base(Component):
    """Represents the <base> element for specifying a base URL."""

    tag: str = "base"


class Link(Component):
    """Represents the <link> element, for linking to external resources."""

    tag: str = "link"


class Meta(Component):
    """Represents the <meta> element for metadata."""

    tag: str = "meta"


class Style(Component):
    """Represents the <style> element for embedding CSS."""

    tag: str = "style"


# Content Sectioning


class Body(Component):
    """Represents the <body> element."""

    tag: str = "body"


class Address(Component):
    """Represents the <address> element for contact information."""

    tag: str = "address"


class Article(Component):
    """Represents the <article> element."""

    tag: str = "article"


class Aside(Component):
    """Represents the <aside> element."""

    tag: str = "aside"


class Footer(Component):
    """Represents the <footer> element."""

    tag: str = "footer"


class Header(Component):
    """Represents a <header> element."""

    tag: str = "header"


class H1(Component):
    """Represents an <h1> heading element."""

    tag: str = "h1"


class H2(Component):
    """Represents an <h2> heading element."""

    tag: str = "h2"


class H3(Component):
    """Represents an <h3> heading element."""

    tag: str = "h3"


class H4(Component):
    """Represents an <h4> heading element."""

    tag: str = "h4"


class H5(Component):
    """Represents an <h5> heading element."""

    tag: str = "h5"


class H6(Component):
    """Represents an <h6> heading element."""

    tag: str = "h6"


class Main(Component):
    """Represents a <main> element."""

    tag: str = "main"


class Nav(Component):
    """Represents a <nav> (navigation) element."""

    tag: str = "nav"


class Section(Component):
    """Represents a <section> element."""

    tag: str = "section"


# Text Content


class Blockquote(Component):
    """Represents a <blockquote> element."""

    tag: str = "blockquote"


class Dd(Component):
    """Represents a <dd> (description details) element in a description list."""

    tag: str = "dd"


class Div(Component):
    """Represents a <div> element."""

    tag: str = "div"


class Dl(Component):
    """Represents a <dl> (description list) element."""

    tag: str = "dl"


class Dt(Component):
    """Represents a <dt> (description term) element in a description list."""

    tag: str = "dt"


class Figcaption(Component):
    """Represents a <figcaption> element for a <figure>."""

    tag: str = "figcaption"


class Figure(Component):
    """Represents a <figure> element."""

    tag: str = "figure"


class Hr(Component):
    """Represents an <hr> (horizontal rule) element."""

    tag: str = "hr"


class Li(Component):
    """Represents an <li> (list item) element."""

    tag: str = "li"


class Ol(Component):
    """Represents an <ol> (ordered list) element."""

    tag: str = "ol"


class P(Component):
    """Represents a <p> (paragraph) element."""

    tag: str = "p"


class Pre(Component):
    """Represents a <pre> (preformatted text) element."""

    tag: str = "pre"


class Ul(Component):
    """Represents a <ul> (unordered list) element."""

    tag: str = "ul"


# Inline Text Semantics


class A(Component):
    """Represents an <a> (anchor/link) element."""

    tag: str = "a"

    def __init__(self, href: str, children: Optional[List[Any]] = None, **kwargs: Any):
        super().__init__(children=children, href=href, **kwargs)


class Abbr(Component):
    """Represents an <abbr> (abbreviation) element."""

    tag: str = "abbr"


class B(Component):
    """Represents a <b> (bold) element."""

    tag: str = "b"


class Bdi(Component):
    """Represents a <bdi> (bi-directional isolation) element."""

    tag: str = "bdi"


class Bdo(Component):
    """Represents a <bdo> (bi-directional override) element."""

    tag: str = "bdo"


class Br(Component):
    """Represents a <br> (line break) element."""

    tag: str = "br"


class Cite(Component):
    """Represents a <cite> element."""

    tag: str = "cite"


class Code(Component):
    """Represents a <code> element."""

    tag: str = "code"


class Data(Component):
    """Represents a <data> element."""

    tag: str = "data"


class Del(Component):
    """Represents a <del> (deleted text) element."""

    tag: str = "del"


class Dfn(Component):
    """Represents a <dfn> (definition) element."""

    tag: str = "dfn"


class Em(Component):
    """Represents an <em> (emphasis) element."""

    tag: str = "em"


class I(Component):
    """Represents an <i> (italic) element."""

    tag: str = "i"


class Ins(Component):
    """Represents an <ins> (inserted text) element."""

    tag: str = "ins"


class Kbd(Component):
    """Represents a <kbd> (keyboard input) element."""

    tag: str = "kbd"


class Mark(Component):
    """Represents a <mark> (marked text) element."""

    tag: str = "mark"


class Q(Component):
    """Represents a <q> (quote) element."""

    tag: str = "q"


class S(Component):
    """Represents an <s> (strikethrough) element."""

    tag: str = "s"


class Samp(Component):
    """Represents a <samp> (sample output) element."""

    tag: str = "samp"


class Small(Component):
    """Represents a <small> element."""

    tag: str = "small"


class Span(Component):
    """Represents a <span> element."""

    tag: str = "span"


class Strong(Component):
    """Represents a <strong> element."""

    tag: str = "strong"


class Sub(Component):
    """Represents a <sub> (subscript) element."""

    tag: str = "sub"


class Sup(Component):
    """Represents a <sup> (superscript) element."""

    tag: str = "sup"


class Time(Component):
    """Represents a <time> element."""

    tag: str = "time"


class U(Component):
    """Represents a <u> (unarticulated annotation, formerly underline) element."""

    tag: str = "u"


class Var(Component):
    """Represents a <var> (variable) element."""

    tag: str = "var"


class Wbr(Component):
    """Represents a <wbr> (word break opportunity) element."""

    tag: str = "wbr"


# Image and Multimedia


class Area(Component):
    """Represents an <area> element within an image map."""

    tag: str = "area"


class Audio(Component):
    """Represents an <audio> element."""

    tag: str = "audio"


class Img(Component):
    """Represents an <img> (image) element."""

    tag: str = "img"

    def __init__(self, src: str, alt: str, **kwargs: Any):
        super().__init__(children=None, src=src, alt=alt, **kwargs)


class Map(Component):
    """Represents a <map> element for an image map."""

    tag: str = "map"


class Track(Component):
    """Represents a <track> element for media elements."""

    tag: str = "track"


class Video(Component):
    """Represents a <video> element."""

    tag: str = "video"


# Embedded Content


class Embed(Component):
    """Represents an <embed> element for external content."""

    tag: str = "embed"


class Iframe(Component):
    """Represents an <iframe> element."""

    tag: str = "iframe"


class Object(Component):
    """Represents an <object> element for external resources."""

    tag: str = "object"


class Picture(Component):
    """Represents a <picture> element for responsive images."""

    tag: str = "picture"


class Source(Component):
    """Represents a <source> element for <picture>, <audio>, or <video>."""

    tag: str = "source"


class Svg(Component):
    """Represents an <svg> element. Children should be other SVG-specific components."""

    tag: str = "svg"


class Canvas(Component):
    """Represents a <canvas> element."""

    tag: str = "canvas"


# Table Content


class Caption(Component):
    """Represents a <caption> element for a table."""

    tag: str = "caption"


class Col(Component):
    """Represents a <col> element within a <colgroup>."""

    tag: str = "col"


class Colgroup(Component):
    """Represents a <colgroup> element for table columns."""

    tag: str = "colgroup"


class Table(Component):
    """Represents a <table> element."""

    tag: str = "table"


class Tbody(Component):
    """Represents a <tbody> element in a table."""

    tag: str = "tbody"


class Td(Component):
    """Represents a <td> (table data) element."""

    tag: str = "td"


class Tfoot(Component):
    """Represents a <tfoot> element in a table."""

    tag: str = "tfoot"


class Th(Component):
    """Represents a <th> (table header) element."""

    tag: str = "th"


class Thead(Component):
    """Represents a <thead> element in a table."""

    tag: str = "thead"


class Tr(Component):
    """Represents a <tr> (table row) element."""

    tag: str = "tr"


# Forms


class Button(Component):
    """Represents a <button> element."""

    tag: str = "button"

    def __init__(self, children: Optional[List[Any]] = None, **kwargs: Any):
        if "type" not in kwargs:
            kwargs["type"] = "button"
        super().__init__(children=children, **kwargs)


class Datalist(Component):
    """Represents a <datalist> element for <input> suggestions."""

    tag: str = "datalist"


class Fieldset(Component):
    """Represents a <fieldset> element."""

    tag: str = "fieldset"


class Form(Component):
    """Represents a <form> element."""

    tag: str = "form"

    def __init__(
        self, action: str, children: Optional[List[Any]] = None, **kwargs: Any
    ):
        if "method" not in kwargs:
            kwargs["method"] = "post"
        super().__init__(children=children, action=action, **kwargs)


class Input(Component):
    """Represents an <input> element. A self-closing tag."""

    tag: str = "input"


class Label(Component):
    """Represents a <label> element."""

    tag: str = "label"


class Legend(Component):
    """Represents a <legend> element for a <fieldset>."""

    tag: str = "legend"


class Meter(Component):
    """Represents a <meter> element (scalar measurement)."""

    tag: str = "meter"


class Optgroup(Component):
    """Represents an <optgroup> element for grouping <option>s."""

    tag: str = "optgroup"


class Option(Component):
    """Represents an <option> element in a <select> or <datalist>."""

    tag: str = "option"


class Output(Component):
    """Represents an <output> element for calculation results."""

    tag: str = "output"


class Progress(Component):
    """Represents a <progress> element."""

    tag: str = "progress"


class Select(Component):
    """Represents a <select> (dropdown) element."""

    tag: str = "select"


# Interactive Elements


class Details(Component):
    """Represents a <details> disclosure widget."""

    tag: str = "details"


class Dialog(Component):
    """Represents a <dialog> element."""

    tag: str = "dialog"


class Summary(Component):
    """Represents a <summary> for a <details> element."""

    tag: str = "summary"


# Web Components


class Slot(Component):
    """Represents a <slot> element for web components."""

    tag: str = "slot"


class Template(Component):
    """Represents a <template> element for holding client-side content."""

    tag: str = "template"


# User-Friendly Aliases

Anchor = A
Image = Img
ListItem = Li
OrderedList = Ol
UnorderedList = Ul
Paragraph = P
