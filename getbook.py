#!/usr/bin/python3
import requests
import mechanize
import urllib.parse
import sys

try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

bookname = input("Input book name: ")

s = requests.Session()
browser = mechanize.Browser()
browser.set_handle_robots(False)


def save_to_file(download_link, file_format):
    print('[+] Download started...')
    with open(bookname + "." + file_format, "wb") as f:
        response = requests.get(download_link, stream=True)
        total_length = response.headers.get('content-length')

        # If no content length header
        if total_length is None:
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50 - done)))
                sys.stdout.flush()

    print('\n[+] Download successful!')


# Download from various mirrors
def download_from_1(download_link, file_format):
    """
    Download from mirror 1. Mirror 1 is typically a http://library.lol
    """
    try:
        browser.open(download_link)
        download_page = browser.response().read()
        parser = BeautifulSoup(download_page, "lxml")
        direct_download = parser.find("a").attrs["href"]
        print(direct_download)
        save_to_file(direct_download, file_format)
#        urllib.request.urlretrieve(direct_download, "./" + bookname + "." + file_format)
        return True
    except Exception as err:
        print(err)
        return False

    
def download_from_2(download_link, file_format="epub", bookname=bookname):
    """
    Download from mirror 2. Mirror 2 is typically a http://libgen.lc/
    """
    
    if not file_format.startswith("."):
        file_format = "." + file_format
    bookname = bookname.replace(" ", "_")

    try:
        # THIS "s" equals s = requests.Session()
        html = s.get(download_link).text
        direct_download = "http://libgen.lc" + [x for x in html.split('"') if "mirr" in x][0]

        book_content = s.get(direct_download)
        with open(bookname + file_format, "wb") as r:
            r.write(book_content.content)
            return True
        
    except Exception as err:
        print(err)
        return False

        
def download_from_3(download_link, file_format):
    """
    Download from mirror 3. Mirror 3 is typically a https://3lib.net/
    """
    pass


def download_from_4(download_link, file_format):
    """
    (broken at time of writing this code)
    Download from mirror 4. Mirror 4 is typically a https://libgen.me/
    """
    pass


def parsebookreq(bookname):
    bookname = urllib.parse.quote(bookname)
    url = f"https://libgen.is/search.php?req={bookname}&lg_topic=libgen&open=0&view=simple&res=25&phrase=1&column=def"
    print(url)
    return url


def download_book(download_links, file_format):
    """
    Try to download from various mirrors until successful download
    """
    
    if not download_from_1(download_links[0], file_format):
        if not download_from_2(download_links[1], file_format):
            if not download_from_3(download_links[2], file_format):
                if not downlaod_from_4(download_links[3], file_format):
                    print("[-] Error")
                    return False
                

    
# embed bookname in URI and open URI
url = parsebookreq(bookname)
browser.open(url)

# get raw HTML and parse it by lxml parser
html = browser.response().read()
parsed_html = BeautifulSoup(html, 'lxml')

# find all <tr valign="top">
books = parsed_html.body.find_all('tr', attrs={'valign':'top'})

books_details = []

# Iterate all books to fill list of books_details
for book in books[1:]:
    raw_book_info = book.find_all("td")
    
    # Get all download links in list
    download_links = []
    for download_elmt in raw_book_info[9:14]:
        if not download_elmt.has_attr("style"):
            download_link = download_elmt.find('a').attrs["href"]
            print(download_link)
            download_links.append(download_link)

    books_details.append({
        "name": raw_book_info[2].text,
        "author": raw_book_info[1].text,
        "publisher": raw_book_info[3].text,
        "year_published": raw_book_info[4].text,
        "pages": raw_book_info[5].text,
        "size": raw_book_info[7].text,
        "extension": raw_book_info[8].text,
        "download_links": download_links
    })

print(books_details)

for book_details in books_details[:2]:
    if book_details["extension"] == "pdf":
        download_book(book_details["download_links"], book_details["extension"])
    else:
        print(book_details["extension"])
