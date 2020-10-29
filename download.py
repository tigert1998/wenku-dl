import re
import json
import os
import logging
import argparse

import requests
from bs4 import BeautifulSoup


def parse_web_page(url: str):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    script = soup.find_all('script')

    page_data = None
    for i in script:
        if i.string is not None and "pageData" in i.string:
            desired = re.search("(?<=var pageData =).*;", i.string)\
                .group(0)[:-1]
            page_data = json.loads(desired)
            break
    if page_data is None:
        logging.fatal("fail to parse wenku web page")
        exit(1)

    doc_info = page_data["docInfo2019"]["doc_info"]
    doc_type = doc_info["doc_type"]
    title = doc_info["title"]

    logging.info("doc title: {}".format(title))
    logging.info("doc type: {}".format(doc_type))

    gen_doc(page_data, "{}.txt".format(title))


def gen_doc(page_data: dict, filepath: str):
    html_urls = json.loads(page_data["readerInfo2019"]["htmlUrls"])

    num_pages = len(html_urls["json"])
    logging.info("#pages: {}".format(num_pages))

    pages = [{} for _ in range(num_pages)]
    for i in range(num_pages):
        for x, y in [("json", "pageLoadUrl"), ("ttf", "param"), ("png", "pageLoadUrl")]:
            pages[html_urls[x][i]["pageIndex"] - 1][x] = html_urls[x][i][y]

    fd = open(filepath, "w")
    for page in pages:
        json_data = requests.get(page["json"]).text.strip()
        valid_content_span = (
            re.search("^wenku_[0-9]+\(", json_data).span(0)[1],
            re.search("\)$", json_data).span(0)[0],
        )
        json_data = json_data[valid_content_span[0]:valid_content_span[1]]
        json_data = json.loads(json_data)

        for segment in json_data["body"]:
            c = segment["c"]
            if isinstance(c, str):
                fd.write("{}".format(c))
    fd.close()


if __name__ == '__main__':
    url = input("input wenku url: ")
    parse_web_page(url)
