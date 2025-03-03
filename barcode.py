#!/usr/bin/python3 -u

import os, sys, io, subprocess, glob, tempfile

from PIL import Image, ImageFont, ImageDraw

PRINTER_GLOB = '/dev/usb/lp0'

def generate_aztec(txt):

  logo = Image.open('why-logo-24mm.png')
  logo = logo.convert('L').point( lambda p: 255 if p > 150 else 0 ).convert('1')

  zint = subprocess.run(['zint', '--barcode', '92', '--vers', '8', '--scale', '2', '--direct', '--data', txt], capture_output=True)
  if zint.returncode != 0:
    print(f'Zint error. Return code:{zint.returncode}\nStdErr: {zint.stderr}\nStdOut: {zint.stdout}')
    os.exit(101)

  barcode = Image.open(io.BytesIO(zint.stdout))

  im = Image.new('1', (128, 214))
  im.paste(1, (0, 0) + im.size)

  im.paste(logo, ((im.size[0]-logo.size[0])//2, 0))
  im.paste(barcode, ((im.size[0]-barcode.size[0])//2, logo.size[1] + 2))

  draw = ImageDraw.Draw(im)

  firacode = ImageFont.truetype('FiraCode-Medium.ttf', size=30)

  while draw.textlength(txt, firacode) > 124:
    firacode = ImageFont.truetype('FiraCode-Medium.ttf', size=firacode.size*0.99)

  draw.text((im.size[0]/2, logo.size[1]+barcode.size[1] + 6), txt, fill=0, font=firacode, anchor='ma')

  im = im.transpose(Image.Transpose.ROTATE_90)

  return im

def generate_code128(txt):

  logo = Image.open('why-logo-12mm.png')
  logo = logo.convert('L').point( lambda p: 255 if p > 150 else 0 ).convert('1')

  zint = subprocess.run(['zint', '--barcode', '20', '--scale', '0.5', '--height', '48', '--direct', '--notext', '--data', txt], capture_output=True)
  if zint.returncode != 0:
    print(f'Zint error. Return code:{zint.returncode}\nStdErr: {zint.stderr}\nStdOut: {zint.stdout}')
    os.exit(102)

  barcode = Image.open(io.BytesIO(zint.stdout))
  
  im = Image.new('1', (logo.size[0] + 4 + barcode.size[0], 128))
  im.paste(1, (0, 0) + im.size)

  im.paste(logo, (0, ((im.size[1]-logo.size[1])//2)))
  im.paste(barcode, (logo.size[0] + 2, 29))

  draw = ImageDraw.Draw(im)

  firacode = ImageFont.truetype('FiraCode-Medium.ttf', size=18)

  draw.text((logo.size[0] + 4 + barcode.size[0]/2, 29 + barcode.size[1] + 1), txt, fill=0, font=firacode, anchor='ma')

  return im

def get_label_size():
  with open('/dev/usb/lp0', 'r+b') as fp:
    buf = io.BytesIO()

    fp.write(b'\x00'*200+b'\x1b\x40\x1b\x69\x53')
    while len(buf.getvalue()) < 32:
      buf.write(fp.read())

    return int(buf.getvalue()[10])

if __name__ == '__main__':
  
  if len(sys.argv) < 3:
    print("Usage:")
    print(f"  {sys.argv[0]} aztec foo [bar [baz [...]]]")
    print(f"  {sys.argv[0]} code128 foo [bar [baz [...]]]")
    sys.exit(1)
  
  printers = glob.glob(PRINTER_GLOB)
  if len(printers) < 1:
    print(f'Printer not found: no matches for {PRINTER_GLOB}')
    sys.exit(2)
    
  printer = printers[0]

  if len(printers) > 1:
    print(f'{len(printers)} printers found, picking {printer}')
  
  label_size = get_label_size()
  if label_size == 0:
    print('Missing label tape')
    sys.exit(3)
  
  if sys.argv[1] == 'aztec' and label_size == 24:
    generate_label = generate_aztec
  elif sys.argv[1] == 'code128' and label_size == 12:
    generate_label = generate_code128
  else:
    print(f'Cannot print {sys.argv[1]} code on {label_size}mm tape.')
    sys.exit(4)

  imgs = []
  for txt in sys.argv[2:]:
    im = generate_label(txt)
    tmp = tempfile.NamedTemporaryFile()
    im.save(tmp, 'PPM')
    imgs.append(tmp)

  ptouch = subprocess.run(['./ptouch-770/ptouch-770-write', '0'] + [i.name for i in imgs], capture_output=True)
  if ptouch.returncode != 0:
    print(f'ptouch error. Return code:{ptouch.returncode}')
    print(f'StdErr: {ptouch.stderr.decode("ascii")}\nStdOut: {ptouch.stdout.decode("ascii")}')
    sys.exit(5)
