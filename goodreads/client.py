import logging
from dateutil import parser as date_parser
import HTMLParser
import requests
from bs4 import BeautifulSoup
from model import Review, Comment, User
from rauth.service import OAuth1Service, OAuth1Session


class GoodReadsError(Exception):
    pass


class GoodReads(object):
    '''A wrapper of the GoodReads API'''
    def __init__(self, key, secret, logger=None):
        super(GoodReads, self).__init__()
        self.key = key
        self.secret = secret
        self.access_token = None
        self.access_token_secret = None
        self.logger = logger or logging.getLogger(__name__)

    def _review_content(self, review_url):
        r = requests.get(review_url)
        if r.status_code != 200:
            raise GoodReadsError(r.text)
        soup = BeautifulSoup(r.content, 'html.parser')
        review_body = soup.find('div', itemprop='reviewBody')
        if review_body:
            return '\n'.join(list(review_body.stripped_strings))
        else:
            return ''

    def review(self, id):
        endpoint = 'https://www.goodreads.com/review/show.xml'
        params = {'id': id, 'key': self.key}
        r = requests.get(endpoint, params=params)
        if r.status_code != 200:
            raise GoodReadsError(r.text)
        review = Review()
        review.raw_content = r.content
        review.parse()
        review.body = self._review_content(review.url)
        return review

    def _parse_onclick(self, onclick):
        page = onclick.split("page=")[-1].split(',')[0][:-1]
        authenticity_token = onclick.split("encodeURIComponent('")[-1].split("')})")[0]
        return page, authenticity_token

    def _find_next_page(self, review_page_html):
        soup = BeautifulSoup(review_page_html, 'html.parser')
        try:
            next_page = soup.find_all('a', {"class": "next_page"})[-1]
            onclick = next_page.get('onclick')
            h = HTMLParser.HTMLParser()
            onclick = h.unescape(onclick)
            return self._parse_onclick(onclick)
        except:
            return None, None

    def _parse_review_page_json(self, book_id, page, authenticity_token):
        review_page_url = 'https://www.goodreads.com/book/reviews/' + str(book_id)
        r = requests.get(review_page_url, params={"page": page, "authenticity_token": authenticity_token})
        review_page_js = r.content
        review_page_html = review_page_js[len('Element.update("reviews", "'):-3].decode('unicode-escape').encode('utf-8')
        soup = BeautifulSoup(review_page_html, "html.parser")
        review_ids = [link_div.get('href').split('/')[-1] for link_div in soup.find_all('link')]
        page, authenticity_token = self._find_next_page(review_page_html)
        return page, authenticity_token, review_ids

    def reviews(self, book_id):
        '''yeild reviews of a book'''
        book_url = 'https://www.goodreads.com/book/show/' + str(book_id)
        self.logger.debug('Sending request to %s', book_url)
        r = requests.get(book_url)
        if r.status_code != 200:
            raise GoodReadsError(r.text)
        soup = BeautifulSoup(r.content, "html.parser")
        reviews_div = soup.find("div", {"id": "reviews"})
        if not reviews_div:
            raise GoodReadsError('Something wrong with the page: %s' % (book_url))
        review_urls = [link_div.get('href') for link_div in reviews_div.find_all('link')]
        for review_url in review_urls:
            review_id = int(review_url.split('/')[-1])
            yield self.review(review_id)
        # find the link to the next page
        pagers_div = reviews_div.find_all('div', {"class": "uitext"})[-1]
        next_page = pagers_div.find_all('a')[-1]
        onclick = next_page.get('onclick')
        page, authenticity_token = self._parse_onclick(onclick)
        while True:
            self.logger.info('On page %s of the reviews of book %s' % (page, book_id))
            page, authenticity_token, review_ids = self._parse_review_page_json(book_id, page, authenticity_token)
            for review_id in review_ids:
                yield self.review(int(review_id))
            if not page:
                break

    def comments(self, review_id):
        '''yeild comments of a review'''
        page = 1
        while True:
            self.logger.info('On page %s of the comments of review %s' % (page, review_id))
            endpoint = 'https://www.goodreads.com/review/show.xml'
            params = {'id': review_id, 'key': self.key, 'page': page}
            r = requests.get(endpoint, params=params)
            if r.status_code != 200:
                raise GoodReadsError(r.text)
            soup = BeautifulSoup(r.content, 'xml')
            if int(soup.GoodreadsResponse.review.comments_count.text) == 0:
                yield None
                break
            end = int(soup.GoodreadsResponse.review.comments['end'])
            total = int(soup.GoodreadsResponse.review.comments['total'])
            for comment_tag in soup.GoodreadsResponse.review.comments.find_all('comment'):
                comment = Comment(int(comment_tag.id.text))
                comment.body = comment_tag.body.text
                try:
                    comment.user_id = int(comment_tag.user.id.text)
                except:
                    comment.user_id = None
                comment.review_id = int(soup.GoodreadsResponse.review.id.text)
                comment.created_at = date_parser.parse(comment_tag.created_at.text)
                yield comment
            if end >= total:
                break
            page += 1

    def _authorize(self):
        oauth_service = OAuth1Service(
            consumer_key=self.key,
            consumer_secret=self.secret,
            name='goodreads',
            request_token_url='http://www.goodreads.com/oauth/request_token',
            authorize_url='http://www.goodreads.com/oauth/authorize',
            access_token_url='http://www.goodreads.com/oauth/access_token',
            base_url='http://www.goodreads.com/'
            )
        # head_auth=True is important here; this doesn't work with oauth2 for some reason
        request_token, request_token_secret = oauth_service.get_request_token(header_auth=True)
        authorize_url = oauth_service.get_authorize_url(request_token)
        print 'Visit this URL in your browser: ' + authorize_url
        accepted = 'n'
        while accepted.lower() == 'n':
            # you need to access the authorize_link via a browser,
            # and proceed to manually authorize the consumer
            accepted = raw_input('Have you authorized me? (y/n) ')
        session = oauth_service.get_auth_session(request_token, request_token_secret)
        self.access_token = session.access_token
        self.access_token_secret = session.access_token_secret

    def followers(self, user_id):
        if not (self.access_token and self.access_token_secret):
            self._authorize()
        page = 1
        while True:
            self.logger.info('On page %s of the followers of user %s' % (page, user_id))
            session = OAuth1Session(
                consumer_key=self.key,
                consumer_secret=self.secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
            )
            endpoint = 'https://www.goodreads.com/user/%s/followers.xml' % (user_id)
            params = {'key': self.key, 'page': page}
            r = session.get(endpoint, params=params)
            if r.status_code != 200:
                raise GoodReadsError(r.text)
            soup = BeautifulSoup(r.content, 'xml')
            end = int(soup.GoodreadsResponse.followers['end'])
            total = int(soup.GoodreadsResponse.followers['total'])
            users = soup.GoodreadsResponse.followers
            for user_tag in users.find_all('user'):
                user = User(int(user_tag.id.text))
                user.name = user_tag.find('name').text
                user.link = user_tag.link.text
                user.friends_count = int(user_tag.friends_count.text)
                user.reviews_count = int(user_tag.reviews_count.text)
                try:
                    user.created_at = date_parser.parse(user_tag.created_at.text)
                except:
                    pass
                yield user
            if end >= total:
                break
            page += 1

    def following(self, user_id):
        if not (self.access_token and self.access_token_secret):
            self._authorize()
        page = 1
        while True:
            self.logger.info('On page %s of the following of user %s' % (page, user_id))
            session = OAuth1Session(
                consumer_key=self.key,
                consumer_secret=self.secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
            )
            endpoint = 'https://www.goodreads.com/user/%s/following.xml' % (user_id)
            params = {'key': self.key, 'page': page}
            r = session.get(endpoint, params=params)
            if r.status_code != 200:
                raise GoodReadsError(r.text)
            soup = BeautifulSoup(r.content, 'xml')
            end = int(soup.GoodreadsResponse.following['end'])
            total = int(soup.GoodreadsResponse.following['total'])
            users = soup.GoodreadsResponse.following
            for user_tag in users.find_all('user'):
                user = User(int(user_tag.id.text))
                user.name = user_tag.find('name').text
                user.link = user_tag.link.text
                user.friends_count = int(user_tag.friends_count.text)
                user.reviews_count = int(user_tag.reviews_count.text)
                try:
                    user.created_at = date_parser.parse(user_tag.created_at.text)
                except:
                    pass
                yield user
            if end >= total:
                break
            page += 1

    def friends(self, user_id):
        if not (self.access_token and self.access_token_secret):
            self._authorize()
        page = 1
        while True:
            self.logger.info('On page %s of the friends of user %s' % (page, user_id))
            session = OAuth1Session(
                consumer_key=self.key,
                consumer_secret=self.secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
            )
            endpoint = 'https://www.goodreads.com/friend/user/%s' % (user_id)
            params = {'format': 'xml', 'key': self.key, 'page': page}
            r = session.get(endpoint, params=params)
            if r.status_code != 200:
                raise GoodReadsError(r.text)
            soup = BeautifulSoup(r.content, 'xml')
            end = int(soup.GoodreadsResponse.friends['end'])
            total = int(soup.GoodreadsResponse.friends['total'])
            users = soup.GoodreadsResponse.friends
            for user_tag in users.find_all('user'):
                user = User(int(user_tag.id.text))
                user.name = user_tag.find('name').text
                user.link = user_tag.link.text
                user.friends_count = int(user_tag.friends_count.text)
                user.reviews_count = int(user_tag.reviews_count.text)
                try:
                    user.created_at = date_parser.parse(user_tag.created_at.text)
                except:
                    pass
                yield user
            if end >= total:
                break
            page += 1

    def user(self, user_id):
        endpoint = 'https://www.goodreads.com/user/show/%s.xml' % (user_id)
        params = {'key': self.key}
        r = requests.get(endpoint, params=params)
        if r.status_code != 200:
            raise GoodReadsError(r.text)
        soup = BeautifulSoup(r.content, 'xml')
        user_tag = soup.user
        user = User(int(user_tag.id.text))
        user.name = user_tag.find('name').text
        user.link = user_tag.link.text
        user.friends_count = int(user_tag.friends_count.text)
        user.reviews_count = int(user_tag.reviews_count.text)
        return user
