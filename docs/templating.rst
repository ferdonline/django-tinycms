Templating
==========

The templates you make to use with Stoat are simply Django templates that take
advantage of an extra variable.

.. contents::
   :local:

The ``Page`` Variable
---------------------

When Stoat renders a template it adds a ``page`` variable to the context.  This
variable has a few properties you'll want to use.

``page.title``
~~~~~~~~~~~~~~

The title of the page as defined in the admin interface.

``page.get_absolute_url``
~~~~~~~~~~~~~~~~~~~~~~~~~

A normal Django ``get_absolute_url`` method that will return the page's URL.

``page.parent``
~~~~~~~~~~~~~~~~~~~~~~~~~

The page's parent.

``page.fields``
~~~~~~~~~~~~~~~

This property contains all of the fields you've defined in ``STOAT_TEMPLATES``, with
their names lowercased and every non-letter/number replaced by an underscore.

For example: look at the following ``STOAT_TEMPLATES`` setting::

    STOAT_TEMPLATES = {
        'Default': ['default.html', [
            ['Heading',         'char'],
            ['Body',            'text'],
            ['Sidebar Heading', 'text'],
        ]],
        'Product': ['pages/product.html', [
            ['Price',       'int'],
            ['Description', 'text'],
            ['Image',       'img'],
            ['Image 2',     'img'],
        ]],
    }

Here's what ``pages/product.html`` might look like::

    {% extends "base.html" %}

    {% block content %}
        <h1>{{ page.title }}</h1>

        <img class="product-image" src="{{ page.fields.image }}" />
        <img class="product-image" src="{{ page.fields.image_2 }}" />

        <p class="price">Price: ${{ page.fields.price }}</p>

        {{ page.fields.description|linebreaks }}
    {% endblock %}

You can use ``page.f`` as a shortcut for ``page.fields`` if you'd like to save on
some typing.

Navigation
----------

Stoat contains two sets of helpers for building navigation menus in your templates:
template tags and ``Page`` methods.

Every page has a ``show_in_nav`` option that determines whether they will be part of
the lists returned by these helpers.

Page Methods
~~~~~~~~~~~~

``page.breadcrumbs``
````````````````````

A list of the page's ancestors and itself.  For example, imagine you have the
following page layout::

    About Us
    |
    +-> The Team
        |
        +-> Jimmy
        |
        +-> Timmy

For the "Timmy" page ``page.breadcrumbs`` will be ``[<About Us>, <The Team>,
<Timmy>]``.

Each item in the list is a normal page object.

Here's an example of creating a simple list of breadcrumbs in an HTML template::

    <ul>
        {% for p in page.breadcrumbs %}
            <li {% if forloop.last %}class="active"{% endif %}>
                <a href="{{ p.get_absolute_url }}">{{ p.title }}</a>
                {% if not forloop.last %}
                    &gt;
                {% endif %}
            </li>
        {% endfor %}
    </ul>

``page.nav_siblings``
`````````````````````

A list of the page's siblings, including itself.

``page.nav_children``
`````````````````````

A list of the page's children.

``page.nav_siblings_and_children``
``````````````````````````````````

A nested list of the page's siblings (including itself) and their children. For
example, imagine the following layout::

    Products
    |
    +-> Guitars
    |
    +-> Drums

    About Us
    |
    +-> Hours
    |
    +-> Return Policy

For the "Products" or "About Us" page ``page.nav_siblings_and_children`` will be::

    [
        [<Products>, [
            <Guitars>,
            <Drums>,
        ]],
        [<About Us>, [
            <Hours>,
            <Return Policy>,
        ]],
    ]

This property can be useful if you're trying to build a two-level navigation list
(possibly with Javascript dropdowns).  Here's an example of building such a list::

    <ul>
        {% for top_page, child_pages in page.nav_siblings_and_children %}
            <li>
                <a href="{{ top_page.get_absolute_url }}">{{ top_page.title }}</a>

                {% if child_pages %}
                    <ul>
                        {% for child_page in child_pages %}
                            <li>
                                <a href="{{ child_page.get_absolute_url }}">{{ child_page.title }}</a>
                            </li>
                        {% endfor %}
                    </ul>
                {% endif %}
            </li>
        {% endfor %}
    </ul>

Template Tags
~~~~~~~~~~~~~

To use these template tags you'll need to ``{% load stoat %}`` first.

These tags do *not* require that there be a Stoat page at the current URL, so you can
safely use them anywhere you like.

``nav_roots``
`````````````

A list of all the root pages.

``nav_roots_and_children``
``````````````````````````

A nested list of all of the root pages and their children (similar in structure to
`page.nav_siblings_and_children`_).
