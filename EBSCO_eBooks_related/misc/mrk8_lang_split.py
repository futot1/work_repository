# coding: shift-jis

import re
import sys

def Run( in_file ):
  out_recs = {}
  with open( in_file, 'r' ) as fi:
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
          if aline.startswith( '=008' ):
            lang1 = re.split( r'\s+', aline )[1][35:38]
            out_recs.setdefault( lang1, [] ).append( arec )
            break
    out_oth = []
    for k in out_recs.keys():
      if k == 'jpn':
        out_s_jpn = '\n\n'.join( out_recs[ k ] )
      else:
        out_oth.append( '\n\n'.join( out_recs[ k ] ) )
    out_file = in_file.split( '.mrk8' )[0] + '_jpn.mrk8'
    f = open( out_file, 'w' )
    f.write( out_s_jpn )
    f.close()
    out_file = in_file.split( '.mrk8' )[0] + '_oth.mrk8'
    out_s_oth = '\n\n'.join( out_oth )
    f = open( out_file, 'w' )
    f.write( out_s_oth )
    f.close()

if __name__ == '__main__':
  in_file = sys.argv[1]
  Run( in_file )

