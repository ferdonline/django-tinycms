# {{{
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models.loading import get_model
from django.db.models.signals import post_save
from treebeard.mp_tree import MP_Node

import stemplates
# }}}

ALLOWED_CHARS = 'abcdefghijklmnopqrstuvwxyz1234567890_'
def clean_field_title(title):
    """Return a "clean" version of the title, suitable for template/variable use.

    Ex:
        "Hello" -> "hello"
        "Hello World!" -> "hello_world"
    """
    return ''.join((c if c in ALLOWED_CHARS else '_') for c in title.lower())


CONTENT_TYPES = (
    ('char', 'char'),
    ('bool', 'bool'),
    ('text', 'text'),
    ('ckeditor', 'ckeditor'),
    ('img', 'img'),
    ('file', 'file'),
    ('fk', 'fk'),
    ('int', 'int'),)
TEMPLATES = sorted([(name, name) for name in settings.TINYCMS_TEMPLATES.keys()])


class Page(MP_Node):
    title = models.CharField(max_length=100, verbose_name='Page title')
    slug = models.SlugField(max_length=100, blank=True, verbose_name = 'Base URL')
    template = models.CharField(max_length=100, choices=TEMPLATES,
                                default=settings.TINYCMS_DEFAULT_TEMPLATE)
    url = models.CharField(max_length=255, blank=True, unique=True)
    show_in_nav  = models.BooleanField(default=False)
    show_in_menu = models.ForeignKey( 'Menu', null=True, blank=True, default=None )
    menu_index   = models.IntegerField( null=True, blank=True, default=None )

    class Meta:
        pass


    def __unicode__(self):
        return u'%s' % self.title

    def full_url(self):
        """Return the full URL of this page, taking ancestors into account."""

        url = '/'.join(p.slug for p in list(self.get_ancestors()) + [self] if p.slug)

        # Make sure the URL ends with a slash, as god intended.
        # This little endswith dance is done to handle the root url ('/') correctly.
        if not url.endswith('.html'):
            url = url + '.html'

        return url

    def save(self, *args, **kwargs):
        """Save the page.

        Does a few interesting things:

        * Regenerates the stored URL.
        * Saves children so their URLs will be regenerated as well.
        * Clears the cache of this page's children.
        """
        skip_cache_clear = kwargs.pop('skip_cache_clear', False)

        # Regenerate the URL.
        self.url = self.full_url()

        if not skip_cache_clear and self.id:
            # Clear this page's ancestor cache.
            key = 'tinycms:pages:%d:children' % (self.id)
            cache.delete(key)

        # Save the page.
        resp = super(Page, self).save(*args, **kwargs)

        # Resave children to update slugs.
        for p in self.get_descendants():
            p.save(skip_cache_clear=True)

        if not skip_cache_clear:
            # Clear the cache for the NEW set of ancestors.
            self._clear_ancestor_caches()

        return resp


    def fields(self):
        """Return a dict of this page's content (MEMOIZED)."""
        if not hasattr(self, '_fields'):
            self._fields = dict((clean_field_title(pc.title), pc.get_content())
                                for pc in self.pagecontent_set.all())

        return self._fields

    def f(self):
        """A simple alias for fields()."""
        return self.fields()


    def parent(self):
        return self.get_parent()

    def get_absolute_url(self):
        return self.url


    def breadcrumbs(self):
        """Return a list of this pages' ancestors and itself."""
        return list(self.get_ancestors()) + [self]


    def nav_siblings(self):
        """Return a list of sibling Page objects (including this page)."""
        return list(self.get_siblings().filter(show_in_nav=True))

    def nav_children(self):
        """Return a list of child Page objects."""
        return list(self.get_children().filter(show_in_nav=True))

    def nav_next_sibling(self):
        """ Return the next sibling object, or None if it was the rightmost sibling."""
        siblings = self.nav_siblings()
        next_sibling = None
        for i, sibling in enumerate(siblings):
            if sibling == self and i < len(siblings) - 1:
                next_sibling = siblings[i+1]
        return next_sibling

    def nav_prev_sibling(self):
        """ Return the previous sibling object, or None if it was the leftmost sibling."""
        siblings = self.nav_siblings()
        prev_sibling = None
        for i, sibling in enumerate(siblings):
            if sibling == self and i > 0:
                prev_sibling = siblings[i-1]
        return prev_sibling

    def nav_siblings_and_children(self):
        """Return a nested list of sibling/children Page objects (including this page)."""
        siblings = self.nav_siblings()
        results = []
        for sibling in siblings:
            results.append([sibling, sibling.get_children().filter(show_in_nav=True)])

        return results


    def _clear_ancestor_caches(self):
        """Clear the child ID caches for all of this page's ancestors."""
        for page in Page.objects.get(id=self.id).get_ancestors():
            key = 'tinycms:pages:%d:children' % (page.id)
            cache.delete(key)


