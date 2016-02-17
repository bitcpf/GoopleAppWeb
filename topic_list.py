from gcloud import pubsub

client = pubsub.Client(project='sandbox-1222')
#topics, next_page_token = client.list_topics()
#topic_ls = [topic.name for topic in topics]
#print type(topic_ls)
# Get all subscriptions
proj_path = '/projects/sandbox-1222/'
resp = client.connection.api_request(method = 'GET', path = proj_path+'subscriptions', query_params={})
subscriptions = resp['subscriptions']

for subscription in subscriptions:
    # topics 5 characters + 1 = 6
    print 'topic is:',subscription['topic'][len(proj_path)+6:]
    print 'Subscription is:' ,subscription['name'][len(proj_path)+13:]
