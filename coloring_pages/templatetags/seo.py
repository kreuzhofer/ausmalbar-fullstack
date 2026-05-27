"""SEO-related template tags: canonical URL, hreflang alternates, JSON-LD."""
import json

from django import template
from django.urls import NoReverseMatch, reverse
from django.utils import translation
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def canonical_url(context):
    """Return the canonical absolute URL for the current request, without query string."""
    request = context['request']
    return request.build_absolute_uri(request.path)


@register.simple_tag(takes_context=True)
def hreflang_alternates(context):
    """Render <link rel="alternate" hreflang="..."> tags for the current page.

    For coloring page detail pages, emit both EN and DE URLs plus x-default.
    For other pages, emit the current URL's language equivalents using the
    same URL name in each available language.
    """
    request = context['request']
    page = context.get('page')  # ColoringPage instance, if any
    links = []

    if page is not None:
        if page.seo_url_en:
            with translation.override('en'):
                en_url = request.build_absolute_uri(
                    reverse('coloring_pages:detail_en', kwargs={'seo_url': page.seo_url_en})
                )
            links.append(('en', en_url))
        if page.seo_url_de:
            with translation.override('de'):
                de_url = request.build_absolute_uri(
                    reverse('coloring_pages:detail_de', kwargs={'seo_url': page.seo_url_de})
                )
            links.append(('de', de_url))
    else:
        match = request.resolver_match
        if match is None:
            return ''
        for lang in ('en', 'de'):
            with translation.override(lang):
                try:
                    url = request.build_absolute_uri(
                        reverse(f'{match.namespace}:{match.url_name}', kwargs=match.kwargs)
                    )
                except NoReverseMatch:
                    continue
                links.append((lang, url))

    if not links:
        return ''

    tags = [
        f'<link rel="alternate" hreflang="{lang}" href="{url}">'
        for lang, url in links
    ]
    # x-default points to the English version (or first available).
    default_url = next((u for lang, u in links if lang == 'en'), links[0][1])
    tags.append(f'<link rel="alternate" hreflang="x-default" href="{default_url}">')
    return mark_safe('\n    '.join(tags))


@register.simple_tag(takes_context=True)
def page_jsonld(context, page):
    """Emit ImageObject JSON-LD for a ColoringPage."""
    request = context['request']
    lang = getattr(request, 'LANGUAGE_CODE', 'en')

    if lang == 'de' and page.title_de:
        title = page.title_de
        description = page.description_de or page.description_en or ''
    else:
        title = page.title_en
        description = page.description_en or ''

    data = {
        '@context': 'https://schema.org',
        '@type': 'ImageObject',
        'name': title,
        'description': description,
        'contentUrl': request.build_absolute_uri(page.image.url) if page.image else '',
        'thumbnailUrl': request.build_absolute_uri(page.thumbnail.url) if page.thumbnail else '',
        'datePublished': page.created_at.isoformat() if page.created_at else '',
        'dateModified': page.updated_at.isoformat() if page.updated_at else '',
        'inLanguage': lang,
        'isAccessibleForFree': True,
        'license': 'https://creativecommons.org/publicdomain/zero/1.0/',
    }
    return mark_safe(
        f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'
    )
