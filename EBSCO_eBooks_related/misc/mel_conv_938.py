# coding: cp932

import re
import sys
import codecs

from string import strip

REC_NUM = 5000

#F1 = 'CAT-P_20121211.txt'

def s2u( s ):
  return( unicode( s, 'cp932' ) )

def u2utf8( s ):
  s = s.replace( '?', unicode( '？', 'cp932' ) )
  return( s.encode( 'utf-8' ) )

def quote_amp( s ):
  s = s.replace( '&', '&amp;' )
  return( s )

def quote_all( s ):
  s = s.replace( '&', '&amp;' )
  s = s.replace( '<', '&lt;' )
  s = s.replace( '>', '&gt;' )
  return( s )

def sht_get( sht ):
  dic = { 'LCSH': '0', 'JVSH': '1', 'MESH': '2', 'NALSH': '3', 'CSHE': '5', 'CSHF': '5', 'BSH': '7', 'NDLSH': '7' }
  if( sht in dic.keys() ):
    return( dic[ sht ] )
  return( '4' )

def sht_get2( sht ):
  dic = { 'BSH': 'jlabsh', 'NDLSH': 'ndlsh' }
  return( dic.get( sht, '' ) )


class DataSet:
  def __init__( self ):
    self.dataset = {}
    self.dataset[ 'leader' ] = [ c for c in '00000nam a2200000zi 4500' ]
    self.dataset[ '008' ] = [' ']*40
    self.tbl007 = { 'a': 8, 'c': 14, 'd': 6, 'f': 10, 'g': 9, 'h': 13, 'k': 6, 'm': 23, 'o': 2, 'q': 2, 'r': 11, 's': 14, 't': 2, 'v': 9, 'z': 2 }

  def init_007( self, gmd ):
    self.dataset[ '007' ] = [ ' ' ] * self.tbl007[ gmd ]

  def apply_gmd_smd( self, gmd, smd ):
    if( ( gmd in 'ghkmv' ) or ( gmd == 'a' and smd in 'gjkqrsyz' ) or ( gmd == 's' and smd in 'degiqstwz' ) ):
      pass
    elif( gmd == 'a' and smd in 'abc' ):
      gmd = 'd'
    elif( gmd == 'w' ):
      gmd = 'c'
    elif( gmd == 's' and smd in 'bc' ):
      smd = 'd'
    elif( gmd == '' and smd == 't' ):
      gmd = 't'
      smd = 'f'
    elif( gmd == '' and smd == 'i' ):
      gmd = 't'
      smd = 'd'
      self.dataset[ '008' ][ 23 ] = smd
    elif( gmd == 'b' ):
      gmd = 'f'
      self.dataset[ '008' ][ 23 ] = gmd
    elif( gmd == 'c' and not smd == 'h' ):
      self.dataset[ 'leader' ][ 6 ] = gmd
      self.dataset[ '008' ][ 20 ] = smd
    elif( gmd == 'c' and smd == 'h' ):
      smd = 'z'
      self.dataset[ 'leader' ][ 6 ] = gmd
      self.dataset[ '008' ][ 20 ] = smd
    elif( gmd == 'x' ):
      gmd = 'r'
      self.dataset[ 'leader' ][ 6 ] = gmd
    elif( gmd == 'y' ):
      gmd = 'o'
      self.dataset[ 'leader' ][ 6 ] = gmd

    self.init_007( gmd )
    self.dataset[ '007' ][ 0 ] = gmd
    self.dataset[ '007' ][ 1 ] = smd

  def simple_out( self, tag ):
    s = ''
    if self.dataset.has_key( tag ):
      if tag == 'leader':
        xmltag = tag
      elif tag.startswith( '00' ):
        xmltag = 'controlfield tag="%s"' % tag
      else:
        pass
      if type( self.dataset[ tag ] ) == type( u'' ):
        val = self.dataset[ tag ]
      elif type( self.dataset[ tag ] ) == type( [] ):
        val = ''.join( self.dataset[ tag ] )
      else:
        pass
      s = '<%s>%s</%s>\n' % ( xmltag, val, xmltag.split( ' ' )[0] )
    return( s )

  def sub_a_out( self, tag, ind1=' ', ind2=' ' ):
    s = ''
    if self.dataset.has_key( tag ):
      s = '<datafield tag="%s" ind1="%s" ind2="%s">\n' % ( tag, ind1, ind2 )
      s += '<subfield code="a">%s</subfield>\n' % self.dataset[ tag ]
      s += '</datafield>\n'
    return( s )

  def sub_a_out2( self, tag, ind1=' ', ind2=' ' ):
    s = ''
    if self.dataset.has_key( tag ):
      for x in self.dataset[ tag ]:
        s += '<datafield tag="%s" ind1="%s" ind2="%s">\n' % ( tag, ind1, ind2 )
        s += '<subfield code="a">%s</subfield>\n' % x
        s += '</datafield>\n'
    return( s )

  def sub_multi_out( self, tag, ind1=' ', ind2=' ' ):
    s = ''
    if self.dataset.has_key( tag ):
      s = '<datafield tag="%s" ind1="%s" ind2="%s">\n' % ( tag, ind1, ind2 )
      for sf in self.dataset[ tag ].keys():
        s += '<subfield code="%s">%s</subfield>\n' % ( sf, self.dataset[ tag ][ sf ] )
      s += '</datafield>\n'
    return( s )

  def sub_multi_out2( self, tag, ind1=' ', ind2=' ' ):
    s = ''
    if self.dataset.has_key( tag ):
      for x in self.dataset[ tag ]:
        s += '<datafield tag="%s" ind1="%s" ind2="%s">\n' % ( tag, ind1, ind2 )
        for sf in x.keys():
          s += '<subfield code="%s">%s</subfield>\n' % ( sf, x[ sf ] )
        s += '</datafield>\n'
    return( s )

