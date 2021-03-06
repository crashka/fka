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

# mapping of header hierarchy (specified by ids) to the functions
# used for tablizing the format; note that the functions are specified
# by name so that this configuration can be moved to an external file,
# if needed
TABLIZE_MAP = {
    'framework-for-kicking-ass-overview': {
        'commitments-and-responsibilities': 'tablize1',
        'qualification-and-accomplishment': 'tablize1'
    },
    'framework-for-kicking-ass-users-guide': {
        'high-level-approach'             : 'tablize2',
        'process-start-to-finish'         : 'tablize3',
        'using-the-scorecard'             : 'tablize3',
        'troubleshooting'                 : 'tablize4'
    },
    'framework-for-kicking-ass-scorecard': {
        'task-or-assignment'              : 'tablize5',
        'scoring-yourself'                : 'tablize6',
        'determining-qualification'       : 'tablize7'
    }
}

######################
# hdr structure/tree #
######################

def hdr(tag):
    """Create a node which can be used to represent h1, h2, etc. tags
    (and their content) hierarchically as a tree, rather than the flat
    html way

    :param tag: [bs4.element.Tag]
    :return: [dict] header node
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
    """Create the dummy root node for the header tree

    :return: [dict] dummy node
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
    """Add child header node to parent node

    :param hdr: [dict] from hdr() or root_header()
    :param parent: [dict] from hdr() or root_header()
    :return: [void]
    """
    parent['children'].append(hdr)
    hdr['parent'] = parent

def add_content(content, parent, skip_empty = False):
    """Add html content to parent node

    :param content: [bs4.element.Tag]
    :param parent: [dict] from hdr() or root_header()
    :parem skip_empty: [bool] skip empty string elements, if desired
    :return: [void]
    """
    if not content.name and skip_empty and re.fullmatch(r'\s*', content.string):
        return
    parent['content'].append(content)
    if content.name:
        if content.name not in parent['content_map']:
            parent['content_map'][content.name] = []
        parent['content_map'][content.name].append(content)

def make_hdr_tree(soup):
    """Create tree of html header tags (and associated content)

    :param soup: [bs4.BeautifulSoup] representing entire document
    :return: [dict] header node for h1 tag
    """
    hdr_tags = ['h1', 'h2', 'h3', 'h4']
    last_tag = [None] * (len(hdr_tags) + 1)  # 1-based for intuitive indexing
    skip_tags = ['header', 'footer']

    # note that root node is only used internally
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
        elif tag.name not in skip_tags:
            add_content(tag, prev_hdr)

    assert len(root['children']) == 1
    h1_hdr = root['children'][0]
    assert h1_hdr['tag'].name == 'h1'
    return h1_hdr
                
def walk_hdr_tree(soup, hdr, func, ctx = None):
    """Walk the header tree recursively starting from the indicated node, invoking specified
    processing function on each node

    :param soup: [bs4.BeautifulSoup] document context
    :param hdr: [dict] starting header node
    :param func: [function] takes args (soup, hdr, ctx)
    :param ctx: [any] context for processing
    :return: [void]
    """
    # note that func returns the context value to be used in interating through
    # children, an empty return value prunes the recursion
    ctx = func(soup, hdr, ctx)
    if ctx:
        for c in hdr['children']:
            walk_hdr_tree(soup, c, func, ctx)

#################
# tablize funcs #
#################

def convert_tag(elem, to_tag):
    """Convert the specified element to a new tag type

    :param elem: [bs4.element.Tag] original element
    :param to_tag: [str] tag type to convert to
    :return: [bs4.BeautifulSoup] converted element
    """
    ptrn = r'(</?)%s([ >])' % (elem.name)
    repl = r'\1%s\2' % (to_tag)
    # have to create a top-level object here, since new_tag() can't construct
    # from raw html; note that this gets converted to the right tag type once
    # integrated into the tree (using append(), etc.)
    return BeautifulSoup(re.sub(ptrn, repl, str(elem)), DFLT_HTML_PARSER)

def convert_content(content, from_tag, to_tag):
    """Convert all of the content pieces of a specific tag type to a new type,
    other element types passed through unchanged.  Note that converted elements
    are removed from the html tree.

    :param content: [list] bs4.element.Tag elements
    :param from_tag: [str] tag type to convert from
    :param to_tag: [str] tag type to convert to
    :return: [list] new list of elements
    """
    new_content = []
    for c in content:
        if c.name == from_tag:
            new_content.append(convert_tag(c, to_tag))
            c.extract()
        else:
            new_content.append(c)
    return new_content

