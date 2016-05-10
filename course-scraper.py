# Script for processing courses.json file into the database

import sys, json, re
import datetime
from datetime import datetime
from quailapp.models import Course

file = open('courses.json', 'r+').read().decode("utf-8")
courses = json.loads(file)

for i in range(len(courses)):
	# dept and number
	listings = courses[i]['listings']
	dept = ""
	number = ""
	for j in range(len(listings)):
		dept += listings[j]['dept'] + '/'
		number += listings[j]['number'] + '/'
	dept = dept[:len(dept)-1]
	number = number[:len(number)-1]
	#title + courseid
	title = courses[i]['title']
	courseid = courses[i]['courseid']
	# profs
	prof = ""
	profs = courses[i]['profs']
	for j in range(len(profs)):
		prof += profs[j]['name'] + '/'
	prof = prof[:len(prof)-1]
	# times
	classes = courses[i]['classes']
	days = ""
	if (len(classes) > 0):
		start = classes[0]['starttime']
		time = datetime.strptime(start, '%I:%M %p')
		start = time
		end = classes[0]['endtime']
		time = datetime.strptime(end, '%I:%M %p')
		end = time
		weekdays = classes[0]['days']
		tues = re.compile(r'T[^h]|T$')
		if(re.search('M', weekdays)):
			days += '0'
		if(re.search(tues, weekdays)):
			days += '1'
		if(re.search('W', weekdays)):
			days += '2'
		if(re.search('Th', weekdays)):
			days += '3'
		if(re.search('F', weekdays)):
			days += '4'
	
	c = Course(dept=dept, num=number, title=title, courseid=courseid, professor=prof, starttime=start, endtime=end, days=days)
	c.save()