def print_xml_header():
  print '''<?xml version="1.0" encoding="UTF-8" ?>
<collection xmlns:marc="http://www.loc.gov/MARC21/slim" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemalocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd" >
'''

def print_xml_hooter():
  print '</collection>'

def print_leader( leader ):
  s = '<leader>%s</leader>' % ''.join( leader )
  print s

def print_cfield( tag, tagdata ):
  if tag == '001':
    s = '<controlfield tag="001">%s</controlfield>' % ( tagdata, )
  elif tag == '005':
    s = '<controlfield tag="005">%s000000.0</controlfield>' % ( tagdata, )
  if tag in ( '007', '008' ):
    s = '<controlfield tag="%s">%s</controlfield>' % ( tag, ''.join( tagdata ) )
  print s

def print_dfield( tag, tagdata ):
  lines = []
  if tag == '020':
    ( vols, isbns, price, xisbns ) = tagdata
##    if len( isbns ) > 1:
    lines.append( '<datafield tag="020" ind1=" " ind2=" ">' )
#    if len(vols) == 0:
#      vols = ['']
#    a = ' '.join( ( isbns[0], vols[0] ) )
    if len( vols ) == 0:
      a = isbns[ 0 ]
#    elif vols[ 0 ] == ': electronic bk':
#      a = isbns[ 0 ]
    else:
      a = isbns[ 0 ] + ' (' + vols[ 0 ] + ')'
    lines.append( '<subfield code="a">%s</subfield>' % u2utf8( quote_all( a ) ) )
    if price != '':
      lines.append( '<subfield code="c">%s</subfield>' % u2utf8( price ) )
    if len( xisbns ) > 0:
      z = xisbns[0]
      lines.append( '<subfield code="z">%s</subfield>' % u2utf8( z ) )
    lines.append( '</datafield>' )
    if len( isbns ) > 1:
      for a in isbns[1:]:
        lines.append( '<datafield tag="020" ind1=" " ind2=" ">' )
        lines.append( '<subfield code="a">%s</subfield>' % u2utf8( a ) )
        lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '022':
    issns = tagdata
    xissns = []
    lines.append( '<datafield tag="022" ind1=" " ind2=" ">' )
    if len( issns ) == 1:
      lines.append( '<subfield code="a">%s</subfield>' % issns[0] )
    for xissn in xissns:
      lines.append( '<subfield code="z">%s</subfield>' % xissn )
    lines.append( '</datafield>' )
    if len( issns ) > 1:
      for issn in issns[1:]:
        lines = [ '<datafield tag="022" ind1=" " ind2=" ">' ]
        lines.append( '<subfield code="a">%s</subfield>' % issn )
        lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '084':
    for cls in tagdata:
      lines.append( '<datafield tag="084" ind1=" " ind2=" ">' )
      for sf in cls.keys():
        lines.append( '<subfield code="%s">%s</subfield>' % ( sf, u2utf8( cls[sf] ) ) )
      lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '100':
