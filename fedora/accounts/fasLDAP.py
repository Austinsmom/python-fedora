#!/usr/bin/python

import ldap

class Server:
    def __init__(self, server='localhost', who='', password=''):
        self.ldapConn = ldap.open(server)
        self.ldapConn.simple_bind_s(who, password)

class Group:
    ''' Group abstraction class '''
    def __init__(self, cn, fedoraGroupOwner, fedoraGroupType, fedoraGroupNeedsSponsor, fedoraGroupUserCanRemove, fedoraGroupJoinMsg):
        self.cn = cn
        self.fedoraGroupOwner = fedoraGroupOwner
        self.fedoraGroupType = fedoraGroupType
        self.fedoraGroupNeedsSponsor = fedoraGroupNeedsSponsor
        self.fedoraGroupUserCanRemove = fedoraGroupUserCanRemove
        self.fedoraGroupJoinMsg = fedoraGroupJoinMsg


class UserGroup:
    ''' Individual User->Group abstraction class '''
    def __init__(self, fedoraRoleApprovalDate, fedoraRoleSponsor, cn, fedoraRoleCreationDate, objectClass, fedoraRoleType, fedoraRoleStatus, fedoraRoleDomain):
        self.fedoraRoleApprovalDate = fedoraRoleApprovalDate
        self.fedoraRoleSponsor = fedoraRoleSponsor
        self.cn = cn
        self.fedoraRoleCreationDate = fedoraRoleCreationDate
        self.objectClass = objectClass
        self.fedoraRoleType = fedoraRoleType
        self.fedoraRoleStatus = fedoraRoleStatus
        self.fedoraRoleDomain = fedoraRoleDomain

