# coding: utf-8

VERSION = '20181011'

# 20181011:
#  260フィールドがない時は264フィールドを使うようにした
#  また優先的に264を使うオプションを新設した
#  しかしこれを設定しても、264がない時あるいは264にaがない場合には260を使う
#
# 20180905:
#  084の処理を追加（ただしNDLC/NDCのみ）
#  110,110,710,711の処理を追加

import re
import sys
import time

from xml.etree import ElementTree

import argparse

class DataSet:
  def __init__( self ):
    self.dataset = {}
    self.__version__ = VERSION
    self.enable_rom2kana = True
    self.enable_id_10digit = False
    self.force_264_field = False
    self.kana_conv = 'kata'

  def set_options( self, options={} ):
    if options.has_key( 'disable_rom2kana' ):
      self.set_opt_rom2kana( not options[ 'disable_rom2kana' ] )
    if options.has_key( 'enable_id_10digit' ):
      self.set_opt_id_10digit( options[ 'enable_id_10digit' ] )
    if options.has_key( 'kana_conv' ):
      self.kana_conv = options[ 'kana_conv' ]
    if options.has_key( 'force_264_field' ):
      self.force_264_field = { 1: True, 0: False }[ options[ 'force_264_field' ] ]

  def set_opt_rom2kana( self, val=True ):
    if( val == True or val == False ):
      self.enable_rom2kana = val

  def set_opt_id_10digit( self, val=True ):
    if( val == True or val == False ):
      self.enable_id_10digit = val

  def process_880( self ):
    if not self.dataset.has_key( '880' ):
      return
    for afield in self.dataset[ '880' ]:
      # afield: 880フィールド
      link_f1 = afield[ '6' ][0]
      # link_f1: 880フィールドのsubfield 6から得たリンク先フィールド情報
      ( lfield, ser_num ) = link_f1.split( '/' )[0].split( '-' )
      # lfield: リンク先フィールド番号, ser_num: リンクシリアル番号
      xrfield = '-'.join( ( '880', ser_num ) )
      # xrfield: リンク先フィールド番号のsubfield 6にあるはずのフィールド情報
      if self.dataset.has_key( lfield ):
        for rf in self.dataset[ lfield ]:
          # rf: リンク先フィールド
          if rf.get( '6', [''] )[0] == xrfield:
            # 880フィールドの方のsubfieldの値でリンク先フィールド（元情報）のsubfieldの値を置き換える
            sf_replaced = {}
            for sf in rf.keys():
              if sf in ( '6', 'l' ):
                continue
              else:
                osf = 'old_' + sf
                rf[ osf ] = rf[ sf ]
                if afield.has_key( sf ):
                  rf[ sf ] = afield[ sf ]
                  sf_replaced[ sf ] = 1
            # 880フィールドの方のsubfieldにしかない値をリンク先フィールド（元情報）のsubfieldに設定
            for sf in afield.keys():
              if sf in ( '6', 'l' ):
                continue
              else:
                if not sf_replaced.has_key( sf ):
                  rf[ sf ] = afield[ sf ]

  def store_field_data( self, arec ):
    for afield in arec.getchildren():
      if afield.tag.endswith( 'leader' ):
        self.dataset[ 'leader' ] = afield.text
      elif afield.tag.endswith( 'controlfield' ):
        fcode = afield.get( 'tag' )
        self.dataset.setdefault( fcode, [] ).append( afield.text )
      elif afield.tag.endswith( 'datafield' ):
        fcode = afield.get( 'tag' )
        ind1 = afield.get( 'ind1', '' )
        ind2 = afield.get( 'ind2', '' )