class PageContent(models.Model):
    page = models.ForeignKey(Page)
    title = models.CharField(max_length=40)
    cleaned_title = models.CharField(max_length=40, editable=False)
    typ = models.CharField(max_length=12, choices=CONTENT_TYPES, verbose_name='type')
    content = models.TextField(blank=True)

    class Meta:
        unique_together = (('title', 'page'),)


    def __unicode__(self):
        return u'%s (%s)' % (self.title, self.typ)

    def save(self, *args, **kwargs):
        self.cleaned_title = clean_field_title(self.title)
        return super(PageContent, self).save(*args, **kwargs)


    def get_content(self):
        """Return the actual content.

        If this is a ForeignKey, the model instance it points at will be returned.
        Otherwise, the content itself is returned as a string.
        """
        if self.typ == 'fk':
            if not self.content:
                return None

            options = stemplates.get_field(self.page.template, self.title)[2]

            app_label = options.get('app', 'tinycms')
            model_name = options.get('model', 'Page')
            model = get_model(app_label, model_name)

            try:
                return model.objects.get(id=self.content)
            except model.DoesNotExist:
                return None
        elif self.typ == 'bool':
            try:
                result = True if int(self.content) else False
            except ValueError:
                result = True
            return result
        elif self.typ in ['file', 'img']:
            from filebrowser.base import FileObject
            from django.conf import settings
            import os
            return FileObject(os.path.join(settings.MEDIA_ROOT, self.content))
        else:
            return self.content


class Menu( models.Model ):
    name = models.CharField( max_length=40 )
    
    def __unicode__(self):
        return self.name
    
    def get_as_list(self):
        from django.utils.safestring import mark_safe
        out = "<ul>\n"
        for page in self.page_set.all().order_by('menu_index'):
            out += '<li> <a href="'+ page.url +'">' + page.title.capitalize() + '</a></li>\n'
        for link in self.staticlink_set.all().order_by('menu_index'):
            out += '<li> <a href="'+ link.url +'">' + link.title.capitalize() + '</a></li>\n'
        out += "</ul>"
        return mark_safe(out)
    
    as_list = property( get_as_list )


class StaticLink( models.Model ):
    title = models.CharField(max_length=40)
    url = models.CharField(max_length=100, blank=True)
    show_in_menu = models.ForeignKey( Menu, null=True, blank=True, default=None )
    menu_index   = models.IntegerField( null=True, blank=True, default=None )
    
    def __unicode__(self):
        return self.title


def clean_content(sender, instance, **kwargs):
    """Clean the PageContent objects for a given Page.

    New, needed PageContent objects will be created.
    Existing, needed PageContent objects will not be touched.
    Unneeded PageContent objects will be deleted.

    """
    if kwargs.get('raw'):
        # We're in loaddata (or something similar).
        return

    page = instance
    fields = dict(stemplates.get_fields_bare(page.template))
    current_contents = list(page.pagecontent_set.all())

    for content in current_contents:
        if content.title not in fields or fields[content.title] != content.typ:
            content.delete()

    existing_contents = dict([(pc.title, pc.typ)
                              for pc in page.pagecontent_set.all()])

    for title, typ in fields.items():
        if title not in existing_contents or existing_contents[title] != typ:
            PageContent(page=page, title=title, typ=typ, content='').save()

post_save.connect(clean_content, sender=Page, dispatch_uid='tinycms-clean_content')

