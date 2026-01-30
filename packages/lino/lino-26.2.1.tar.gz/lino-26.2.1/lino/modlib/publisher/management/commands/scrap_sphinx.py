# -*- coding: UTF-8 -*-
# Copyright 2025 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

import json
import re
import requests
from bs4 import BeautifulSoup
from collections import defaultdict, deque
from django.conf import settings
from django.core.management.base import BaseCommand
from urllib.parse import urljoin, urldefrag, urlparse, urlunparse


# Gathered using chatgpt
def is_sphinx_site(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, "lxml")

    # 1. Meta tag
    meta = soup.find("meta", attrs={"name": "generator"})
    if meta and "sphinx" in meta.get("content", "").lower():
        return True

    # # 2. Assets in _static
    # if soup.find(src=lambda s: s and "_static" in s) or soup.find(href=lambda h: h and "_static" in h):
    #     return True
    #
    # # 3. TOC tree wrapper (common in classic / alabaster themes)
    # if soup.find("div", class_="toctree-wrapper"):
    #     return True

    # 4. Footer "Created using Sphinx"
    footer = soup.find(string=lambda t: t and "created using sphinx" in t.lower())
    if footer:
        return True

    return False


BASE_URL = None
visited = set()
site_map = {}


def fetch(url):
    html = requests.get(url).text
    return BeautifulSoup(html, "lxml")

heading_count = 0

def extract_nodes(soup, base_url, url):
    """Extract hierarchical headings from one page (ignores toctree)."""
    headings = []
    stack = []

    # Only look inside the main document body
    content_area = soup.select_one("div.document") or soup.body

    h_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]

    for tag in content_area.find_all(h_tags):
        level = int(tag.name[1])
        title = tag.get_text(strip=True)
        anchor = tag.get("id") or (tag.find("a") and tag.find("a").get("id"))

        node = {
            "type": "heading",
            "title": title,
            "anchor": anchor,
            "content": "",
            "url_for_ref": url,
            "children": [],
            "end_title": title,
        }

        # Collect content until next heading
        html_chunks = []
        for sib in tag.next_siblings:
            if getattr(sib, "name", None) in h_tags:
                break
            if hasattr(sib, "find_all") and sib.find_all(h_tags):
                break
            if hasattr(sib, "get") and "toctree-wrapper" in sib.get("class", []):
                for elem in sib.select(".toctree-wrapper>ul>li.toctree-l1>a[href]"):
                    url, _ = urldefrag(urljoin(base_url, elem["href"]))
                    node["children"].append({"url": url})
                continue
            if getattr(sib, "name") == "nav" and hasattr(sib, "get") and "contents" in sib.get("class", []):
                continue
            html_chunks.append(str(sib))

        node["content"] = "\n".join(html_chunks).strip()

        global heading_count
        heading_count += 1

        # Place into correct hierarchy by heading level
        while stack and stack[-1]["level"] >= level:
            stack.pop()

        if stack:
            stack[-1]["node"]["children"].append(node)
        else:
            headings.append(node)

        stack.append({"level": level, "node": node})

    return headings


def crawl(url, base_url):
    if url in visited:
        return []
    visited.add(url)

    soup = fetch(url)
    nodes = extract_nodes(soup, base_url, url)

    # Recurse: attach children nodes under the right parent
    for node in nodes:
        # global heading_count
        # if heading_count > 5:
        #     break
        children = []
        # for i, child in enumerate(node["children"]):
        for child in node["children"]:
            if (url := child.get("url", None)) is not None:
                parsed = urlparse(url)
                path = re.sub(r'/\w+\.html$', '/', parsed.path)
                base_url = urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
                children.extend(crawl(url, base_url))
            else:
                children.append(child)
        node["children"] = children

    return nodes


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            "url",
            help="The url to scrap for.",
        )

    def handle(self, **options):
        url = options["url"]
        # if not is_sphinx_site(url):
        #     raise Exception("This command works only with sphinx generated websites.")

        global BASE_URL
        BASE_URL = url

        site_map = crawl(url, BASE_URL)

        print(json.dumps(site_map, indent=2))