#        print '%s ind1:%s ind2:%s' % ( fcode, ind1, ind2 )
        asubdata = { 'ind1': ind1, 'ind2': ind2 }
        for asubfield in afield.getchildren():
          if asubfield.tag.endswith( 'subfield' ):
            scode = asubfield.get( 'code' )
            svalue = asubfield.text
            asubdata.setdefault( scode, [] ).append( svalue )
        self.dataset.setdefault( fcode, [] ).append( asubdata )



  def u8print( self, s ):
    print s.encode( 'utf-8' )

  def print_a_record( self ):
    sline = []
    # ID
    sline.append( '_DBNAME_=BOOK' )
    if self.enable_id_10digit:
      sline.append( 'ID=%s' % gen_id_10digit( self.dataset[ '001' ][0] ) )
    else:
      sline.append( 'ID=%s' % self.dataset[ '001' ][0] )
    #
    # CRTDT/RNWDT
    sline.append( 'CRTDT=%04d%02d%02d' % time.localtime()[:3] )
    sline.append( 'RNWDT=%04d%02d%02d' % time.localtime()[:3] )
    #
    # GMD/SMD
    sline.append( 'GMD=w\nSMD=r' )
    #
    # YEAR
    v = self.dataset[ '008' ][0]
    if len( v ) > 6:
      t = v[6]
    if t in ( 's', 'm' ):
      if len( v ) > 10:
        y1 = v[7:11]
        try:
          if '%04d' % int( y1 ) == y1:
            sline.append( '<YEAR>\nYEAR1=%s' % y1 )
            if t == 'm' and len( v ) > 15:
              y2 = v[11:15]
              if '%04d' % int( y2 ) == y2:
                sline.append( 'YEAR2=%s' % y2 )
            sline.append( '</YEAR>' )
        except ValueError:
          pass

    #
    # CNTRY
    if len( v ) > 18:
      cntry1 = v[15:18]
      if cntry1 in ( 'abc', 'bcc', 'mbc', 'nfc', 'nkc', 'nsc', 'ntc', 'onc', 'pic', 'quc', 'snc', 'ykc' ):
        cntry1 = 'cn'
      elif cntry1 in ( 'enk', 'nik', 'stk', 'uik', 'wlk' ):
        cntry1 = 'uk'
      elif cntry1 in ( 'aku', 'alu', 'aru', 'azu', 'cau', 'cou', 'ctu', 'dcu', 'deu', 'flu', 'gau', 'hiu', 'iau', 'idu', 'ilu', 'inu', 'ksu', 'kyu', 'lau', 'mau', 'mdu', 'meu', 'miu', 'mnu', 'mou', 'msu', 'mtu', 'nbu', 'ncu', 'ndu', 'nhu', 'nju', 'nmu', 'nvu', 'nyu', 'ohu', 'oku', 'oru', 'pau', 'riu', 'scu', 'sdu', 'tnu', 'txu', 'utu', 'vau', 'vtu', 'wau', 'wiu', 'wvu', 'wyu' ):
        cntry1 = 'us'
      elif cntry1 in ( 'aca', 'xga', 'xna', 'xoa', 'qea', 'xra', 'tma', 'vra', 'wea' ):
        cntry1 = 'at'
      cntry1 = cntry1.strip()
      sline.append( 'CNTRY=%s' % ( cntry1, ) )
    #
    # TTLL
    ttll = ''
    if len( v ) > 39:
      ttll = v[35:39].strip()
      sline.append( 'TTLL=%s' % ttll )
    #
    # TXTL/ORGL
    txtl = ''
    orgl = ''
    if self.dataset.has_key( '041' ):
      txtl = self.dataset[ '041' ][0].get( 'a', [''] )[0]
      orgl = self.dataset[ '041' ][0].get( 'h', [''] )[0]
    if txtl == '' and ttll != '':
      txtl = ttll
    if txtl != '':
      sline.append( 'TXTL=%s' % txtl )
    if orgl != '':
      sline.append( 'ORGL=%s' % orgl )
    #
    # VOLG
    if self.dataset.has_key( '020' ):
      for adat in self.dataset[ '020' ]:
        sline.append( '<VOLG>' )
        if adat.has_key( 'a' ):
          vals = adat.get( 'a', [''] )[0].split( ' (' )
          if len( vals ) > 1:
            vol1 = vals[1].split( ')' )[0]
            sline.append( 'VOL=%s' % ( vol1, ) )
          sline.append( 'ISBN=%s' % ( vals[0], ) )
        elif adat.has_key( 'z' ):
          vals = adat.get( 'z', [''] )[0].split( ' (' )
          if len( vals ) > 1:
            vol1 = vals[1].split( ')' )[0]
            sline.append( 'VOL=%s' % ( vol1, ) )
          sline.append( 'XISBN=%s' % ( vals[0], ) )
        sline.append( '</VOLG>' )
    #
    # LCCN/OTHN
    if self.dataset.has_key( '010' ):
      lccn1 = self.dataset[ '010' ][0].get( 'a', [''] )[0].strip()
      if lccn1 != '':
        sline.append( 'LCCN=%s' % ( lccn1, ) )
    othns = {}
    for adat in self.dataset.get( '035', [] ):
      if adat.has_key( 'a' ):
        if adat.get( 'a' )[0].startswith( '(OCoLC)' ):
          othns[ 'OCLC' ] = adat.get( 'a' )[0].split( ')' )[ 1 ]
    for adat in othns.items():
      sline.append( 'OTHN=%s:%s' % adat )
    for adat in self.dataset.get( '938', [] ):
      if adat.get( 'a', [] )[0] == 'EBSCOhost':
        if adat.has_key( 'n' ):
          sline.append( 'OTHN=NLID:%s' % ( adat.get( 'n' )[0], ) )
    #
    # TR
    tr1 = ''
    if self.dataset.has_key( '245' ):
      adat = self.dataset[ '245' ][ 0 ]
      tr1a = adat.get( 'a', [''] )[0]
      tr1b = adat.get( 'b', [''] )[0]
      tr1c = adat.get( 'c', [''] )[0]
      tr1p = adat.get( 'p', [''] )[0]
      if tr1p != '':
        tr1a = ' '.join( ( tr1a, tr1p ) )
      tr1 = tr1a
      if tr1b != '':
        tr1 += ' ' + tr1b
      if tr1c != '':
        tr1 += ' ' + tr1c
      if tr1.endswith( '.' ):
        tr1 = tr1[:-1]
      sline.append( '<TR>' )
      sline.append( 'TRD=%s' % ( tr1, ) )
      sline.append( '</TR>' )
    #
    # VT
    pass
    #
    # ED
    if self.dataset.has_key( '250' ):
      adat = self.dataset[ '250' ][0]
      ed1 = adat.get( 'a', [''] )[0]
      if ed1.endswith( '.' ):
        ed1 = ed1[:-1]
      if ed1 != '':
        sline.append( 'ED=%s' % ( ed1, ) )
    #
    # PUB
    kpb = ''
    if self.force_264_field:
      if self.dataset.has_key( '264' ) and self.dataset[ '264' ][0].has_key( 'a' ):
        kpb = '264'
      elif self.dataset.has_key( '260' ) and self.dataset[ '260' ][0].has_key( 'a' ):
        kpb = '260'
    else:
      if self.dataset.has_key( '260' ) and self.dataset[ '260' ][0].has_key( 'a' ):
        kpb = '260'
      elif self.dataset.has_key( '264' ) and self.dataset[ '264' ][0].has_key( 'a' ):
        kpb = '264'
    if kpb != '':
      for adat in self.dataset.get( kpb, [] ):
        puba = ' '.join( adat.get( 'a', [''] ) )
        pubb = adat.get( 'b', [''] )[0]
        pubc = adat.get( 'c', [''] )[0]
