#!/usr/bin/env -S python3 -u

import requests, glob, json, configparser, re, sys, os, inotify_simple

config = configparser.ConfigParser()
config.read('config.ini')

session = requests.Session()
session.headers = {
  'Authorization': f'Bearer {config["odarissy"]["token"]}',
}

def update_trackers():
  r = session.get(f'{config["odarissy"]["url"]}/devices')
  
  if r.status_code >= 400:
    print('- ERROR -')
    print(f'odarissy returned HTTP error {r.status_code}:')
    print(r.text)
    sys.exit(r.status_code-400)
  
  odarissy_devices = r.json()

  print(f'Found {len(odarissy_devices)} trackers in odarissy.')
  
  for odarissy_device in odarissy_devices:
    id = odarissy_device['uniqueId']

    if not id.startswith(config['odarissy']['prefix']):
      continue

    if not os.path.exists(f'{config["db"]["db"]}/{id}.json'):
      print(f'{id} found in odarissy but not in shalog, creating...')      
      with open(f'{config["db"]["db"]}/{id}.json', 'w') as f:
        json.dump({'stays': False, 'id': odarissy_device['uniqueId'], 'class':'Thing'}, f)
      continue
      
    with open(f'{config["db"]["db"]}/{id}.json') as f:
      shalog_thing = json.load(f)

      if 'location' not in shalog_thing:
        print(f'{id} found in shalog without location, skipping...')
        continue

      loc = shalog_thing["location"]

      if not os.path.exists(f'{config["db"]["db"]}/{loc}.json'.lower()):
        print(f'{id} found at {loc}, but that does not exist, skipping...')
        continue

      print(f'{id} found at {loc}', end=', ')

      with open(f'{config["db"]["db"]}/{loc}.json'.lower()) as f2:
        shalog_parent_thing = json.load(f2)

        if 'comment' not in shalog_parent_thing:
          print(f'{loc} found in shalog without comment, skipping...')
          continue

        label = shalog_parent_thing['comment']

        if shalog_parent_thing['comment'] == '':
          label = id
          print(f'has empty comment, resetting to "{id}"...')
        elif odarissy_device['name'] == label:
          print(f'already set to "{label}", skipping...')
          continue
        else:
          print(f'setting to "{label}"')

        odarissy_device['name'] = label
        r = session.put(f'{config["odarissy"]["url"]}/devices/{odarissy_device["id"]}', json=odarissy_device)


update_trackers()


inotify = inotify_simple.INotify()
watch_flags = inotify_simple.flags.CREATE | inotify_simple.flags.MODIFY | inotify_simple.flags.DELETE
wd = inotify.add_watch(config["db"]["db"], watch_flags)

print(f'Watching {config["db"]["db"]} for stats')

while True:
  for event in inotify.read(read_delay=250):
    print(event, inotify_simple.flags.from_mask(event.mask))
    update_trackers()
