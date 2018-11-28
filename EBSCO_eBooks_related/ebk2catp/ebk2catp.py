# coding: utf-8

import sys
import time
import codecs
import urllib
import urllib2
from xml.etree import ElementTree

import argparse

PURCHASED_LIST = 'purchased_titles.txt'
EIT_SEARCH = 'http://eit.ebscohost.com/Services/SearchService.asmx/Search'
PROFILE = '********'
PASSWORD = '********'

DB1 = 'edsebk'
DATA_LIST = ( ( 'btl', 'bkinfo/btl' ), ( 'sertl', 'bkinfo/sertl' ), ( 'pubp', 'pubinfo/pub' ), ( 'publ', 'pubinfo/place' ), ( 'vid', 'pubinfo/vid' ) )

def auth_info():
  d = {}
  d[ 'prof' ] = PROFILE
  d[ 'pwd' ] = PASSWORD
  d[ 'authtype' ] = 'profile'
  return d

def dic2s( dic ):
  s = ''
  vals = []
  for k, v in dic.items():
    vals.append( '%s=%s' % ( k, v ) )
  return '&'.join( vals )

def get_value( db, query ):
  d = auth_info()
  d[ 'db' ] = db
  d[ 'query' ] = query
  return d

def search( db, qs ):
  url = EIT_SEARCH + '?' + dic2s( get_value( db, qs ) )
  return urllib2.urlopen( url ).read()


def write_to_file( output_file, fstype, records ):
  fout = codecs.open( output_file, 'wb', 'utf-8-sig' )
  for dat1 in records:
    fout.write( '\r\n'.join( gen_catp( fstype, dat1 ) ) + '\r\n' )
  fout.close()

def gen_catp( fstype, dat1 ):
  catp_lines = [ gen_catp_fs_start( fstype ) ]
  catp_lines.append( '_DBNAME_=BOOK' )
  if dat1.has_key( 'oclc' ):
    id1 = get_id_oclc( dat1[ 'oclc' ] )
  else:
    id1 = get_id_nl( dat1[ 'an' ] )
  catp_lines.append( 'ID=%s' % ( id1, ) )
  dt1 = '%04d%02d%02d' % time.localtime( time.time() )[:3]
  catp_lines.append( 'CRTDT=%s' % ( dt1, ) )
  catp_lines.append( 'RNWDT=%s' % ( dt1, ) )
  catp_lines.append( 'GMD=w' )
  catp_lines.append( 'SMD=r' )
  if dat1.has_key( 'pubdt' ):
    catp_lines.append( '<YEAR>' )
    catp_lines.append( 'YEAR1=%s' % ( dat1[ 'pubdt' ] ) )
    catp_lines.append( '</YEAR>' )
  catp_lines.append( 'CNTRY=us' )
  if dat1.has_key( 'lang' ):
    catp_lines.append( 'TTLL=%s' % ( dat1[ 'lang' ] ) )
    catp_lines.append( 'TXTL=%s' % ( dat1[ 'lang' ] ) )
  if dat1.has_key( 'isbn' ):
    if dat1[ 'isbn' ].has_key( 'electronic' ):
      for ib1 in dat1[ 'isbn' ][ 'electronic' ]:
        catp_lines.append( '<VOLG>' )
        catp_lines.append( 'VOL=: electronic bk' )
        catp_lines.append( 'ISBN=%s' % ( ib1, ) )
        catp_lines.append( '</VOLG>' )
    if dat1[ 'isbn' ].has_key( 'print' ):
      for ib1 in dat1[ 'isbn' ][ 'print' ]:
        catp_lines.append( '<VOLG>' )
        catp_lines.append( 'XISBN=%s' % ( ib1, ) )
        catp_lines.append( '</VOLG>' )
  if dat1.has_key( 'oclc' ):
    catp_lines.append( 'OTHN=OCLC:%s' % ( dat1[ 'oclc' ], ) )
  catp_lines.append( 'OTHN=NLID:%s' % ( dat1[ 'an' ], ) )
  if len( dat1[ 'aug' ] ) > 0:
    tr1 = ' / '.join( ( dat1[ 'btl' ], dat1[ 'aug' ][ 0 ] ) )
  else:
    tr1 = dat1[ 'btl' ]
  catp_lines.append( '<TR>' )
  catp_lines.append( 'TRD=%s' % ( tr1, ) )
  catp_lines.append( '</TR>' )
  catp_lines.append( '<PUB>' )
  if dat1.has_key( 'pubp' ):
    catp_lines.append( 'PUBP=%s' % ( dat1[ 'pubp' ], ) )
  if dat1.has_key( 'publ' ):
    catp_lines.append( 'PUBL=%s' % ( dat1[ 'publ' ], ) )
  if dat1.has_key( 'pubdt' ):
    catp_lines.append( 'PUBDT=%s' % ( dat1[ 'pubdt' ], ) )
  catp_lines.append( '</PUB>' )
  catp_lines.append( '<PHYS>' )
  catp_lines.append( 'PHYSP=1 online resource' )
  catp_lines.append( '</PHYS>' )
  if dat1.has_key( 'sertl' ):
    catp_lines.append( '<PTBL>' )
    catp_lines.append( 'PTBK=a' )
    catp_lines.append( 'PTBTR=%s' % ( dat1[ 'sertl' ], ) )
    if dat1.has_key( 'vid' ):
      try:
        v1 = 'Vol.%d' % ( int( dat1[ 'vid' ] ), )
      except ValueError:
        v1 = dat1[ 'vid' ]
      catp_lines.append( 'PTBNO=%s' % ( v1, ) )
    catp_lines.append( '</PTBL>' )
  for n in range( len( dat1[ 'aug' ] ) ):
    catp_lines.append( '<AL>' )
    if n == 0:
      catp_lines.append( 'AFLG=*' )
    catp_lines.append( 'AHDNG=%s' % ( dat1[ 'aug' ][ n ], ) )
    catp_lines.append( '</AL>' )
  if dat1.has_key( 'su' ):
    for sh1 in dat1[ 'su' ]:
      catp_lines.append( '<SH>' )
      catp_lines.append( 'SHT=FREE' )
      catp_lines.append( 'SHD=%s' % ( sh1, ) )
      catp_lines.append( 'SHK=K' )
      catp_lines.append( '</SH>' )
  url1 = 'http://search.ebscohost.com/login.aspx?direct=true&scope=site&db=nlebk&lang=ja&AN=%s' % ( dat1[ 'an' ], )
  catp_lines.append( 'IDENT=%s' % ( url1, ) )
  catp_lines.append( gen_catp_fs_end( fstype ) )
  return( catp_lines )



