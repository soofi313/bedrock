# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import codecs
from collections import OrderedDict

import yaml
from markdown import markdown


def parse_md_front_matter(lines):
    """Return the YAML and MD sections.

    :param: lines iterator
    :return: str YAML, str Markdown
    """
    # fm_count: 0: init, 1: in YAML, 2: in Markdown
    fm_count = 0
    yaml_lines = []
    md_lines = []
    for line in lines:
        # first line we care about is FM start
        if fm_count < 2 and line.strip() == '---':
            fm_count += 1
            continue

        if fm_count == 1:
            yaml_lines.append(line)

        if fm_count == 2:
            md_lines.append(line)

    if fm_count < 2:
        raise ValueError('Front Matter not found.')

    return ''.join(yaml_lines), ''.join(md_lines)


def yaml_ordered_safe_load(stream, object_pairs_hook=OrderedDict):
    """
    Load YAML mappings as OrderedDicts

    from http://stackoverflow.com/a/21912744
    """
    class OrderedLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                                  construct_mapping)
    return yaml.load(stream, OrderedLoader)


def parse_md_file(file_name):
    """Return the YAML and MD sections for file_name."""
    with codecs.open(file_name, encoding='utf8') as fh:
        yamltext, mdtext = parse_md_front_matter(fh)

    return yaml_ordered_safe_load(yamltext), markdown(mdtext)
