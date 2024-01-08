import datetime, os, subprocess, time, re, json, sys, requests, urllib3
from bs4 import BeautifulSoup
from stem import Signal
from stem.control import Controller
from urllib.parse import urlparse
from pgpy import PGPKey
from requests.adapters import HTTPAdapter
from webdriver_manager.chrome import ChromeDriverManager
from urllib3.util import Retry
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
import threading
from PIL import Image
from io import BytesIO
import platform
import os.path
import argparse
 
from csilibs.utils import pathme
#----------------------- GLOBAL INIT ------------------------------#
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os_name = platform.system()
csitoolname = "CSI Scanner Darkly Scraper"
capture_thread = None
config_file = "agency_data.json"
# init in main_scraper function
case_directory = ''
evidence_dir = ''
domains_dir = ''
filepathhtm = ''

keywords_folder = pathme('data/keywordlists')
if not os.path.exists(keywords_folder):
    raise FileNotFoundError("No Keyword Lists")
keywords_files = [f for f in os.listdir(keywords_folder) if f.endswith('.txt')]

keywords = {}
for file_name in keywords_files:
    keyword_group = os.path.splitext(file_name)[0]
    file_path = os.path.join(keywords_folder, file_name)
    try:
        with open(file_path, encoding='utf-8') as file:  # Specify the correct encoding here
            keyword_list = file.read().splitlines()
            if keyword_list:
                keywords[keyword_group] = keyword_list
    except UnicodeDecodeError:
        print(f"Skipping file {file_path} due to decoding error.")

#------------------------------------------------------------------#

def genFileName(url, ext):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    if parsed_url.path == '' or parsed_url.path == '/':
        filename = 'index'  # Assuming `url` is defined
    else:
        filename = parsed_url.path.replace("/","_")[1:]

    file_name = f"{filename}.{ext}"

    return file_name

def capture_screenshot_thread(url, driver):
    global capture_thread
    try:
        capture_thread = threading.Thread(target=capture_screenshot, args=(url, driver))
        capture_thread.start()
    except Exception as e:
        print(f"Failed to start capture thread. Error: {e}")

def capture_screenshot(url, driver, onion=False):
    # Create directories if they don't exist
    tor_proxy = "127.0.0.1:9050"  # Assuming this is your SOCKS5 proxy address
    parsed_url = urlparse(url)     
    domain = parsed_url.netloc  # Assuming `url` is defined
    if not os.path.exists(evidence_dir):
        os.makedirs(evidence_dir)
    if not os.path.exists(os.path.join(evidence_dir, domains_dir)):
        os.makedirs(os.path.join(evidence_dir, domains_dir))
    if not os.path.exists(os.path.join(evidence_dir, domains_dir, domain)):
        os.makedirs(os.path.join(evidence_dir, domains_dir, domain))
    try:
        tor_proxy = "127.0.0.1:9050"  # Assuming this is your SOCKS5 proxy address     
        filename = genFileName(url,'png')
        filepath = os.path.join(evidence_dir, domains_dir, domain, filename)
        
        print('capture_url', url)
        driver.get(url)
        
        total_height = driver.execute_script("return document.documentElement.scrollHeight")
        driver.set_window_size(1280, total_height)
        screenshots = []
        while True:
            # Capture the current viewport screenshot
            screenshots.append(driver.get_screenshot_as_png())

            # Scroll down the page
            driver.execute_script("window.scrollBy(0, window.innerHeight);")

            # Break the loop when reaching the end of the page
            if driver.execute_script("return window.pageYOffset + window.innerHeight >= document.documentElement.scrollHeight"):
                break

        # Stitch the captured screenshots together
        stitched_image = Image.new("RGB", (1280, total_height))
        y_offset = 0
        for screenshot in screenshots:
            image = Image.open(BytesIO(screenshot))
            stitched_image.paste(image, (0, y_offset))
            y_offset += image.size[1]

        # Save the final stitched screenshot
        stitched_image.save(filepath)        
        
        print(f"Capture is complete for {driver.title}")
        driver.save_screenshot(filepath)
        timestamp = get_current_timestamp()
        auditme(case_directory, f"{csitoolname} captured a screenshot of {filename}") 
        # subprocess.Popen(["ristretto", filepath])
    except Exception as e:
        print(f"Failed to capture screenshot for {url}. Error: {str(e)}")
        traceback.print_exc()
        
