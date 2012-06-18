from django.conf import settings

settings.TINYCMS_TEMPLATES = getattr( settings, 'TINYCMS_TEMPLATES', {
   'Default': ('default.html', (
        ('Heading',       'char'),
        ('Body',          'ckeditor' )
    ))
})
settings.TINYCMS_DEFAULT_TEMPLATE = getattr( settings, 'TINYCMS_DEFAULT_TEMPLATE', 'Default')

def get_template(tname=settings.TINYCMS_DEFAULT_TEMPLATE):
    return settings.TINYCMS_TEMPLATES[tname]

def get_fields(tname=settings.TINYCMS_DEFAULT_TEMPLATE):
    return [f if len(f) >= 3 else list(f) + [{},]
            for f in get_template(tname)[1]]

def get_fields_bare(tname=settings.TINYCMS_DEFAULT_TEMPLATE):
    return [f[:2] for f in get_template(tname)[1]]

def get_field(tname, fname):
    return [f if len(f) >= 3 else f + ({},)
            for f in get_template(tname)[1]
            if f[0] == fname][0]

def get_path(tname=settings.TINYCMS_DEFAULT_TEMPLATE):
    return get_template(tname)[0]

