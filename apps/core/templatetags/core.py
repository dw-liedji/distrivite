from django import template
from django.utils.timesince import timesince
from datetime import datetime
from django.utils import translation
from num2words import num2words
from django.utils.formats import date_format

register = template.Library()


@register.filter
def to_words(value):
    return num2words(value, lang="fr")


@register.filter
def extract_years(value):
    timesince_value = timesince(value)
    years = timesince_value.split(",")[0]
    return years


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context["request"].GET.copy()
    query.update(kwargs)
    return query.urlencode()


@register.filter
def current_month(value):
    now = datetime.now()
    locale = translation.get_language()
    month_name = date_format(now, "F", use_l10n=True)
    return month_name.capitalize()


@register.filter
def current_year(value):
    now = datetime.now()
    return now.strftime("%Y")
