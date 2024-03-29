#!/usr/bin/python3
import requests
import urllib.parse
import threading
import argparse
import progressbar

try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

bookname = ""
books = [0, 0]
books_details = []
pgno = 0
verbose = False

s = requests.Session()
request_lock = threading.Lock()


def verbose_print(*args):
    if verbose:
        print(*args)



def save_to_file(download_link, file_format, bookname=bookname):
    """
    Download file from download link with progress bar
    """
    bookname = bookname.replace(" ", "_")
    
    print('[+] Download started...')
    with open(bookname + "." + file_format, "wb") as f:
        response = requests.get(download_link, stream=True, timeout=10)
        total_length = response.headers.get('content-length')

        bar = progressbar.ProgressBar(max_value=int(total_length)).start()

        # If no content length header
        if total_length is None:
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                bar.update(dl)


    bar.finish()


# Download from various mirrors
def download_from_1(download_link, file_format="epub", bookname=bookname):
    """
    Download from mirror 1. Mirror 1 is typically a http://library.lol
    """
    try:
        response = requests.get(download_link)
        download_page = response.text
        parser = BeautifulSoup(download_page, "lxml")
        direct_download = parser.find("a").attrs["href"]
        save_to_file(direct_download, file_format, bookname)
        return True
    except Exception as err:
        print(err)
        return False

    
def download_from_2(download_link, file_format="epub", bookname=bookname):
    """
    Download from mirror 2. Mirror 2 is typically a http://libgen.lc/
    """
    try:
        # THIS "s" equals s = requests.Session()
        html = s.get(download_link).text
        direct_download = "http://libgen.lc" + [x for x in html.split('"') if "mirr" in x][0]

        save_to_file(direct_download, file_format, bookname)
        return True
        
    except Exception as err:
        print(err)
        return False

        
def download_from_3(download_link, file_format="epub", bookname=bookname):
    """
    Download from mirror 3. Mirror 3 is typically a https://3lib.net/
    """
    print("[!] Currently not supported")


def download_from_4(download_link, file_format="epub", bookname=bookname):
    """
    (broken at time of writing this code)
    Download from mirror 4. Mirror 4 is typically a https://libgen.me/
    """
    print("[!] Currently not supported")

def download_from_5(download_link, file_format="epub", bookname=bookname):
    """
    (broken at time of writing this code)
    Download from mirror 5. Mirror 5 is typically a http://bookfi.net/
    """
    print("[!] Currently not supported")

def parsebookreq(bookname, pagenum = 1):
    bookname = urllib.parse.quote(bookname)
    url = f"https://libgen.is/search.php?req={bookname}&lg_topic=libgen&open=0&view=simple&res=25&phrase=1&column=def&page={pagenum}"
    return url


def download_book(download_links, file_format, bookname):
    """
    Try to download from various mirrors until successful download
    """
    print("[*] Total Available Mirrors: {}".format(len(download_links)))


    downloaded = False
    
    while not downloaded:    
        for i in range(0, len(download_links)):
            print(i + 1 ,download_links[i])

        while True:
            try:
                download_from = int(input("[>] "))
                if download_from > len(download_links) or download_from == 0:
                    print("[!] Please enter correct value")
                    continue
                break

            except ValueError:
                print("[!] Invalid Input")

        downloaded = eval(f"download_from_{str(download_from)}(download_links[{download_from - 1}], file_format, bookname)")        
                

def parseargs():
    global bookname
    parser = argparse.ArgumentParser(description="Download book from library Genesis with filters")
    parser.add_argument('bookname', type=str, help="name of the book to download")
    parser.add_argument('--author', type=str, help="author of the book to download")
    parser.add_argument('--publisher', type=str, help="publisher of the book to download")
    parser.add_argument('--year', type=str, help="publish year of the book to download")
    parser.add_argument('--savecsv', type=str, help="save all retrieved books to CSV file")
    parser.add_argument('--extension', type=str, help="extension of the book to download")
    parser.add_argument('--verbose', type=bool, help="extension of the book to download")

    args = parser.parse_args()
    bookname = args.bookname
    if args.extension != None:
        args.extension = args.extension.strip(".")

    if args.verbose:
        verbose = True

    return args


