#!/usr/bin/env -S python3 -u

import os, sys, io, subprocess, glob, tempfile

from PIL import Image, ImageFont, ImageDraw

ASSET_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'label-assets')
FONT_FILE = ASSET_DIR + '/FiraCode-Medium.ttf'
FONT_SIZE = 20 # px

PRINTER_GLOB = '/dev/usb/lp0'

def generate_aztec(txt):

  logo = Image.open(ASSET_DIR + '/why-logo-24mm.png')
  logo = logo.convert('L').point( lambda p: 255 if p > 150 else 0 ).convert('1')

  zint = subprocess.run(['zint', '--barcode', '92', '--vers', '8', '--scale', '2', '--direct', '--data', txt], capture_output=True)
  if zint.returncode != 0:
    print(f'Zint error. Return code: \033[96m\033[1m{zint.returncode}\033[0m', file=sys.stderr)
    print(f'\nStdErr: {zint.stderr}\nStdOut: {zint.stdout}', file=sys.stderr)
    os.exit(101)

  barcode = Image.open(io.BytesIO(zint.stdout))

  im = Image.new('1', (128, 214), color=1)
  # im.paste(1, (0, 0) + im.size)

  im.paste(logo, ((im.width-logo.width)//2, 0))
  im.paste(barcode, ((im.width-barcode.width)//2, logo.height + 2))

  draw = ImageDraw.Draw(im)

  font = ImageFont.truetype(FONT_FILE, size=20)

  txtWidth = draw.textlength(txt, font)
  lines = [txt]
  if txtWidth > 124:
    if '#' in txt:
      # check if wrapping with name + #number on two lines is enough
      (name, number) = txt.split('#', 1)
      nameWidth = draw.textlength(name, font)
      if nameWidth <= 124:
        lines = [name, '#' + number]
    if len(lines) == 1:
      lines = []
      chunk = ''
      chunkWidth = 0
      for c in list(txt):
        chunkWidth = draw.textlength(chunk + c, font)
        if chunkWidth > 124:
          lines.append(chunk)
          chunk = c
        else:
          chunk += c
      if len(chunk) > 0:
        lines.append(chunk)
  
  extendLines = len(lines) - 1
  if extendLines >= 1:
    oldIm = im
    im = Image.new('1', (128, oldIm.height + FONT_SIZE * extendLines), color=1)
    im.paste(oldIm)
    draw = ImageDraw.Draw(im)

  draw.multiline_text((im.width/2, logo.height + barcode.height + 6), '\n'.join(lines), fill=0, font=font, anchor='ma', align='center')

  im = im.transpose(Image.Transpose.ROTATE_90)

  return im

def generate_tiny(txt):

  zint = subprocess.run(['zint', '--barcode', '92', '--vers', '10', '--scale', '1.5', '--direct', '--data', txt], capture_output=True)
  if zint.returncode != 0:
    print(f'Zint error. Return code: \033[96m\033[1m{zint.returncode}\033[0m', file=sys.stderr)
    print(f'\nStdErr: {zint.stderr}\nStdOut: {zint.stdout}', file=sys.stderr)
    os.exit(101)

  barcode = Image.open(io.BytesIO(zint.stdout))

  im = Image.new('1', (128, barcode.height), color=1)

  im.paste(barcode, ((im.width-barcode.width)//2, 0))

  im = im.transpose(Image.Transpose.ROTATE_90)

  return im

def generate_code128(txt):

  zint = subprocess.run(['zint', '--barcode', '20', '--scale', '1', '--height', '50', '--direct', '--notext', '--data', txt], capture_output=True)
  if zint.returncode != 0:
    print(f'Zint error. Return code: \033[96m\033[1m{zint.returncode}\033[0m', file=sys.stderr)
    print(f'\nStdErr: {zint.stderr}\nStdOut: {zint.stdout}', file=sys.stderr)
    os.exit(102)

  barcode = Image.open(io.BytesIO(zint.stdout))
  print("barcode", barcode.width, barcode.height)
  
  im = Image.new('1', (barcode.width + 26, 128), color=1)

  im.paste(barcode, (13, 28))

  draw = ImageDraw.Draw(im)
  draw.rectangle([0, 128 - 40, im.width, 128], fill=1)

  font = ImageFont.truetype(FONT_FILE, size=15.5)

  draw.text((im.width/2, 128 - 40), txt, fill=0, font=font, anchor='ma')

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
