from bs4 import BeautifulSoup
from dateutil import parser as date_parser


class Review(object):
    """docstring for Review"""
    def __init__(self, id=None):
        super(Review, self).__init__()
        self.id = id
        self.book_id = None
        self.raw_content = None

    def parse(self):
        if not self.raw_content:
            raise Exception('The content of this review is none')
        soup = BeautifulSoup(self.raw_content, 'xml')
        # parse for meta-data
        self.id = int(soup.GoodreadsResponse.review.id.text)
        self.rating = int(soup.GoodreadsResponse.review.rating.text)
        self.votes = int(soup.GoodreadsResponse.review.votes.text)
        self.user_id = int(soup.GoodreadsResponse.review.user.id.text)
        self.book_id = int(soup.GoodreadsResponse.review.book.id.text)
        self.date_added = date_parser.parse(soup.GoodreadsResponse.review.date_added.text)
        self.url = soup.GoodreadsResponse.review.url.text.strip()


class Book(object):
    """docstring for Book"""
    def __init__(self, arg):
        super(Book, self).__init__()
        self.arg = arg


class Comment(object):
    """Comment"""
    def __init__(self, id):
        super(Comment, self).__init__()
        self.id = id
        self.body = None
        self.user_id = None
        self.created_at = None
        self.review_id = None


class User(object):
    """User"""
    def __init__(self, id):
        super(User, self).__init__()
        self.id = id
        self.name = None
        self.link = None
        self.friends_count = None
        self.reviews_count = None
        self.created_at = None
