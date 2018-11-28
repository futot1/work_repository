#coding: utf-8

GUI_VERSION = '20181025'

# 20181025
# Implemented RapidMARC file support (need to pre examine unexpected line breaks)
#
# 2018.10.11 (0.5)
# 264フィールドを優先するオプションを追加
#
# 2018.10.10 (0.4)
# コンソールに出力後にその位置までスクロールするようにした
#
# 2018.09.18 (0.3)
# ファイル名に日本語が含まれる場合にエラーが出るのを修正
#
# 2018.09.11
# カタカナ／ひらがな変換オプションを追加

import os
import re
import codecs
import tempfile
import subprocess
from StringIO import StringIO

from Tkinter import *
import tkFileDialog
from ScrolledText import ScrolledText

from jp_marc2catp import *

MARCEDIT = r'C:\Program Files\MarcEdit 6'

class App( Frame ):
  def __init__(self, master=None):
    Frame.__init__(self, master)
    self.input_fn = StringVar()
    self.output_fn = StringVar()
    self.fstype = IntVar()
    self.fstype.set( 3 )
    self.id10 = IntVar()
    self.id10.set( 0 )
    self.force_264_field = IntVar()
    self.force_264_field.set( 0 )
    self.enable_rom2kana = IntVar()
    self.enable_rom2kana.set( 0 )
    self.kana_conv = StringVar()
    self.kana_conv.set( 'kata' )

    self.master.title( 'MARC21 to CATP converter GUI (%s) by F.Tanuma' % ( VERSION, ) )
#    self.master.maxsize( 400, 400 )
    self.grid( row=0, column=0, sticky=(N, E, W, S ) )
    self.createWidgets()
    self.console_out( 'MARC21 to CATP converter (%s) by F.Tanuma' % ( VERSION, ) )
    self.cmarcedit = self.get_cmarcedit()

  def createWidgets( self ):
    Label( self, text=u'MARC21 → CATP 変換プログラム %s 版 (GUI %s 版)' % ( VERSION, GUI_VERSION ) ).grid( row=1, column=1, columnspan=3, sticky=W )

    lf1 = LabelFrame( self, text=u'入力ファイル', relief=GROOVE )
    Entry( lf1, width=40, textvariable=self.input_fn ).grid( row=1, column=1, padx=5 )
    Button( lf1, text=u'参照...', command=self.browse ).grid( row=1, column=2, padx=5 )
    lf1.grid( row=2, column=1, padx=5, pady=5, ipadx=5, ipady=5 )

    lf2 = LabelFrame( self, text=u'出力ファイル（オプション）', relief=GROOVE )
    Entry( lf2, width=40, textvariable=self.output_fn ).grid( row=1, column=1, padx=5 )
    lf2.grid( row=3, column=1, padx=5, pady=5, ipadx=5, ipady=5 )

    lf3 = LabelFrame( self, text=u'レコードセパレータ', relief=GROOVE )
    Radiobutton( lf3, text=u'【】', value=1, variable=self.fstype ).grid( row=1, column=1 )
    Radiobutton( lf3, text=u'--NACSIS-CATP--', value=2, variable=self.fstype ).grid( row=1, column=2 )
    Radiobutton( lf3, text=u'<RECORD> (default)', value=3, variable=self.fstype ).grid( row=1, column=3 )
    lf3.grid( row=4, column=1, padx=5, pady=5, ipadx=5, ipady=5 )

    lf4 = LabelFrame( self, text=u'オプション', relief=GROOVE )
    Checkbutton( lf4, text=u'IDを10桁に設定', variable=self.id10 ).grid( row=1, column=1, sticky=W )
    Checkbutton( lf4, text=u'260フィールドより264を優先して<PUB>を生成', variable=self.force_264_field ).grid( row=2, column=1, sticky=W )
    Checkbutton( lf4, text=u'ローマ字をひらがなに変換（β版機能）', variable=self.enable_rom2kana, command=self.tgl_conv ).grid( row=3, column=1, sticky=W )
    lf41 = Frame( lf4 )
    self.rb_conv_kata = Radiobutton( lf41, text=u'カタカナに変換', variable=self.kana_conv, value='kata', state=DISABLED )
    self.rb_conv_kata.grid( row=1, column=1, sticky=W )
    self.rb_conv_hira = Radiobutton( lf41, text=u'ひらながに変換', variable=self.kana_conv, value='hira', state=DISABLED )
    self.rb_conv_hira.grid( row=1, column=2, sticky=W )
    lf41.grid( row=4, column=1, sticky=W )
    lf4.grid( row=5, column=1, padx=5, pady=5, ipadx=5, ipady=5 )

    lf5 = Frame( self )
    Button( lf5, text=u'変換', width=10, command=self.convert ).grid( row=1, column=1, padx=5 )
    Button( lf5, text=u'終了', width=10, command=self.quit ).grid( row=1, column=2, padx=5 )
    lf5.grid( row=6, column=1, padx=5, pady=5, ipadx=5, ipady=5 )

    self.console = ScrolledText( self, height=5, state=DISABLED )
    self.console.grid( row=7, column=1, padx=10, pady=10, ipadx=5, ipady=5 )

  def browse( self ):