#        if puba + pubb + pubc != '':
        if puba + pubb != '':
          sline.append( '<PUB>' )
          if puba != '':
            sline.append( 'PUBP=%s' % ( self.strip_last( puba ), ) )
          if pubb != '':
            sline.append( 'PUBL=%s' % ( self.strip_last( pubb ), ) )
          if pubc != '':
            sline.append( 'PUBDT=%s' % ( self.strip_last( pubc ), ) )
          sline.append( '</PUB>' )
    #
    # PHYS
    if self.dataset.has_key( '300' ):
      adat = self.dataset[ '300' ][ 0 ]
      physa = adat.get( 'a', [''] )[0]
      physb = adat.get( 'b', [''] )[0]
      physc = adat.get( 'c', [''] )[0]
      physe = adat.get( 'e', [''] )[0]
      if physa + physb + physc + physe != '':
        sline.append( '<PHYS>' )
        if physa != '':
          sline.append( 'PHYSP=%s' % ( self.strip_last( physa ), ) )
        if physb != '':
          sline.append( 'PHYSI=%s' % ( self.strip_last( physb ), ) )
        if physc != '':
          sline.append( 'PHYSS=%s' % ( self.strip_last( physc ), ) )
        if physe != '':
          sline.append( 'PHYSA=%s' % ( self.strip_last( physe ), ) )
        sline.append( '</PHYS>' )
    #
    # CW
    for adat in self.dataset.get( '505', [] ):
      if adat.has_key( 'a' ):
        cw = adat.get( 'a', [''] )[0]
        for val in cw.split( ' -- ' ):
          vals = val.split( ' / ' )
          cwt1 = vals[0]
          if cwt1.endswith( '.' ):
            cwt1 = cwt1[:-1]
          if cwt1 != '':
            sline.append( '<CW>' )
            sline.append( 'CWT=%s' % ( cwt1, ) )
            if len( vals ) > 1:
              sline.append( 'CWA=%s' % ( vals[1], ) )
            sline.append( '</CW>' )
      elif adat.has_key( 'g' ):
        if len( adat.get( 'g' ) ) == len( adat.get( 't' ) ):
          for n in xrange( len( adat.get( 'g' ) ) ):
            cwt1 = ' '.join( ( adat.get( 'g' )[n], adat.get( 't' )[n] ) )
            if cwt1.endswith( ' --' ):
              cwt1 = cwt1.split( ' --' )[0]
            if cwt1.endswith( '.' ):
              cwt1 = cwt1[:-1]
            sline.append( '<CW>' )
            sline.append( 'CWT=%s' % ( cwt1, ) )
            sline.append( '</CW>' )
    #
    # NOTE
    for k in self.dataset.keys():
      if k.startswith( '5' ) and k != '505':
        if k.startswith( '59' ):
          continue
        for adat in self.dataset[ k ]:
          if adat.get( 'a', [''] )[0] != '':
            note1 = adat.get( 'a' )[0]
            for sf1 in ( 'b', 'c', 'd', 'h' ):
              if adat.has_key( sf1 ):
                note1 = note1 + ' ' + adat.get( sf1 )[0]
            if note1.endswith( '.' ):
              note1 = note1[:-1]
            sline.append( 'NOTE=%s' % ( note1, ) )
    #
    # PTBL
  #  for adat in self.dataset.get( '440', [] ):
    for adat in self.dataset.get( '490', [] ):
      ptbla = adat.get( 'a', [''] )[0]
      ptblv = adat.get( 'v', [''] )[0]
      if ptbla + ptblv != '':
        sline.append( '<PTBL>' )
        sline.append( 'PTBK=a' )
        if ptbla != '':
          sline.append( 'PTBTR=%s' % ( ptbla, ) )
        if ptblv != '':
          sline.append( 'PTBNO=%s' % ( ptblv, ) )
        sline.append( '</PTBL>' )
    #
    # AL
    for k in [ k for k in self.dataset.keys() if k.startswith( '1' ) ]:
      if k in ( '100', '110', '111' ):
        adat = self.dataset[ k ][ 0 ]
        ala = adat.get( 'a', [''] )[0]
        ald = adat.get( 'd', [''] )[0]
        if ala + ald != '':
          sline.append( '<AL>' )
          if ala != '':
            if k == '100':
              sline.append( 'AFLG=*' )
            s = 'AHDNG=%s' % ( ala, )
            if ald != '':
              s += ' %s' % ( ald, )
            sline.append( s )
            sline.append( '</AL>' )
    for k in [ k for k in self.dataset.keys() if k.startswith( '7' ) ]:
      if k in ( '700', '710', '711' ):
        for adat in self.dataset.get( k, [] ):
          ala = adat.get( 'a', [''] )[0]
          ald = adat.get( 'd', [''] )[0]
          if ala + ald != '':
            sline.append( '<AL>' )
            if ala != '':
              s = 'AHDNG=%s' % ( ala, )
              if ald != '':
                s += ' %s' % ( ald, )
              sline.append( s )
              sline.append( '</AL>' )
    #
    # CLS
  #  for k in self.dataset.keys():
    for k in [ k for k in self.dataset.keys() if k.startswith( '08' ) ]:
      if k == '080':
        pass
      elif k == '082':
        for adat in self.dataset[ k ]:
          clsa = adat.get( 'a', [''] )[0]
          cls2 = adat.get( '2', [''] )[0]
          sline.append( '<CLS>' )
          sline.append( 'CLSK=DC%s' % ( adat.get( '2', [''] )[0], ) )
          sline.append( 'CLSD=%s' % ( adat.get( 'a', [''] )[0], ) )
          sline.append( '</CLS>' )
      elif k == '084':
        for adat in self.dataset[ k ]:
          cls2 = adat.get( '2', [''] )[0]
          clsk = ''
          if cls2.startswith( 'kktb' ):
            clsk = 'NDLC'
          elif cls2.startswith( 'njb' ):
            clsk = 'NDC'
            if cls2.find( '/' ) > 0:
              try:
                clsk += '%d' % ( int( cls2.split( '/' )[1] ), )
              except:
                pass
          else:
            break
          for clsa1 in adat.get( 'a', [] ):
            sline.append( '<CLS>' )
            sline.append( 'CLSK=%s' % ( clsk, ) )
            sline.append( 'CLSD=%s' % ( clsa1, ) )
            sline.append( '</CLS>' )
    #
    # SH
    for k in [ k for k in self.dataset.keys() if k.startswith( '6' ) ]:
      for adat in self.dataset[ k ]:
        shk1 = { '600': 'A', '610': 'B', '611': 'C', '630': 'D', '647': 'K', '648': 'K', '650': 'K', '651': 'F', '653': 'K', '654': 'K', '655': 'J' }[ k ]
        ind2 = adat.get( 'ind2', [''] )[0]
        if not ind2 in ( '0', '1', '2', '3', '4', '5', '6', '7' ):
          ind2 = '7'
        sht1 = { '0': 'LCSH', '1': 'JVSH', '2': 'MESH', '3': 'NALSH', '4': 'BSH', '5': 'CSHE', '6': 'FREE', '7': 'FREE' }[ ind2 ]
        if adat.get( 'ind2', [''] )[0] == '7' and adat.has_key( '2' ):
          sht1 = adat.get( '2', [''] )[0].upper()
        if not sht1 in ( 'BISACSH', 'BLSH', 'BSH', 'CSHE', 'CSHF', 'CTSH', 'ECSH', 'JUSH', 'JVSH', 'LCSH', 'MESH', 'NALSH', 'NDLSH', 'OECDSH', 'PRECIS', 'RAM', 'RSWK', 'DDB', 'SWD', 'SHIBUSH', 'UNSH', 'FREE' ):
          sht1 = 'FREE'
        shd1 = adat.get( 'a', [''] )[0]
        if adat.has_key( 'd' ):
          shd1 = shd1 + ' ' + adat.get( 'd', [''] )[0]
  #      for subd1 in ( 'v', 'x', 'y', 'z' ):
        for subd1 in ( 'y', 'z', 'x', 'v' ):
          if adat.has_key( subd1 ):
            for asubdat1 in adat.get( subd1 ):
              shd1 = ' -- '.join( ( shd1, asubdat1 ) )
        shr1 = ''
        if adat.has_key( 'old_a' ):
          shr1 = adat.get( 'old_a' )[0]
          if adat.has_key( 'old_d' ):
            shr1 = shr1 + ' ' + adat.get( 'old_d', [''] )[0]
          elif adat.has_key( 'd' ):
            shr1 = shr1 + ' ' + adat.get( 'd', [''] )[0]
          for subd1 in ( 'v', 'x', 'y', 'z' ):
            if adat.has_key( 'old_' + subd1 ):
              for asubdat1 in adat.get( 'old_' + subd1 ):
                shr1 = ' -- '.join( ( shr1, asubdat1 ) )
            elif adat.has_key( subd1 ):
              for asubdat1 in adat.get( subd1 ):
                shr1 = ' -- '.join( ( shr1, asubdat1 ) )
        if shd1.endswith( '.' ):
          shd1 = shd1[:-1]
        sline.append( '<SH>' )
        sline.append( 'SHT=%s' % ( sht1, ) )
        sline.append( 'SHD=%s' % ( shd1, ) )
        sline.append( 'SHK=%s' % ( shk1, ) )
        if shr1 != '':
          sline.append( 'SHR=%s' % ( shr1, ) )
        sline.append( '</SH>' )
    #
    # IDENT
    if self.dataset.has_key( '856' ):
      for adat in self.dataset.get( '856', [] ):
        url1 = adat.get( 'u', [''] )[0]
        if url1 != '':
          sline.append( 'IDENT=%s' % ( url1, ) )

    if sline != []:
      s = '\n'.join( sline )
      self.u8print( s )

  def strip_last( self, s ):
    if type( s ) in ( type( '' ), type( u'' ) ):
      s = s.strip()
      if s[-1] in ( ':', ',', '.' ):
        s = s[:-1]
      s = s.strip()
    return( s )

  def get_version( self ):
    return self.__version__