#    for adata in tagdata:
#      a = adata['a']
#      d = adata['d']
#      lines.append( '<datafield tag="100" ind1="1" ind2=" ">' )
#      lines.append( '<subfield code="a">%s</subfield>' % ( u2utf8( a ) ) )
#      if d != '':
#        lines.append( '<subfield code="d">%s</subfield>' % ( u2utf8( d ) ) )
#      lines.append( '</datafield>' )
    a = tagdata['a']
    d = tagdata['d']
    lines.append( '<datafield tag="100" ind1="1" ind2=" ">' )
    lines.append( '<subfield code="a">%s</subfield>' % ( u2utf8( a ) ) )
    if d != '':
      lines.append( '<subfield code="d">%s</subfield>' % ( u2utf8( d ) ) )
    lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '245':
    lines.append( '<datafield tag="245" ind1="1" ind2="0">' )
    sf_list = tagdata.keys()
    sf_list.sort()
    for sf in sf_list:
      val = tagdata[ sf ]
      if val != '':
        lines.append( '<subfield code="%s">%s</subfield>' % ( sf, u2utf8( val ) ) )
    lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '246':
    for adata in tagdata:
      lines.append( '<datafield tag="246" ind1="3" ind2="1">' )
      lines.append( '<subfield code="a">%s</subfield>' % u2utf8( adata ) )
      lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '250':
    for adata in tagdata:
      lines.append( '<datafield tag="250" ind1=" " ind2=" ">' )
      sf_list = adata.keys()
      sf_list.sort()
      for sf in sf_list:
        val = adata[ sf ]
        if val != '':
          lines.append( '<subfield code="%s">%s</subfield>' % ( sf, u2utf8( val ) ) )
      lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '260':
    for adata in tagdata:
      lines.append( '<datafield tag="260" ind1=" " ind2=" ">' )
      sf_list = adata.keys()
      sf_list.sort()
      for sf in sf_list:
        val = adata[ sf ]
        if val != '':
          lines.append( '<subfield code="%s">%s</subfield>' % ( sf, u2utf8( val ) ) )
      lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '300':
    for adata in tagdata:
      lines.append( '<datafield tag="300" ind1=" " ind2=" ">' )
      sf_list = adata.keys()
      sf_list.sort()
      for sf in sf_list:
        val = adata[ sf ]
        if val != '':
          lines.append( '<subfield code="%s">%s</subfield>' % ( sf, u2utf8( val ) ) )
      lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '440':
    for adata in tagdata:
      lines.append( '<datafield tag="440" ind1=" " ind2="0">' )
      lines.append( '<subfield code="a">%s</subfield>' % ( u2utf8( adata[ 'a' ] ) ) )
      lines.append( '<subfield code="n">%s</subfield>' % ( u2utf8( adata[ 'n' ] ) ) )
      lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag.startswith( '6' ):
    for adata in tagdata:
      ind1 = adata[ 'ind1' ]
      ind2 = adata[ 'ind2' ]
      lines.append( '<datafield tag="%s" ind1="%s" ind2="%s">' % ( tag, ind1, ind2 ) )
      lines.append( '<subfield code="a">%s</subfield>' % ( u2utf8( quote_all( adata[ 'a' ] ) ) ) )
      if adata[ '2' ] != '':
        lines.append( '<subfield code="2">%s</subfield>' % ( adata[ '2' ], ) )
      lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '500':
    for adata in tagdata:
      lines.append( '<datafield tag="500" ind1=" " ind2=" ">' )
      lines.append( '<subfield code="a">%s</subfield>' % ( u2utf8( quote_all( adata ) ) ) )
      lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '505':
    for adata in tagdata:
      a = adata['a']
      lines.append( '<datafield tag="505" ind1="0" ind2=" ">' )
      lines.append( '<subfield code="a">%s</subfield>' % ( u2utf8( quote_all( a ) ) ) )
      lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '700':
    for adata in tagdata:
      a = adata['a']
      d = adata['d']
      lines.append( '<datafield tag="700" ind1="1" ind2=" ">' )
      lines.append( '<subfield code="a">%s</subfield>' % ( u2utf8( a ) ) )
      if d != '':
        lines.append( '<subfield code="d">%s</subfield>' % ( u2utf8( d ) ) )
      lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '856':
    for adata in tagdata:
      lines.append( '<datafield tag="856" ind1="4" ind2="0">' )
      sf_list = adata.keys()
      sf_list.sort()
      for sf in sf_list:
        val = adata[ sf ]
        if val != '':
          if sf == 'u':
            lines.append( '<subfield code="%s">%s</subfield>' % ( sf, val.encode( 'utf-8') ) )
          else:
            lines.append( '<subfield code="%s">%s</subfield>' % ( sf, u2utf8( val ) ) )
      lines.append( '</datafield>' )
    print '\n'.join( lines )
  elif tag == '938':
    lines.append( '<datafield tag="938" ind1=" " ind2=" ">' )
    sf_list = tagdata.keys()
    for sf in sf_list:
      val = tagdata[ sf ]
      lines.append( '<subfield code="%s">%s</subfield>' % ( sf, val.encode( 'utf-8') ) )
    lines.append( '</datafield>' )
    print '\n'.join( lines )
  else:
    print tag

