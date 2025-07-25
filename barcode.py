#!/usr/bin/env -S python3 -u

import os, sys, io, subprocess, glob, tempfile

from PIL import Image, ImageFont, ImageDraw

PRINTER_GLOB = '/dev/usb/lp0'

def generate_aztec(txt):

  logo = Image.open('why-logo-24mm.png')
  logo = logo.convert('L').point( lambda p: 255 if p > 150 else 0 ).convert('1')

  zint = subprocess.run(['zint', '--barcode', '92', '--vers', '8', '--scale', '2', '--direct', '--data', txt], capture_output=True)
  if zint.returncode != 0:
    print(f'Zint error. Return code: \033[96m\033[1m{zint.returncode}\033[0m', file=sys.stderr)
    print(f'\nStdErr: {zint.stderr}\nStdOut: {zint.stdout}', file=sys.stderr)
    os.exit(101)

  barcode = Image.open(io.BytesIO(zint.stdout))

  im = Image.new('1', (128, 214))
  im.paste(1, (0, 0) + im.size)

  im.paste(logo, ((im.width-logo.width)//2, 0))
  im.paste(barcode, ((im.width-barcode.width)//2, logo.height + 2))

  draw = ImageDraw.Draw(im)

  firacode = ImageFont.truetype('FiraCode-Medium.ttf', size=30)

  while '\n' not in txt and draw.textlength(txt, firacode) > 124:
    firacode = ImageFont.truetype('FiraCode-Medium.ttf', size=firacode.size*0.99)

  draw.text((im.width/2, logo.height+barcode.height + 6), txt, fill=0, font=firacode, anchor='ma')

  im = im.transpose(Image.Transpose.ROTATE_90)

  return im

def generate_tiny(txt):

  zint = subprocess.run(['zint', '--barcode', '92', '--vers', '10', '--scale', '1.5', '--direct', '--data', txt], capture_output=True)
  if zint.returncode != 0:
    print(f'Zint error. Return code: \033[96m\033[1m{zint.returncode}\033[0m', file=sys.stderr)
    print(f'\nStdErr: {zint.stderr}\nStdOut: {zint.stdout}', file=sys.stderr)
    os.exit(101)

  barcode = Image.open(io.BytesIO(zint.stdout))

  im = Image.new('1', (128, barcode.height))
  im.paste(1, (0, 0) + im.size)

  im.paste(barcode, ((im.width-barcode.width)//2, 0))

  im = im.transpose(Image.Transpose.ROTATE_90)

  return im

def generate_code128(txt):

  logo = Image.open('why-logo-12mm.png')
  logo = logo.convert('L').point( lambda p: 255 if p > 150 else 0 ).convert('1')

  zint = subprocess.run(['zint', '--barcode', '20', '--scale', '0.5', '--height', '48', '--direct', '--notext', '--data', txt], capture_output=True)
  if zint.returncode != 0:
    print(f'Zint error. Return code: \033[96m\033[1m{zint.returncode}\033[0m', file=sys.stderr)
    print(f'\nStdErr: {zint.stderr}\nStdOut: {zint.stdout}', file=sys.stderr)
    os.exit(102)

  barcode = Image.open(io.BytesIO(zint.stdout))
  
  im = Image.new('1', (logo.width + 4 + barcode.width, 128))
  im.paste(1, (0, 0) + im.size)

  im.paste(logo, (0, ((im.height-logo.height)//2)))
  im.paste(barcode, (logo.width + 2, 29))

  draw = ImageDraw.Draw(im)

  firacode = ImageFont.truetype('FiraCode-Medium.ttf', size=18)

  draw.text((logo.width + 4 + barcode.width/2, 29 + barcode.height + 1), txt, fill=0, font=firacode, anchor='ma')

  return im

def get_label_size(printer):
  with open(printer, 'r+b') as fp:
    buf = io.BytesIO()

    fp.write(b'\x00'*200+b'\x1b\x40\x1b\x69\x53')
    while len(buf.getvalue()) < 32:
      buf.write(fp.read())

    return int(buf.getvalue()[10])

if __name__ == '__main__':
  
  debug = False
  if '-d' in sys.argv:
    debug = True
    sys.argv.remove('-d')

  if len(sys.argv) < 3 or sys.argv[1] not in ['aztec', 'tiny', 'code128']:
    print(f'Usage: {sys.argv[0]} [-d] {{aztec|tiny|code128}} <text> ...')
    print(f'  -d        display (instead of print) the barcode')
    print(f'  aztec     square 2d barcode')
    print(f'  tiny      very small 2d barcode (without text)')
    print(f'  code128   long 1d barcode')
    print(f'  <text>    text to be encoded in the barcode')
    sys.exit(1)

  printers = glob.glob(PRINTER_GLOB)
  if len(printers) < 1:
    print(f'Printer not found: no matches for \033[96m\033[1m{PRINTER_GLOB}\033[0m', file=sys.stderr)
    print('Continuing for debug') if debug else sys.exit(2)
  else:
    printer = printers[0]

    if len(printers) > 1:
      print(f'{len(printers)} printers found, picking \033[96m\033[1m{printer}\033[0m')
    
    label_size = get_label_size(printer)
    if label_size == 0:
      print('Missing label tape', file=sys.stderr)
      print('Continuing for debug') if debug else sys.exit(3)

  if sys.argv[1] == 'aztec' and (debug or label_size >= 18):
    generate_label = generate_aztec
  elif sys.argv[1] == 'tiny' and (debug or label_size == 12):
    generate_label = generate_tiny
  elif sys.argv[1] == 'code128' and (debug or label_size == 12):
    generate_label = generate_code128
  else:
    print(f'Cannot print {sys.argv[1]} code on \033[96m\033[1m{label_size}mm\033[0m tape.', file=sys.stderr)
    sys.exit(4)

  imgs = []
  for txt in sys.argv[2:]:
    im = generate_label(txt)
    tmp = tempfile.NamedTemporaryFile()
    im.save(tmp, 'PPM')
    imgs.append(tmp)
    if debug:
      im.show()

  if not debug:
    ptouch = subprocess.run(['./ptouch-770/ptouch-770-write', '0'] + [i.name for i in imgs], capture_output=True)
    if ptouch.returncode != 0:
      print(f'ptouch-770 error. Return code: \033[96m\033[1m{ptouch.returncode}\033[0m', file=sys.stderr)
      print(f'StdErr: {ptouch.stderr.decode("ascii")}\nStdOut: {ptouch.stdout.decode("ascii")}', file=sys.stderr)
      sys.exit(5)
