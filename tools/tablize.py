#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tablize module
"""

import sys
import re

from bs4 import BeautifulSoup

#########################
# common constants/data #
#########################

mymodule  = sys.modules[__name__]

DFLT_HTML_PARSER = 'html.parser'

TABLIZE_MAP = {
    'framework-for-kicking-ass-overview': {
        'commitments-and-responsibilities': 'tablize1',
        'qualification-and-accomplishment': 'tablize1'
    },
    'framework-for-kicking-ass-users-guide': {
        'process-start-to-finish'         : 'tablize3',
        'using-the-scorecard'             : 'tablize3',
        'troubleshooting'                 : 'tablize4'
    }
}

######################
# hdr structure/tree #
######################

def hdr(tag):
    """
    """
    level = int(tag.name[1:])
    return {
        'tag'        : tag,
        'level'      : level,
        'parent'     : None,
        'content'    : [],
        'content_map': {},
        'children'   : []
    }

def root_hdr():
    """
    """
    return {
        'tag'        : None,
        'level'      : 0,
        'parent'     : None,
        'content'    : [],
        'content_map': {},
        'children'   : []
    }

def add_hdr(hdr, parent):
    """
    """
    parent['children'].append(hdr)
    hdr['parent'] = parent

def add_content(content, parent):
    """
    """
    parent['content'].append(content)
    if content.name:
        if content.name not in parent['content_map']:
            parent['content_map'][content.name] = []
        parent['content_map'][content.name].append(content)

def make_hdr_tree(soup):
    """
    """
    hdr_tags = ['h1', 'h2', 'h3', 'h4']
    last_tag = [None] * (len(hdr_tags) + 1)  # 1-based for intuitive indexing

    root = root_hdr()
    root_level = root['level']
    last_tag[root_level] = root
    prev_hdr = root

    for tag in soup.html.body.children:
        if tag.name in hdr_tags:
            h = hdr(tag)
            level = h['level']
            par_level = h['level'] - 1
            prev_level = prev_hdr['level']
            if level > prev_level:
                if level != prev_level + 1:
                    raise("Header levels not sequential (%s, %s)" % (prev_hdr, h))
                parent = last_tag[par_level]
                assert parent == prev_hdr
                assert len(parent['children']) == 0
            elif level == prev_level:
                parent = last_tag[par_level]
                assert parent == prev_hdr['parent']
            else:
                parent = last_tag[par_level]
                assert len(parent['children']) > 0
            add_hdr(h, parent)
            last_tag[level] = h
            prev_hdr = h
        else:
            add_content(tag, prev_hdr)

    assert len(root['children']) == 1
    h1_hdr = root['children'][0]
    assert h1_hdr['tag'].name == 'h1'
    return h1_hdr
                
def walk_hdr_tree(soup, hdr, func, ctx = None):
    """
    """
    ctx = func(soup, hdr, ctx)
    if ctx:
        for c in hdr['children']:
            walk_hdr_tree(soup, c, func, ctx)

#################
# tablize funcs #
#################

def convert_tag(orig_tag, to_tag):
    """
    """
    ptrn = r'(</?)%s([ >])' % (orig_tag.name)
    repl = r'\1%s\2' % (to_tag)
    # have to create a top-level object here, since new_tag() can't construct
    # from raw html; note that this gets converted to the right tag type once
    # integrated into the tree (using append(), etc.)
    return BeautifulSoup(re.sub(ptrn, repl, str(orig_tag)), DFLT_HTML_PARSER)

def tablize1(soup, hdr):
    """
    """
    hdrs3 = hdr['children']
    for h3 in hdrs3:
        hdrs4 = h3['children']
        assert len(hdrs4) > 0
        table = soup.new_tag('table', border="1")
        # insert the table this way so we don't disturb any content elements
        # between the h3 and the start of its structured children
        first_h4 = hdrs4[0]['tag']
        first_h4.insert_before(table)
        # NOTE: column widths are hard-wired to this formatting function
        col1 = soup.new_tag('col', width="20%")
        table.append(col1)
        for h4 in hdrs4:
            tr = soup.new_tag('tr')
            table.append(tr)
            extracted = h4['tag'].extract()
            # NOTE: this tag conversion is hard-wired to this formatting function
            converted = convert_tag(extracted, 'p')
            td1 = soup.new_tag('td')
            td1.append(converted)
            td2 = soup.new_tag('td')
            td2.extend(h4['content'])
            tr.extend([td1, td2])

def tablize2(soup, hdr):
    """
    """
    hdrs3 = hdr['children']
    for h3 in hdrs3:
        table = soup.new_tag('table', border="1")
        h3['tag'].insert_after(table)
        # NOTE: column widths are hard-wired to this formatting function
        col1 = soup.new_tag('col', width="35%")
        table.append(col1)
        content_map = h3['content_map']
        assert len(content_map['p']) > 0
        assert len(content_map['ol']) == len(content_map['p'])
        for p in content_map['p']:
            tr = soup.new_tag('tr')
            table.append(tr)
            td1 = soup.new_tag('td')
            td1.append(p)
            td2 = soup.new_tag('td')
            td2.append(content_map['ol'].pop())
            tr.extend([td1, td2])

def tablize3(soup, hdr):
    """
    """
    hdrs3 = hdr['children']
    for h3 in hdrs3:
        table = soup.new_tag('table', border="1")
        h3['tag'].insert_after(table)
        # NOTE: column widths are hard-wired to this formatting function
        col1 = soup.new_tag('col', width="10%")
        table.append(col1)
        content_map = h3['content_map']
        assert len(content_map['p']) > 0
        assert len(content_map['ol']) == len(content_map['p'])
        for p in content_map['p']:
            table.insert_before(p)
        steps = soup.new_tag('p')
        steps.string = "Steps"
        for ol in content_map['ol']:
            tr = soup.new_tag('tr')
            table.append(tr)
            td1 = soup.new_tag('td')
            td1.append(steps)
            td2 = soup.new_tag('td')
            td2.append(ol)
            tr.extend([td1, td2])

def tablize4(soup, hdr):
    """
    """
    hdrs3 = hdr['children']
    for h3 in hdrs3:
        hdrs4 = h3['children']
        assert len(hdrs4) > 0
        table = soup.new_tag('table', border="1")
        # insert the table this way so we don't disturb any content elements
        # between the h3 and the start of its structured children
        first_h4 = hdrs4[0]['tag']
        first_h4.insert_before(table)
        # NOTE: column widths are hard-wired to this formatting function
        col1 = soup.new_tag('col', width="25%")
        table.append(col1)
        for h4 in hdrs4:
            tr = soup.new_tag('tr')
            table.append(tr)
            extracted = h4['tag'].extract()
            # NOTE: this tag conversion is hard-wired to this formatting function
            #converted = convert_tag(extracted, 'p')
            td1 = soup.new_tag('td')
            td1.append(extracted)
            td2 = soup.new_tag('td')
            td2.extend(h4['content'])
            tr.extend([td1, td2])

####################
# processing funcs #
####################

def print_hdr(soup, hdr, ctx = None):
    """
    """
    tag    = hdr['tag']
    tag_id = tag['id']
    indent = (hdr['level'] - 1) * ' '
    # do this replacement for (relative) readability
    content_tags = ["<%s>" % (h.name) if h.name else str(h) for h in hdr['content']]
    print("%s%s - %s" % (indent, tag.name, tag_id))
    print("%s     %s" % (indent, content_tags))
    return ctx

def tablize_hdr(soup, hdr, map = None):
    """
    """
    tag    = hdr['tag']
    tag_id = tag['id']
    if map is None or tag_id not in map:
        return None
    if isinstance(map[tag_id], dict):
        return map[tag_id]
    assert isinstance(map[tag_id], str)
    tbl_func = getattr(mymodule, map[tag_id])
    tbl_func(soup, hdr)
    return None

def tablize_soup(soup):
    """
    """
    h1_hdr = make_hdr_tree(soup)

    #walk_hdr_tree(soup, h1_hdr, print_hdr, True)
    walk_hdr_tree(soup, h1_hdr, tablize_hdr, TABLIZE_MAP)

#####################
# command line tool #
#####################

import click

@click.command()
@click.option('--html_parser', default=DFLT_HTML_PARSER, help="Possible overrides: \"lxml\", \"html5lib\"")
@click.argument('file', required=True)
def main(html_parser, file):
    """Reformat sections of HTML file (generated from Markdown) as tables
    """
    with open(file) as f:
        soup = BeautifulSoup(f, html_parser)

    tablize_soup(soup)  # throws exception if error
    print(str(soup))
    return 0

if __name__ == '__main__':
    main()