def print_record( ds ):
  print '<record>'
  print_leader( ds[ 'leader' ] )
  tag_list = ds.keys()
  tag_list.sort()
  for tag in tag_list:
    if tag == 'leader':
      pass
    elif tag in ( '001', '005', '007', '008' ):
      print_cfield( tag, ds[ tag ] )
    else:
      print_dfield( tag, ds[ tag ] )
  print '</record>'


def xml_out( datasets ):
  print_xml_header()
  for ds in datasets:
    print_record( ds )
  print_xml_hooter()

def process_a_record( lines ):
  ds1 = DataSet()
  gmd = ''
  smd = ''
  for y in lines:
    if y == '':
      continue

    if y.startswith( '_DBNAME_' ):
      continue

    if y.startswith( 'ID=' ):
      id1 = y.split( 'ID=' )[-1]
      ds1.dataset[ '001' ] = id1

    if y.startswith( 'CRTDT=' ):
      crtdt = y.split( 'CRTDT=' )[-1]

    if y.startswith( 'RNWDT=' ):
      rnwdt = y.split( 'RNWDT=' )[-1]
      if rnwdt != '':
        ds1.dataset[ '005' ] = rnwdt
      else:
        ds1.dataset[ '005' ] = crtdt

    if y == '<VOLG>':
      vols = []
      isbns = []
      price = ''
      xisbns = []
      issns = []
      xissns = []
      while( y != '</VOLG>' ):
        y = lines.next()
        if y.startswith( 'VOL=' ):
          vol1 = y.split( 'VOL=' )[-1]
          vols.append( vol1 )
        if y.startswith( 'ISBN=' ):
          isbn1 = y.split( 'ISBN=' )[-1]
          isbns.append( isbn1 )
        if y.startswith( 'PRICE=' ):
          price = y.split( 'PRICE=' )[-1]
        if y.startswith( 'XISBN=' ):
          xisbn1 = y.split( 'XISBN=' )[-1]
