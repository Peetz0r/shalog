#!/usr/bin/python3

import glob, json, pprint

files = glob.glob('../2017-db/*.json')
# ~ files = glob.glob('db/*.json')

numTotalItems = 0
numUnusedItems = 0
numTotalLoans = 0
numCurrentLoans = 0
numTotalAngels = 0
numActiveAngels = 0
numBusyAngels = 0

activeAngels = []
busyAngels = []

for fn in files:
  with open(fn) as f:
    j = json.load(f)
    if j['class'] == 'Person':
      numTotalAngels +=1
    elif j['class'] == 'Thing':
      numTotalItems +=1
      if 'location_history' in j:
        numTotalLoans += len(j['location_history'])
        for h in j['location_history']:
          if 'location' in h and h['location'] != 'lhq-returns':
            if h['location'].startswith('angel') and h['location'] not in activeAngels:
              activeAngels.append(j['location'])
      else:
        numUnusedItems +=1
      if 'location' in j and j['location'] != 'lhq-returns':
        numCurrentLoans +=1
        if j['location'].startswith('angel') and j['location'] not in busyAngels:
          busyAngels.append(j['location'])

numActiveAngels = len(activeAngels)
numBusyAngels = len(busyAngels)

print(f'numTotalItems    =  {numTotalItems}')
print(f'numUnusedItems   =  {numUnusedItems}')
print(f'numTotalLoans    =  {numTotalLoans}')
print(f'numCurrentLoans  =  {numCurrentLoans}')
print(f'numTotalAngels   =  {numTotalAngels}')
print(f'numActiveAngels  =  {numActiveAngels}')
print(f'numBusyAngels    =  {numBusyAngels}')
