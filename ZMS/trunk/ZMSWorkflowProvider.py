################################################################################
# ZMSWorkflowProvider.py
#
# $Id:$
# $Name:$
# $Author:$
# $Revision:$
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
from zope.interface import implements
from App.special_dtml import HTMLFile
import copy
import time
import urllib
# Product Imports.
import IZMSWorkflowProvider, ZMSWorkflowActivitiesManager, ZMSWorkflowTransitionsManager
import ZMSItem
import _fileutil
import _versionmanager


"""
################################################################################
#
#   XML IM/EXPORT
#
################################################################################
"""

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
ZMSWorkflowProvider.initConf:
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def initConf(self, filename, REQUEST):
  xmlfile = open(_fileutil.getOSPath(filename),'rb')
  importXml(self, xmlfile, REQUEST)
  # Return filename.
  return filename

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
ZMSWorkflowProvider.importXml
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def importXml(self, xml, REQUEST):
  ids = map(lambda x: self.activities[x*2], range(len(self.activities)/2))
  for id in ids:
    self.delItem(id,'activities')
  ids = map(lambda x: self.transitions[x*2], range(len(self.transitions)/2))
  for id in ids:
    self.delItem(id,'transitions')
  v = self.parseXmlString(xml)
  l = v.get('activities',[])
  for li in range(len(l)/2):
    id = l[li*2]
    i = l[li*2+1]
    self.setActivity(id=None,newId=id,newName=i['name'],newIcon=i.get('icon'))
  l = v.get('transitions',[])
  for li in range(len(l)/2):
    id = l[li*2]
    i = l[li*2+1]
    self.setTransition(id=None,newId=id,newName=i['name'],newFrom=i.get('from',[]),newTo=i.get('to',[]),newPerformer=i.get('performer',[]),newDtml=i.get('dtml',''))
  # Roles.
  roles = []
  for transition in self.getTransitions():
    roles = self.concat_list(roles,transition.get('performer',[]))
  for newRole in self.difference_list(roles, self.userdefined_roles()):
    REQUEST.set('newId', newRole)
    lang = REQUEST.get('lang')
    key = 'obj'
    btn = self.getZMILangStr('BTN_INSERT')
    self.manage_roleProperties(btn, key, lang, REQUEST)

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
ZMSWorkflowProvider.exportXml
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def exportXml(self, REQUEST, RESPONSE):
  value = {}
  value['activities'] = map(lambda x: self.getActivity(x),self.getActivityIds())
  value['transitions'] = map(lambda x: self.getTransition(x),self.getTransitionIds())
  export = self.getXmlHeader() + self.toXmlString(value,1)
  content_type = 'text/xml; charset=utf-8'
  filename = 'workflow.xml'
  RESPONSE.setHeader('Content-Type',content_type)
  RESPONSE.setHeader('Content-Disposition','inline;filename=%s'%filename)
  return export


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
class ZMSWorkflowProvider(
        ZMSItem.ZMSItem,
        ZMSWorkflowActivitiesManager.ZMSWorkflowActivitiesManager,
        ZMSWorkflowTransitionsManager.ZMSWorkflowTransitionsManager):
    implements(IZMSWorkflowProvider.IZMSWorkflowProvider)

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Properties
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    meta_type = 'ZMSWorkflowProvider'
    icon = "misc_/zms/ZMSWorkflowProvider.png"

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Options
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    manage_options_default_action = '../manage_customize'
    def manage_options(self):
      return map( lambda x: self.operator_setitem( x, 'action', '../'+x['action']), copy.deepcopy(self.aq_parent.manage_options))

    manage_sub_options = (
    {'label': 'TAB_WORKFLOW','action': 'manage_main'},
    )

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Interface
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    manage = manage_main = HTMLFile('dtml/ZMSWorkflowProvider/manage_main', globals())

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Permissions
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    __administratorPermissions__ = (
        'manage_main',
        'manage_changeWorkflow',
        'manage_changeActivities',
        'manage_changeTransitions',
        )
    __ac_permissions__=(
        ('ZMS Administrator', __administratorPermissions__),
        )


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.__init__: 
    
    Constructor.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def __init__(self, autocommit=1, nodes=['{$}'], activities=[], transitions=[]):
      self.id = 'workflow_manager'
      self.autocommit = autocommit
      self.nodes = nodes
      self.activities = []
      self.transitions = []
      l = activities
      for li in range(len(l)/2):
        id = l[li*2]
        i = l[li*2+1]
        self.setActivity(id=None,newId=id,newName=i['name'],newIcon=i.get('icon'))
      l = transitions
      for li in range(len(l)/2):
        id = l[li*2]
        i = l[li*2+1]
        self.setTransition(id=None,newId=id,newName=i['name'],newFrom=i.get('from',[]),newTo=i.get('to',[]),newPerformer=i.get('performer',[]),newDtml=i.get('dtml',''))


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.getAutocommit
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getAutocommit(self):
      return self.autocommit


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.getNodes
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getNodes(self):
      return self.nodes


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.delItem
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def delItem(self, id, key):
      obs = getattr(self,key,[])
      # Update attribute.
      if id in obs:
        i = obs.index(id)
        ob = obs[i+1]
        for obj_id in [id,'%s.icon'%id]:
          if obj_id in self.objectIds():
            self.manage_delObjects([obj_id])
        del obs[i] 
        del obs[i] 
      # Update attribute.
      setattr(self,key,copy.copy(obs))
      # Return with empty id.
      return ''


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.moveItem
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def moveItem(self, id, pos, key):
      obs = getattr(self,key,[])
      # Move.
      i = obs.index(id)
      id = obs[i] 
      values = obs[i+1]
      del obs[i] 
      del obs[i] 
      obs.insert(pos*2,values)
      obs.insert(pos*2,id)
      # Update attribute.
      setattr(self,key,copy.copy(obs))


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.doAutocommit:
    
    Auto-Commit ZMS-tree.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def doAutocommit(self, lang, REQUEST):
      _versionmanager.doAutocommit(self,REQUEST)


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.writeProtocol
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def writeProtocol(self, entry):
      if len(filter(lambda x: x.id()=='protocol.txt', self.objectValues(['File'])))==0:
        self.manage_addFile(id='protocol.txt',file='',title='')
      file = filter(lambda x: x.id()=='protocol.txt', self.objectValues(['File']))[0]
      file.manage_edit(title=file.title,data=file.data+'\n'+entry)

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.manage_changeWorkflow:
    
    Chang workflow.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def manage_changeWorkflow(self, lang, key='', btn='', REQUEST=None, RESPONSE=None):
      """ ZMSWorkflowProvider.manage_changeWorkflow """
      message = ''
      
      # Active.
      # -------
      if key == 'custom' and btn == self.getZMILangStr('BTN_SAVE'):
        # Autocommit & Nodes.
        old_autocommit = self.autocommit
        new_autocommit = REQUEST.get('workflow',0) == 0
        self.autocommit = new_autocommit
        self.nodes = self.string_list(REQUEST.get('nodes',''))
        if old_autocommit == 0 and new_autocommit == 1:
          self.doAutocommit(lang,REQUEST)
        message = self.getZMILangStr('MSG_CHANGED')
      
      # Export.
      # -------
      elif key == 'export' and btn == self.getZMILangStr('BTN_EXPORT'):
        return exportXml(self, REQUEST, RESPONSE)
      
      # Import.
      # -------
      elif key == 'import' and btn == self.getZMILangStr('BTN_IMPORT'):
        f = REQUEST['file']
        if f:
          filename = f.filename
          importXml(self, xml=f, REQUEST=REQUEST)
        else:
          filename = REQUEST.get('init')
          filename = initConf(self, filename, REQUEST)
        message = self.getZMILangStr('MSG_IMPORTED')%('<i>%s</i>'%f.filename)
      
      # Return with message.
      message = urllib.quote(message)
      return RESPONSE.redirect('manage_main?lang=%s&manage_tabs_message=%s#_%s'%(lang,message,key))

################################################################################
