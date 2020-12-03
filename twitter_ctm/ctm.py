"""
    C = R/10 + F + U

    where:
            C: Coefficient of Traffic Manipulation
            R: percentage of retweets
            F: percentage of traffic from the top fifty users
            U: average number of tweets per user

https://comprop.oii.ox.ac.uk/wp-content/uploads/sites/93/2019/01/Manipulating-Twitter-Traffic.pdf
"""
from collections import Counter
from twarc import Twarc
import json, sys, argparse

consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''

VERSION = "0.1"
BANNER = """
{0} v. {1} - CTM: Coefficient of Traffic Manipulation calculator

More info: https://comprop.oii.ox.ac.uk/wp-content/uploads/sites/93/2019/01/Manipulating-Twitter-Traffic.pdf

by sowdust
""".format(sys.argv[0],VERSION)


def parse_args():
    parser = argparse.ArgumentParser(description='Calculator for the Coefficient of Traffic Manipulation as ... by Ben Nimmo')
    parser.add_argument('-k', '--keyword', metavar='KEYWORD', type=str, help='Keyword to filter tweets')
    parser.add_argument('-l', '--limit', metavar='LIMIT', type=int, default=10000, help='Max number of tweets to download')
    parser.add_argument('-j', '--json-output', metavar='FILE', type=str, help='Store json output to FILE')
    parser.add_argument('--live', action='store_true', help='Use live streaming instead of past tweets. Will hang...')
    args = parser.parse_args(args=None if len(sys.argv) > 1 else ['--help'])

    return args


def top_traffic_count(users_list,users,top=50):
    top_traffic = 0
    top_users = []

    for u in Counter(users_list).most_common(top):
        top_traffic += u[1]
        top_users.append(users[u[0]])
    return [top_traffic,top_users]


def parse_tweets(tweets):
    n_tweets = 0
    n_retweets = 0
    n_users = 0
    users_list = []
    users = {}

    for t in tweets:
        users_list.append(t['user']['id_str'])
        if t['user']['id_str'] in users.keys():
            users[t['user']['id_str']]['n_tweets']  += 1
            users[t['user']['id_str']]['dates'].append(t['created_at'])
            users[t['user']['id_str']]['sources'].append(t['source'])
        else:
            n_users +=1
            users[t['user']['id_str']] = {}
            users[t['user']['id_str']]['n_tweets']  = 1
            users[t['user']['id_str']]['screen_name'] = t['user']['screen_name']
            users[t['user']['id_str']]['dates'] = []
            users[t['user']['id_str']]['sources'] = []
            users[t['user']['id_str']]['dates'].append(t['created_at'])
            users[t['user']['id_str']]['sources'].append(t['source'])
            users[t['user']['id_str']]['geo_enabled'] = t['user']['geo_enabled']
            users[t['user']['id_str']]['favourites_count'] = t['user']['favourites_count']
            users[t['user']['id_str']]['followers_count'] = t['user']['followers_count']
            users[t['user']['id_str']]['friends_count'] = t['user']['friends_count']
            users[t['user']['id_str']]['id_str'] = t['user']['id_str']
            users[t['user']['id_str']]['lang'] = t['user']['lang']
            users[t['user']['id_str']]['profile_image_url_https'] = t['user']['profile_image_url_https']
        n_tweets += 1
        if 'retweeted_status' in t.keys():
            n_retweets += 1
    return [n_tweets,n_retweets,n_users,users_list,users]


def get_tweets(keyword,limit,live=False):
    tweets = []
    n = 0
    msg = ''
    t = Twarc(consumer_key, consumer_secret, access_token, access_token_secret)
    if not live:
        iterator = t.search(keyword)
    else:
        iterator = t.filter(keyword)

    for tweet in iterator:
        if n >= limit: break
        n += 1
        tweets.append(tweet)
        if n % 5 == 0:
            msg = '%s[*] Downloading tweets ... %d' % ('\r'*len(msg),n)
            print(msg, end='\r')
    print()
    return tweets


def print_users(user_list):
    for u in user_list:
        sources = set(u['sources'])
        sources = [x.split('>')[1].split('<')[0] for x in sources]
        sources_text = ','.join(sources)
        print('[%d] %s\tFollowers: %d   Friends: %d   Sources: %s' % (u['n_tweets'],u['screen_name'],u['followers_count'],u['friends_count'],sources_text))


def main():

    print(BANNER)
    args = parse_args()

    # get tweets 
    tweets = get_tweets(args.keyword,args.limit,args.live)
    print('[*] Found %d tweets using keyword %s' % (len(tweets),args.keyword))

    # store tweets to json file
    if args.json_output:
        print('[*] Storing tweets to json file %s' % args.json_output)
        with open(args.json_output, 'w') as outfile:
            json.dump(tweets, outfile)

    # make sense of tweets
    [n_tweets,n_retweets,n_users,users_list,users] = parse_tweets(tweets)
    [top_traffic,top_users] = top_traffic_count(users_list,users)

    print_users(top_users)

    # compute indicators
    R = n_retweets / n_tweets * 100
    F = top_traffic / n_tweets * 100
    U = n_tweets / n_users
    C = R/10 + F + U

    # print results 
    print('C = R/10 + F + U')
    print('%.2f = %.2f/10 + %.2f + %.2f' % (C,R,F,U))


if __name__ == '__main__':
    main()