from gcloud import pubsub

client = pubsub.Client(project='sandbox-1222')
topic = client.topic('BLEtest')

if topic.exists():
    topics, next_page_token = client.list_topics()
    topic_ls = [topic.name for topic in topics]
    print type(topic_ls)
    print topic_ls[0]
    print str(topic_ls[0])