def tablize1(soup, hdr):
    """
    :param soup: [bs4.BeautifulSoup] document context
    :param hdr: [dict] header node to process
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
    :param soup: [bs4.BeautifulSoup] document context
    :param hdr: [dict] header node to process
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
        method = soup.new_tag('p')
        method.string = "Method"
        for p in content_map['p']:
            tr = soup.new_tag('tr')
            table.append(tr)
            td1 = soup.new_tag('td')
            td1.append(method)
            td2 = soup.new_tag('td')
            td2.append(p)
            tr.extend([td1, td2])

def tablize3(soup, hdr):
    """
    :param soup: [bs4.BeautifulSoup] document context
    :param hdr: [dict] header node to process
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

def tablize3a(soup, hdr):
    """
    :param soup: [bs4.BeautifulSoup] document context
    :param hdr: [dict] header node to process
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

def tablize4(soup, hdr):
    """
    :param soup: [bs4.BeautifulSoup] document context
    :param hdr: [dict] header node to process
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
            converted = extracted
            td1 = soup.new_tag('td')
            td1.append(converted)
            td2 = soup.new_tag('td')
            td2.extend(h4['content'])
            tr.extend([td1, td2])

def tablize5(soup, hdr):
    """
    :param soup: [bs4.BeautifulSoup] document context
    :param hdr: [dict] header node to process
    """
    hdrs3 = hdr['children']
    assert len(hdrs3) > 0
    table = soup.new_tag('table', border="1", style="max-width:75%")
    # insert the table this way so we don't disturb any content elements
    # between the h2 and the start of its structured children
    first_h3 = hdrs3[0]['tag']
    first_h3.insert_before(table)
    # NOTE: column widths are hard-wired to this formatting function
    col1 = soup.new_tag('col', width="30%")
    table.append(col1)
    for h3 in hdrs3:
        tr = soup.new_tag('tr')
        table.append(tr)
        extracted = h3['tag'].extract()
        # NOTE: this tag conversion is hard-wired to this formatting function
        converted = convert_tag(extracted, 'strong')
        td1 = soup.new_tag('td')
        td1.append(converted)
        td1.extend(h3['content'])
        td2 = soup.new_tag('td')
        tr.extend([td1, td2])

def tablize6(soup, hdr):
    """
    :param soup: [bs4.BeautifulSoup] document context
    :param hdr: [dict] header node to process
    """
    hdrs3 = hdr['children']
    assert len(hdrs3) > 0
    table = soup.new_tag('table', border="1")
    # insert the table this way so we don't disturb any content elements
    # between the h2 and the start of its structured children
    first_h3 = hdrs3[0]['tag']
    first_h3.insert_before(table)
    # NOTE: column widths are hard-wired to this formatting function
    col1 = soup.new_tag('col', width="25%")
    col2 = soup.new_tag('col', width="25%")
    col3 = soup.new_tag('col', width="25%")
    col4 = soup.new_tag('col', width="25%")
    table.extend([col1, col2, col3, col4])
    score_tr = soup.new_tag('tr')
    rules_tr = soup.new_tag('tr')
    value_tr = soup.new_tag('tr')
    table.extend([score_tr, rules_tr, value_tr])
    for h3 in hdrs3:
        extracted = h3['tag'].extract()
        # NOTE: this tag conversion is hard-wired to this formatting function
        converted = convert_tag(extracted, 'strong')
        td1 = soup.new_tag('td')
        td1.append(converted)
        score_tr.append(td1)

        hdrs4 = h3['children']
        assert len(hdrs4) == 2
        rules = hdrs4[0]
        value = hdrs4[1]
        rules_tag = rules['tag'].extract()
        value_tag = value['tag'].extract()
        assert re.fullmatch(r'rules(-\d)?', rules_tag['id'])
        assert re.fullmatch(r'value(-\d)?', value_tag['id'])
        td2 = soup.new_tag('td')
        td3 = soup.new_tag('td')
        td2.extend(rules['content'])
        td3.extend(convert_content(value['content'], 'p', 'span'))
        rules_tr.append(td2)
        value_tr.append(td3)

