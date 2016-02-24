import re
import os
from nose.tools import *
from goodreads import GoodReads
import responses


gr = GoodReads(
    key=os.environ['GOODREADS_KEY'],
    secret=os.environ['GOODREADS_SECRET']
    )


@responses.activate
def test_get_reviews_of_a_book():
    book_page = open('tests/resources/book_page.html').read()
    review_xml = open('tests/resources/review.xml').read()
    review_content = open('tests/resources/review_content.html').read()
    second_page = open('tests/resources/second_page.json').read()
    responses.add(responses.GET, 'https://www.goodreads.com/book/show/41865',
                  body=book_page, status=200,
                  content_type='text/html')
    responses.add(responses.GET, 'https://www.goodreads.com/review/show.xml',
                  body=review_xml, status=200,
                  content_type='text/xml')
    url_re = re.compile(r'https://www.goodreads.com/review/show/\d+')
    responses.add(responses.GET, url_re,
                  body=review_content, status=200,
                  content_type='text/html')
    responses.add(responses.GET, 'https://www.goodreads.com/book/reviews/41865?page=2&authenticity_token=TTQlGsewVuLglb4RUGmrjhNBs6ecJMk5bJSX41uwJ1tYt9gipJGP3baJTGRoC4fDHH7aDHCcIrP0d593tmYd7g%3D%3D',
                  match_querystring=True,
                  body=second_page, status=200,
                  content_type='application/json')
    responses.add(responses.GET, 'https://www.goodreads.com/book/reviews/41865',
                  body='', status=200,
                  content_type='application/json')
    reviews = list(gr.reviews(41865))
    assert(reviews is not None)
    assert(len(reviews) == 60)
    review = reviews[0]
    assert(review.id == 26448271)
    assert(review.book_id == 41865)


@responses.activate
def test_get_comments_of_a_review():
    comments_page_1 = open('tests/resources/comments_page_1.xml').read()
    comments_page_2 = open('tests/resources/comments_page_2.xml').read()
    responses.add(responses.GET, 'https://www.goodreads.com/review/show.xml?id=26448271&key=' + os.environ['GOODREADS_KEY'] + '&page=1',
                  match_querystring=True,
                  body=comments_page_1, status=200,
                  content_type='text/xml')
    responses.add(responses.GET, 'https://www.goodreads.com/review/show.xml',
                  body=comments_page_2, status=200,
                  content_type='text/xml')
    comments = list(gr.comments(26448271))
    assert(comments is not None)
    print len(comments)
    assert(len(comments) == 100)
    comment = comments[0]
    print comment.__dict__
    assert(comment.id == 1149442)
    assert(comment.review_id == 26448271)


@responses.activate
def test_get_followers_of_a_user():
    followers_page_1 = open('tests/resources/followers_page_1.xml').read()
    followers_page_2 = open('tests/resources/followers_page_2.xml').read()
    responses.add(responses.GET,
                  'ttps://www.goodreads.com/user/5834647/followers.xml?oauth_nonce=09bc087cf5a9c8a7a898d66d89deeb7035359bb5&oauth_timestamp=1452265717&oauth_consumer_key=3WTEwSejHvuT5V3nGcmjA&oauth_signature_method=HMAC-SHA1&oauth_version=1.0&oauth_token=token&key=3WTEwSejHvuT5V3nGcmjA&page=1',
                  # match_querystring=True,
                  body=followers_page_1, status=200,
                  content_type='text/xml')
    responses.add(responses.GET, 'https://www.goodreads.com/user/5834647/followers.xml',
                  body=followers_page_2, status=200,
                  content_type='text/xml')
    gr.access_token ='token'
    gr.access_token_secret ='secret'
    followers = list(gr.followers(user_id=5834647))
    assert(followers is not None)
    assert(len(followers) == 30)


@responses.activate
def test_get_following_of_a_user():
    following_page_1 = open('tests/resources/following_page_1.xml').read()
    following_page_2 = open('tests/resources/following_page_2.xml').read()
    responses.add(responses.GET,
                  'https://www.goodreads.com/user/5834647/following.xml?oauth_nonce=09bc087cf5a9c8a7a898d66d89deeb7035359bb5&oauth_timestamp=1452265717&oauth_consumer_key=3WTEwSejHvuT5V3nGcmjA&oauth_signature_method=HMAC-SHA1&oauth_version=1.0&oauth_token=token&key=3WTEwSejHvuT5V3nGcmjA&page=1',
                  # match_querystring=True,
                  body=following_page_1, status=200,
                  content_type='text/xml')
    responses.add(responses.GET, 'https://www.goodreads.com/user/5834647/following.xml',
                  body=following_page_2, status=200,
                  content_type='text/xml')
    gr.access_token ='token'
    gr.access_token_secret ='secret'
    following = list(gr.following(user_id=5834647))
    assert(following is not None)
    assert(len(following) == 24)


@responses.activate
def test_get_friends_of_a_user():
    friends_page_1 = open('tests/resources/friends_page_1.xml').read()
    friends_page_2 = open('tests/resources/friends_page_2.xml').read()
    responses.add(responses.GET,
                  'https://www.goodreads.com/friend/user/5834647?oauth_nonce=54a668034507f351b83500af4690a85c2fc44077&oauth_timestamp=1452609735&oauth_consumer_key=3WTEwSejHvuT5V3nGcmjA&format=xml&oauth_signature_method=HMAC-SHA1&oauth_version=1.0&oauth_token=token&key=3WTEwSejHvuT5V3nGcmjA&oauth_signature=VYnIppjcOahZPD%2B%2FNtbe5s8OQ8s%3D&page=1',
                  # match_querystring=True,
                  body=friends_page_1, status=200,
                  content_type='text/xml')
    responses.add(responses.GET, 'https://www.goodreads.com/friend/user/5834647',
                  body=friends_page_2, status=200,
                  content_type='text/xml')
    gr.access_token ='token'
    gr.access_token_secret ='secret'
    friends = list(gr.friends(user_id=5834647))
    assert(friends is not None)
    print len(friends)
    assert(len(friends) == 30)


@responses.activate
def test_get_a_user():
    user_xml = open('tests/resources/user.xml').read()
    responses.add(responses.GET, 'https://www.goodreads.com/user/show/5834647.xml',
                  body=user_xml, status=200,
                  content_type='text/xml')
    user = gr.user(user_id=5834647)
    assert(user is not None)
    assert(user.friends_count == 756)
    assert(user.link == 'https://www.goodreads.com/user/show/5834647-jared-vincent-lacaran')
