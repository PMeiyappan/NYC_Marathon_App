#This code scrapes the results from the NYC marathon website

import argparse
import csv
import itertools
import requests
import socket
import time

from BeautifulSoup import BeautifulSoup
from datetime import datetime, timedelta
from hashlib import md5
from memcache import Client
import sys


class Crawler(object):
    
    SITE_ROOT = (
        'http://web2.nyrrc.org/cgi-bin/htmlos.cgi/'
        'mar-programs/archive/archive_search.html'
    )
    REQUEST_SPACING = timedelta(seconds=1)
    NEXT_PAGE_BUTTON_VALUE = 'Next 100 >'


    def __init__(self, year):
        #sets a bunch of variables
        self.year = year
        self.last_url = None
        self.post_url = None
        self.last_request = None
        
        #initialize the memcache, which isn't running currently
        self.cache = self.get_cache()


    def crawl(self):
        """
        Heavy lifting
        """
        #just get some initial setup data that we will need for later
        self.crawl_root(initial=True)
               
        #This is the *real* heavy lifting
        generator_a = self.generate_results()
        
        #This generator will filter the first one, to make sure it only outputs
        #unique results
        generator_b = self.generate_unique(generator_a)
        
        return generator_b

    def generate_unique(self, results_generator):
        uniques = set()

        for result in results_generator:
            #this makes the result - which is a dictionary of per-runner data - and makes it hashable (immutable)
            # so that it can be used in a set
            items = tuple(result.items())
            if result and items not in uniques:
                uniques.add(items)
                yield result


    def generate_results(self):
        """
        This generator will:
        
        1. go through all the states and countries
        2. for each one, it will crawl the state or country
        3. and then it will yield the results (it is a generator)
        """
        for abbrev, name in self.states:
            for result in self.crawl_state(abbrev, name):
                yield result

        
        #print self.countries
        
        
        for abbrev, name in self.countries:
            for result in self.crawl_country(abbrev, name):
                yield result


    def crawl_root(self, initial=False):
        """
        * Start a session
        * go to the homepage
        * get the post-url (the page that pressing submit will get you to)
        * if initial is true,
            * it will get the list of states and countries and store them
        """
    
        #get a session, to keep state information between calls to the web
        # such as cookies
        self.session = requests.Session()
        
        #just get the root data
        root = self.curl(self.SITE_ROOT)
        
        #read and parse the html into something navigable
        soup = BeautifulSoup(root)
        
        
        self.refresh_post_url(soup)

        if initial:
            #find all the US states in the form
            state_select = soup.find('select', {'name': 'input.state'})
            state_options = state_select.findAll('option')[1:]
            self.states = [
                (c.get('value').strip(), c.text) for c in state_options
            ]

            #find all the countries in the form
            country_select = soup.find('select', {'name': 'input.country'})
            country_options = country_select.findAll('option')[1:]
            
            
            
            self.countries = []
            for c in country_options:
                
                somestring = c.get('value')
                
                somestring = somestring.strip()
                
                parts = somestring.split(',')
                
                parts = parts[:2]
                
                parts = tuple(parts)
                
                self.countries.append(parts)
            

    def refresh_post_url(self, soup):
        """
        Checks the page for a form, and stores the url of the next page of the
        form to the self.post_url. Returns true if this form is actually
        a button that says "next 100". Meaning this function is meant
        to handle several different types of forms, but it indicates
        when it is handling the special "next 100" case.
        """
        forms = soup.findAll('form')

        if not forms:
            return False

        last_form = forms[-1]

        self.post_url = last_form.get('action')

        submit = last_form.find('input', {'type': 'submit'})
        has_next = submit.get('value') == self.NEXT_PAGE_BUTTON_VALUE
        return has_next


    def crawl_state(self, abbrev, name):
        print 'crawling', name, abbrev
        sys.stdout.flush()
        return self.crawl_type('search.state', input_state=abbrev)


    def crawl_country(self, abbrev, name):
        print 'crawling', name, abbrev
        sys.stdout.flush()
        return self.crawl_type(
            'search.country',
            input_country=','.join([abbrev, name])
        )


    def crawl_type(self, search_type, **kwargs):
        self.crawl_root()

        results = []
        page = 0

        while True:
            #do the post (or get the cache)
            response = self.post_or_cache(
                search_method=search_type,
                page=page,
                **kwargs
            )

            page_results, has_next = self.parse_crawl(response)
            results.extend(page_results)
            # this means results += page_results
            print 'page', page, len(results), 'result(s)'
            sys.stdout.flush()

            if not has_next:
                break

            page += 1

        return results


    def post_or_cache(self, **kwargs):
        """
        In english: "Do whatever self.post() does, except, that if you did it before,
        return the cached results (if memcached is even running)
        
        """
        cache_key = self.cache_key(**kwargs)

        if self.cache:
            response = self.cache.get(cache_key)

            if response is not None:
                return response

        response = self.post(**kwargs)

        if self.cache:
            self.cache.set(cache_key, response, time=0)

        return response


    def cache_key(self, **kwargs):
        return md5(str(kwargs)).hexdigest()


    def parse_crawl(self, response):
        try:
            soup = BeautifulSoup(response)

            #finds if this page has no results
            if soup.find('span', text='Your search returns no match.'):
                print 'no results'
                sys.stdout.flush()
                #this returns an empty list, for no results, and "has_next" of False
                return [], False

            #get the table
            table = soup.find('table', {'width': 750})
            
            #for each row
            rows = table.findAll('tr', {'bgcolor': '#FFFFFF'})
            
            #for each item, run parse_row on it, and get a list of results
            results = map(self.parse_row, rows)
            #this function returns has_next, if you recall, so we can check if we shall
            # continue to crawl this particular country or state
            has_next = self.refresh_post_url(soup)
            
            #return the results
            return results, has_next
        except Exception:
            print 'parse error'
            print response
            sys.stdout.flush()
            raise


    def parse_row(self, row):
        keys = (
            'first_name', 'last_name', 'sex_age', 'bib', 'team', 'state',
            'country', 'country_abbrev', 'place', 'place_gender', 'place_age',
            'gun_time', 'net_time', '5km', '10km', '15km', '20km', '13.1mi',
            '25km', '30km', '35km', '40km', 'minutes_per_mile',
            'age_graded_time', 'age_graded_pct',
        )

        values = [self.no_unicode(td.text) for td in row.findAll('td')]
        return {k: v for k, v in zip(keys, values[:-1])}


    @staticmethod
    def no_unicode(x):
        return x.encode('utf-8') if isinstance(x, unicode) else x


    def curl(self, url, method='GET', referer=None, data=None):
        """
        Blackbox function that acts like "wget" and just retrieves
        the data at the URL specified.
        """
        if self.last_request is not None:
            while datetime.now() - self.last_request < self.REQUEST_SPACING:
                time.sleep(1)

        self.last_request = datetime.now()

        headers = {
            'Origin': 'http://web2.nyrrc.org',
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) '
                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.71 '
                'Safari/537.36'
            ),
        }

        if url != self.SITE_ROOT:
            headers['Referer'] = self.last_url

        fn = getattr(self.session, method.lower())
        response = fn(url, data=data, headers=headers)

        if 200 != response.status_code:
            raise RuntimeError((
                response.status_code, response.text
            ))

        self.last_url = response.url

        return response.text


    def post(self, search_method, page, input_state=None, input_country=None):
        """
        This function is delegating to the self.curl, and it uses the post method
        to submit the form on the current page. However, depending on situation
        there can be different forms to submit.
        
        * If this is the first page, then we have to submit the big form with all the
            data, such as "search by country", or "search by state" and all sorts
            of things such as the year (which is stored in self.year) and other things
            such as to make the gender not matter (I think), and which country, and which state
            to search for (which is specified in the call)
        * If this is not the first page, there is a much simpler form: it only has a submit button
            with no values, and just says "next" or something like that.
        """
        if page > 1:
            data = {
                'submit': self.NEXT_PAGE_BUTTON_VALUE,
            }
        else:
            data = {
                'AESTIVACVNLIST': ','.join([
                    'input.searchyear', 'input.top', 'input.agegroup',
                    'team_code', 'input.state', 'input.country',
                    'input.top.wc',
                ]),
                'input.country': input_country,
                'input.searchyear': self.year,
                'input.state': input_state,
                'input.top': 10,
                'input.top.wc': 10,
                'search.method': search_method,
                'top.type': 'B',
                'top.wc.type': 'P',
                'top.wc.gender': 'B',
            }

        return self.curl(self.post_url, method='POST', data=data)


    def get_cache(self):
        try:
            socket.create_connection(('localhost', 11211))
            print 'using local memcached'
            sys.stdout.flush()

            return Client(['localhost:11211'])
        except socket.error:
            print 'no local memcached'
            sys.stdout.flush()
            return None





if '__main__' == __name__:
    parser = argparse.ArgumentParser(
        description='Crawl 2014 NYC Marathon results'
    )

    default_fn = 'crawl.csv'
    parser.add_argument('--filename', default=default_fn,
                        help='output filename (default {})'.format(default_fn))

    args = parser.parse_args()

    #results = list(Crawler(year=1970).crawl())
    
    #this constructs a Crawler object
    # basically this means it calles the __init__() function of the Crawler
    crawler = Crawler(year=1970)
    
    #all the heavy lifting
    #it returns an iterator
    v = crawler.crawl()
    
    results = list(v)
    
    

    if results:
        print 'writing', len(results), 'to', args.filename
        sys.stdout.flush()

        with open(args.filename, 'wb') as f:
            writer = csv.DictWriter(f, results[0].keys())
            writer.writeheader()
            map(writer.writerow, results)
