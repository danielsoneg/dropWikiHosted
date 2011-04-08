#!/usr/bin/env python
# encoding: utf-8
"""
userdb.py

Created by Eric Danielson on 2011-03-21.
Copyright (c) 2011 __MyCompanyName__. All rights reserved.
"""

import sys
import os
import unittest
import sqlite3


class userDB(object):
    def __init__(self, f='user.sql'):
        self.file = f
        self.handle = sqlite3.connect(self.file)
        self.cursor = self.handle.cursor()
        self.created = self.__isCreated()
        
    def addUser(self, username, token, email):
        if not self.created:
            self.__create()
        if str(username) != username or str(token) != token: 
            return False
        self.cursor.execute('''insert into users(username,token,email) values(:username,:token,:email)''', {'username':username,'token':token,'email':email})
        if self.cursor.lastrowid == None:
            return False
        else:
            self.handle.commit()
            return True
    
    def getUser(self, username):
        if not self.created:
            return False
        self.cursor.execute('''select token,email from users where username=:username''', {'username':username})
        row = self.cursor.fetchone()
        if not row: 
            return False
        else: return row
    
    def __create(self):
        if self.created: return
        """docstring for create"""
        self.cursor.execute('''create table users(username,token,email);''')
        self.handle.commit()
        self.created = True
    
    def __isCreated(self):
        self.cursor.execute('''SELECT name FROM sqlite_master WHERE name = "users"''')
        return bool(len(self.cursor.fetchall()) == 1)

    
    # Debugging
    def raw(self, command):
        return self.cursor.execute(command)


class userdbTests(unittest.TestCase):
    def setUp(self):
        if os.path.exists('test.sql'): os.remove('test.sql')
        self.users = userDB('test.sql')
    
    def testInit(self):
        self.assertEqual(self.users.file, 'test.sql')
        self.assertNotEqual(self.users.handle, None)
        self.assertNotEqual(self.users.cursor, None)
        self.assertEqual(self.users.created, False)
    
    def testCreate(self):
        self.users._userDB__create()
        self.assertEqual(self.users._userDB__isCreated(),True)
        self.assertEqual(self.users.created,True)
    
    def testAddGetUser(self):
        self.assertEqual(self.users.addUser('Test','Token','token@token.com'), True)
        self.assertEqual(self.users.addUser('Test',False,False),False)
        self.assertEqual(self.users.getUser('Test')[0], u'Token')
    

if __name__ == '__main__':
    unittest.main()