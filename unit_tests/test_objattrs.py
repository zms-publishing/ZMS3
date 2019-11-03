# encoding: utf-8

from OFS.Folder import Folder
import sys
import time
import unittest
sys.path.append("..")
# Product imports.
from zms_test_util import *
import zms
import _confmanager
import _multilangmanager

# /Products/zms> python -m unittest discover -s unit_tests
# /Products/zms> python -m unittest unit_tests.test_objattrs.ObjAttrsTest
class ObjAttrsTest(ZMSTestCase):

  temp_lang = 'xxx'
  temp_title = 'temp-test'

  def setUp(self):
    print(self,"MultiLanguageTest.setUp")
    # super
    ZMSTestCase.setUp(self)
    zmscontext = self.context
    # create language
    prim_lang = zmscontext.getPrimaryLanguage()
    request = zmscontext.REQUEST
    request.set('lang',prim_lang)
    print('[setUp] create language %s'%self.temp_lang)
    newLabel = 'Test Language'
    newParent = prim_lang
    newManage = 'eng'
    zmscontext.setLanguage(self.temp_lang, newLabel, newParent, newManage)
    print('[setUp] create %s'%self.temp_title)
    self.folder = zmscontext.manage_addZMSCustom('ZMSFolder',{'active':1,'title':self.temp_title,'titlealt':self.temp_title},request)

  def test_attr(self):
    zmscontext = self.context
    prim_lang = zmscontext.getPrimaryLanguage()
    other_lang = self.temp_lang
    context = self.folder
    context.setObjProperty('title','the Primary title',prim_lang)
    context.setObjProperty('title','the Other title',other_lang)
    self.assertEqual('the Primary title',context.attr('title'))

  def tearDown(self):
    zmscontext = self.context
    # remove language
    prim_lang = zmscontext.getPrimaryLanguage()
    request = zmscontext.REQUEST
    request.set('lang',prim_lang)
    print('[tearDown] remove %s'%self.temp_title)
    zmscontext.manage_delObjects([self.folder.id])
    print('[tearDown] delete language %s'%self.temp_lang)
    zmscontext.delLanguage(self.temp_lang)
    # super
    ZMSTestCase.tearDown(self)
