import json, sys, csv
import requests
import warnings
warnings.filterwarnings("ignore")

"""
Export firewall rules from Sophos XG450 Firewall in CSV format
june 2021
by sowdust


"""


""" START CONFIGURATION """

# output file path
FILENAME = 'firewall_rules.csv'
# host and port
HOST = '192.168.1.254:4444'
# jsessionid cookie
JSESSIONID = ''
# csrf token - Http header named "X-CSRF-Token"
CSRFTOKEN = ''
# range of rule ids to query
START_RULE = 1
END_RULE = 500

""" END CONFIGURATION  """


cookies = {}
headers = {}
cookies['JSESSIONID'] = JSESSIONID
headers['X-CSRF-Token'] = CSRFTOKEN
headers['X-Requested-With'] = 'XMLHttpRequest'
headers['Referer'] = 'https://%s/webconsole/webpages/index.jsp' % HOST
headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0'
headers['Accept'] = '*/*'
headers['Accept-Language'] = 'en-US,en;q=0.5'
headers['Accept-Encoding'] = 'gzip, deflate'

# GET LABELS 
print('[*] Getting labels')
url = 'https://%s/webconsole/Controller?mode=138&json={"main":"3","ipType":"0"}&isSecurityPolicy=true&__RequestType=ajax' % HOST
r = requests.get(url, headers=headers,cookies=cookies, verify=False)
if 'Session Expired' in r.text:
	print('[!] JSESSIONID not valid.')
	sys.exit(0)
labels = json.loads(r.text)


# GET DATA
rules = []
print('[*] Getting rules')
for i in range(START_RULE,END_RULE):
	url = 'https://%s/webconsole/Controller?mode=300&operation=105&ipType=0&objectID=%d&Entity=securitypolicy' % (HOST, i)
	r = requests.get(url, headers=headers, cookies=cookies, verify=False)
	if r.text == '{"status":502}':
		print('[!] Skipping rule %d' % i)
	else:
		p = json.loads(r.text)
		q = {}
		record = p['Record']
		q['name'] = record['name']
		q['id'] = record['ruleid']
		if record['isenable'] == '1':
			q['status'] = 'ON'
		else:
			q['status'] = 'OFF'

		if record['logginglevel'] == '1':
			q['log'] = 'ON'
		else:
			q['log'] = 'OFF'
		q['src zones'] = ''
		if record['srcZoneList'] == 'Any':
			q['src zones'] = 'Any'
		else:
			q['src zones'] = ''
			for s in record['srcZoneList']:
				q['src zones'] += labels['networkZoneList'][s]['label'] + ' + '
			q['src zones'] = q['src zones'][:-3]
		q['src hosts'] = ''
		if record['sourceidList'] == 'Any':
			q['src hosts'] = 'Any'
		else:
			q['src hosts'] = ''
			for s in record['sourceidList']:
				q['src hosts'] += labels['HostList'][s]['label'] + ' + '
			q['src hosts'] = q['src hosts'][:-3]
		if record['destZoneList'] == 'Any':
			q['dst zones'] = 'Any'
		else:
			q['dst zones'] = ''
			for s in record['destZoneList']:
				q['dst zones'] += labels['networkZoneList'][s]['label'] + ' + '
			q['dst zones'] = q['dst zones'][:-3]
		if record['destidList'] == 'Any':
			q['dst hosts'] = 'Any'
		else:
			q['dst hosts'] = ''		
			for s in record['destidList']:
				q['dst hosts'] += labels['HostList'][s]['label'] + ' + '
			q['dst hosts'] = q['dst hosts'][:-3]
		if record['serviceidList'] == 'Any':
			q['dst ports'] = 'Any'
		else:
			q['dst ports'] = ''
			for s in record['serviceidList']:
				q['dst ports'] += labels['ServiceList'][s]['label'] + ' + ' 
			q['dst ports'] = q['dst ports'][:-3]
		q['web filter'] = labels['WebFilterList'][record['webfilterid']]['label']
		if q['web filter'] == 'Language.None':
			q['web filter'] = 'None'
		if record['useridList'] == 'Any':
			q['users'] = 'Any'
		else:
			q['users'] = ''
			for s in record['useridList']:
				q['users'] += labels['UserList'][s]['label'] + ' + ' 
			q['users'] = q['users'][:-3]
		rules.append(q)
		print('[-] Got rule %s' % q['name'])

# STORE CSV 
with open(FILENAME, 'w', newline='') as csvfile:
	fieldnames = q.keys()
	writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	writer.writeheader()
	for rule in rules:
		writer.writerow(rule)

print('[*] Written %d to file %s' % (len(rules), FILENAME))
print('[*] Done. ')
