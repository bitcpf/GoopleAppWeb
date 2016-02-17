import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
from gcloud import pubsub

import jinja2
import webapp2
import json


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


DEFAULT_GUESTBOOK_NAME = 'default_guestbook'

# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('Guestbook', guestbook_name)


class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)


class Greeting(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


# [START main_page]
class MainPage(webapp2.RequestHandler):
    def get(self):
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        test = 'bitcpf'
        template_values = {
            'test':test,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
        # [END main_page]



class Fetchdata(webapp2.RequestHandler):
    def get(self):
        client = pubsub.Client(project='sandbox-1222')
        topic = client.topic('BLEtest')
        subscription = topic.subscription('BLE_sub')
        prereceived = subscription.pull(return_immediately=True)


        status = ["NA"]
        attrdict = {}
        if len(prereceived) >= 1:
            messages = [recv[1] for recv in prereceived]
            status = [message.data for message in messages]
            ack_ids = [recv[0] for recv in prereceived]
            subscription.acknowledge(ack_ids)
            #            light_flag = status_s[0]
            print type(status[0])
            print status[0]
            if status[0] == "ANUD":
                attributes = [message.attributes for message in messages]
                attrdict = reduce(lambda r, d: r.update(d) or r, attributes, {})
        print 'attrdict' , attrdict
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(attrdict))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    #('/sign', Guestbook),
    ('/fetchdata', Fetchdata),
    #('/fetchdata', Fetchdata),
], debug=True)