#          xisbns.append( xisbn1 )
          isbns.append( xisbn1 )
        if y.startswith( 'ISSN=' ):
          issn1 = y.split( 'ISSN=' )[-1]
          issns.append( issn1 )
        if y.startswith( 'XISSN=' ):
          xissn1 = y.split( 'XISSN=' )[-1]
          xissns.append( xissn1 )
      if isbns != [] or xisbns != []:
        ds1.dataset[ '020' ] = ( vols, isbns, price, xisbns )
      if issns != [] or xissns != []:
        ds1.dataset[ '022' ] = ( issns, xissns )

    if y.startswith( 'ISSN=' ):
      issn1 = y.split( 'ISSN=' )[-1]
      ds1.dataset.setdefault( '022', [] ).append( issn1 )

    if y.startswith( 'GMD=' ):
      gmd = y.split( 'GMD=' )[-1]
    if y.startswith( 'SMD=' ):
      smd = y.split( 'SMD=' )[-1]

    if y.startswith( '<YEAR>' ):
      year1 = ''
      year2 = ''
      while( y != '</YEAR>' ):
        y = lines.next()
        if y.startswith( 'YEAR1=' ):
          year1 = y.split( 'YEAR1=' )[-1]
        if y.startswith( 'YEAR2=' ):
          year2 = y.split( 'YEAR2=' )[-1]
      if year1 == '':
        ds1.dataset[ '008' ][ 6 ] = 'n'
      else:
        ds1.dataset[ '008' ][ 7:11 ] = year1[:4]
        if year2 == '':
          ds1.dataset[ '008' ][ 6 ] = 's'
        else:
          ds1.dataset[ '008' ][ 11:15 ] = year2[:4]
          ds1.dataset[ '008' ][ 6 ] = 'm'

    if y.startswith( 'OTHN=' ):
      othn = y.split( 'OTHN=' )[-1]
      if othn.startswith( 'NLID:' ):
        nlid = othn.split( 'NLID:' )[-1]
        ds1.dataset[ '938' ] = { 'a': 'EBSCOhost', 'b': 'EBSC', 'n': nlid }

    if y.startswith( 'CNTRY=' ):
      cntry = y.split( 'CNTRY=' )[-1]

    if y.startswith( 'TTLL=' ):
      ttll = y.split( 'TTLL=' )[-1]

    if y.startswith( 'TXTL=' ):
      txtl = y.split( 'TXTL=' )[-1]
      ds1.dataset[ '008' ][ 35:38 ] = txtl[:4]

    if y.startswith( '<TR>' ):
      while( y != '</TR>' ):
#        y = quote_amp( lines.next() )
        y = lines.next()
        if y.startswith( 'TRD=' ):
          trd = y.split( 'TRD=' )[-1]
          if trd.find( ' = ' ) == -1 and trd.find( ' . ' ) == -1:
            if trd.find( ' / ' ) == -1:
              p3 = ''
              pp = trd
            else:
              try:
#                ( pp, p3 ) = map( strip, trd.split( ' / ' ) )
# 2016.08.31 changed to below ( Title itself included " / " ID:3000029391 )
                ( pp, p3 ) = map( strip, trd.rsplit( ' / ', 1 ) )
              except:
                print id1
                print trd
                raise
            if pp.find( ':' ) == -1:
              p2 = ''
              p1 = pp
            else:
              aaa = map( strip, pp.split( ':' ) )
              if( len( aaa ) > 2 ):
                if re.match( '[0-9\-]*', aaa[1] ):
                  p1 = ' : '.join( aaa[:2] )
                  p2 = aaa[2]
                else:
                  print '####hoge'
              else:
                ( p1, p2 ) = aaa[:]
