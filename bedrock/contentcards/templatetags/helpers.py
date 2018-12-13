# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django_jinja import library

from bedrock.contentcards.models import ContentCard


@library.global_function
def get_content_card(page_name, name, locale, size=None):
    try:
        cc = ContentCard.objects.get_card(page_name, name, locale)
    except ContentCard.DoesNotExist:
        return None

    ccd = cc.card_data
    if size:
        ccd['class'] = 'mzp-c-card-' + size

    return ccd
