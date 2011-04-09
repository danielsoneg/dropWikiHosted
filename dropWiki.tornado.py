#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.escape
import os
from tornado.options import define, options

from db import SQLite as db

from dropbox import auth, client
try: import simplejson as json
except ImportError: import json
import files

import logging

Files = files.FileModel()

define("port", default=8080, help="run on the given port", type=int)

Users = db.userDB() 

class dbAuth(object):
    """docstring for dbAuth"""
    def __init__(self):
        super(dbAuth, self).__init__()
        config = auth.Authenticator.load_config("config/config.ini")
        addconfig =  auth.Authenticator.load_config("config/apikeys.ini")
        config.update(addconfig)
        self.dba = auth.Authenticator(config)
        self.tokens = {}
        self.user_tokens = {}

Auth = dbAuth()    

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class ClassName(object):
    """docstring for ClassName"""
    def __init__(self, arg):
        self.arg = arg
        

class LoginHandler(BaseHandler):    
    """docstring for LoginHandler"""
    def get(self):
        if self.get_argument('oauth_token',False):
            self.setAccess()
        else:
            self.getAccess()
        
    def getAccess(self):
        userToken = Auth.dba.obtain_request_token()
        Auth.tokens[userToken.key] = userToken
        sentpath = self.get_argument('next','/')
        self.set_secure_cookie('destpath',sentpath) 
        userAuthURL= Auth.dba.build_authorize_url(userToken,'http://localhost:8080/login')
        self.redirect(userAuthURL)
        pass
    
    def setAccess(self):
        uid = self.get_argument('uid')
        token = Auth.tokens[self.get_argument('oauth_token')]
        oauth_token = Auth.dba.obtain_access_token(token,'')
        Auth.user_tokens[uid] = oauth_token
        dbc = client.DropboxClient(Auth.dba.config['server'], Auth.dba.config['content_server'], Auth.dba.config['port'], Auth.dba, oauth_token)
        email = dbc.account_info().data['email']
        Users.addUser(uid,oauth_token,email)
        self.set_secure_cookie("user", uid)
        dest = self.get_secure_cookie('destpath')
        self.set_secure_cookie('destpath','')
        self.redirect(dest)

class LogoutHandler(BaseHandler):    
    """docstring for LoginHandler"""
    def get(self):
        
        self.clear_all_cookies()
        self.render('templates/blank.html', title='Logged Out', message="You've been logged out!")

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def prepare(self):
        if self.current_user not in Auth.user_tokens:
            self.set_secure_cookie("user", '')
            self.redirect("/login?next=%s"% self.request.full_url())
        oauth_token = Auth.user_tokens[self.current_user]
        self.dbc = client.DropboxClient(Auth.dba.config['server'], Auth.dba.config['content_server'], Auth.dba.config['port'], Auth.dba, oauth_token)
        self.clear_cookie('destpath') 

        
    def __preflight(self, path):
        """Catch-all function to fix paths before we hand them off"""
        path = path.replace('%20',' ')
        return path
        
    def get(self,path):
        npath = self.__preflight(path)
        (t, ret) = Files.getPath(npath, self.dbc)
        getattr(self, 'get_%s' % t)(ret)
        
    def get_index(self, flist):
        self.render("templates/index.html", title="Hello", dirs=flist['dirs'], files=flist['files'])
        #self.render("templates/blank.html", title="Hello", message="Hi there")
    
    def get_text(self, f):
        self.render('templates/page.html', title=f.name, text=f.read())

    
    def get_raw(self, resp):
        self.render("templates/blank.html", title="RAW", message=resp)
    
    def get_go(self, url):
        """docstring for go"""
        self.redirect(url)
        pass
    
    def post(self, path):
        if path == "": 
            raise tornado.web.HTTPError(400)
        try: 
            action = self.get_argument('action')
        except:
            raise tornado.web.HTTPError(400)
        if hasattr(self, 'post_%s' % action):
            status = getattr(self, 'post_%s' %action)(path)
            self.write(status)
        else:
            raise tornado.web.HTTPError(400)
    
    def post_write(self,path):
        content = self.get_argument('text')
        content = tornado.escape.xhtml_unescape(content)
        f = Files.getFile(path,self.dbc)
        status = f.write(content)
        return status
        
    def post_rename(self,path):
        newName = self.get_argument('name')
        f = Files.getFile(path,self.dbc)
        status = f.rename(newName)
        return status
    

def main():
    tornado.options.parse_command_line()
    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
        "cookie_secret": "TmV2ZXJHZXRNZUx1Y2t5Q2hhcm1z",
        "login_url": "/login",
        "debug": "true",
    }
    application = tornado.web.Application([
        (r"/login", LoginHandler),
        (r'/logout', LogoutHandler),
        (r"/(.*?)", MainHandler),
    ],**settings)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()