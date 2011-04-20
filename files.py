#!/usr/bin/env python
# encoding: utf-8

import os
import re
import tempfile
import logging
try: import simplejson as json
except ImportError: import json

class FileModel(object):
    def __init__(self, client):
        self.client = client
    
    def getPath(self, path):
        """docstring for getPath"""
        path = "/%s" % path
        resp = self.client.metadata("dropbox", path)
        logging.info("%s , %s" % (resp.data, resp.status))
        if 'is_dir' in resp.data and resp.data['is_dir']:
            t = 'index'
            ret = self.listDir(resp)
        elif 'mime_type' in resp.data and resp.data['mime_type'].split('/')[0] == 'text':
            #logging.info(path)
            t = 'text'
            ret = self.getFile(path[1:])
        elif 'error' in resp.data and resp.status == 404:
            t = 'new'
            ret = self.getFile(path[1:])
        return (t, ret)
    
    def getFile(self, name):
        (path, name) = name.rsplit('/',1) if '/' in name else ('', name)
        #logging.info("%s / %s" % (path, name))
        return dropBoxFile(name, path, self.client)
    
    def listDir(self,resp):
        dirlist = {}
        dirlist['files'] = [i['path'][1:] for i in filter(lambda x: 'mime_type' in x and x['mime_type'].split('/')[0] == 'text', resp.data['contents'])]
        dirlist['dirs'] = [i['path'][1:] for i in filter(lambda x: x['is_dir'], resp.data['contents'])]
        return dirlist

class dropBoxFile( object ):
    def __init__(self, name, sdir,client):
        self.name = name
        self.dir = '/%s' % sdir if sdir else ''
        self.path = "%s/%s" % (self.dir, self.name)
        self.client = client
        self.content = ""

    def read(self):
        self.handle = self.client.get_file("dropbox", self.path)
        self.content = self.handle.read()
        self.handle.close()
        self.__addLinks()
        return self.content

    def test(self):
        self.handle = self.client.get_file("dropbox", self.path)
        return dir(self.handle)

    def write(self,content):
        self.content = content
        self.__preSave()
        self.__stripLinks()
        self.handle = tempfile.SpooledTemporaryFile()
        self.handle.name = self.name
        self.handle.write(self.content.encode('ascii','replace'))
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
        return self.__success("Renamed",{'oldURL':oldName,'newURL':newName,'newName':self.name, 'newDir':self.dir})

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