#                ( p1, p2 ) = map( strip, pp.split( ':' ) )
          else:
#            parts = map( strip, re.split( '( = )|( \. )', trd ) )
            parts = map( strip, re.split( ' = | \. ', trd ) )
#            parts = map( strip, pp.split( ' = ' ) )
            p1s = []
            p3s = []
            for prt1 in parts:
              if prt1.find( ' / ' ) == -1:
                p3 = ''
                p1s.append( prt1 )
              else:
                ( pp, p3 ) = map( strip, prt1.split( ' / ' ) )
                p1s.append( pp )
                p3s.append( p3 )
            p1 = ' . '.join( p1s )
            p2 = ''
            p3 = ' ; '.join( p3s )
        if y.startswith( 'TRR=' ):
          trr = y.split( 'TRR=' )[-1]
          ds1.dataset.setdefault( '246', [] ).append( quote_all( trr ) )
      ds1.dataset[ '245' ] = { 'a': quote_all( p1 ), 'b': quote_all( p2 ), 'c': quote_all( p3 ) }

    if y.startswith( 'ED=' ):
      ed = y.split( 'ED=' )[-1]
      ds1.dataset.setdefault( '250', [] ).append( { 'a': quote_all( ed ) } )

    if y.startswith( '<PUB>' ):
      pubp = ''
      publ = ''
      pubdt = ''
      while( y != '</PUB>' ):
        y = quote_amp( lines.next() )
        if y.startswith( 'PUBP=' ):
          pubp = y.split( 'PUBP=' )[-1]
        if y.startswith( 'PUBL=' ):
          publ = y.split( 'PUBL=' )[-1]
        if y.startswith( 'PUBDT=' ):
          pubdt = y.split( 'PUBDT=' )[-1]
      ds1.dataset.setdefault( '260', [] ).append( { 'a': pubp, 'b': publ, 'c': pubdt } )

    if y.startswith( '<PHYS>' ):
      physp = ''
      physi = ''
      physs = ''
      physa = ''
      while( y != '</PHYS>' ):
        y = quote_amp( lines.next() )
        if y.startswith( 'PHYSP=' ):
          physp = y.split( 'PHYSP=' )[-1]
        if y.startswith( 'PHYSI=' ):
          physi = y.split( 'PHYSI=' )[-1]
        if y.startswith( 'PHYSS=' ):
          physs = y.split( 'PHYSS=' )[-1]
        if y.startswith( 'PHYSA=' ):
          physa = y.split( 'PHYSA=' )[-1]
      ds1.dataset.setdefault( '300', [] ).append( { 'a': physp, 'b': physi, 'c': physs, 'e': physa } )

    if y.startswith( 'NOTE=' ):
      note = y.split( 'NOTE=' )[-1]
      ds1.dataset.setdefault( '500', [] ).append( note )

#    if y.startswith( '<PTBL>' ):
#      while( y != '</PTBL>' ):
#        y = quote_amp( lines.next() )
#        if y.startswith( 'PTBTR=' ):
#          ptbtr = y.split( 'PTBTR=' )[-1]
#          ds1.dataset.setdefault( '440', [] ).append( ptbtr )
#        if y.startswith( 'PTBTRR=' ):
#          ptbtrr = y.split( 'PTBTRR=' )[-1]
#          ds1.dataset.setdefault( '440', [] ).append( ptbtrr )

    if y.startswith( '<PTBL>' ):
      ptbtr = ''
      ptbno = ''
      while( y != '</PTBL>' ):
