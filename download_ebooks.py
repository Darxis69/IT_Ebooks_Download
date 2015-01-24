from datetime import datetime
import re
import os
import urllib.request
import urllib.error
import socket
import html

from lxml import etree


base_url = "http://www.it-ebooks.info"
root_directory = "ebooks/"
max_retries = 2 ** 64
default_timeout = 10
socket.setdefaulttimeout(default_timeout)


def retry(function, how_many, *arguments):
    def try_it():
        def f():
            attempts = 0
            while attempts < how_many:
                # noinspection PyBroadException
                try:
                    return function(*arguments)
                except KeyboardInterrupt as e:
                    raise e
                except:
                    attempts += 1
            raise Exception("Number of attempts exceeded maximum value.")

        return f()

    return try_it()


def get_max_ebook_id():
    while True:
        parser = etree.HTMLParser()
        tree = etree.parse(base_url, parser)
        max_ebook_url = str(tree.xpath("/html/body/table/tr[3]/td/table/tr[1]/td[2]/a/@href")[0])
        non_decimal = re.compile(r'[^\d]+')
        ebook_id = int(non_decimal.sub('', max_ebook_url))
        return int(ebook_id)


def get_ebook_url_by_id(ebook_id):
    return base_url + "/book/" + str(ebook_id)


def get_ebook_download_link(ebook_id):
    ebook_url = get_ebook_url_by_id(ebook_id)
    parser = etree.HTMLParser()
    tree = etree.parse(ebook_url, parser)
    download_url = str(tree.xpath(
        "/html/body/table/tr/td/div/table/tr/td/table/tr/td/a[../../td[1]/text() = 'Download:']/@href")[0])
    return download_url


def get_size_string(size_in_bytes):
    size = size_in_bytes
    size_suffixes = ["B", "KB", "MB", "GB", "TB", "PB"]
    size_suffix_index = 0
    while size > 1024:
        size /= 1024
        size_suffix_index += 1

    return "{0:.2f}".format(round(size, 2)) + " " + size_suffixes[size_suffix_index]


def replace_invalid_path_characters(path):
    path = path.replace(':', ' -').replace('/', '_').replace('\\', '_')
    path = path.replace('*', '').replace('?', '').replace('"', '\'')
    path = path.replace('<', '').replace('>', '').replace('|', '')
    return path


def unescape_html_string(html_encoded_string):
    return html.unescape(html_encoded_string)


def get_file_name_from_content_disposition_header(content_disposition_header_value):
    extract_file_name_re = re.compile(r'"(.*?)"')
    values = extract_file_name_re.findall(content_disposition_header_value)
    if len(values) > 0:
        return values[0]
    extract_file_name_re = re.compile(r'=([^=]*)$')
    values = extract_file_name_re.findall(content_disposition_header_value)
    if len(values) > 0:
        return values[0]
    raise Exception("Cannot extract file name from Content-disposition header.")


def download_ebook_by_id(ebook_id, directory):
    download_url = get_ebook_download_link(ebook_id)
    if download_url.startswith("/"):
        download_url = base_url + download_url
    request = urllib.request.Request(download_url)
    request.add_header('Referer', get_ebook_url_by_id(ebook_id))
    response = urllib.request.urlopen(request, timeout=default_timeout)

    content_disposition_header_value = response.getheader("Content-disposition")
    file_size = int(response.getheader("Content-Length"))

    file_name = get_file_name_from_content_disposition_header(content_disposition_header_value)
    file_name = unescape_html_string(file_name)
    file_name = replace_invalid_path_characters(file_name)
    file_path = directory + file_name

    print("Ebook ID: " + str(
        ebook_id) + ". File name: '" + file_name + "'. File size: " + get_size_string(
        file_size))
    print('Downloading... ', end="", flush=True)

    file_size_downloaded = 0
    block_size = 8192

    file = open(file_path, "wb")
    download_start_time = datetime.now()
    while True:
        buffer = response.read(block_size)
        if not buffer:
            if file_size_downloaded != file_size:
                raise Exception("Invalid downloaded file size.")
            break

        file_size_downloaded += len(buffer)
        file.write(buffer)
    download_end_time = datetime.now()
    download_time_in_seconds = (download_end_time - download_start_time).seconds
    average_download_speed = file_size / download_time_in_seconds
    file.close()
    print("OK. Average download speed: " + get_size_string(average_download_speed) + "/s.\n")


def ebook_exists(ebook_id):
    ebook_url = get_ebook_url_by_id(ebook_id)
    parser = etree.HTMLParser()
    tree = etree.parse(ebook_url, parser)
    download_urls = tree.xpath(
        "/html/body/table/tr/td/div/table/tr/td/table/tr/td/a[../../td[1]/text() = 'Download:']/@href")
    if len(download_urls) < 1:
        return False
    return True


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
        if ebook_exists(ebook_id):
            retry(download_ebook_by_id, max_retries, ebook_id, ebook_dir_path)
        else:
            print("Ebook ID " + str(ebook_id) + " doesn't exists.")


main()
