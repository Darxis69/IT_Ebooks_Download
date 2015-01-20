import re
import os
import urllib.request
import urllib.error

from lxml import etree


base_url = "http://www.it-ebooks.info/"
root_directory = "ebooks/"
max_retries = 2 ** 64


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


def get_download_size_string(size_in_bytes):
    size = size_in_bytes
    size_suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]
    size_suffix_index = 0
    while size > 1024:
        size /= 1024
        size_suffix_index += 1

    return "{0:.2f}".format(round(size, 2)) + " " + size_suffixes[size_suffix_index]


def download_ebook_by_id(ebook_id, directory):
    current_try = 1
    while current_try < max_retries:
        # noinspection PyBroadException
        try:
            download_url = get_ebook_download_link(ebook_id)
            request = urllib.request.Request(download_url)
            request.add_header('Referer', get_ebook_url_by_id(ebook_id))
            response = urllib.request.urlopen(request)

            content_disposition_header_value = response.getheader("Content-disposition")
            file_size = int(response.getheader("Content-Length"))

            extract_file_name_re = re.compile(r'"(.*?)"')
            file_name = extract_file_name_re.findall(content_disposition_header_value)[0]
            file_name = file_name.replace(':', ' -')
            file_path = directory + file_name

            print("Ebook ID: " + str(
                ebook_id) + ". File name: '" + file_name + "'. File size: " + get_download_size_string(
                file_size))
            print('Downloading... ', end="", flush=True)

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

            print("OK\n")
            return
        except Exception as e:
            print("Exception thrown, retrying: " + str(e))
            current_try += 1
            continue
    raise Exception("Retries reached exceeded maximum value.")


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