#        y = quote_amp( lines.next() )
        y = lines.next()
        if y.startswith( 'PTBTR=' ):
          ptbtr = y.split( 'PTBTR=' )[-1]
#        if y.startswith( 'PTBTRR=' ):
#          ptbtrr = y.split( 'PTBTRR=' )[-1]
        if y.startswith( 'PTBNO=' ):
          ptbno = y.split( 'PTBNO=' )[-1]
      ds1.dataset.setdefault( '440', [] ).append( { 'a': quote_all( ptbtr) , 'n': quote_all( ptbno ) } )

    if y.startswith( '<CLS>' ):
      while( y != '</CLS>' ):
        y = lines.next()
        if y.startswith( 'CLSK=' ):
          clsk = y.split( 'CLSK=' )[-1]
        if y.startswith( 'CLSD=' ):
          clsd = y.split( 'CLSD=' )[-1]
      if clsk == 'UDC':
        ds1.dataset.setdefault( '080', [] ).append( { 'a': clsd } )
      elif clsk == 'DC':
        ds1.dataset.setdefault( '082', [] ).append( { 'a': clsd } )
      else:
        ds1.dataset.setdefault( '084', [] ).append( { '2': clsk, 'a': clsd } )

    if y.startswith( '<SH>' ):
      shk = 'A'
      while( y != '</SH>' ):
        y = lines.next()
        if y.startswith( 'SHT=' ):
          sht = y.split( 'SHT=' )[-1]
        if y.startswith( 'SHD=' ):
          shd = y.split( 'SHD=' )[-1]
        if y.startswith( 'SHK=' ):
          shk = y.split( 'SHK=' )[-1]
      if shk == 'A':
        ind1 = '1'
        ind2 = sht_get( sht )
        hdterm = sht_get2( sht )
        ds1.dataset.setdefault( '600', [] ).append( { 'ind1': ind1, 'ind2': ind2, 'a': shd, '2': hdterm } )
      elif shk == 'B':
        ind1 = '1'
        ind2 = sht_get( sht )
        hdterm = sht_get2( sht )
        ds1.dataset.setdefault( '610', [] ).append( { 'ind1': ind1, 'ind2': ind2, 'a': shd, '2': hdterm } )
      elif shk == 'C':
        ind1 = '1'
        ind2 = sht_get( sht )
        hdterm = sht_get2( sht )
        ds1.dataset.setdefault( '611', [] ).append( { 'ind1': ind1, 'ind2': ind2, 'a': shd, '2': hdterm } )
      elif shk == 'D':
        ind1 = '0'
        ind2 = sht_get( sht )
        hdterm = sht_get2( sht )
        ds1.dataset.setdefault( '630', [] ).append( { 'ind1': ind1, 'ind2': ind2, 'a': shd, '2': hdterm } )
      elif shk in ( 'E', 'F', 'G' ):
        ind1 = ' '
        ind2 = sht_get( sht )
        hdterm = sht_get2( sht )
        ds1.dataset.setdefault( '651', [] ).append( { 'ind1': ind1, 'ind2': ind2, 'a': shd, '2': hdterm } )
      elif shk == 'H':
        ind1 = ' '
        ind2 = ' '
        hdterm = sht_get2( sht )
        ds1.dataset.setdefault( '653', [] ).append( { 'ind1': ind1, 'ind2': ind2, 'a': shd, '2': hdterm } )
      elif shk in ( 'J', 'K', 'L' ):
        ind1 = ' '
        ind2 = sht_get( sht )
        hdterm = sht_get2( sht )
        ds1.dataset.setdefault( '650', [] ).append( { 'ind1': ind1, 'ind2': ind2, 'a': shd, '2': hdterm } )

    if y.startswith( '<AL>' ):
      while( True ):
        y = quote_amp( lines.next() )
        if( y.startswith( 'AFLG=' ) ):