#def gen_catp_fs():
#  return( '--NACSIS-CATP--' )

def gen_catp_fs_start( fstype ):
  return( { 1: u'【】', 2: '--NACSIS-CATP--', 3: '<RECORD>' }[ fstype ] )

def gen_catp_fs_end( fstype ):
  return( { 1: '--NACSIS-CATP--', 2: '--NACSIS-CATP--', 3: '</RECORD>' }[ fstype ] )

def get_id_oclc( oclc_id ):
  if len( str( oclc_id ) ) > 8:
    id1 = 'o' + chr( 99 - 48 + ord( oclc_id[-9] ) ) + oclc_id[-8:]
  else:
    id1 = 'oc' + oclc_id
  return( id1 )

def get_id_nl( nl_id ):
  id1 = 'nl' + '%08d' % ( int( nl_id[-8:] ) )
  return( id1 )

def get_purchased_list( purchased_list_file ):
  purchased_list = []
  f1 = open( purchased_list_file, 'r' )
  f1.next()
  while True:
    try:
      aline = f1.next().strip()
    except StopIteration:
      break
    if aline == '':
      continue
    purchased_list.append( aline )
  f1.close()
  return( purchased_list )

def get_arguments():
  parser = argparse.ArgumentParser()
  parser.add_argument( '-l', '--list', metavar='List_File', help='specify list file' )
  parser.add_argument( '-o', '--output', metavar='Output_File', help='specify outpout file' )
  parser.add_argument( '-fs', '--fstype', type=int, choices=[1,2,3], help=u'specify field separator type\n1: 【】\n2: --NACSIS-CATP--\n3: <RECORD> (default)' )
  args = parser.parse_args();
  return( args )

def Run():
  args = get_arguments()
  if args.list:
     purchased_list_file = args.list
  else:
     purchased_list_file = PURCHASED_LIST
  if args.output:
    output_file = args.output
  else:
    output_file = 'catp_out.txt'
  if args.fstype:
    fstype = args.fstype
  else:
    fstype = 3

  purchased_list = get_purchased_list( purchased_list_file )
  dat_records = []
#  for an1 in purchased_list[:10]:
  for an1 in purchased_list:
    q1 = urllib.quote( 'AN %s' % ( an1, ) )
    xml1 = search( DB1, q1 )
#    print xml1
#    xml1 = open( 'hoge1.xml', 'r' ).read()
    dat1 = {}
    root = ElementTree.fromstring( xml1 )
    cinfo1 = root.find( './/rec/header/controlInfo' )
    for ( valname1, xpath1 ) in DATA_LIST:
      v1 = cinfo1.find( '.' + xpath1 )
      if v1 != None:
        dat1[ valname1 ] = v1.text
    aug1 = cinfo1.findall( './bkinfo/aug/au' )
    if aug1 != None:
      dat1[ 'aug' ] = map( lambda x: x.text, [ y for y in aug1 if y != None ] )
    pubdt1 = cinfo1.find( './pubinfo/dt' )
    if pubdt1 != None:
      dat1[ 'pubdt' ] = pubdt1.get( 'year', '' )
    isbns = {}
    for isbn1 in cinfo1.findall( './bkinfo/isbn' ):
      isbns.setdefault( isbn1.get( 'type' ), [] ).append( isbn1.text )
    dat1[ 'isbn' ] = isbns
    lang1 = cinfo1.find( './language' )
    if lang1 != None:
      dat1[ 'lang' ] = lang1.get( 'code', 'en' )
    su1 = cinfo1.find( './artinfo/su' )
    if su1 != None:
      dat1.setdefault( 'su', [] ).append( su1.text )
    for subj1 in cinfo1.findall( './artinfo/sug/subj' ):
      dat1.setdefault( 'su', [] ).append( subj1.text )
    for ui1 in cinfo1.findall( './artinfo/ui' ):
      if ui1.get( 'type', '' ) == 'oclc':
        dat1[ 'oclc' ] = ui1.text
    dat1[ 'an' ] = an1
    dat_records.append( dat1 )
    time.sleep( 2 )

    write_to_file( output_file, fstype, dat_records )


if __name__ == '__main__':
  Run()

# IDの振り方。oclcが8桁ならそのまま先頭に oc を付ける。oclcが9桁なら、1桁目が1->od, 2->oe, 3->of,.... 9->olを先頭に付ける