def gen_catp_fs_start( fstype ):
  return( { 1: u'【】', 2: '--NACSIS-CATP--', 3: '<RECORD>' }[ fstype ] )

def gen_catp_fs_end( fstype ):
  return( { 1: '--NACSIS-CATP--', 2: '--NACSIS-CATP--', 3: '</RECORD>' }[ fstype ] )

def gen_id_10digit( marc_id ):
  oclc_id = re.sub( r'^oc[mn]', '', marc_id )
  if len( str( oclc_id ) ) > 8:
    id1 = 'o' + chr( 99 - 48 + ord( oclc_id[-9] ) ) + oclc_id[-8:]
  else:
    id1 = 'oc' + oclc_id
  return( id1 )

def print_catp( fstype, data_list ):
  for ds1 in data_list:
    ds1.u8print( gen_catp_fs_start( fstype ) )
    try:
      ds1.print_a_record()
    except:
      e = '### error occurred with "%s" ###' % ( ds1.dataset[ '001' ][0], )
      error_msg( e )
      raise
    ds1.u8print( gen_catp_fs_end( fstype ) )

def error_msg( s ):
  sys.stderr.write( s + '\n' )

def load_xml_file( xml_file, options={} ):
  xml = open( xml_file, 'r' ).read()
  tree = ElementTree.fromstring( xml )
  data_list = []
  for arec in tree.getchildren():
    ds1 = DataSet()
    ds1.set_options( options )
    ds1.store_field_data( arec )
    try:
      ds1.process_880()
    except:
      e = '### error occurred with "%s" ###' % ( ds1.dataset[ '001' ][0], )
      error_msg( e )
      raise
    data_list.append( ds1 )
  return( data_list )

def marc2catp( xml_file, fs_type ):
  data_list = load_xml_file( xml_file, {} )
  print_catp( fs_type, data_list )

if __name__ == '__main__':
  pass

