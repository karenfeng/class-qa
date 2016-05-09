import urllib2
from bs4 import BeautifulSoup



# change the class year to parse a different class. May take awhile to run
class = '2019'
def get_netids(url):
	all_netids = []
	prevpage_netids = []
	for i in range(1,10):
		currentpage_netids = []
		url_pagenum = url + str(i)
		request = urllib2.Request(url_pagenum)
		response = urllib2.urlopen(request)		
		soup = BeautifulSoup(response, 'html.parser')

		contact_info = soup.find_all('div', {'class': 'contact-info'})
		for contact in contact_info:
			contact_fields = contact.find_all('span', {'class':'value'})
			netid = str(contact_fields[len(contact_fields)-1].get_text())
			currentpage_netids.append(netid)
		if currentpage_netids == prevpage_netids:
			return all_netids
		else:
			all_netids += currentpage_netids
			prevpage_netids = list(currentpage_netids)

	return all_netids


alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
#alphabet = ['r']
netids = []
for letter in alphabet:
	url_searchlastname = 'http://search.princeton.edu/search/index/ff/b/f//af/c/a//lf/b/l/' + letter + '/pf/c/p//tf/c/t//faf/c/fa//df/c/d/Undergraduate+Class+of+'+classYear+'/ef/c/e//submit/submit/page/'
	netids += get_netids(url_searchlastname)

for netid in netids:
	print netid
print len(netids)