def filter_books(books, args):
    filtered_books = []
    for book in books:
        if args.author != None:
            if not args.author.lower() in book["author"].lower():
                continue

        if args.year != None:
            if not args.year.lower() in book["year_published"].lower():
                continue

        if args.publisher != None:
            if not args.publisher.lower() in book["publisher"].lower():
                continue

        if args.extension != None:
            if not args.extension.lower() in book["extension"].lower():
                continue

        filtered_books.append(book)
    
    return filtered_books



def search_worker(bookname, pg_no):
    # embed bookname in URI and open URI
    url = parsebookreq(bookname, pg_no)
    request_lock.acquire(True)
    response = requests.get(url)
    request_lock.release()

    # get raw HTML and parse it by lxml parser
    html = response.text
    parsed_html = BeautifulSoup(html, 'lxml')

    # find all <tr valign="top">
    books = parsed_html.body.find_all('tr', attrs={'valign':'top'})

    serial_num = 1

    # Iterate all books to fill list of books_details
    for book in books[1:]:
        raw_book_info = book.find_all("td")
        
        # Get all download links in list
        download_links = []
        for download_elmt in raw_book_info[9:14]:
            if not download_elmt.find('a').has_attr("style"):
                download_link = download_elmt.find('a').attrs["href"]
                download_links.append(download_link)

        books_details.append({
            "sno": serial_num + (pg_no - 1) * 25,
            "name": raw_book_info[2].text.strip(","),
            "author": raw_book_info[1].text.strip(","),
            "publisher": raw_book_info[3].text.strip(","),
            "year_published": raw_book_info[4].text.strip(","),
            "pages": raw_book_info[5].text.strip(","),
            "size": raw_book_info[7].text.strip(","),
            "extension": raw_book_info[8].text.strip(","),
            "download_links": download_links
        })
        serial_num += 1


def save_csv():
    book_csv_list = []
    for book in books_details:
        book_csv_list.append(f"{book['sno']},{book['name']},{book['author']},{book['publisher']},{book['year_published']},{book['pages']},{book['size']},{book['extension']},{' - '.join(book['download_links'])}\n")

    with open(args.savecsv, "w") as f:
        f.writelines(book_csv_list)
    


args = parseargs()
threads = []
url = parsebookreq(bookname)
response = requests.get(url)

# get raw HTML and parse it by lxml parser
html = response.text
parsed_html = BeautifulSoup(html, 'lxml')

# find all <tr valign="top">
page_len = int(parsed_html.body.find('font', attrs={'color':'grey', 'size': '1'}).text.split(" ")[0])
pages = int(page_len / 25 + 1) + 1

verbose_print("[*] Searching in {} pages".format(pages))

verbose_print("[*] Starting {} threads".format(pages - 1))
for pgno in range(1, pages):
    threads.append(threading.Thread(target=search_worker, args=(bookname, pgno)))

for thread in threads:
    thread.start()

verbose_print("[*] Waiting for threads to finish...")

bar = progressbar.ProgressBar(max_value=len(threads)).start()

for index, thread in enumerate(threads):
    bar.update(index + 1)
    thread.join()

bar.finish()

print("")
# books_details = books_details.sort(key=lambda x: x["sno"], reverse=True)

verbose_print("[*] Found {} results before applying filters".format(len(books_details)))
books_details = filter_books(books_details, args)
verbose_print("[*] Found {} results after filtering".format(len(books_details)))


if len(books_details) == 0:
    print("- No result found")
    exit(0)


if args.savecsv:
    verbose_print("[*] Saving data to csv file")
    save_csv()

print("Results:")
for index, book_details in enumerate(books_details):
    print(index + 1, " [" + book_details["extension"] + "]", book_details["name"], "by " + book_details["author"])

while True:
    try:
        book_selected = int(input("Which book to download?\n[>] "))
        if book_selected > len(books_details) or book_selected == 0:
            print("[!] Invalid Option")
            continue
        break
    except ValueError:
        print("[!] Invalid Input")


download_book(books_details[book_selected - 1]["download_links"], books_details[book_selected - 1]["extension"], books_details[book_selected - 1]["name"])
