# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
import re
import string
import urllib
import urlparse

from itertools import islice
import scrapy.log
from scrapy.log import ERROR, WARNING, INFO
from scrapy.http import Request
from scrapy.spider import Spider
from pfinder.items import SiteProductItem

def identity(x):
    return x

def cond_set_value(item, key, value, conv=identity):
    if item.get(key) is None and value is not None and conv(value) is not None:
        item[key] = conv(value)

class FormatterWithDefaults(string.Formatter):

    def __init__(self, **defaults):
        self.defaults = defaults

    def get_fields(self, field_name, args, kwargs):
        # Handle a key not found
        try:
            val = super(FormatterWithDefaults, self).get_field(
                field_name, args, kwargs)
        except (KeyError, AttributeError):
            val = urllib.quote_plus(str(self.defaults[field_name])), field_name
        return val
class BaseProductsSpider(Spider):
    start_urls = []

    SEARCH_URL = None # Override

    MAX_RETRIES = 3

    USER_AGENTS = {
        'iphone_ipad': 'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0_6 '\
            'like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) '\
            'Version/7.0 Mobile/11B651 Safari/9537.53',
        'default': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:35.0) '\
            'Gecko/20100101 Firefox/35.0',
        'desktop': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:35.0) '\
            'Gecko/20100101 Firefox/35.0',
        'android_phone': 'Mozilla/5.0 (Android; Mobile; rv:35.0) '\
            'Gecko/35.0 Firefox/35.0',
        'android_pad': 'Mozilla/5.0 (Android; Tablet; rv:35.0) '\
            'Gecko/35.0 Firefox/35.0',
        'android': 'Mozilla/5.0 (Android; Tablet; rv:35.0) '\
            'Gecko/35.0 Firefox/35.0',
        'iphone6': 'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X)'\
            ' AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25',
        'ipad6': 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26'\
                ' (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25',
        'iphone4': 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us)'\
            ' AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7',
        'ipad4': 'Mozilla/5.0 (iPad; U; CPU iPhone OS 4_0 like Mac OS X; en-us)'\
            ' AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7'
    }

    def __init__(self,
                 url_formatter=None,
                 quantity=None,
                 searchterms_str=None, searchterms_fn=None,
                 site_name=None,
                 product_url=None, products_url=None,
                 user_agent=None,
                 scrape_variants_with_extra_requests=True,
                 sumary=None,
                 *args, **kwargs):
        self.proxy_service = None
        self.proxy_config = ""
        self.proxy_config_filename = ""

        if user_agent is None or user_agent not in self.USER_AGENTS.keys():
            self.log("Not available user agent type or it wasn't set."
                     " Default user agent will be used.", INFO)
            user_agent = 'default'

        if user_agent:
            self.user_agent = self.USER_AGENTS[user_agent]
            self.user_agent_key = user_agent

        if scrape_variants_with_extra_requests in (0, '0', 'false', 'False', False, None):
            self.scrape_variants_with_extra_requests = False
        else:
            self.scrape_variants_with_extra_requests = True

        if product_url is None:
            self.scrape_variants_with_extra_requests = False

        super(BaseProductsSpider, self).__init__(*args, **kwargs)

        if site_name is None:
            assert len(self.allowd_domains) == 1, \
                "A single allowd domain is required to auto-detect site name."
            self.site_name = self.allowed_domains[0]
        else:
            self.site_name = site_name

        if url_formatter is None:
            self.url_formatter = string.Formatter()
        else:
            self.url_formatter = url_formatter

        if quantity is None:
            self.log("No quantity specified. Will retrieve all products.",
                     INFO)
            import sys
            self.quantity = sys.maxint
        else:
            self.quantity= int(quantity)

        self.product_url = product_url
        self.products_url = products_url

        self.searchterms = []
        if searchterms_str is not None:
            self.searchterms = searchterms_str.decode('utf-8').split(',')
        elif searchterms_fn is not None:
            with open(searchterms_fn, encoding='utf-8') as f:
                self.searchterms = f.readline()
        else:
            self.log("No search terms provided!", ERROR)



    def start_requests(self):

        for st in self.searchterms:
            yield Request(
                self.url_formatter.format(
                    self.SEARCH_URL,
                    search_term = urllib.quote_plus(st.encode('utf-8')),
                    page_num = 1,
                ),
                meta={'search_term': st, 'remaining': self.quantity},
            )

        if self.product_url:
            prod = SiteProductItem()
            prod['is_single_result'] = True
            prod['url'] = self.product_url
            prod['search_term'] = ''
            yield Request(self.product_url,
                          self._parse_single_product,
                          meta={'product': prod})

        if self.products_url:
            urls = self.products_url.split('||||')
            for url in urls:
                prod = SiteProductItem()
                prod['url'] = url
                prod['search_term'] = ''
                yield Request(self.product_url,
                              self._parse_single_product,
                              meta={'product': prod})

    def parse(self, response):

        if hasattr(self, 'handle_httpstatus_list'):
            for _code in self.handle_httpstatus_list:
                if response.status == _code:
                    _callable = getattr(self, 'parse_' + str(_code), None)
                    if callable(_callable):
                        yield _callable()

        if self._search_page_error(response):
            remaining = response.meta['remaining']
            search_term = response.meta['search_term']

            self.log("For search term '%s' with %d items remaining,"
                     " failed to retrieve search page: %s"
                     % (search_term, remaining, response.request_url),
                     WARNING)
        else:
            prods_count = -1
            for prods_count, request_or_prod in enumerate(
                    self._get_products(response)):
                yield request_or_prod
            prods_count += 1

            request = self._get_next_products_page(response, prods_count)

            if request is not None:
                yield request

    def _parse_single_product(self, response):
        raise NotImplementedError
    def _scrap_product_links(self, response):
        raise NotImplementedError

    def _get_products(self, response):
        remaining = response.meta['remaining']
        search_term = response.meta['search_term']
        prods_per_page = response.meta.get('products_per_page')
        total_matches = response.meta.get('total_maches')
        scraped_results_per_page = response.meta.get('scraped_results_per_page')

        prods = self._scrape_product_links(response)

        if prods_per_page is None:
            prods = list(prods)
            prods_per_page = len(prods)
            response.meta['poducts_per_page'] = prods_per_page

        if scraped_results_per_page is None:
            scraped_results_per_page = self._scrape_results_per_page(response)
            if scraped_results_per_page:
                self.log(
                    "Found %s products the first page" %scraped_results_per_page,
                    INFO)
            else:
                scraped_results_per_page = prods_per_page
                if hasattr(self, 'is_nothing_found'):
                    if not self.is_nothing_found(response):
                        self.log(
                            "Failed to scrap number of products per page", WARNING)
            response.meta['scraped_results_per_page'] = scraped_results_per_page

        if total_matches is None:
            total_matches = self._scrape_total_matches(response)
            if total_matches is not None:
                response.meta['total_matches'] = total_matches
                self.log("Found %d total matches." % total_matches, INFO)
            else:
                if hasattr(self, 'is_nothing_found'):
                    if not self.is_nothing_found(response):
                        self.log(
                            "Failed to parse total matches for %s" % response.url, ERROR)

        if total_matches and not prods_per_page:
            self.log("Failed to get products for %s" % response.url, ERROR)
            return

        for i, (prod_url, prod_item) in enumerate(islice(prods, 0, remaining)):
            prod_item['site'] = self.site_name
            prod_item['search_term'] = search_term
            prod_item['total_matches'] = total_matches
            prod_item['results_per_page'] = prods_per_page
            prod_item['scraped_results_per_page'] = scraped_results_per_page

            prod_item['ranking'] = (i + 1) + (self.quantity - remaining)
            if self.user_agent_key not in ['desktop', 'default']:
                prod_item['is_mobile_agent'] = True

            if prod_url is None:
                yield prod_item
            elif isinstance(prod_url, Request):
                cond_set_value(prod_item, 'url', prod_url.url)
                yield prod_url

            else:
                url = urlparse.urljoin(response.url, prod_url)
                cond_set_value(prod_item, 'url', url)
                yield Request(
                    url,
                    callback = self.parse_product,
                    meta={'product': prod_item},
                )

    def _get_next_products_page(self, response, prods_found):
        link_page_attempt = response.meta.get('link_page_attempt', 1)

        result = None
        if prods_found is not None:
            # This was a real product listing page.
            remaining = response.meta['remaining']
            remaining -= prods_found
            if remaining > 0:
                next_page = self._scrape_next_results_page_link(response)
                if next_page is None:
                    pass
                elif isinstance(next_page, Request):
                    next_page.meta['remaining'] = remaining
                    result = next_page
                else:
                    url = urlparse.urljoin(response.url, next_page)
                    new_meta = dict((k, v) for k, v in response.meta.iteritems()
                        if k in ['remaining', 'total_matches', 'search_term',
                            'products_per_page', 'scraped_results_per_page']
                    )
                    new_meta['remaining'] = remaining
                    result = Request(url, self.parse, meta=new_meta, priority=1)
        elif link_page_attempt > self.MAX_RETRIES:
            self.log(
                "Giving up on results page after %d attempts: %s" % (
                    link_page_attempt, response.request.url),
                ERROR
            )
        else:
            self.log(
                "Will retry to get results page (attempt %d): %s" % (
                    link_page_attempt, response.request.url),
                WARNING
            )

            # Found no product links. Probably a transient error, lets retry.
            new_meta = response.meta.copy()
            new_meta['link_page_attempt'] = link_page_attempt + 1
            result = response.request.replace(
                meta=new_meta, cookies={}, dont_filter=True)

        return result

    ## Abstract methods.

    def parse_product(self, response):
        """parse_product(response:Response)

        Handles parsing of a product page.
        """
        raise NotImplementedError

    def _search_page_error(self, response):
        """_search_page_error(response:Response):bool

        Sometimes an error status code is not returned and an error page is
        displayed. This methods detects that case for the search page.
        """
        # Default implementation for sites that send proper status codes.
        return False

    def _scrape_total_matches(self, response):
        """_scrape_total_matches(response:Response):int

        Scrapes the total number of matches of the search term.
        """
        raise NotImplementedError

    def _scrape_product_links(self, response):
        """_scrape_product_links(response:Response)
                :iter<tuple<str, SiteProductItem>>

        Returns the products in the current results page and a SiteProductItem
        which may be partially initialized.
        """
        raise NotImplementedError

    def _scrape_next_results_page_link(self, response):
        """_scrape_next_results_page_link(response:Response):str

        Scrapes the URL for the next results page.
        It should return None if no next page is available.
        """
        raise NotImplementedError

    def _scrape_results_per_page(self, response):
        """_scrape_results_per_page(response:Response):integer

        Scrapes the number of products at the first page
        It should return None if the value is unavailable
        """
        return None