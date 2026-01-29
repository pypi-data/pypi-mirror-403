from abstract_webtools.managers import *

class usurpManager:
    def __init__(
        self,
        url_mgr,
        ua_mgr,
        req_mgr,
        soup_mgr,
        output_dir=None,
        max_depth=5,
        wait_between_requests=1,
        website_bot=None,
    ):
        self.url_mgr = url_mgr
        self.ua_mgr = ua_mgr
        self.req_mgr = req_mgr
        self.soup_mgr = soup_mgr

        self.BASE_URL = url_mgr.url
        self.OUTPUT_DIR = output_dir or "download_site"
        self.MAX_DEPTH = max_depth
        self.WAIT_BETWEEN_REQUESTS = wait_between_requests

        self.visited_pages = set()
        self.downloaded_assets = set()


    def process_page(self, url, depth, base_domain):
        if url in self.visited_pages or depth > self.MAX_DEPTH:
            return

        self.visited_pages.add(url)

        self.req_mgr.update_url(url)
        soup_mgr = soupManager(req_mgr=self.req_mgr)
        soup = soup_mgr.soup
        
 
            
        # Use your get_soup_mgr function to get the soup and attributes
        soup_mgr = get_soup_mgr(req_mgr=self.req_mgr)
        soup = soup_mgr.soup
        all_attributes = soup_mgr.get_all_attribute_values()
        # Now you can use all_attributes as needed

        # Update asset links to local paths
        for tag in soup.find_all(['img', 'script', 'link']):
            attr = 'src' if tag.name != 'link' else 'href'
            asset_url = tag.get(attr)
            if asset_url:
                full_asset_url = normalize_url(asset_url, url)
                parsed_asset_url = urlparse(full_asset_url)

                if is_valid_url(full_asset_url, base_domain):
                    self.downloaded_assets = save_asset(full_asset_url,
                                                        self.url,
                                                        self.OUTPUT_DIR,
                                                        self.downloaded_assets,
                                                        self.session)
                    # Update tag to point to the local asset
                    local_asset_path = '/' + parsed_asset_url.path.lstrip('/')
                    tag[attr] = local_asset_path

        # Save the modified page
        save_page(url, str(soup),self.OUTPUT_DIR)
        # Use your linkManager to find all domain links
        link_mgr = linkManager(url=url)
        all_domains = link_mgr.find_all_domain()
        
        # Process each domain link
        for link_url in make_list(all_domains):
            normalized_link = normalize_url(link_url, url)
            if is_valid_url(normalized_link, base_domain):
                time.sleep(self.WAIT_BETWEEN_REQUESTS)
                self.process_page(normalized_link, depth + 1, base_domain)


    def main(self):
        # Ensure output directory exists
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

        base_parsed = urlparse(self.BASE_URL)
        base_domain = base_parsed.netloc

        self.process_page(self.BASE_URL, 0, base_domain)
        print("Website copying completed.")
def get_verified_mgr(
        url,
        ua_mgr=None,
        wait_between_requests=None,
        operating_system=None,
        browser=None,
        version=None,
        headers=None,
        user_agent=None,
        user_agent_manager=None,
        ssl_manager=None,
        tls_adapter=None,
        proxies=None,
        cookies=None,
        ciphers=None,
        certification=None,
        ssl_options=None
        ):
    ua_mgr = ua_mgr or UserAgentManager(
        randomAll=True,
        user_agent=user_agent,
        browser=browser,
        version=version,
        operating_system=operating_system
        )
    while True:
        req_mgr = requestManager(
             url=url,
             ua_mgr=ua_mgr,
             headers=ua_mgr.generate_headers(),
             ssl_manager=ssl_manager,
             tls_adapter=tls_adapter,
             user_agent=user_agent,
             proxies=proxies,
             cookies=cookies,
             ciphers=ciphers,
             certification=certification,
             ssl_options=ssl_options
             )
        soup_mgr = soupManager(req_mgr=req_mgr)
        text = soup_mgr.soup.text
        if 'Please update your browser' not in text and 'Bitte aktualisiere deinen BrowserDein Browser' not in text and 'browser is no longer supported' not in text:
            return {
                    "req_mgr": req_mgr,
                    "soup_mgr": soup_mgr,
                    "ua_mgr": ua_mgr,
                    "url_mgr": req_mgr.url_mgr,
                }

def usurpit(
            url,
            output_dir=None,
            max_depth=None,
            wait_between_requests=None,
            browser=None,
            version=None,
            website_bot=None,
            ua_mgr=None,
            headers=None,
            operating_system=None,
            user_agent=None,
            ssl_manager=None,
            tls_adapter=None,
            proxies=None,
            cookies=None,
            ciphers=None,
            certification=None,
            ssl_options=None
            ):
    verified = get_verified_mgr(
            url=url,
            user_agent=user_agent,
            browser=browser,
            version=version,
            operating_system=operating_system,
            ua_mgr=ua_mgr,
            headers=headers,
            ssl_manager=ssl_manager,
            tls_adapter=tls_adapter,
            proxies=proxies,
            cookies=cookies,
            ciphers=ciphers,
            certification=certification,
            ssl_options=ssl_options
            )
    output_dir = get_domain_name_from_url(url) or  make_directory(path='usurped')
    site_mgr = usurpManager(
            url_mgr=verified["url_mgr"],
            ua_mgr=verified["ua_mgr"],
            req_mgr=verified["req_mgr"],
            soup_mgr=verified["soup_mgr"],
            output_dir=output_dir,
            max_depth=max_depth,
            wait_between_requests=wait_between_requests,
            website_bot=website_bot,
            )
    site_mgr.main()



