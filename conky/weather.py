#!/usr/bin/env python

import getopt
import sys
import urllib.request
import xml.etree.ElementTree as etree

TOD = {'0':'Night', '1':'Morning', '2':'Day', '3':'Evening'}
CLOUD = {'0':'Fair','1':'Partly Cloudy', '2':'Cloudy', '3':'Mainly Cloudy'}
PREC = {'4':'Light Rain', '5':'Rain', '6':'Show', '7':'Snow', '8':'Storm', '9':'', '10':''}
DIR = {'0': 'C', '1':'N', '2':'N-E', '3':'E', '4':'S-E', '5':'S', '6':'S-W', '7':'W', '8':'N-W'}

location_string = "${goto 15}${color2}%s, %s"
day_string = "${goto %s}${color2}%s"
phen_string = "${goto %s}${color1}%s"
pres_string = "${goto %s}${color1}%s"
temp_string = "${goto %s}${color1}%s"
wind_string = "${goto %s}${color1}%s"

def __main__(argv=None):
    if argv is None:
        argv = sys.argv

    try:
        opts, args = getopt.getopt(argv[1:], "l:")
    except getopt.error as msg:
         raise Usage(msg)

    location = ''
    for o, v in opts:
        if o == "-l":
            location = v

    if location == '':
        print('No Location code specified')
        exit(0)

#    url = 'http://informer.gismeteo.ru/xml/27553_1.xml'
    url = 'http://554838a8.services.gismeteo.ru/inform-service/87963fc3c2447108a296270d050d951c/forecast/?city=' + location + '&lang=en'
    response = urllib.request.urlopen(url)
    data = response.read()
    text = data.decode('utf-8')

    day1 = []
    day2 = []
    phen1 = []
    phen2 = []
    pres = []
    temp = []
    wind = []

    root = etree.fromstring(text)

    child = root.find('.//location')
    print(location_string % (child.attrib['name'], child.attrib['country']))
    print('')

    child = root.find('.//fact')
    ss = child.attrib['valid'].split('T')[0].split('-')
    day1.append(ss[2] + ' ' + ss[1] + ' ' + ss[0])
    day2.append('Now')

    child2 = child.find('./values')
    temp.append(child2.attrib['t'] + ' °C')
    pres.append(child2.attrib['p'] + ' mmHg')
    wind.append(child2.attrib['ws'] + ' m/s, ' + DIR[ child2.attrib['wd'] ])
    phen1.append(child2.attrib['descr'].split(', ')[0].title())
    if len(child2.attrib['descr'].split(', ')) >= 2:
        phen2.append(child2.attrib['descr'].split(', ')[1].title())
    else:
        phen2.append('')


    for child in root.findall('.//forecast'):

        ss = child.attrib['valid'].split('T')[0].split('-')
        day1.append(ss[2] + ' ' + ss[1] + ' ' + ss[0])
        day2.append(TOD[child.attrib['tod']])

        child2 = child.find('./values')

        temp.append(child2.attrib['t'] + ' °C')
        pres.append(child2.attrib['p'] + ' mmHg')
        wind.append(child2.attrib['ws'] + ' m/s, ' + DIR[ child2.attrib['wd'] ])
        phen1.append(child2.attrib['descr'].split(', ')[0].title())
        if len(child2.attrib['descr'].split(', ')) >= 2:
            phen2.append(child2.attrib['descr'].split(', ')[1].title())
        else:
            phen2.append('')

    i = 15
    for item in day1:
        print(day_string % (i, item), end='')
        i = i + 150

    print('')

    i = 15
    for item in day2:
        print(day_string % (i, item), end='')
        i = i + 150

    print('')
    print('')
    i = 15

    for item in phen1:
        print(phen_string % (i, item), end='')
        i = i + 150

    print('')
    i = 15

    for item in phen2:
        print(phen_string % (i, item), end='')
        i = i + 150

    print('')
    print('')
    i = 15

    for item in temp:
        print(temp_string % (i, item), end='')
        i = i + 150

    print('')
    i = 15

    for item in wind:
        print(wind_string % (i, item), end='')
        i = i + 150

    print('')
    i = 15

    for item in pres:
        print(pres_string % (i, item), end='')
        i = i + 150

    print('')

if __name__ == "__main__":
    sys.exit(__main__())