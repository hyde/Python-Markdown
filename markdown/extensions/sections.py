#!/usr/bin/python
"""
Sections extension for Python Markdown
=========================================

This extension wraps paragraphs with headers inside <section> tags.

Single section:

    >>> import markdown
    >>> text = "# Some Header #"
    >>> md = markdown.markdown(text, ['attr_list', 'headerid', 'sections'])
    >>> print md
    <section class="level1" id="section_some-header"><h1 id="some-header">Some Header</h1>
    </section>

Single section with id attribute:

    >>> import markdown
    >>> text = "# Some Header{@id=the_header}"
    >>> md = markdown.markdown(text, ['attr_list', 'headerid', 'sections'])
    >>> print md
    <section class="level1" id="section_the_header"><h1 id="the_header">Some Header</h1>
    </section>

Single section with class attribute:

    >>> import markdown
    >>> text = "# Some Header{: .title #the_header}"
    >>> md = markdown.markdown(text, ['attr_list', 'headerid', 'sections'])
    >>> print md
    <section class="level1 title" id="section_the_header"><h1 class="title" id="the_header">Some Header</h1>
    </section>

Two sections:

    >>> import markdown
    >>> text = '''
    ... # Some Header #
    ... Some text
    ... ## Some second level header
    ... Some more text
    ... '''
    >>> md = markdown.markdown(text, ['attr_list', 'headerid', 'sections'])
    >>> print md
    <section class="level1 has1" id="section_some-header"><h1 id="some-header">Some Header</h1>
    <p>Some text</p>
    <section class="level2" id="section_some-second-level-header"><h2 id="some-second-level-header">Some second level header</h2>
    <p>Some more text</p>
    </section></section>

Three sections:

    >>> import markdown
    >>> text = '''
    ... # Some Header #
    ... Some text
    ... ## Some second level header
    ... Some more text
    ... ## Another second level header
    ... Even more text
    ... '''
    >>> md = markdown.markdown(text, ['attr_list', 'headerid', 'sections'])
    >>> print md
    <section class="level1 has2" id="section_some-header"><h1 id="some-header">Some Header</h1>
    <p>Some text</p>
    <section class="level2" id="section_some-second-level-header"><h2 id="some-second-level-header">Some second level header</h2>
    <p>Some more text</p>
    </section><section class="level2" id="section_another-second-level-header"><h2 id="another-second-level-header">Another second level header</h2>
    <p>Even more text</p>
    </section></section>


Author:
Lakshmi Vyasarajan for the Hyde project(http://github.com/hyde)     2012-02-16

License: BSD (see ../docs/LICENSE for details)

Dependencies:
* [Python 2.4+](http://python.org)
* [Markdown 2.0+](http://www.freewisdom.org/projects/python-markdown/)

"""

import re
import markdown
from markdown.util import etree

def is_true(s, default=False):
    """ Convert a string to a booleen value. """
    s = str(s)
    if s.lower() in ['0', 'f', 'false', 'off', 'no', 'n']:
        return False
    elif s.lower() in ['1', 't', 'true', 'on', 'yes', 'y']:
        return True
    return default

class SectionsAssember(object):

    def __init__(self, md, config):
        self.md = md
        self.config = config
        self.section_stack = []
        self.current_section = None
        self.current_level = 0
        self.class_prefix = self._get_config_value('class_prefix')
        self.max_level = int(self._get_config_value('max_level'))
        self.allheaders = ['h%d' % level for level in range(1, 7)]
        self.headers = ['h%d' % level for level in range(1, self.max_level+1)]

    def _get_config_value(self, key):

        try:
            val = self.md.Meta[key]
        except (AttributeError, KeyError):
            val = self.config[key]
        return val

    def get_level(self, header):
        return int(header.tag[-1])

    def make_section(self, header, parent):
        atts = {}
        header_id = header.get('id', None)
        if header_id:
            atts['id'] = 'section_' + header_id
        css_class = ''
        if self.class_prefix:
            css_class = '%s%d' % (self.class_prefix, self.get_level(header))
        header_class = header.get('class', None)
        if header_class:
            css_class = css_class + ' ' + header_class
        atts['class'] = css_class.strip()
        return etree.SubElement(parent, 'section', atts)

    def begin_section(self, header, parent):
        level = self.get_level(header)
        while (not self.current_section is None and
                    self.current_level >= level):
                self.end_section()
        if not self.current_section is None:
            self.section_stack.append((self.current_section, self.current_level))
            parent = self.current_section
            css_classes = self.current_section.get('class', 'has0').split(' ')
            count = 0
            for css_class in css_classes:
                if css_class.startswith('has'):
                    count = int(css_class.replace('has', ''))
            has_class = 'has{count}'.format(count=count)
            if has_class in css_classes:
                css_classes.remove(has_class)
            count = count + 1
            css_classes.append('has' + str(count))
            self.current_section.set('class', ' '.join(css_classes))

        self.current_section = self.make_section(header, parent)
        self.current_level = level

    def end_section(self):
        if self.current_section is None: return
        if len(self.section_stack):
            self.current_section, self.current_level = self.section_stack.pop()
        else:
            self.current_level = 0
            self.current_section = None

    def add_element(self, element, parent):
        if parent:
            parent.remove(element)
            self.current_section.append(element)

    def assemble(self, elem):
        section = None
        children = elem.getchildren
        for child in elem.getchildren():
            if child.tag in self.headers:
                self.begin_section(child, elem)
                section = self.current_section
            if not section is None:
                self.add_element(child, elem)
            if len(child):
                self.assemble(child)


class SectionsTreeprocessor(markdown.treeprocessors.Treeprocessor):

    def __init__(self):
        markdown.treeprocessors.Treeprocessor.__init__(self)

    def run(self, doc):
        """
        Look for a header. If found begin a section block.
        """
        assember = SectionsAssember(self.md, self.config)
        assember.assemble(doc)


class SectionsExtension(markdown.Extension):

    def __init__(self, configs):
        # set defaults
        self.config = {
                'max_level' : ['3', 'Maximum header level for adding sections.'],
                'class_prefix' : ['level', 'Prefix for section\'s class attribute.']
            }

        for key, value in configs:
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        """ Add SectionsTreeProcessor to the Markdown instance. """
        md.registerExtension(self)
        self.processor = SectionsTreeprocessor()
        self.processor.md = md
        self.processor.config = self.getConfigs()
        md.treeprocessors.add('sections',
                                 self.processor,
                                 "_end")

def makeExtension(configs=None):
    return SectionsExtension(configs=configs)

if __name__ == "__main__":
    import doctest
    doctest.testmod()