#    self.input_fn.set( tkFileDialog.askopenfilename(filetypes=[( u'すべてのファイル', '*.*' ) ],initialdir='C:\\') )
    self.input_fn.set( tkFileDialog.askopenfilename(filetypes=[( u'すべてのファイル', '*.*' ) ],initialdir=os.getcwd()) )
    self.set_default_output_fn()

  def set_default_output_fn( self ):
    input_fn = self.input_fn.get().encode( 'shift-jis' )
    if input_fn != '':
      m = re.compile( '\.(mrc|xml)$' )
      if m.search( input_fn ):
        output_fn = m.sub( '.txt', input_fn )
      else:
        output_fn = in_file + '.txt'
      self.output_fn.set( unicode( output_fn, 'shift-jis' ) )

  def tgl_conv( self ):
    if self.enable_rom2kana.get() == 0:
      self.rb_conv_kata.configure( state=DISABLED )
      self.rb_conv_hira.configure( state=DISABLED )
    else:
      self.rb_conv_kata.configure( state=NORMAL )
      self.rb_conv_hira.configure( state=NORMAL )

  def get_options( self ):
    options = {}
    options[ 'disable_rom2kana'] = { True: 0, False: 1 }[ self.enable_rom2kana.get() ]
    options[ 'enable_id_10digit' ] = self.id10.get()
    options[ 'force_264_field' ] = self.force_264_field.get()
    options[ 'kana_conv' ] = self.kana_conv.get()
    return( options )

  def console_out( self, s ):
    self.console.configure( state=NORMAL )
    self.console.insert( END, s + '\n' )
    self.console.configure( state=DISABLED )
    self.console.yview_moveto( "%d.0" % ( len( self.console.get( "1.0", END ).split( '\n' ) ), ) )

  def convert( self ):
    if self.input_fn.get().endswith( '.xml' ):
      xml_file = self.input_fn.get().encode( 'shift-jis' )
    else:
      xml_file = self.convert_xml( self.input_fn.get().encode( 'shift-jis' ) )
    self.console_out( 'MARCXML: %s' % ( unicode( xml_file, 'shift-jis' ), ) )

    options = self.get_options()
    data_list = load_xml_file( xml_file, options )

    self.console_out( 'Converting MARCXML to CATP...' )
    if options[ 'disable_rom2kana' ]:
      self.console_out( 'Disabling Romaji to Kana conversion...' )
    buf = StringIO()
    sys.stdout = buf

    print_catp( self.fstype.get(), data_list )

    sys.stdout = sys.__stdout__
    out_file = self.output_fn.get().encode( 'shift-jis' )
    f = open( out_file, 'w' )
    f.write( buf.getvalue() )
    f.close()
    self.console_out( 'Conversion done...' )
    self.console_out( 'CATP file: %s...\n' % ( unicode( out_file, 'shift-jis' ), ) )


  def get_cmarcedit( self ):
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
        self.console_out( 'Cannot find cmarcedit.exe' )
        return( '' )
    self.console_out( 'Found cmarcedit.exe as %s' % ( cmarcedit, ) )
    return( cmarcedit )

  def convert_xml( self, in_file ):
    if in_file.endswith( '.mrc' ):
      xml_file = re.sub( '\.mrc$', '.xml', in_file )
    else:
      xml_file = in_file + '.xml'
    mrc_file = self.check_mrc_file( in_file )
    if mrc_file != False:
      cmds = [ self.cmarcedit, '-s', mrc_file, '-d', xml_file, '-marcxml', '-utf8' ]
      self.console_out( 'Converting MARC21 to MARCXML using cmarcedit.exe ...' )
      p = subprocess.Popen( cmds, stdout=subprocess.PIPE )
      self.console_out( p.communicate()[0] )
      if mrc_file != in_file:
        os.unlink( mrc_file )
      return( xml_file )

  def check_mrc_file( self, in_file ):
    buf = open( in_file, 'rb' ).read( 100 )
    if buf.startswith( codecs.BOM_UTF8 ):
      buf = buf[ len( codecs.BOM_UTF8 ): ]
    try:
      rsz = int( buf[:5] )
    except ValueError:
      self.console_out( 'Invalid MARC file' )
      return( False )
    buf2 = open( in_file, 'rb' ).read( rsz + 20 )
    if buf2.find( '\r\n' ) > 0:
      tfn = tempfile.mktemp()
      tfn1 = tfn + '.mrk8'
      tfn2 = tfn + '.mrc'
      cmds1 = [ self.cmarcedit, '-s', in_file, '-d', tfn1, '-break', '-utf8' ]
      self.console_out( 'Pre-converting process 1/2 using cmarcedit.exe ...' )
      p = subprocess.Popen( cmds1, stdout=subprocess.PIPE )
      self.console_out( p.communicate()[0] )
      cmds2 = [ self.cmarcedit, '-s', tfn1, '-d', tfn2, '-make', '-utf8' ]
      self.console_out( 'Pre-converting process 2/2 using cmarcedit.exe ...' )
      p = subprocess.Popen( cmds2, stdout=subprocess.PIPE )
      self.console_out( p.communicate()[0] )
      os.unlink( tfn1 )
      return( tfn2 )
    return( in_file )


def Run():
  root = Tk()
  app = App(master=root)
  app.mainloop()
  root.destroy()


if __name__ == '__main__':
  Run()
