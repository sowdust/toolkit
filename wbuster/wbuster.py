import sys, json, csv, os
import requests, argparse
import threading

EXCLUDE = ['png', 'js', 'gif', 'jpg', 'png', 'css', 'ico', 'xjsp']
MAX_THREADS = 10
BASE_URL = 'https://web.archive.org/cdx/search?url=%s/&matchType=prefix&collapse=urlkey&output=json&fl=original,mimetype,timestamp,endtimestamp,groupcount,uniqcount&filter=!statuscode:[45]..&limit=100000&_=1547318148315'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0'}

VERSION = "0.1"
BANNER = """
{0} v. {1} - wbuster: Scrape domain URLs from the WayBack Machine

by sowdust
""".format(sys.argv[0],VERSION)


found_urls = {}
threadLimiter = None

def get_urls(domain, max_date, exclude):
    threadLimiter.acquire()
    try:
        print('[*] Trying domain %s' % domain)
        ret = []
        url = BASE_URL % domain
        r = requests.get(url, headers=HEADERS)
        results = json.loads(r.text)
        for res in results:
            clean_url = res[0].split('?')[0]
            extension = clean_url[-3:]
            date = res[2]
            if date <= max_date and extension not in exclude:
                print('[%s] %s' % (date, res[0]))
                found_urls[domain].append(res[0])
    except Exception as ex:
            print('[!] Error: %s' % ex)
    finally:
        threadLimiter.release()


def parse_args():

    parser = argparse.ArgumentParser(description='Scrape URLs from the WayBack Machine')
    parser.add_argument('-i', '--input-file', metavar='INPUTFILE', type=str, help='Input file containing list of domains')
    parser.add_argument('-o','--output-file', metavar='OUTPUTFILE', type=str, help='Output files to save results as a CSV')
    parser.add_argument('-d','--max-date', metavar='MAX_DATE', type=str, help='Only show URLs first seen up to this date (format yyyymmddhhmmss)')
    parser.add_argument('-t','--threads', metavar='THREADS', type=int, help='Concurrent threads. Dafault is %d' % MAX_THREADS)
    parser.add_argument('-e','--exclude', metavar='EXCLUDE', nargs='+', type=str, help='List of extensions to exclude, separated by a space. Default: %s' % ' '.join(EXCLUDE))
    args = parser.parse_args(args=None if len(sys.argv) > 1 else ['--help'])
    return args

    
def main():
    global threadLimiter

    args = parse_args()
    if not args.input_file or not os.path.isfile(args.input_file):
        error('Input file not valid or not set')
    if not args.output_file:
        error('Output file not set')
    exclude = args.exclude if args.exclude else EXCLUDE
    max_date = args.max_date if args.max_date else sys.maxint
    max_threads = args.threads if args.threads else MAX_THREADS

    threads = []
    threadLimiter = threading.BoundedSemaphore(max_threads)

    with open(args.input_file, 'r') as ifile:
        domains = [line.strip() for line in ifile.readlines()]

    for domain in domains:
        found_urls[domain] = []
        thread = threading.Thread(target=get_urls, args=(domain, max_date, exclude,))
        threads.append(thread)
    for i in range(len(threads)):
        threads[i].start()
    for i in range(len(threads)):
        threads[i].join()

    print('[*] Writing results to csv file %s' % args.output_file)
    with open(args.output_file, 'w', newline='', encoding='utf-8') as ofile:
        csv_writer = csv.writer(
            ofile, delimiter=',',quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for domain in found_urls.keys():
            csv_data = [[domain, url] for url in found_urls[domain]]
            csv_writer.writerows(csv_data)


if __name__ == '__main__':
    main()