def update_tor_hidden_records(url, session, keywords, records):
    base_link = '/'.join(url.split('/')[:3])  # Get the base URL
    existing_record = next((record for record in records if record["link"] == base_link), None)
    if existing_record:
        print(f"The site has been seen before {url}\nUpdating data...")
        existing_record["last_seen"] = datetime.datetime.now().isoformat()
        page_id = url.split('/')[-1]
        try:
            page_response = session.get(url)
            existing_record["html"][page_id] = {"html": page_response.text}
        except Exception:
            pass
    else:
        try:
            fresh_record(url, session, keywords, records)
        except Exception:
            pass

def delete_record(link, records):
    updated_records = [record for record in records if link not in record["link"]]
    # Save the updated records to the JSON file
    with open("site_capture.json", "w") as file:
        json.dump(updated_records, file, indent=4)
    timestamp = get_current_timestamp()
    auditme(case_directory, f"{timestamp}: {csitoolname} deleted records for {link}") 
    return updated_records

def fresh_record(url, session, keywords, records, driver, onion, recurse=False, scraped_urls=None, depth=1):   #scraped_urls for recursive option
    print(f"New site found {url}\nAttempting to connect...")
    record = {
        "link": url,
        "first_seen": datetime.datetime.now().isoformat(),
        "last_seen": datetime.datetime.now().isoformat()
    } 
    
    try:
        headers = getRandomUserAgent()

        if onion:
            driver.options.add_argument("--proxy-server=socks5://127.0.0.1:9050")       
        site_response = session.get(url, headers=headers, timeout=10)
        site_soup = BeautifulSoup(site_response.text, "html.parser")
        html_code = site_response.text
        filepathhtm = os.path.join(evidence_dir, domains_dir, urlparse(url).netloc, genFileName(url,'html'))
        with open(filepathhtm, 'w', encoding='utf-8') as file:
            file.write(html_code)
        title = site_soup.title.string if site_soup.title else None
        meta_description = site_soup.find("meta", attrs={"name": "description"})
        description = meta_description["content"] if meta_description else None

        try:
            capture_screenshot_thread(url, driver)
        except:
            print("error")

        record["first_connected"] = datetime.datetime.now().isoformat()
        record["last_connected"] = datetime.datetime.now().isoformat()
          
        
        server = site_response.headers.get('Server')
        if server:
            record["server"] = server

        record["title"] = title
        record["description"] = description
        

        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b', site_response.text)
        filtered_emails = []
        for email in emails:
            if not email.endswith((".png", ".jpg", ".gif", ".jpeg", ".ico", ".svg", ".bmp")):
                filtered_emails.append(email)

        # Deals with cloudflare Email address obfuscation
        span_element = site_soup.find('span', class_='__cf_email__')
        if span_element is not None:
            data_cfemail = span_element['data-cfemail']

            def decode_email(encoded_email):
                decoded_email = ''
                key = int(encoded_email[:2], 16)

                for i in range(2, len(encoded_email), 2):
                    hex_value = int(encoded_email[i:i+2], 16) ^ key
                    decoded_email += chr(hex_value)

                return decoded_email
            
            filtered_emails.append(decode_email(data_cfemail))
        #-----------------------------------

        filtered_emails = list(set(filtered_emails))
        record["emails"] = filtered_emails


        bitcoin_addresses = re.findall(r'\b([13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-zA-HJ-NP-Za-km-z]{6,})\b', site_response.text)
        if bitcoin_addresses:
            record["bitcoin_wallets"] = bitcoin_addresses
        
        litecoin_addresses = re.findall(r'\b(?:[LM3][a-km-zA-HJ-NP-Z1-9]{26,33})\b', site_response.text)
        litecoin_addresses = [address for address in litecoin_addresses if address not in bitcoin_addresses]  # Exclude Bitcoin addresses
        if litecoin_addresses:
            record["litecoin_wallets"] = litecoin_addresses
                
        monero_addresses = re.findall(r'\b4[0-9AB][a-zA-Z0-9]{93}\b', site_response.text)
        if monero_addresses:
            record["monero_wallets"] = monero_addresses
                
        ethereum_addresses = re.findall(r'\b0x[a-fA-F0-9]{40}\b', site_response.text)
        if ethereum_addresses:
            record["ethereum_wallets"] = ethereum_addresses
                
        dash_addresses = re.findall(r'\bX[1-9A-HJ-NP-Za-km-z]{33}\b', site_response.text)
        if dash_addresses:
            record["dash_wallets"] = dash_addresses

        pgp_key_pattern = r'-----BEGIN PGP PUBLIC KEY BLOCK-----(?:.|\n)*?-----END PGP PUBLIC KEY BLOCK-----'
        pgp_keys = re.findall(pgp_key_pattern, site_response.text)
        pgp_key_owners = []
        for key in pgp_keys:
            try:
                min_key_length = 1000
                if len(key) < min_key_length:
                    continue
                example_key_pattern = r'EXAMPLE'
                broken_key_pattern = r'BROKEN'
                if re.search(example_key_pattern, key, re.IGNORECASE) or re.search(broken_key_pattern, key, re.IGNORECASE):
                    continue
                record["pgp_key"] = key.strip()
                owner_pattern = r'(?:^|\n)([A-Za-z0-9 ]+)[<>].*?@.*?(?=\n|$)'
                owner = re.search(owner_pattern, key)
                if owner:
                    pgp_key_owners.append(owner.group(1).strip())
                    print("Owner:")
                    print(owner.group(1).strip())
                    record["pgp_key_owner"] = owner.group(1).strip()
                print("--------------")
            except:
                print("Error processing PGP key")
        record["pgp_keys"] = pgp_keys
        record["pgp_key_owners"] = pgp_key_owners
      
        ip_addresses = re.findall(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
            site_response.text)
        record["ip_addresses"] = ip_addresses

        keyword_count = {}
        print("Searching for keywords")
        for keyword_group, keyword_list in keywords.items():
            keyword_count[keyword_group] = {}
            
            # print(f"Searching for {keyword_group} keywords")
            for keyword in keyword_list:
                count = len(re.findall(fr'\b{re.escape(keyword)}\b', site_response.text, re.IGNORECASE))
                if count > 0:
                    keyword_count[keyword_group][keyword] = count
        record["keywords"] = keyword_count

        record["md5_hash"] = {filepathhtm: generate_md5(filepathhtm)}        
        
    except Exception as e:
        record["first_connected"] = None
        record["last_connected"] = None
        record["title"] = None
        record["description"] = None

    # Finding links in the website for the recursive scraping
    internal_urls = []
    external_urls = []

    a_tags = site_soup.find_all('a')
    href_list = [a.get('href') for a in a_tags]
    href_list = [x for x in href_list if x is not None]

    for href in href_list:
        parsed_url = urlparse(href)
        if parsed_url.netloc == '':
            if parsed_url.path != '' and parsed_url.path.startswith('/'):
                complete_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}{parsed_url.path}"
                internal_urls.append(complete_url)
        elif parsed_url.path.startswith('/'):
            # extracting only domain name from the netloc without subdomain
            domain_name = '.'.join(parsed_url.netloc.split('.')[-2:])
            if urlparse(url).netloc.endswith(domain_name):
                internal_urls.append(href)
            else:
                external_urls.append(href)
            # extracting
    record["external_urls"] = list(set(external_urls)) 
    if recurse == False or depth == 0:
        record["internal_urls"] = list(set(internal_urls)) 
    elif recurse == True and depth != 0:
        print("it's depth :",depth)
        urls_not_to_scrape = internal_urls
        urls_not_to_scrape.append(url)
        if scraped_urls is not None:
            urls_not_to_scrape.extend(scraped_urls)
        urls_not_to_scrape = list(set(urls_not_to_scrape)) 
        for in_url in set(internal_urls):
            if in_url != url and (scraped_urls is None or in_url not in scraped_urls):
                record[in_url] = fresh_record(in_url, session, keywords, records, driver, onion, recurse=True, scraped_urls=urls_not_to_scrape, depth=depth-1)
    
    if scraped_urls is None:
        # Check if the URL is already present in the records
        url_without_protocol = urlparse(url).netloc + urlparse(url).path
        url_found = False

        for existing_record in records:
            parsed_url = urlparse(existing_record["link"])
            existing_url_without_protocol = parsed_url.netloc + parsed_url.path
            if url_without_protocol == existing_url_without_protocol:
                url_found = True
                existing_record.update(record)
                break

        if not url_found:
            records.append(record)

        with open(f"{evidence_dir}/site_capture.json", "w") as file:
            json.dump(records, file, indent=4)
        
        driver.quit()
        return record
    else:
        return record