##          a = y.split( '=' )[-1]
##          if a == '*':
##            if ds1.dataset.has_key( '100' ):
##              ds1.dataset.setdefault( '700', [] ).append( ds1.dataset[ '100' ] )
##              del ds1.dataset[ '100' ]
          continue
        if( y.startswith( 'AF=' ) ):
          continue
        if( y == '</AL>' ):
          break
        if( y.startswith( 'AID' ) ):
          continue
        if( y.startswith( 'AHDNG=' ) ):
          a = y.split( 'AHDNG=' )[-1]
          d = ''
          m = re.search( r'^(.*)\((\d{4}-.*)\)$', a )
          if m:
            ( a, d ) = m.groups()
          else:
            m = re.search( r'^(.*)\({0,1}(\d{4}-.*)\){0,1}$', a )
            if m:
              ( a, d ) = m.groups()
          ( a, d ) = map( quote_all, ( a, d ) )
          if ds1.dataset.has_key( '100' ):
            ds1.dataset.setdefault( '700', [] ).append( { 'a': a, 'd': d } )
          else:
            ds1.dataset[ '100' ] = { 'a': a, 'd': d }
        else:
          a = y.split( '=' )[-1]
          d = ''
          m = re.search( r'^(.*)\((\d{4}-.*)\)$', a )
          if m:
            ( a, d ) = m.groups()
          ( a, d ) = map( quote_all, ( a, d ) )
          if ds1.dataset.has_key( '100' ):
            ds1.dataset.setdefault( '700', [] ).append( { 'a': a, 'd': d } )
          else:
            ds1.dataset[ '100' ] = { 'a': a, 'd': d }

    if y.startswith( '<CW>' ):
      while( y != '</CW>' ):
        cw1 = { 'ind1': '0', 'ind2': '0' }
        cwt1 = ''
        cwa1 = ''
        y = lines.next()
        if y.startswith( 'CWT=' ):
          cwt1 = y.split( 'CWT=' )[-1]
        if y.startswith( 'CWA=' ):
          cwa1 = y.split( 'CWA=' )[-1]
        if cwt1+cwa1 != '':
          cw1[ 'a' ] = quote_all( ' / '.join( ( cwt1, cwa1 ) ) )
          ds1.dataset.setdefault( '505', [] ).append( cw1 )

    if y.startswith( 'IDENT=' ):
      ident = y.split( 'IDENT=' )[-1]
      if ident.find( '&' ) > 0 and ident.find( '&amp;' ) < 0:
        ident = ident.replace( '&', '&amp;' )
      ds1.dataset.setdefault( '856', [] ).append( { 'u': ident } )

  ds1.apply_gmd_smd( gmd, smd )
#  print ds1.dataset
  return( ds1 )


def Run( in_file ):
#  fno = in_file.split( '.' )[0] + '.xml'
  fno1 = in_file.split( '.' )[0] + '_%04d.xml'

  dat = codecs.open( in_file, 'r', 'utf-8' ).read()

  dat2 = dat.split( s2u( '【】' ) )

  cnt = 0
  datasets = []
#  for x in dat2[:2]:
  for x in dat2:
    if x == '':
      continue
    if x.startswith( u'\ufeff' ):
      continue
    lines = iter( x.split( '\r\n' ) )
    ds1 = process_a_record( lines )
    datasets.append( ds1.dataset )
    cnt += 1

#  f = open( fno, 'w' )
#  sys.stdout = f
#  xml_out( datasets )
#  f.close()

  cnt = 0
  fn_cnt = 1
  while( True ):
    if len( datasets ) <= cnt:
      break
    fno = fno1 % fn_cnt
    f = open( fno, 'w' )
    sys.stdout = f
    xml_out( datasets[ cnt:cnt+REC_NUM ] )
    f.close()
    fn_cnt += 1
    cnt += REC_NUM

if __name__ == '__main__':
  in_file = sys.argv[1]
  Run( in_file )

