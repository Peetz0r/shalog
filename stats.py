#!/usr/bin/env -S python3 -u

import glob, json, pprint, paho.mqtt.publish, inotify_simple, configparser

config = configparser.ConfigParser()
config.read("config.ini")

def post_stats():
  files = glob.glob(config['db']['db']+'/*.json')

  numTotalThings = 0
  numUnusedThings = 0
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
        if j['id'].startswith('H#') or j['id'].startswith('R#'):
          continue
        numTotalThings +=1
        isUnused = 1
        if 'location_history' in j:
          numLoansThisThing = 0
          for h in j['location_history']:
            if 'location' in h and h['location'].startswith('angel'):
              isUnused = 0
              numLoansThisThing += 1
              if h['location'] not in activeAngels:
                activeAngels.append(h['location'])
              if j['location'] not in busyAngels:
                busyAngels.append(j['location'])
          numTotalLoans += numLoansThisThing
        numUnusedThings += isUnused
        if 'location' in j and j['location'].startswith('angel'):
          numCurrentLoans +=1
          if j['location'].startswith('angel') and j['location'] not in busyAngels:
            busyAngels.append(j['location'])

  numActiveAngels = len(activeAngels)
  numBusyAngels = len(busyAngels)

  print(f'numTotalThings   =  {numTotalThings}')
  print(f'numUnusedThings  =  {numUnusedThings}')
  print(f'numTotalLoans    =  {numTotalLoans}')
  print(f'numCurrentLoans  =  {numCurrentLoans}')
  print(f'numTotalAngels   =  {numTotalAngels}')
  print(f'numActiveAngels  =  {numActiveAngels}')
  print(f'numBusyAngels    =  {numBusyAngels}')


  msgs = [
    {'topic': config['stats']['topicPrefix'] + '/numTotalThings', 'payload': numTotalThings},
    {'topic': config['stats']['topicPrefix'] + '/numUnusedThings', 'payload': numUnusedThings},
    {'topic': config['stats']['topicPrefix'] + '/numTotalLoans', 'payload': numTotalLoans},
    {'topic': config['stats']['topicPrefix'] + '/numCurrentLoans', 'payload': numCurrentLoans},
    {'topic': config['stats']['topicPrefix'] + '/numTotalAngels', 'payload': numTotalAngels},
    {'topic': config['stats']['topicPrefix'] + '/numActiveAngels', 'payload': numActiveAngels},
    {'topic': config['stats']['topicPrefix'] + '/numBusyAngels', 'payload': numBusyAngels}
  ]

  paho.mqtt.publish.multiple(msgs, hostname=config['stats']['host'], auth={'username': config['stats']['user'], 'password': config['stats']['pass']})

  print(f"Posted to {config['stats']['host']} {config['stats']['topicPrefix']}")
  print('='*40)

post_stats()

inotify = inotify_simple.INotify()
watch_flags = inotify_simple.flags.CREATE | inotify_simple.flags.MODIFY | inotify_simple.flags.DELETE
wd = inotify.add_watch(config['db']['db'], watch_flags)

print(f"Watching {config['db']['db']} for stats")

while True:
  for event in inotify.read(read_delay=1000):
    print(event, inotify_simple.flags.from_mask(event.mask))
    post_stats()
