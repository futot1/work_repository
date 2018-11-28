# coding: utf-8

CUI_VERSION = '20181025'

# 20181025
# Implemented RapidMARC file support (need to pre examine unexpected line breaks)
#
# 2018.10.10
# Implemented force-264-field option
#
# 2018.09.11
# Implemented katakana/hiragana option

import os
import re
import sys
import time
import codecs
import os.path
import tempfile
import subprocess

from xml.etree import ElementTree
from StringIO import StringIO

import argparse

from jp_marc2catp import *

MARCEDIT = r'C:\Program Files\MarcEdit 6'

def get_cmarcedit():
  opath = os.getenv( 'PATH' ).split( ';' )
  cmarcedit = ''
  for p1 in opath:
    p1 = os.path.expandvars( p1 )
    if p1.startswith( '"' ) and p1.endswith( '"' ):
      p1 = p1[1:-1]
    cmd1 = os.path.join( p1, 'cmarcedit.exe' )
    if os.access( cmd1, os.X_OK ):
      cmarcedit = cmd1
      break
  if cmarcedit == '':
    v1 = os.getenv( 'MARCEDIT' )
    if v1:
      cmd1 = os.path.join( v1, 'cmarcedit.exe' )
    else:
      cmd1 = os.path.join( MARCEDIT, 'cmarcedit.exe' )
    if os.access( cmd1, os.X_OK ):
      cmarcedit = cmd1
    else:
      print 'cannot find cmarcedit.exe'
      sys.exit()
  return( cmarcedit )

def convert_xml( in_file ):
  if in_file.endswith( '.mrc' ):
    xml_file = re.sub( '\.mrc$', '.xml', in_file )
  else:
    xml_file = in_file + '.xml'
  mrc_file = check_mrc_file( in_file )
  cmarcedit = get_cmarcedit()
  cmds = [ cmarcedit, '-s', mrc_file, '-d', xml_file, '-marcxml', '-utf8' ]
  print 'Converting MARC21 to MARCXML using cmarcedit.exe ...'
  subprocess.call( cmds )
  if mrc_file != in_file:
    os.unlink( mrc_file )
  return( xml_file )

def check_mrc_file( in_file ):
  buf = open( in_file, 'rb' ).read( 100 )
  if buf.startswith( codecs.BOM_UTF8 ):
    buf = buf[ len( codecs.BOM_UTF8 ): ]
  try:
    rsz = int( buf[:5] )
  except ValueError:
    print 'Invalid MARC file'
    sys.exit()
  buf2 = open( in_file, 'rb' ).read( rsz + 20 )
  if buf2.find( '\r\n' ) > 0:
    tfn = tempfile.mktemp()
    tfn1 = tfn + '.mrk8'
    tfn2 = tfn + '.mrc'
    cmarcedit = get_cmarcedit()
    cmds1 = [ cmarcedit, '-s', in_file, '-d', tfn1, '-break', '-utf8' ]
    print 'Pre-converting process 1/2 using cmarcedit.exe ...'
    subprocess.call( cmds1 )
    cmds2 = [ cmarcedit, '-s', tfn1, '-d', tfn2, '-make', '-utf8' ]
    print 'Pre-converting process 2/2 using cmarcedit.exe ...'
    subprocess.call( cmds2 )
    os.unlink( tfn1 )
    return( tfn2 )
  return( in_file )

def show_command_name():
  print 'MARC21 to CATP converter (ver: %s, CUI: %s) by F.Tanuma' % ( VERSION, CUI_VERSION)

def get_arguments():
  parser = argparse.ArgumentParser()
  parser.add_argument( '-o', '--output', metavar='Output_File', help='specify outpout file' )
  parser.add_argument( '-fs', '--fstype', type=int, choices=[1,2,3], help=u'specify field separator type\n1: 【】\n2: --NACSIS-CATP--\n3: <RECORD> (default)' )
  parser.add_argument( '-id10', '--enable-id-10digit', action='store_true', help='enable 10 digit ID' )
  parser.add_argument( '-nr', '--disable-rom2kana', action='store_true', help='disable romaji to kana conversion' )
  parser.add_argument( '-f264', '--force-264-field', action='store_true', help='force 264 field to get PUB instead of 260' )
  grp = parser.add_mutually_exclusive_group()
  grp.add_argument( '-kk', '--katakana', action='store_true', help='kana conversion to katakana (default)' )
  grp.add_argument( '-kh', '--hiragana', action='store_true', help='kana conversion to hiragana' )
  parser.add_argument( 'in_file', metavar='Input_File' )
  args = parser.parse_args();
  return( args )

def Run():
  show_command_name()
  args = get_arguments()
  if args.in_file:
    in_file = args.in_file
  if args.output:
    out_file = args.output
  else:
    out_file = ''
  if args.fstype:
    fstype = args.fstype
  else:
    fstype = 3

  if in_file.endswith( '.xml' ):
    xml_file = in_file
  else:
    xml_file = convert_xml( in_file )
  if out_file == '':
    m = re.compile( '\.(mrc|xml)$' )
    if m.search( in_file ):
      out_file = m.sub( '.txt', in_file )
    else:
      out_file = in_file + '.txt'

  options = {}
  if hasattr( args, 'disable_rom2kana' ):
    options[ 'disable_rom2kana' ] = args.disable_rom2kana
  else:
    options[ 'disable_rom2kana' ] = False
  if hasattr( args, 'enable_id_10digit' ):
    options[ 'enable_id_10digit' ] = args.enable_id_10digit
  else:
    options[ 'enable_id_10digit' ] = False
  if hasattr( args, 'force_264_field' ):
    options[ 'force_264_field' ] = args.force_264_field
  if args.hiragana:
    options[ 'kana_conv' ] = 'hira'
  else:
    options[ 'kana_conv' ] = 'kata'

  data_list = load_xml_file( xml_file, options )

  print 'Converting MARCXML to CATP...'
  if not options[ 'disable_rom2kana' ]:
    print 'Disabling Romaji to Hiragana conversion...'
  buf = StringIO()
  sys.stdout = buf

  print_catp( fstype, data_list )

  sys.stdout = sys.__stdout__
  f = open( out_file, 'w' )
  f.write( buf.getvalue() )
  f.close()
  print 'Conversion done...'
  print 'CATP file: %s...' % ( out_file, )

if __name__ == '__main__':
  Run()