class Groups:
    ''' Class contains group information '''
    __userName = None

    @classmethod
    def byUserName(self, cn, includeUnapproved=None, unapprovedOnly=None):
        ''' Return list of groups a certain user is in.  Excludes all non-approved groups'''
        server = Server()
        groups = {}
        if includeUnapproved:
            filter = 'objectClass=FedoraRole'
        elif unapprovedOnly:
            filter = '(&(!(fedoraRoleStatus=approved)) (objectClass=fedoraRole))'
        else:
            filter = '(&(fedoraRoleStatus=approved)(objectClass=FedoraRole))'

        base = 'ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % cn
        groupsDict = search(base, filter)
        for group in groupsDict:
            cn = group[0][1]['cn'][0]
            groups[cn] = UserGroup(
                fedoraRoleApprovalDate = group[0][1]['fedoraRoleApprovalDate'][0],
                fedoraRoleSponsor = group[0][1]['fedoraRoleSponsor'][0],
                cn = group[0][1]['cn'][0],
                fedoraRoleCreationDate = group[0][1]['fedoraRoleCreationDate'][0],
                objectClass = group[0][1]['objectClass'][0],
                fedoraRoleType = group[0][1]['fedoraRoleType'][0],
                fedoraRoleStatus = group[0][1]['fedoraRoleStatus'][0],
                fedoraRoleDomain = group[0][1]['fedoraRoleDomain'][0]
                        )
        self.__userName = cn
        return groups
    
    @classmethod
    def groups(self, searchExpression='*', attributes=[]):
        groups = {}
        filter = 'cn=%s' % (searchExpression)
        base = 'ou=FedoraGroups,dc=fedoraproject,dc=org'
        groupsDict = search(base, filter, attributes)
        if groupsDict:
            for group in groupsDict:
                name = group[0][1]['cn'][0]
                print group
                groups[name] = Group(
                    cn = group[0][1]['cn'][0],
                    fedoraGroupOwner = group[0][1]['fedoraGroupOwner'][0],
                    fedoraGroupType = group[0][1]['fedoraGroupType'][0],
                    fedoraGroupNeedsSponsor = group[0][1]['fedoraGroupNeedsSponsor'][0],
                    fedoraGroupUserCanRemove = group[0][1]['fedoraGroupUserCanRemove'][0],
                    fedoraGroupJoinMsg = group[0][1]['fedoraGroupJoinMsg'][0])
        else:
            return None
        return groups

    @classmethod
    def remove(self, groupName, userName=None):
        if not userName:
            userName = self.__userName
        if groupName in self.byUserName(userName):
            # Probably shouldn't be 'TypeError'
            delete('cn=%s,ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % (groupName, userName))
        else:
            raise TypeError, 'User not in that group'

    @classmethod
    def apply(self, groupName, userName=None):
        ''' Apply for a group '''
        import datetime

        if not userName:
            userName = self.__userName

        if groupName in self.byUserName(userName):
            # Probably shouldn't be 'TypeError'
            raise TypeError, 'Already in that group'
        try:
            self.byGroupName(groupName)
        except TypeError:
            raise TypeError, 'Group "%s" does not exist' % groupName

        dt = datetime.datetime.now()
        now = '%s-%s-%s %s:%s:%s.%s' % (dt.year,
                                        dt.month,
                                        dt.day,
                                        dt.hour,
                                        dt.minute,
                                        dt.second,
                                        dt.microsecond)

        attributes = { 'cn' : groupName,
                    'fedoraRoleApprovaldate' : 'NotApproved',
                    'fedoraRoleCreationDate' : now,
                    'fedoraRoleDomain' : 'None',
                    'fedoraRoleSponsor' : 'None',
                    'fedoraRoleStatus' : 'unapproved',
                    'fedoraRoleType' : 'user',
                    'objectClass' : ('fedoraRole')}

        add('cn=%s,ou=Roles,cn=%s,ou=People,dc=fedoraproject,dc=org' % (groupName, userName), attributes) 


    @classmethod
    def byGroupName(cls, cn, includeUnapproved=None, unapprovedOnly=None):
        self = cls()
        server = Server()
        users = {}
        if includeUnapproved:
            filter = 'cn=%s' % cn
        elif unapprovedOnly:
            filter = '(&(cn=%s) (objectClass=fedoraRole) (!(fedoraRoleStatus=approved)))' % cn
        else:
            filter = '(&(cn=%s) (objectClass=fedoraRole)  (fedoraRoleStatus=approved))' % cn
        base = 'ou=People,dc=fedoraproject,dc=org'
        self.__attributes = ['cn']
        attributes = ['cn']
        usersDict = search(base, filter)
        for user in usersDict:
            userName = user[0][0].split(',')[2].split('=')[1]

            users[userName] = UserGroup(
                fedoraRoleApprovalDate = user[0][1]['fedoraRoleApprovalDate'][0],
                fedoraRoleSponsor = user[0][1]['fedoraRoleSponsor'][0],
                cn = user[0][1]['cn'][0],
                fedoraRoleCreationDate = user[0][1]['fedoraRoleCreationDate'][0],
                objectClass = user[0][1]['objectClass'][0],
                fedoraRoleType = user[0][1]['fedoraRoleType'][0],
                fedoraRoleStatus = user[0][1]['fedoraRoleStatus'][0],
                fedoraRoleDomain = user[0][1]['fedoraRoleDomain'][0]
            )
        return users

class Person:
    ''' information and attributes about users '''
    __base = 'ou=People,dc=fedoraproject,dc=org'
    __server = Server()
    __filter = ''

    def __getattr__(self, attr):
        if attr.startswith('_'):
            print 'GET %s=%s' % (attr, self.__getattr__(attr))
        if attr == 'userName':
            return self.__getattr__('cn')
        try:
            attributes = []
            attributes.append(attr)
            return search(self.__base, self.__filter, attributes)[0][0][1][attr][0]
        except:
            # Should probably raise here.
            return None

    def __setattr__(self, attr, value):
        if attr.startswith('_'):
            return setattr(self.__class__, attr, value)

        base = 'cn=%s,ou=People,dc=fedoraproject,dc=org' % self.__getattr__('cn')
        modify(base, attr, value, self.__getattr__(attr))
        return setattr(self.__class__, attr, value)

    @classmethod
    def users(self, searchExpression='*', findAttr='cn'):
        ''' Returns a list of users '''
        users = []
        filter = '(&(objectClass=top)(%s=%s))' % (findAttr, searchExpression)
        attributes = ['cn']
        usersDict = search(self.__base, filter, attributes)
        if usersDict:
            for user in usersDict:
                users.append(user[0][1]['cn'][0])
        else:
            return None
        return users

    @classmethod
    def byFilter(cls, filter):
        ''' Returns only the first result in the search '''
        self = cls()
        self.__filter = filter
        return self

    @classmethod
    def byUserName(self, cn):
        '''Wrapper for byFilter - search by cn'''
        return self.byFilter('cn=%s' % cn)

    @classmethod
    def auth(self, who, password, ldapServer=None):
        ''' Basic Authentication Module '''
        if not ldapServer:
            s = Server()
            ldapServer = s.ldapConn

        who = 'cn=%s,ou=People,dc=fedoraproject,dc=org' % who
        ldapServer.simple_bind_s(who, password)


    def generatePassword(self,length=14,password=None,salt=''):
        from random import Random
        import sha
        import sha
        from base64 import b64encode
        import sys
    
        secret = {} # contains both hash and password

        if not password:
            rand = Random() 
            password = ''
            # Exclude 0,O and l,1
            righthand = '23456qwertasdfgzxcvbQWERTASDFGZXCVB'
            lefthand = '789yuiophjknmYUIPHJKLNM'
            for i in range(length):
                if i%2:
                    password = password + rand.choice(lefthand)
                else:
                    password = password + rand.choice(righthand)
        
        ctx = sha.new(password)
        ctx.update(salt)
        secret['hash'] = "{SSHA}%s" % b64encode(ctx.digest() + salt)
        secret['pass'] = password

        return secret


class UserAccount:
    def __init__(self):
        self.realName = ''
        self.userName = ''
        self.primaryEmail = ''
        self.groups = []

def delete(base, ldapServer=None):
    ''' Delete target base '''
    if not ldapServer:
        s = Server()
        ldapServer = s.ldapConn

    ldapServer.simple_bind_s('cn=directory manager', 'test')
    ldapServer.delete_s(base)

def add(base, attributes, ldapServer=None):
    ''' Add a new record to LDAP instance '''
    if not ldapServer:
        s = Server()
        ldapServer = s.ldapConn
    attributes=[ (k,v) for k,v in attributes.items() ]

    ldapServer.simple_bind_s('cn=directory manager', 'test')
    ldapServer.add_s(base, attributes)

def modify(base, attribute, new, old=None, ldapServer=None):
    ''' Modify an attribute, requires write access '''
    if old == new:
        print "same"
        return None
    else:
        print "diff %s %s %s" % (attribute, new, old)

    if not ldapServer:
        s = Server()
        ldapServer = s.ldapConn

    from ldap import modlist
    ldapServer.simple_bind_s('cn=directory manager', 'test')


    o = { attribute : old }
    n = { attribute : new }
    print attribute
    print o
    print n
    ldif = modlist.modifyModlist(o, n)
    
    #commit
    ldapServer.modify_s(base, ldif)
    ldapServer.unbind_s()
    
    

def search(base, filter, attributes=None, ldapServer=None):
    if not ldapServer:
            s = Server()
            ldapServer = s.ldapConn
    scope = ldap.SCOPE_SUBTREE
    count = 0
    timeout = 2
    ldapServer.simple_bind_s('cn=directory manager', 'test')
    result_set = []
    try:
        result_id = ldapServer.search(base, scope, filter, attributes)
        while 1:
            result_type, result_data = ldapServer.result(result_id, timeout)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    result_set.append(result_data)
        if len(result_set) == 0:
            print "No results."
            return
    except ldap.LDAPError, e:
        print "Crap: %s" % e
        raise
    ldapServer.unbind_s()

    return result_set