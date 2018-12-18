import json

from django.conf import settings
from django.db import models, transaction

from django_extensions.db.fields.json import JSONField
from jinja2 import Markup
from pathlib2 import Path


def get_data_from_file_path(file_path):
    name, locale = file_path.stem.split('.')
    page_name = file_path.parts[-2]
    page_id = '{}-{}-{}'.format(page_name, name, locale)
    return {
        'name': name,
        'locale': locale,
        'page_name': page_name,
        'page_id': page_id,
    }


class ContentCardManager(models.Manager):
    def get_card(self, page_name, name, locale='en-US'):
        card_id = '{}-{}-{}'.format(page_name, name, locale)
        return self.get(name=card_id)

    def get_card_data(self, page_name, name, locale):
        card = self.get_card(page_name, name, locale)
        if locale == 'en-US':
            return card.card_data
        else:
            en_card = self.get_card(page_name, name)
            data = en_card.card_data
            data.update(card.card_data)
            return data

    def refresh(self):
        card_objs = []
        cc_path = Path(settings.CONTENT_CARDS_PATH, 'content')
        with transaction.atomic(using=self.db):
            self.all().delete()
            cc_files = cc_path.glob('*/*.json')
            for ccf in cc_files:
                path_data = get_data_from_file_path(ccf)
                with ccf.open(encoding='utf-8') as ccfo:
                    data = json.load(ccfo)

                card_objs.append(ContentCard(
                    name=path_data['page_id'],
                    page_name=path_data['page_name'],
                    locale=path_data['locale'],
                    content=data.pop('html_content', ''),
                    data=data,
                ))
            self.bulk_create(card_objs)

        return len(card_objs)


class ContentCard(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    page_name = models.CharField(max_length=100)
    locale = models.CharField(max_length=10)
    content = models.TextField(blank=True)
    data = JSONField()

    objects = ContentCardManager()

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return '{} ({})'.format(self.name, self.locale)

    @property
    def html(self):
        return Markup(self.content)

    @property
    def card_data(self):
        """Return a dict appropriate for calling the card() macro"""
        data = {}
        data.update(self.data)
        if 'image' in data:
            data['image_url'] = '%scontentcards/img/%s' % (settings.STATIC_URL, data['image'])
            del data['image']

        if 'highres_image' in data:
            data['highres_image_url'] = '%scontentcards/img/%s' % (settings.STATIC_URL, data['highres_image'])
            del data['highres_image']

        if 'ga_title' not in data:
            data['ga_title'] = data['title']

        if 'media_icon' in data:
            data['media_icon'] = 'mzp-has-%s' % data['media_icon']

        if 'aspect_ratio' in data:
            data['aspect_ratio'] = 'mzp-has-aspect-%s' % data['aspect_ratio']

        return data
