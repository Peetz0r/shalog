#!/usr/bin/python3 -u

import glob, json, pprint, paho.mqtt.publish, inotify_simple

with open('stats-config.json') as f:
  config = json.load(f)

def post_stats():
  files = glob.glob(config['db']+'/*.json')

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
          isUnused = 1
          for h in j['location_history']:
            if 'location' in h and h['location'] != 'lhq-returns' and not h['location'].startswith('emmer'):
              if h['location'].startswith('angel'):
                isUnused = 0
                if h['location'] not in activeAngels:
                  activeAngels.append(j['location'])
          numUnusedItems += isUnused
        if 'location' in j and j['location'] != 'lhq-returns' and not j['location'].startswith('emmer'):
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


  msgs = [
    {'topic': config['topicPrefix'] + '/numTotalItems', 'payload': numTotalItems},
    {'topic': config['topicPrefix'] + '/numUnusedItems', 'payload': numUnusedItems},
    {'topic': config['topicPrefix'] + '/numTotalLoans', 'payload': numTotalLoans},
    {'topic': config['topicPrefix'] + '/numCurrentLoans', 'payload': numCurrentLoans},
    {'topic': config['topicPrefix'] + '/numTotalAngels', 'payload': numTotalAngels},
    {'topic': config['topicPrefix'] + '/numActiveAngels', 'payload': numActiveAngels},
    {'topic': config['topicPrefix'] + '/numBusyAngels', 'payload': numBusyAngels}
  ]

  paho.mqtt.publish.multiple(msgs, hostname=config['host'], auth={'username': config['user'], 'password': config['pass']})

  print(f"Posted to {config['host']} {config['topicPrefix']}")
  print('='*40)

post_stats()

inotify = inotify_simple.INotify()
watch_flags = inotify_simple.flags.CREATE | inotify_simple.flags.MODIFY | inotify_simple.flags.DELETE
wd = inotify.add_watch(config['db'], watch_flags)

print(f"Watching {config['db']} for stats")

while True:
  for event in inotify.read(read_delay=1000):
    print(event, inotify_simple.flags.from_mask(event.mask))
    post_stats()
