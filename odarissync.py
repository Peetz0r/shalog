#!/bin/python3

import requests, glob, json, configparser, re, sys, os, inotify_simple

config = configparser.ConfigParser()
config.read('config.ini')

session = requests.Session()
session.headers = {
  'Authorization': f'Bearer {config["odarissy"]["token"]}',
}

def update_trackers(filter=None):
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

    if filter and id not in filter:
      continue

    if not os.path.exists(f'{config["db"]["db"]}/{id}.json'):
      print(f'{id} found in odarissy but not in shalog, creating...')      
      with open(f'{config["db"]["db"]}/{id}.json', 'w') as f:
        json.dump({'stays': False, 'id': odarissy_device['uniqueId'], 'class':'Thing'}, f)
      continue
      
    with open(f'{config["db"]["db"]}/{id}.json') as f:
      shalog_device = json.load(f)
      
      if 'comment' not in shalog_device:
        print(f'{id} found in shalog without comment, skipping...')
        continue

      location = shalog_device['comment']

      if shalog_device['comment'] == '':
        location = id
        print(f'{id} has empty comment, resetting to "{id}"...')
      elif odarissy_device['name'] == location:
        print(f'{id} found, already set to "{location}", skipping...')
        continue
      else:
        print(f'{id} found, setting to "{location}"')

      odarissy_device['name'] = location
      r = session.put(f'{config["odarissy"]["url"]}/devices/{odarissy_device["id"]}', json=odarissy_device)


update_trackers()


inotify = inotify_simple.INotify()
watch_flags = inotify_simple.flags.CREATE | inotify_simple.flags.MODIFY | inotify_simple.flags.DELETE
wd = inotify.add_watch(config["db"]["db"], watch_flags)

print(f'Watching {config["db"]["db"]} for stats')

while True:
  for event in inotify.read(read_delay=250):
    if event.name.startswith(config['odarissy']['prefix']):
      print(event, inotify_simple.flags.from_mask(event.mask))
      update_trackers(event.name)