def tablize7(soup, hdr):
    """
    :param soup: [bs4.BeautifulSoup] document context
    :param hdr: [dict] header node to process
    """
    hdrs3 = hdr['children']
    assert len(hdrs3) > 0
    table = soup.new_tag('table', border="1", style="max-width:75%")
    # insert the table this way so we don't disturb any content elements
    # between the h2 and the start of its structured children
    first_h3 = hdrs3[0]['tag']
    first_h3.insert_before(table)
    # NOTE: column widths are hard-wired to this formatting function
    col1 = soup.new_tag('col', width="25%")
    col2 = soup.new_tag('col', width="60%")
    col3 = soup.new_tag('col', width="15%")
    table.extend([col1, col2, col3])
    tr = soup.new_tag('tr')
    table.append(tr)
    for h4 in hdrs3[0]['children']:
        if re.fullmatch(r'verdict-check-one(-\d)?', h4['tag']['id']):
            td = soup.new_tag('td', align="center")
            header = convert_tag(h4['tag'], 'span')
        else:
            td = soup.new_tag('td')
            header = convert_tag(h4['tag'], 'strong')
        td.append(header)
        tr.append(td)
    for h3 in hdrs3:
        tr = soup.new_tag('tr')
        table.append(tr)
        extracted = h3['tag'].extract()
        # NOTE: this tag conversion is hard-wired to this formatting function
        converted = convert_tag(extracted, 'strong')
        td1 = soup.new_tag('td')
        br1 = soup.new_tag('br')
        tr.append(td1)
        td1.append(converted)
        # this is an ugly way to wrap the "level" description with a <p> so
        # we get consistent margins with "criteria"; note that the ugliness
        # continues below
        td1.strong.wrap(soup.new_tag('p'))
        td1.strong.insert_after(br1)

        hdrs4 = h3['children']
        assert len(hdrs4) == 3
        levl = hdrs4[0]
        crit = hdrs4[1]
        verd = hdrs4[2]
        levl_tag = levl['tag'].extract()
        crit_tag = crit['tag'].extract()
        verd_tag = verd['tag'].extract()
        assert re.fullmatch(r'level(-\d)?', levl_tag['id'])
        assert re.fullmatch(r'criteria(-\d)?', crit_tag['id'])
        assert re.fullmatch(r'verdict-check-one(-\d)?', verd_tag['id'])
        td2 = soup.new_tag('td')
        td3 = soup.new_tag('td', align="center")
        # here is that continued ugliness
        for c in reversed(convert_content(levl['content'], 'p', 'span')):
            br1.insert_after(c)
        td2.extend(crit['content'])
        td3.extend(verd['content'])
        tr.extend([td2, td3])

####################
# processing funcs #
####################

def print_hdr(soup, hdr, file = None):
    """
    :param soup: [bs4.BeautifulSoup] document context
    :param hdr: [dict] header node to process
    :param file: [stream] I/O stream to print to
    :return: [stream] pass on the I/O stream so descent continues
    """
    tag = hdr['tag']
    tag_id = tag['id']
    indent = (hdr['level'] - 1) * '  '
    # do this replacement for (relative) readability
    content_tags = ["<%s>" % (h.name) if h.name else h.string for h in hdr['content']]
    print("%s%s - %s %s" % (indent, tag.name, tag_id, content_tags), file=file)
    return file

def tablize_hdr(soup, hdr, map = None):
    """
    :param soup: [bs4.BeautifulSoup] document context
    :param hdr: [dict] header node to (perhaps) process and/or descend
    :param map: [dict] function map for current node
    :return: [dict] function map for child nodes, or None (if no descent is needed)
    """
    tag = hdr['tag']
    tag_id = tag['id']
    if map is None or tag_id not in map:
        return None
    if isinstance(map[tag_id], dict):
        return map[tag_id]
    assert isinstance(map[tag_id], str)
    tbl_func = getattr(mymodule, map[tag_id])
    tbl_func(soup, hdr)
    return None

def tablize_soup(soup, debug = 0):
    """
    :param soup: [bs4.BeautifulSoup] parsed html to process
    :param debug: [bool] print debugging info to stderr if specified
    :return: [void]
    """
    h1_hdr = make_hdr_tree(soup)

    if debug > 0:
        walk_hdr_tree(soup, h1_hdr, print_hdr, sys.stderr)
    walk_hdr_tree(soup, h1_hdr, tablize_hdr, TABLIZE_MAP)

#####################
# command line tool #
#####################

import click

@click.command()
@click.option('--html_parser', default=DFLT_HTML_PARSER, help="Possible overrides: \"lxml\", \"html5lib\"")
@click.option('--debug', default=0, type=int, help="Debug level (0-2)")
@click.argument('file', required=True)
def main(html_parser, debug, file):
    """Reformat sections of HTML file (generated from Markdown) as tables, new HTML is output to stdout
    """
    with open(file) as f:
        soup = BeautifulSoup(f, html_parser)

    tablize_soup(soup, debug)  # throws exception if error
    print(str(soup))
    return 0

if __name__ == '__main__':
    main()
