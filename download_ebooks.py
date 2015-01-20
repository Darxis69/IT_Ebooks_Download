import re
from lxml import etree
import os
import urllib.request

base_url = "http://www.it-ebooks.info/"

root_directory = "ebooks/"


def get_max_ebook_id():
    while True:
        parser = etree.HTMLParser()
        tree = etree.parse(base_url, parser)
        max_ebook_url = str(tree.xpath("/html/body/table/tr[3]/td/table/tr[1]/td[2]/a/@href")[0])
        non_decimal = re.compile(r'[^\d]+')
        ebook_id = int(non_decimal.sub('', max_ebook_url))
        return int(ebook_id)


def get_ebook_url_by_id(ebook_id):
    return base_url + "book/" + str(ebook_id) + "/"


def get_ebook_download_link(ebook_id):
    ebook_url = get_ebook_url_by_id(ebook_id)
    parser = etree.HTMLParser()
    tree = etree.parse(ebook_url, parser)
    download_url = str(tree.xpath(
        "/html/body/table/tr/td/div/table/tr/td/table/tr/td/a[../../td[1]/text() = 'Download:']/@href")[0])
    return download_url


def download_ebook_by_id(ebook_id, directory):
    download_url = get_ebook_download_link(ebook_id)
    request = urllib.request.Request(download_url)
    request.add_header('Referer', get_ebook_url_by_id(ebook_id))
    response = urllib.request.urlopen(request)

    content_disposition_header_value = response.getheader("Content-disposition")

    extract_file_name_re = re.compile(r'"(.*?)"')
    file_name = extract_file_name_re.findall(content_disposition_header_value)[0]
    file_path = directory + file_name

    file_size_downloaded = 0
    block_size = 8192

    file = open(file_path, "wb")
    while True:
        buffer = response.read(block_size)
        if not buffer:
            break

        file_size_downloaded += len(buffer)
        file.write(buffer)
    file.close()


def main():
    first_ebook_id = None

    try:
        first_ebook_id = int(input("Enter beginning ebook ID: "))
    except ValueError:
        print("Not a number")
        exit()
    max_ebook_id = get_max_ebook_id()

    if not os.path.exists(root_directory):
        os.makedirs(root_directory)

    for ebook_id in range(first_ebook_id, max_ebook_id + 1):
        ebook_dir_path = root_directory + str(ebook_id) + "/"
        if not os.path.exists(ebook_dir_path):
            os.makedirs(ebook_dir_path)
        download_ebook_by_id(ebook_id, ebook_dir_path)


main()