def main_scraper(case, dom_dir, url, options, recurse=False, depth=1):
    
    print("Starting Scanner Darkly Scraper")
    TorCheck("on")
    
    global case_directory, evidence_dir, domains_dir, filepathhtm
    domains_dir = dom_dir
    case_directory = CaseDirMe(case, create=True).case_dir
    create_case_folder(case_directory)

    auditme(case_directory, f"Opening {csitoolname}") 

    evidence_dir = os.path.join(case_directory, "Evidence", "Online")
    os.makedirs(evidence_dir, exist_ok=True)
    print(evidence_dir) 

    if not os.path.exists(f"{evidence_dir}/site_capture.json"):
        with open(f"{evidence_dir}/site_capture.json", "w") as file:
            json.dump([], file)
    print("Opening Site Capture Database...")
    with open(f"{evidence_dir}/site_capture.json", "r") as file:
        records = json.load(file)

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    # print('fil_ext',parsed_url)
    # if parsed_url.path == '' or parsed_url.path == '/':
    #     filename = 'index'  # Assuming `url` is defined
    # else:
    #     filename = parsed_url.path.replace("/","_")[1:]

    # filenamehtm = f"{filename}.html"
    # filepathhtm = os.path.join(evidence_dir, domains_dir, domain, filenamehtm)

    retries = Retry(total=3, backoff_factor=0.1)
    adapter = HTTPAdapter(max_retries=retries)
    session = requests.Session()
    session.mount('http://', adapter)
    session.mount('https://', adapter)


    # Create directories if they don't exist
    if not os.path.exists(evidence_dir):
        os.makedirs(evidence_dir)
    if not os.path.exists(os.path.join(evidence_dir, domains_dir)):
        os.makedirs(os.path.join(evidence_dir, domains_dir))
    if not os.path.exists(os.path.join(evidence_dir, domains_dir, domain)):
        os.makedirs(os.path.join(evidence_dir, domains_dir, domain))

    # Check if domain is a .onion domain
    if domain.endswith('.onion'):
        print("Configuring the Tor proxy...")
        proxy_address = "127.0.0.1:9050"  # Proxy address for .onion domains
        proxy = Proxy()
        proxy.proxy_type = ProxyType.MANUAL
        proxy.socks_proxy = proxy_address
        session = requests.Session()
        session.proxies = {
            'http': 'socks5h://localhost:9050',
            'https': 'socks5h://localhost:9050'
        }
        retries = 3
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        if os_name == "Windows":
            from lib.WindowsConfig import ConfigMe

            # Run tor.exe as a subprocess
            current_dir = getattr(sys, "_MEIPASS", os.getcwd())
            torbin = os.path.join(current_dir, "tor", "tor.exe")
            print(f"Tor bin: {torbin}")
            torbin = f'"{torbin}"'  # Wrap torbin variable with double quotes
            print(f"Tor bin with quotes: {torbin}")
            tor_process = subprocess.Popen(torbin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Wait for the Tor process to establish a connection
            while True:
                output = tor_process.stdout.readline().decode().strip()
                if 'Bootstrapped 100%' in output:
                    print('Connected')
                    break
                elif 'Bootstrapped ' in output:
                    progress = output.split(' ')[1]
                    print(f'Bootstrapping: {progress}')
                time.sleep(1)
                timestamp = get_current_timestamp()
                auditme(case_directory, f"{timestamp}: {csitoolname} is setting up Tor for {domain}")
                
        else:
            print("Configuring Tor connection...")
        
        extra_options = ["--disable-extensions", "--incognito", "--headless", "--disable-javascript", "--disable-popup-blocking", "--disable-notifications", "--incognito"]
        driver = ChromedriverCheck("on", additional_options=extra_options, onion=True)
            
        print("Tor setup complete")
    else: 
        extra_options = ["--disable-extensions", "--incognito", "--headless", "--disable-javascript", "--disable-popup-blocking", "--disable-notifications", "--incognito"]
        driver = ChromedriverCheck("on", additional_options=extra_options, onion=False)
        print("Internet setup complete")

    if options == 'n':
        record = fresh_record(url, session, keywords, records, driver, onion=False, recurse=recurse, depth=depth)
        if capture_thread is not None:
            capture_thread.join()
        else:
            print("Capture thread is None.")
        print("Scraping is complete.")
    elif options == 'r':
        link_to_delete = url
        records = delete_record(link_to_delete, records)
        print("Removal complete.")
    elif options == 'c':
        updated_records = [record for record in records if record.get("first_connected") is not None]
        # Save the updated records to the JSON file
        with open(f"{evidence_dir}/site_capture.json", "w") as file:
            json.dump(updated_records, file, indent=4)
        print("Clearinf site_capture database complete.")    
    else:
        capture_screenshot_thread(url, driver)
        update_tor_hidden_records(url, session, keywords, records)
        if capture_thread is not None:
            capture_thread.join()
        else:
            print("Capture thread is None.")
        print("Scraping is complete.")


        
        
    timestamp = get_current_timestamp()
    auditme(case_directory, f"{timestamp}: {csitoolname} Scraping of {url} is complete")   


    for record in records:
        if domain in record['link']:
            print(f"Link: {record['link']}")
            print(f"First Seen: {record['first_seen']}")
            print(f"Last Seen: {record['last_seen']}")
            if 'first_connected' in record:
                print(f"First Connected: {record['first_connected']}")
            if 'last_connected' in record:
                print(f"Last Connected: {record['last_connected']}")
            if 'title' in record:
                print(f"Title: {record['title']}")
            if 'description' in record:
                print(f"Description: {record['description']}")
            if 'emails' in record:
                print(f"Emails: {record['emails']}")
            if 'bitcoin_wallets' in record:
                print(f"Bitcoin: {record['bitcoin_wallets']}")
            if 'litecoin_wallets' in record:
                print(f"Litecoin: {record['litecoin_wallets']}")    
            if 'monero_wallets' in record:
                print(f"Monero: {record['monero_wallets']}")    
            if 'ethereum_wallets' in record:
                print(f"Ethereum: {record['ethereum_wallets']}")    
            if 'dash_wallets' in record:
                print(f"Dash: {record['dash_wallets']}")
            if 'pgp_key' in record:
                print(f"PGP_Key: {record['pgp_key']}")
            if 'ip_addresses' in record:
                print(f"IP Addresses: {record['ip_addresses']}")
            if 'keywords' in record:
                print(f"Keywords: {record['keywords']}")
            # if os.path.exists(filepathhtm):
            #     print(f"HTML code saved to: {filepathhtm}")
            # else:
            #     print(f"HTML file does not exists: {filepathhtm}")

            print("----------\n")
            
    # Terminate Tor process if it is still running
    if 'tor_process' in locals() and tor_process.poll() is None:
        tor_process.terminate()
        print('Tor process terminated')  

    print("Complete")

    if record is not None:
        return record


if __name__  == "__main__":
    # Define command-line arguments
    parser = argparse.ArgumentParser(description="CSI Scanner Darkly Scraper")
    parser.add_argument('--case', type=str, help="case name")
    parser.add_argument('--edir', type=str, help="Path to the Evidence sub-directory")
    parser.add_argument('-u', type=str, help="URL to capture", required=True)
    parser.add_argument('-o', type=str, help="Option r, n, c")
    parser.add_argument('--recurse', action='store_true')
    parser.add_argument('--depth', type=int, help="depth 1,2,3..",default=1)

    args = parser.parse_args()

    main_scraper(args.case, args.edir, args.u, args.o, args.recurse, args.depth)