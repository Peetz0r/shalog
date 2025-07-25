#!/usr/bin/env -S python3 -u

import os, sys, io, subprocess, glob, tempfile

from PIL import Image, ImageFont, ImageDraw

if __name__ == '__main__':
  
  imgs = []
  for num in range(int(sys.argv[1])):
    im = Image.open('why-generic-label-24mm.png')
    im = im.convert('L').point( lambda p: 255 if p > 150 else 0 ).convert('1')
    tmp = tempfile.NamedTemporaryFile()
    im.save(tmp, 'PPM')
    imgs.append(tmp)

  ptouch = subprocess.run(['./ptouch-770/ptouch-770-write', '0'] + [i.name for i in imgs], capture_output=True)
  if ptouch.returncode != 0:
    print(f'ptouch-770 error. Return code: \033[96m\033[1m{ptouch.returncode}\033[0m', file=sys.stderr)
    print(f'StdErr: {ptouch.stderr.decode("ascii")}\nStdOut: {ptouch.stdout.decode("ascii")}', file=sys.stderr)
    sys.exit(5)
