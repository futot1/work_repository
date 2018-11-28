# coding: utf-8

import re
import os
import sys
import glob
import os.path
import subprocess

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

def mrc2mrk8( in_files ):
  out_files = []
  for fn1 in in_files:
    if fn1.endswith( '.mrc' ):
      fn2 = re.sub( '\.mrc$', '.mrk8', fn1 )
      cmarcedit = get_cmarcedit()
      cmds = [ cmarcedit, '-s', fn1, '-d', fn2, '-break', '-marc8', '-utf8' ]
      print 'Converting MARC21 to MARC8 using cmarcedit.exe ...'
      subprocess.call( cmds )
      out_files.append( fn2 )
  return( out_files )

def mrk82mrc( in_files ):
  out_files = []
  for fn1 in in_files:
    if fn1.endswith( '.mrk8' ):
      fn2 = re.sub( '\.mrk8$', '.mrc', fn1 )
      cmarcedit = get_cmarcedit()
      cmds = [ cmarcedit, '-s', fn1, '-d', fn2, '-make', '-raw', '-utf8' ]
      print 'Converting MARC8 to MARC21 using cmarcedit.exe ...'
      subprocess.call( cmds )
      out_files.append( fn2 )
  return( out_files )

def get_mrc_files():
  return( glob.glob( '*.mrc' ) )

def conv_260( in_files ):
  out_files = []
  for fn1 in in_files:
    fn2 = re.sub( '\.mrk8$', '_mod.mrk8', fn1 )
    f1 = open( fn1, 'rb' )
    recs = []
    rec_lines = []
    while True:
      try:
        aline = f1.next()
      except StopIteration:
        if len( rec_lines ) > 0:
          recs.append( process_a_record( rec_lines ) )
          rec_lines = []
        break
      if aline.startswith( '=LDR' ):
        if len( rec_lines ) > 0:
          recs.append( process_a_record( rec_lines ) )
          rec_lines = []
      rec_lines.append( aline )
    fo = open( fn2, 'wb' )
    fo.write( ''.join( recs ) )
    fo.close()
    out_files.append( fn2 )
  return( out_files )

def process_a_record( rec_lines ):
  flag260 = False
  flag264 = False
  for aline in rec_lines:
    if aline.startswith( '=260' ):
      flag260 = True
    if aline.startswith( r'=264  \1' ):
      flag264 = True
  if flag260:
    return( ''.join( rec_lines ) )
  elif flag264:
    rec_lines2 = []
    for aline in rec_lines:
      if aline.startswith( r'=264  \1' ):
        prts = aline.split( '$', 1 )
        newline = r'=260  \\$' + prts[1]
        rec_lines2.append( newline )
      rec_lines2.append( aline )
    return( ''.join( rec_lines2 ) )
  else:
    return( ''.join( rec_lines ) )

def Run( in_files ):
  if( len( in_files ) == 0 ):
    in_files = get_mrc_files()
  mrk8_files = mrc2mrk8( in_files )
  mod_files = conv_260( mrk8_files )
  mrk82mrc( mod_files )


if __name__ == '__main__':
  if len( sys.argv ) > 1:
    in_files = sys.argv[1:]
  else:
    in_files = []
  Run( in_files )

