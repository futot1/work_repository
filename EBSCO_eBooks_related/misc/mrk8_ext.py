# coding: utf-8

# MARK8ファイル (.mrk8) よりURLをたよりにリストのANのレコードのみ抜き出す

import sys
import argparse

PURCHASED_TITLES = 'purchased_titles.txt'

def get_arguments():
  parser = argparse.ArgumentParser()
  parser.add_argument( '-l', '--list', metavar='List_File', help='specify list file' )
  parser.add_argument( '-o', '--output', metavar='Output_File', help='specify outpout file' )
  parser.add_argument( 'in_file', metavar='Input_File' )
  args = parser.parse_args();
  return( args )

def Run():
  args = get_arguments()
  if args.in_file:
    in_file = args.in_file
  if args.list:
    purchased_list_file = args.list
  else:
    purchased_list_file = PURCHASED_TITLES
  if args.output:
    out_file = args.output
  else:
    out_file = in_file.split( '.mrk8' )[0] + '_extracted.mrk8'
  purchased_list = {}
  for x in open( purchased_list_file, 'r' ).read().split( '\n' )[1:]:
    if x == '':
      continue
    purchased_list[ x ] = 1

  with open( in_file, 'r' ) as fi:
    out_recs = []
    pbuf = ''
    while( True ):
      buf = fi.read( 1000000 )
      buf = pbuf + buf
      if buf == '':
        break
      recs = buf.split( '\n\n' )
      pbuf = recs[ -1 ]
      for n in xrange( len( recs ) -1 ):
        arec = recs[ n ]
        for aline in arec.split( '\n' ):
          if aline.startswith( '=856' ):
            if purchased_list.has_key( aline.split( 'AN=' )[ 1 ] ):
              out_recs.append( arec )
              break
    out_s = '\n\n'.join( out_recs )
    f = open( out_file, 'w' )
    f.write( out_s )
    f.close()

if __name__ == '__main__':
  Run()

