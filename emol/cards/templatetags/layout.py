import math

from cards.models.authorization import Authorization
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def as_chunks(lst, chunk_size):
    limit = math.ceil(len(lst) / chunk_size)
    for idx in range(limit):
        yield lst[chunk_size * idx : chunk_size * (idx + 1)]


@register.simple_tag
def yes_no_auth(card, authorization):
    if card.has_authorization(authorization):
        return mark_safe('<i class="fa fa-check fa-lg green yes-no-icon"></i>')

    return mark_safe('<i class="fa fa-close fa-lg red yes-no-icon"></i>')


@register.simple_tag
def yes_no_warrant(card, marshal):
    if card.has_warrant(marshal):
        return mark_safe('<i class="fa fa-check fa-lg green yes-no-icon"></i>')

    return mark_safe('<i class="fa fa-close fa-lg red yes-no-icon"></i>')


@register.filter
def card_ordered_auths(self):  # noqa: ARG001
    return Authorization.objects.order_by("is_primary", "name")
