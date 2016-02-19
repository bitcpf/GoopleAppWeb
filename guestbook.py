import os

from gcloud import pubsub

import jinja2
import webapp2
import json
import time

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent.  However, the write rate should be limited to
# ~1/second.

# [START main_page]
class MainPage(webapp2.RequestHandler):
    def get(self):
        client = pubsub.Client(project='sandbox-1222')
        topics, npt = client.list_topics()
        tp_name = [topic.name for topic in topics]
        template_values = {
            'topics':tp_name,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
        # [END main_page]

class Fetchdata(webapp2.RequestHandler):
    ble_data = {}
    def ls_topic(self, client):
        # return only one sub for each topic, if no sub, create one
        # Has problem but works

        proj_path = '/projects/sandbox-1222/'
        resp = client.connection.api_request(method = 'GET', path = proj_path+'subscriptions', query_params={})
        if len(resp) > 0:
            subscriptions = resp['subscriptions']
        else:
            subscriptions = []
        tps,np_token = client.list_topics()
        tp_name = [tp.name for tp in tps]
        # Creat topic dict
        topic_subs = {}
        for tp in tp_name:
            topic_subs[tp] = []


        if len(subscriptions) > 0:
            for subscription in subscriptions:
                tmp_topic = subscription['topic'][len(proj_path)+6:]
                tmp_sub = subscription['name'][len(proj_path)+13:]
                if len(topic_subs[tmp_topic]) == 0:
                    topic_subs[tmp_topic] = tmp_sub
        cnt = 1
        for tp in tp_name:
            self.ble_data[tp] = {}
            while len(topic_subs[tp]) == 0:
                try:
                    tmp_sub = None
                    topic = client.topic(tp)
                    tmp_sub = topic.subscription('weblisten'+str(cnt))
                    tmp_sub.create()
                    topic_subs[tp] = 'weblisten'+str(cnt)
#                   time.sleep(2)
                except:
                    #print 'except'
                    pass
                cnt = cnt + 1

        return topic_subs

    def latest_parse(self,client,item):
        # Input the topic and subscription, return the latest data of each topic
        #print "Latest Parse Called"
        topic = client.topic(item[0])
        subscription = topic.subscription(item[1])
        latesttime = 0

        agg_dict = {}

        received = subscription.pull(max_messages=1, return_immediately=True)


        while len(received) > 0 :
            messages = [recv[1] for recv in received]
            attributes = [message.attributes for message in messages]
            attrdict = reduce(lambda r, d: r.update(d) or r, attributes, {})
            #print attrdict
            uptime = int(attrdict['timestamp'])
            aggbd = attrdict.pop('aggbdaddr',None)
            attrdict.pop('taraddr',None)
            #print 'Update TIme is:', uptime
            #print 'latesttime  is:', latesttime

            if not agg_dict.has_key(aggbd):
                agg_dict[aggbd] = attrdict
                received = subscription.pull(max_messages=1, return_immediately=True)
                continue
            if latesttime == uptime:
                received = subscription.pull(max_messages=1, return_immediately=True)
                continue

            if latesttime < uptime:
                #print uptime
                if latesttime > 0 :
                    subscription.acknowledge(ack_id)
                latesttime = uptime
                # Package data as dict
                agg_dict[aggbd] = attrdict
                ack_id = [recv[0] for recv in received]
                #print "New update",latesttime
            else:
                ack_id = [recv[0] for recv in received]
                subscription.acknowledge(ack_id)
                #print 'ack elder one'
            #time.sleep(1)
            received = subscription.pull(max_messages=1, return_immediately=True)
        #print "In parse function", agg_dict
        return agg_dict



    # topic_subs is dict (tracker_bdaddr:[subs])
    def parse_subs(self,client, topic_subs):
        for item in topic_subs.items():
            # Get latest agg report under certain topic
            tmp_topic_agg_dict = self.latest_parse(client, item)
            if len(tmp_topic_agg_dict) > 0:
                for agg_device in list(tmp_topic_agg_dict):
                    #print agg_device
                    self.ble_data[item[0]][agg_device] = tmp_topic_agg_dict[agg_device]





    def get(self):
        client = pubsub.Client(project='sandbox-1222')
        #st_time = time.time()
        #print "Start time is : ",st_time


       # topic = client.topic('BLEtest')
       # subscription = topic.subscription('BLE_sub')
       # prereceived = subscription.pull(return_immediately=True)


        #topic_subscriptions = self.ls_topic(client)
        #self.parse_subs(client,topic_subscriptions)
        #print "Main Funm ble data", self.ble_data
        #print "Response time is : ", time.time()-st_time
        self.response.headers['Content-Type'] = 'application/json'
        test = {u'test1': {}, u'BLEtest': {u'12:34:21:32:32:a2': {u'distance': u'4', u'rssi': u'-65', u'timestamp': u'1118'}, u'12:34:21:32:32:23': {u'distance': u'4', u'rssi': u'-65', u'timestamp': u'1116'}}, u'repository-changes.default': {}}
        print json.dumps(test)
        self.response.write(json.dumps(test))
        #self.response.write(json.dumps(self.ble_data))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    #('/sign', Guestbook),
    ('/fetchdata', Fetchdata),
    ('/fetadv', Fetchdata.ls_topic),
    #('/fetchdata', Fetchdata),
], debug=True)
