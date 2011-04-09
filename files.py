#!/usr/bin/env python
# encoding: utf-8

import os
import re
import tempfile
import logging
from dropbox import auth, client
try: import simplejson as json
except ImportError: import json

class FileModel(object):
    def __init__(self, path='../'):
        self.dir = path
        
    def getPath(self, path,client):
        """docstring for getPath"""
        self.client = client #convenience
        t = ''
        path = "/%s" % path
        resp = client.metadata("dropbox", path)
        if resp.data['is_dir']:
            t = 'index'
            ret = self.listDir(resp)
        elif resp.data['mime_type'] == 'text/plain':
            t = 'text'
            ret = self.getFile(path[1:],client)
        else:
            t = 'raw'
            ret = resp.data
        return (t, ret)
    
    def getFile(self, name, client):
        path, name = name.rsplit('/',1)
        f = dropBoxFile(name, path, client)
        return f
    
    def listDir(self,resp):
        data = resp.data
        dirlist = {}
        dirlist['files'] = [i['path'][1:] for i in filter(lambda x: 'mime_type' in x and x['mime_type'] == 'text/plain', data['contents'])]
        dirlist['dirs'] = [i['path'][1:] for i in filter(lambda x: x['is_dir'], data['contents'])]
        return dirlist


class FileObject(object):
    def __init__(self, name, sdir,items):
        """docstring for __init__"""
        self.name    = name
        self.items   = items
        self.dir     = sdir
        self.path    = "%s/%s.txt" % (self.dir, self.name)
        self.content = ""
        self.handle  = False
    
    # Main Commands
    def read(self):
        if self.name in self.items:
            self.__existing()
        else:
            self.__new()
        return self.content
    
    def write(self, content):
        #return self._error("Error Test");
        if content == self.content:
            return self.__success(self.content)
        else:
            self.content = content
            self.__preSave()
            self.__stripLinks()
            self.handle = open(self.path,'w')
            try:
                self.handle.write(self.content)
            except OSError, e:
                return self.__error("Could not write file")
            self.handle.close()
            self.__addLinks()
            return self.__success(self.content)
    
    def rename(self, newName):
        newName = newName.replace('../','').replace('/','');
        newPath = "%s/%s.txt" % (self.dir, newName)
        try:
            os.rename(self.path, newPath)
        except OSError, e:
            return self.__error("Could not rename file! %s" % e)
        oldName = self.name
        self.name = newName
        self.path = newPath
        return self.__success("Renamed",{'oldURL':oldName,'newURL':newName});
    
    # Helpers
    def __existing(self):
        if os.path.isfile(self.path):
            self.handle = open(self.path)
            self.content = self.handle.read()
            self.handle.close()
            self.__addLinks()
            self.handle.close()
    
    def __new(self):
        self.content=""
    
    def __preSave(self):
        """docstring for _preSave"""
        content = self.content
        content = content.replace('<br/>', '\n')
        content = content.replace('<div><br>', '\n')
        content = content.replace('<br>', '\n')
        content = content.replace('</div><div>','\n')
        content = content.replace('<div>','\n')
        content = content.replace('</div>','')
        content = reUnspan.sub("\\1", content)
        self.content = content
    
    # Link Handling
    def __addLinks(self):
        self.__stripLinks()
        self.__webLinks()
        self.__pageLinks()
    
    def __stripLinks(self):
        self.content = reUnlink.sub(self.__stripLinks_linkType, self.content)
    
    def __stripLinks_linkType(self, link):
        if link.group(1).startswith('http'):
            return link.group(2)
        else:
            return "`%s`" % link.group(2)
    
    def __pageLinks(self):
        self.content = reLink.sub('<a href="\\1">\\1</a>', self.content,0)
    
    def __webLinks(self):
        self.content = reHref.sub(self.__webLinks_fixHref, self.content, 0)
    
    def __webLinks_fixHref(self, link):
        url = link.group(0)
        href = url
        if not url.startswith('http'):
            href = "http://%s" % url
        return '<a href="%s">%s</a>' % (href, url)
    
    #Returns
    def __error(self,message,code={}):
        code['Code'] = 0
        code['Message'] = message
        return json.dumps(code)
    
    def __success(self,message,code={}):
        code['Code'] = 1
        code['Message'] = message
        return json.dumps(code)
    


class dropBoxFile( object ):
    def __init__(self, name, sdir,client):
        self.name = name
        self.dir = '/%s' % sdir if sdir else ''
        self.path = "%s/%s" % (self.dir, self.name)
        self.client = client
        self.content = ""

    def read(self):
        self.handle = self.client.get_file("dropbox", self.path)
        content = self.handle.read()
        self.handle.close()
        return content

    def test(self):
        self.handle = self.client.get_file("dropbox", self.path)
        return dir(self.handle)

    def write(self,content):
        self.content = content
        self.__preSave()
        self.__stripLinks()
        self.handle = tempfile.SpooledTemporaryFile()
        self.handle.name = self.name
        self.handle.write(self.content)
        self.handle.seek(0)
        self.client.put_file('dropbox', self.dir, self.handle)
        self.handle.close()
        self.__addLinks()
        return self.__success(self.content)

    def rename(self,newName):
        self.client.file_move('dropbox', self.path, newName)
        oldName = self.path
        self.path = newName
        self.dir, self.name = self.path.rsplit('/',1)
        return self.__success("Renamed",{'oldURL':oldName,'newURL':newName,'newName':self.name})

    def __preSave(self):
        """docstring for _preSave"""
        content = self.content
        content = content.replace('<meta charset="utf-8">','')
        content = content.replace('<br/>', '\n')
        content = content.replace('<div><br>', '\n')
        content = content.replace('<br>', '\n')
        content = content.replace('</div><div>','\n')
        content = content.replace('<div>','\n')
        content = content.replace('</div>','')
        content = reUnspan.sub("\\1", content)
        self.content = content

    # Link Handling
    def __addLinks(self):
        self.__stripLinks()
        self.__webLinks()
        self.__pageLinks()

    def __stripLinks(self):
        self.content = reUnlink.sub(self.__stripLinks_linkType, self.content)

    def __stripLinks_linkType(self, link):
        if link.group(1).startswith('http'):
            return link.group(2)
        else:
            return "`%s`" % link.group(2)

    def __pageLinks(self):
        self.content = reLink.sub('<a href="\\1">\\1</a>', self.content,0)

    def __webLinks(self):
        self.content = reHref.sub(self.__webLinks_fixHref, self.content, 0)

    def __webLinks_fixHref(self, link):
        url = link.group(0)
        href = url
        if not url.startswith('http'):
            href = "http://%s" % url
        return '<a href="%s">%s</a>' % (href, url)


    def __success(self,message,code={}):
        code['Code'] = 1
        code['Message'] = message
        return json.dumps(code)



reLink   = re.compile(r'`(.*?)`', re.U)
reUnlink = re.compile(r'<a href="(.*?)">(.*?)</a>', re.U)
reUnspan = re.compile(r'<span .*?>(.*?)</span>', re.MULTILINE)
reHref   = re.compile(r'''(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''', re.U)