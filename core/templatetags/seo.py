from django import template

from core import seo as seo_helpers

register = template.Library()


@register.simple_tag(takes_context=True)
def seo_head(context):
    """{% seo_head as seo %}: <head> için başlık, açıklama, kanonik adres, OG ve JSON-LD değerleri."""
    return seo_helpers.head(context.flatten())
