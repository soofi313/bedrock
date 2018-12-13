from django.conf import settings
from django.db import models, transaction

from django_extensions.db.fields.json import JSONField
from jinja2 import Markup
from pathlib2 import Path

from bedrock.externalfiles.utils import parse_md_file


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
    def get_card(self, page_name, name, locale):
        page_id = '{}-{}-{}'.format(page_name, name, locale)
        return self.get(name=page_id)

    def refresh(self):
        card_objs = []
        cc_path = Path(settings.CONTENT_CARDS_PATH, 'content')
        with transaction.atomic(using=self.db):
            self.get_queryset().delete()
            cc_files = cc_path.glob('*/*.md')
            for ccf in cc_files:
                path_data = get_data_from_file_path(ccf)
                data, html = parse_md_file(str(ccf))
                card_objs.append(ContentCard(
                    name=path_data['page_id'],
                    page_name=path_data['page_name'],
                    locale=path_data['locale'],
                    content=html,
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
        data = {
            'title': self.data['title'],
            # TODO this may mean we need the en-US title for all translations
            'ga_title': self.data['title'],
            # TODO make this a url and upload the image
            'image_url': self.data['image'],
            'link_url': self.data['link_url'],
            'desc': self.data['desc'],
            'tag_label': self.data['tag_label'],
        }
        if 'media_icon' in self.data:
            data['media_icon'] = 'mzp-has-' + self.data['media_icon']

        if 'aspect_ratio' in self.data:
            data['aspect_ratio'] = 'mzp-has-aspect-' + self.data['aspect_ratio']

        if self.data.get('highres_image', False):
            data['include_highres_image'] = True

        return data
