# -*- coding: utf-8 -*- 
################################################################################
# ZMSRepositoryManager.py
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
################################################################################

# Imports.
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from distutils.version import LooseVersion
import copy
import inspect
import os
import re
import stat
import time
import urllib
from zope.interface import implementer, providedBy
# Product Imports.
import IZMSConfigurationProvider
import IZMSDaemon
import IZMSRepositoryManager
import IZMSRepositoryProvider
import ZMSItem
import _fileutil
import standard
import zopeutil


def get_class(py):
  id = re.findall('class (.*?):',py)[0]
  exec(py)
  return eval(id)


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
@implementer(
        IZMSConfigurationProvider.IZMSConfigurationProvider,
        IZMSDaemon.IZMSDaemon,
        IZMSRepositoryManager.IZMSRepositoryManager)
class ZMSRepositoryManager(
        ZMSItem.ZMSItem):

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Properties
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    meta_type = 'ZMSRepositoryManager'
    icon = "++resource++zms_/img/ZMSRepositoryManager.png"
    icon_clazz = "icon-random"

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Options
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    manage_options_default_action = '../manage_customize'
    def manage_options(self):
      return map( lambda x: self.operator_setitem( x, 'action', '../'+x['action']), copy.deepcopy(self.aq_parent.manage_options()))

    manage_sub_options__roles__ = None
    def manage_sub_options(self):
      return (
        {'label': 'Repository','action': 'manage_main'},
        )

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Interface
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    manage = PageTemplateFile('zpt/ZMSRepositoryManager/manage_main', globals())
    manage_main = PageTemplateFile('zpt/ZMSRepositoryManager/manage_main', globals())
    manage_main_diff = PageTemplateFile('zpt/ZMSRepositoryManager/manage_main_diff', globals())

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Permissions
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    __administratorPermissions__ = (
        'manage_main',
        'manage_change',
        )
    __ac_permissions__=(
        ('ZMS Administrator', __administratorPermissions__),
        )


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSRepositoryManager.__init__: 
    
    Constructor.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def __init__(self):
      self.id = 'repository_manager'


    """
    Returns direction of copying config files:
    Loading from file system (coloring ZMS changes) vs.
    Saving to file system (coloring filesystem changes)
    """
    def get_update_direction(self):
      return getattr(self,'update_direction','Loading')


    """
    Returns auto-update.
    """
    def get_auto_update(self):
      return getattr(self, 'auto_update', False)


    """
    Returns last-update.
    """
    def get_last_update(self):
      return getattr(self, 'last_update', 0)


    """
    Returns ignore-orphans.
    """
    def get_ignore_orphans(self):
      return getattr(self, 'ignore_orphans', True)


    """
    Returns conf-basepath.
    """
    def get_conf_basepath(self, id='conf'):
      basepath = self.get_conf_property('ZMS.conf.path')
      basepath = basepath.replace('$INSTANCE_HOME', self.getINSTANCE_HOME())
      basepath = basepath.replace('$HOME_ID',"/".join([x.getHome().id for x in self.breadcrumbs_obj_path() if x.meta_id=='ZMS']))
      basepath = basepath.replace("/", os.path.sep)
      basepath = os.path.join(basepath, id)
      return basepath

    """
    @see IZMSDaemon
    """
    def startDaemon(self):
      self.writeLog("[startDaemon]")
      self.exec_auto_update()


    """
    @see IZMSRepositoryManager
    """
    def exec_auto_commit(self, provider, id):
      if self.get_auto_update():
        ids = [':'.join([provider.id, id])]
        self.writeLog("[exec_auto_commit]: Run... %s"%str(ids))
        self.commitChanges(ids)


    """
    @see IZMSRepositoryManager
    """
    def exec_auto_update(self):
      #-- [ReqBuff]: Fetch buffered value from Http-Request.
      reqBuffId = 'ZMSRepositoryManager.exec_auto_update'
      try:
        return self.fetchReqBuff(reqBuffId)
      except:
        #-- [ReqBuff]: Returns value and stores it in buffer of Http-Request.
        self.storeReqBuff(reqBuffId, True)
        # Execute once.
        self.writeLog("[exec_auto_update]")
        current_time = time.time()
        if self.get_auto_update():
          last_update = self.get_last_update()
          if ( last_update==0 or standard.getDateTime(last_update)<standard.getDateTime(self.Control_Panel.process_start) ) and self.getConfProperty('ZMS.debug', 0)==True:
            self.writeBlock("[exec_auto_update]: Run...")
            def traverse(path):
              l = []
              if os.path.exists(path):
                for file in os.listdir(path):
                  filepath = os.path.join(path, file)
                  mode = os.stat(filepath)[stat.ST_MODE]
                  if stat.S_ISDIR(mode):
                    l.extend(traverse(filepath))
                  else:
                    l.append((os.path.getmtime(filepath), filepath))
              return l
            basepath = self.get_conf_basepath()
            files = traverse(basepath)
            mtime = max(map(lambda x:x[0],files)+[None])
            self.writeBlock("[exec_auto_update]: %s < %s"%(str(last_update),str(mtime)))
            if last_update==0 or ( standard.getDateTime(last_update) < standard.getDateTime(mtime) ):
              update_files = map(lambda x:x[1][len(basepath):],filter(lambda x:last_update is None or standard.getDateTime(x[0])<standard.getDateTime(last_update),files))
              temp_files = map(lambda x:x.split(os.path.sep),update_files)
              temp_files = \
                map(lambda x:[x[0],x[-1].replace('.py', '')],filter(lambda x:len(x)==2,temp_files)) + \
                map(lambda x:[x[0],x[-2]],filter(lambda x:len(x)>2,temp_files))
              # avoid processing of hidden files, e.g. .DS_Store on macOS
              temp_files = filter(lambda x: str(x).startswith('.'), temp_files)
              ids = list(set(map(lambda x:':'.join(x),temp_files)))
              # avoid processing of hidden files, e.g. .DS_Store on macOS
              ids = filter(lambda x: ':.' not in x, ids)
              self.writeBlock("[exec_auto_update]: %s"%str(ids))
              self.updateChanges(ids, override=True)
            self.last_update = standard.getDateTime(current_time)
        self.writeLog("[exec_auto_update]: %s"%str(time.time()-current_time))


    def getDiffs(self, provider, ignore=True):
      self.writeBlock("[getDiffs]: provider=%s"%str(provider))
      diff = []
      local = self.localFiles(provider)
      remote = self.remoteFiles(provider)
      filenames = list(set(local.keys()+remote.keys()))
      filenames.sort()
      for filename in filenames:
        if ignore and filename not in local.keys():
          # ignore orphaned files in filesystem
          # if there are no references in model
          continue
        l = local.get(filename,{})
        r = remote.get(filename,{})
        if l.get('data','') != r.get('data',''):
          data = l.get('data',r.get('data',''))
          mt, enc = standard.guess_content_type(filename,data)
          diff.append((filename,mt,l.get('id',r.get('id','?')),l,r))
      return diff


    def getRepositoryProviders(self):
      obs = self.getDocumentElement().objectValues()
      return filter(lambda x:IZMSRepositoryProvider.IZMSRepositoryProvider in list(providedBy(x)),obs)


    def localFiles(self, provider, ids=None):
      self.writeBlock("[localFiles]: provider=%s"%str(provider))
      l = {}
      local = provider.provideRepository(ids)
      for id in local.keys():
        o = local[id]
        filename = o.get('__filename__', [id, '__init__.py'])
        # Write python-representation.
        py = []
        py.append('class %s:'%id.replace('.','_').replace('-','_'))
        py.append('\t"""')
        py.append('\tpython-representation of %s'%o['id'])
        py.append('\t"""')
        py.append('')
        e = sorted([x for x in o if not x.startswith('__') and x==x.capitalize() and type(o[x]) is list])
        keys = sorted([x for x in o if not x.startswith('__') and x not in e])
        for k in keys:
          v = o.get(k)
          py.append('\t# %s'%k.capitalize())
          py.append('\t%s = %s'%(standard.id_quote(k),standard.str_json(v,encoding="utf-8",formatted=True,level=2,allow_booleans=False)))
          py.append('')
        for k in e:
          v = o.get(k)
          if v and type(v) is list:
            py.append('\t# %s'%k.capitalize())
            py.append('\tclass %s:'%standard.id_quote(k).capitalize())
            for i in v:
              if 'id' in i.keys():
                ob = i.get('ob')
                if ob is not None:
                  fileexts = {'DTML Method':'.dtml', 'DTML Document':'.dtml', 'External Method':'.py', 'Page Template':'.zpt', 'Script (Python)':'.py', 'Z SQL Method':'.zsql'}
                  fileprefix = i['id'].split('/')[-1]
                  data = zopeutil.readData(ob)
                  if type(data) is unicode:
                    data = data.encode('utf-8')
                  d = {}
                  d['id'] = id
                  d['filename'] = os.path.sep.join(filename[:-1]+['%s%s'%(fileprefix,fileexts.get(ob.meta_type,''))])
                  d['data'] = data
                  d['version'] = self.getLangFmtDate(ob.bobobase_modification_time().timeTime(),'eng')
                  d['meta_type'] = ob.meta_type
                  l[d['filename']] = d
                if i.has_key('ob'):
                  del i['ob']
                py.append('\t\t%s = %s'%(self.id_quote(i['id']),standard.str_json(i,encoding="utf-8",formatted=True,level=3,allow_booleans=False)))
                py.append('')
        d = {}
        d['id'] = id
        d['filename'] = os.path.sep.join(filename)
        d['data'] = '\n'.join(py)
        d['version'] = LooseVersion(o.get('revision','0.0.0'))
        d['meta_type'] = 'Script (Python)'
        l[d['filename']] = d
      return l


    def remoteFiles(self, provider):
      self.writeBlock("[remoteFiles]: provider=%s"%str(provider))
      r = {}
      basepath = self.get_conf_basepath(provider.id)
      if os.path.exists(basepath):
        def traverse(base,path):
          names = os.listdir(path)
          for name in names:
            filepath = os.path.join(path,name)
            mode = os.stat(filepath)[stat.ST_MODE]
            if stat.S_ISDIR(mode):
              traverse(base,filepath)
            elif name.startswith('__') and name.endswith('__.py'):
              # Read python-representation of repository-object
              self.writeLog("[remoteFiles]: read %s"%filepath)
              f = open(filepath,"rb")
              py = f.read()
              f.close()
              # Analyze python-representation of repository-object
              d = {}
              try:
                c = get_class(py)
                d = c.__dict__
              except:
                d['revision'] = self.writeError("[traverse]: can't analyze filepath=%s"%filepath)
              id = d.get('id',name)
              rd = {}
              rd['id'] = id
              rd['filename'] = filepath[len(base)+1:]
              rd['data'] = py
              rd['version'] = d.get("revision",self.getLangFmtDate(os.path.getmtime(filepath),'eng'))
              r[rd['filename']] = rd
              # Read artefacts
              for file in [x for x in names if x != name]:
                artefact = os.path.join(path,file)
                mode = os.stat(artefact)[stat.ST_MODE]
                if not stat.S_ISDIR(mode):
                  self.writeLog("[remoteFiles]: read artefact %s"%artefact)
                  f = open(artefact,"rb")
                  data = f.read()
                  f.close()
                  rd = {}
                  rd['id'] = id
                  rd['filename'] = artefact[len(base)+1:]
                  rd['data'] = data
                  rd['version'] = self.getLangFmtDate(os.path.getmtime(artefact),'eng')
                  r[rd['filename']] = rd
        traverse(basepath,basepath)
      return r


    def readRepository(self, provider):
      self.writeBlock("[readRepository]: provider=%s"%str(provider))
      r = {}
      basepath = self.get_conf_basepath(provider.id)
      if os.path.exists(basepath):
        def traverse(base, path):
          names = os.listdir(path)
          for name in names:
            filepath = os.path.join(path, name)
            mode = os.stat(filepath)[stat.ST_MODE]
            if stat.S_ISDIR(mode):
              traverse(base, filepath)
            elif name.startswith('__') and name.endswith('__.py'):
              # Read python-representation of repository-object
              self.writeBlock("[readRepository]: read %s"%filepath)
              f = open(filepath, "rb")
              py = f.read()
              f.close()
              # Analyze python-representation of repository-object
              d = {}
              try:
                c = get_class(py)
                d = c.__dict__
              except:
                d['revision'] = self.writeError("[readRepository]: ")
              id = d.get('id',name)
              r[id] = {}
              for k in [x for x in d if not x.startswith('__')]:
                v = d[k]
                if inspect.isclass(v):
                  dd = v.__dict__
                  v = []
                  for kk in [x for x in dd if not x.startswith('__')]:
                    vv = dd[kk]
                    # Try to read artefact.
                    if 'id' in vv:
                      fileprefix = vv['id'].split('/')[-1]
                      for file in [x for x in names if x==fileprefix or x.startswith('%s.'%fileprefix)]:
                        artefact = os.path.join(path, file)
                        self.writeBlock("[readRepository]: read artefact %s"%artefact)
                        f = open(artefact, "rb")
                        data = f.read()
                        f.close()
                        if artefact.endswith('.zpt') and type(data) is str:
                          data = unicode(data,'utf-8')
                        vv['data'] = data
                        break
                    v.append((py.find('\t\t%s ='%kk), vv))
                  v.sort()
                  v = [x[1] for x in v]
                r[id][k] = v
        traverse(basepath, basepath)
      return r


    """
    Commit ZODB to repository.
    """
    def commitChanges(self, ids):
      self.writeBlock("[commitChanges]: ids=%s"%str(ids))
      standard.triggerEvent(self,'beforeCommitRepositoryEvt')
      success = []
      failure = []
      for provider_id in list(set(map(lambda x:x.split(':')[0],ids))):
        provider = getattr(self,provider_id)
        for id in list(set(map(lambda x:x.split(':')[1],filter(lambda x:x.split(':')[0]==provider_id,ids)))):
          try:
            # Read local-files from provider.
            files = self.localFiles(provider,[id])
            # Recreate folder.
            basepath = self.get_conf_basepath(provider.id)
            if os.path.exists(basepath):
              for name in os.listdir(basepath):
                filepath = os.path.join(basepath,name)
                mode = os.stat(filepath)[stat.ST_MODE]
                if stat.S_ISDIR(mode) and name == id:
                  self.writeBlock("[commitChanges]: clear dir %s"%filepath)
                  dir = map(lambda x:os.path.join(filepath,x),os.listdir(filepath))
                  dir = filter(lambda x:not stat.S_ISDIR(os.stat(x)[stat.ST_MODE]),dir)
                  map(lambda x:_fileutil.remove(x),dir)
                elif not stat.S_ISDIR(mode) and name == '%s.py'%id:
                  self.writeBlock("[commitChanges]: remove file %s"%filepath)
                  _fileutil.remove(filepath)
            # Write files.
            for file in files:
              filepath = os.path.join(basepath,file)
              folder = filepath[:filepath.rfind(os.path.sep)]
              if not os.path.exists(folder):
                self.writeBlock("[commitChanges]: create folder %s"%folder)
                _fileutil.mkDir(folder)
              self.writeBlock("[commitChanges]: write %s"%filepath)
              data = files[file]['data']
              if data is not None:
                f = open(filepath,"wb")
                f.write(data)
                f.close()
              else:
                failure.append('%s is None'%file)
            success.append(id)
          except:
            standard.writeError(self,"[commitChanges]: can't %s"%id)
            failure.append(id)
      standard.triggerEvent(self,'afterCommitRepositoryEvt')
      return success,failure

    """
    Update ZODB from repository.
    """
    def updateChanges(self, ids, override=False):
      self.writeBlock("[updateChanges]: ids=%s"%str(ids))
      standard.triggerEvent(self,'beforeUpdateRepositoryEvt')
      success = []
      failure = []
      repositories = {}
      for i in ids:
        # Initialize.
        provider_id = i[:i.find(':')]
        id = i[i.find(':')+1:]
        provider = getattr(self,provider_id)
        # Read repositories for provider.
        if not repositories.has_key(provider_id):
          repositories[provider_id] = self.readRepository(provider)
        repository = repositories[provider_id]
        # Update.
        try:
          r = repository[id]
          provider.updateRepository(r)
          success.append(id)
        except:
          standard.writeError(self,"[updateChanges]: can't %s"%id)
          failure.append(id)
      standard.triggerEvent(self,'afterUpdateRepositoryEvt')
      return success,failure


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSRepositoryManager.manage_change:
    
    Change.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def manage_change(self, btn, lang, REQUEST=None, RESPONSE=None):
      """ ZMSRepositoryManager.manage_change """
      message = ''
      error_message = ''
      
      if btn == 'save':
        self.auto_update = REQUEST.get('auto_update','')!=''
        self.last_update = self.parseLangFmtDate(REQUEST.get('last_update',''))
        self.ignore_orphans = REQUEST.get('ignore_orphans','')!=''
        self.setConfProperty('ZMS.conf.path',REQUEST.get('basepath',''))
        self.update_direction = REQUEST.get('update_direction','Loading')
        message = self.getZMILangStr('MSG_CHANGED')
      
      elif btn == 'commit':
        success,failure = self.commitChanges(REQUEST.get('ids',[]))
        message = self.getZMILangStr('MSG_EXPORTED')%('<em>%s</em>'%', '.join(success))
        if failure:
          error_message = '<em>%s</em>'%', '.join(failure)
      
      elif btn in ['override','update']:
        success,failure = self.updateChanges(REQUEST.get('ids',[]),btn=='override')
        message = self.getZMILangStr('MSG_IMPORTED')%('<em>%s</em>'%', '.join(success))
        if failure:
          error_message = '<em>%s</em>'%', '.join(failure)
      
      # Return with message.
      target = standard.url_append_params('manage_main',{'lang':lang})
      if message:
        target = standard.url_append_params(target,{'manage_tabs_message':message})
      if error_message:
        target = standard.url_append_params(target,{'manage_tabs_error_message':error_message})
      return RESPONSE.redirect(target)

################################################################################
