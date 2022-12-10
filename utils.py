import os
import os.path
import platform
import psutil
import configparser

from urllib.parse import urlparse, urljoin, unquote
from pathlib import Path
import requests

import re

#import codecs
#import chardet

import hashlib
import http.cookies
import tldextract






#
# Takes as input a variable length list of arguments,
# transforms them into strings and prints them out as
# one message in the same order as given.
#
# Function to be used in inline debug messages.
def toString( *args ):
    try:   
       lst = [str(i) for i in args]
    except Exception as toStrEx:
           return( '[ERROR] ' + str(toStrEx) )
       
    return( ''.join(lst) )   




# Calculates sha256 checksum for textual data.
# Cuts it in sizes of 4K and calculates sha256
# TODO: Not yet used.           
def txtHash( txt, chnunkSize=4096 ):
        
       chunks = [txt[i:i+chnunkSize] for i in range(0, len(txt), chnunkSize)]
       sha256Hash = hashlib.sha256()
       for c in chunks:
           sha256Hash.update( str.encode(c) )

       return(sha256Hash.hexdigest()) 


# Calculates sha256 checksum for binary data.
# Cuts it in sizes of 4K and calculates sha256
# TODO: Not yet used.           
def byteHash(byteArray, chnunkSize=4096):
       chunks = [byteArray[i:i+chnunkSize] for i in range(0, len(byteArray), chnunkSize)]
       sha256Hash = hashlib.sha256()
       for c in chunks:
           sha256Hash.update( c )

       return(sha256Hash.hexdigest()) 




def canonicalURL( u ):
          parsedURL =  urlparse(unquote(u))  
          canonURL = parsedURL.scheme + '://' + parsedURL.netloc
    
          canonURL +=  parsedURL.path
          if parsedURL.query != '':
             canonURL = canonURL + '?' + parsedURL.query

          return( canonURL )




       

# TODO: Replace characters and create directories
#       Also, enforce a maximum file name length. 
def urlToFilename( root, u ):
                
            parsedUrl = urlparse(unquote(u))
            if not root.endswith('/'):
               prefix = root + '/' + parsedUrl.netloc
            else:
               prefix = root +  parsedUrl.netloc

            # split path in name and extension tuple   
            if os.path.splitext( os.path.basename(parsedUrl.path))[-1].lower() != '':
               # TODO: Remove next line 
               #print( os.path.splitext( os.path.basename(parsedUrl.path))[-1].lower() )
               return(prefix + parsedUrl.path)
            else:
               qParams =  parsedUrl.query.replace('&', 'X').replace('!', 'X').replace('@','X').replace("/", 'oXo') 
               if parsedUrl.path.endswith('/'):
                  if qParams == '':
                     return(prefix + parsedUrl.path + 'index.html' )
                  else:
                     return(prefix + parsedUrl.path + 'X' + qParams+'-index.html' )
               else:
                  if qParams == '':
                     return(prefix + parsedUrl.path + '/index.html' )
                  else:
                     return(prefix + parsedUrl.path + 'X' + qParams+'-index.html' ) 



def urlToPlainFilename( root='', namePrefix='', u='' ):
       
    toReplace = {'/': '-', '&': '-','|': '-', '@':'-', '\\':'-', '*':'-', '<':'-', '>':'-', ':':'-', '?':'-', '=':'-'}
    
    if root=='' or root.endswith('/'):
       return( root + namePrefix + u.translate(str.maketrans(toReplace)) )
    else:
       return( root + '/' +  namePrefix + u.translate(str.maketrans(toReplace)) )    
    



# TODO: change this to use regular expressions.
def isText(contentType):             
    textCT = ['text/html', 'text/css', 'text/csv', 'text/javascript', 'text/plain ', 'text/xml', 'application/rss+xml']
    #print("\tChecking", contentType)

    # Checks are done in this way becuse content types
    # may have additional fields. E.g. text/html; charset=utf-8
    for ct in textCT:
        if ct in contentType.lower():  
           return(True)
              
    return(False)



def ctIsText(contentType):
    if re.search('(?i)(text/?|rss\+xml)', contentType) is None:
       return(False)

    return(True)  



# mime-type strings based on this: https://www.iana.org/assignments/media-types/media-types.xhtml
def isHTML(contentType):
    if re.search('(?i)text/html?', contentType) is None:
       return(False)

    return(True)  


def isBinary(contentType, ctList):
    pass






def saveWebPageToLocalFile(u, rsp,  m=False, mRoot='.'):
    try:
       targetName = urlToFilename(mRoot, u)
       #print('\t[DEBUG] [mirror] Saving to ', targetName)
       targetName = targetName.replace(':', '').replace('*', '').replace('?', '').replace('<', '').replace('>', '').replace('|', '').replace('"', '').replace("'", '')
       targetDir = os.path.dirname(targetName)
       Path(targetDir).mkdir(parents=True, exist_ok=True)
       #print('\t[DEBUG] Content-type:', rsp.get('Content-Type', '') )
       if isText( rsp.get('Content-Type', '') ):
          #print('\t[DEBUG] Writing text')
          # TODO: What about encoding?
          with open(targetName, 'w', errors='ignore') as f:
               f.write( rsp.text )
       else:
           # TODO: Is this correct???   
           #print('\t[DEBUG] Writing binary')
           r = rsp.getResponse().content
           with open(targetName, 'wb') as f:
                #f.write( rsp.html )
                f.write( r )

       return(True)                  
    except Exception as pcEx:
           print('\tERROR creating directories or creating file ', targetName, str(pcEx))
           return(False)



# Check if file is in UTF-8
# TODO: Testing.
def fileIsUTF8(filename):
    pass
    '''
    try:
       rawdata = open(filename, "r").read()
       result = chardet.detect(rawdata.encode())
       if charenc['encoding'] < 0.30:
          return(False)
        
       return( result['encoding'].lower() == 'utf-8' )
    
    except Exception as fEx: 
       return(False)
    '''   
        
    





def strToBool(s):
       
    if s.lower().strip() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']:
       return(True)

    return(False)




       
def getDomain(url):
    extractedDomain = tldextract.extract(url)  
    return( '.'.join( [extractedDomain.domain, extractedDomain.suffix] ) )


# Get domain as defined in http cookies.
def getCookieDomain(url):
    return( urlparse(url).netloc )   





def getPlatformName():
    return( platform.system() )  



'''       
def isWindows():
    if 'windows' in getPlatformName().lower():
       return(True)
    return(False)



def isMac():
    if 'darwin' in getPlatformName().lower():
       return(True)
    return(False)

def isLinux():
    if 'linux' in getPlatformName().lower():
       return(True)
    return(False)


def isAndroid():
    if 'android' in getPlatformName().lower():
       return(True)
    return(False)




def killProcess( processName ):
    nK = 0 
    for proc in psutil.process_iter():
        # check whether the process name matches
        if proc.name() == processName:
           proc.kill()
           nK += 1

    return(nK)
'''



#####################################
#
# http cookie related stuff
#
#####################################







# This function takes as input one dictionary where each cookie is a key:value pair
# (i.e. in the form of <cookie name>:<cookie value>) and transforms it into
# dictionaries (one for each key:value pair) where each individual cookie has the form { 'name':<cookie name>, 'value':<cookie value> }
# Returns a list of dictionaries, one dict for each cookie.
#
# IMPORTANT! specifying url in cookie is fine i.e. session is recognized.
#            domain in cookie though, is not ok i.e. session is not recognized
def cookiesFromDict( d, url ):

    #print(d)
    cookieList = []
    
    if url is None or url == '' :
       return(cookieList)

    
    
    for k, v in d.items():
        #c = {'name':k, 'value':v, 'domain':getDomain(url) }

        # TODO: Cookies starting with __Secure should have  'secure':True
        c = {'name':k, 'value':v, 'url':url }
        cookieList.append(c)

    return(cookieList)

        
        
    '''
    cParams = {'url':'', 'domain':'', 'path':'', 'expires':'', 'httponly':True, 'secure':True, 'samesite':'None'}
    for k,v in d.items():
        if k in cParams.keys():
           if k.lower() == 'expires':
              cParams[k] = datetime.timestamp(datetime.strptime(v, '%d-%m-%YT%H:%M:%S.000Z'))
           else:   
              cParams[k] = v   

    if cParams['domain'] == '':
       cParams['domain'] = utils.getDomain(url)

    if cParams['url'] == '':
       cParams['url'] = url


    cParams['httponly'] = utils.strToBool(cParams['httponly'])
    cParams['secure'] = utils.strToBool(cParams['secure'])
    
    for k, v in d.items():
        if k in cParams.keys():
           continue
      
        c = cParams.copy()
        c['name'] = k
        c['value'] = v
        cookieList.append(c)
    '''
        

def cookieStringToDict(cs):
    
    cD = {}
    cks = http.cookies.SimpleCookie()
    #print('Loading Cookie:[', cs, ']', sep='')
    cks.load(cs)
    for k, v in cks.items():
        #print('\tAdding ', k)
        cD[k] = v.value

    return( cD )    
    #return( {key: value.value  for key, value in cookie.items()} )


# Take one string of the form <cookie name>=<cookie value> and returns a dictionary
# of the form { 'name':<cookie name>, 'value':<cookie value> }
#
# IMPORTANT! specifying url in cookie is fine i.e. session is recognized.
#            domain in cookie though, is not ok i.e. session is not recognized

def cookiesFromString( s, url ):

    #print('HELLO!!!!')
    cookieList = []
    if url is None or url == '' :
       return(cookieList)
    
    cks = http.cookies.SimpleCookie()
    cks.load(s)
    for k, m in cks.items():
        # SimpleCookie returns a key and a Morsel (m)
        #c ={ 'name':k, 'value':m.value, 'domain': getDomain(url)}
        c ={ 'name':k, 'value':m.value, 'url': url}
        cookieList.append(c)
        
    return(cookieList) 
    


              
# Takes as input a list of strings, whare each string in the form:
#    cookieName1=cookieValue1;cookieName2=cookieValue2;cookieName3=cookieValue3;...
# and returns a list of dictionaries where each dictionary is a cookie in the form
# { 'name':<cookie name>, 'value':<cookie value> }
#
def cookiesFromStringList( strList, url ):
    cList = []
    for idx, c in enumerate(strList):
        cookie = cookieFromString( c, url )
        if cookie is None:
           return(None)   
           #print('Cookie', c, 'has no valid format')
        else:
             cList.append(cookie)               
             
    return(cList)   
        


# TODO: Not tested
def cookieJarFromDict( d, url ):
       
    lst = []
    
    dmn = ''
    if dmn == '':
       dmn = getCookieDomain(url)
       
    for k, v in d.items():
        # TODO: Should this be domain or url???
        #       a url is always passed.
        #print('Adding [', k, '=', v)
        lst.append( k+'='+v + ';domain=' + dmn )   
       
    strCookie = ';\n'.join(lst)
    #print('cookieJar:[', strCookie, ']')
    sCookie = http.cookies.SimpleCookie(strCookie)
    cJar = requests.cookies.RequestsCookieJar()
    cJar.update(sCookie)

    return(cJar)


# Takes a dictionary of key:value
# and turns it into a string of key=value; key=value
# that will be sent to remote host in the Cookie section of the
# request header.
def dictToCookieString(d):
    cookieList = []
    for ck in d.keys():
        # TODO: Should we replace double quotes in cookie names?
        #cookieList.append( ck.replace('"', '') + '=' + d[ck] )
        cookieList.append( ck + '=' + d[ck] )

    return( ';'.join(cookieList) )
    
              



########################################################
#
# General purpose string formatting
# functions for displaying strings on console.
#
########################################################

# 
# Functions f and fL format string messages to be printed
# on the screen as right and left aligned, as the example below:
#
#       .(72/72/72/33.59).(72/72/144/44.39).(72/72/216/46.04).(7
#	2/72/288/47.96).(72/72/360/48.39).(72/72/432/52.74).(72/
#	72/504/52.48).(72/72/576/52.41).(72/72/648/53.91).(72/72
#	/720/53.80).(72/72/792/57.08).(72/72/864/59.74).(72/72/9
#	36/61.53).(72/72/1008/61.32).(72/72/1080/60.90).(72/72/1
#	152/60.10).(72/72/1224/60.30).(72/72/1296/60.34).(72/72/
#	1368/60.19).(72/72/1440/60.03).(72/72/1512/59.44).(72/72
#	/1584/59.75).(72/72/1656/59.59).(72/72/1728/59.24).(72/7    
#
# It can do this for sucessive calls of the function
#
# TODO: Function has not been thoroughly tested. It has been sloppy
#       written and must be optimized. ALSO, do we really need this?
#       Aren't there any Python modules that do a similar job?
#



# Variable clc (Current Line Count).
#
# Important as it keeps the state of the current line in functions
# f() and fL(). I.e. how many chars have already been printed.
# Reset it manually everytime you need formatted
# messages generated by f() or fL()
#
# Used by f() and fL()
# Pls don't remove it or change its initialization value
clc = 0


#
# Format strings, but prints formatted strings on the screen.
# Uses global clc.
#
def f(string,  every=26, prefix='', startOver=False):
    global clc

    if startOver:
       print('')
       clc = 0

       
    rest = every - clc
    if clc == 0:
       print( '\t', prefix, string[ :min(len(string), rest)],  sep='', end='')
    else:
       print(  string[ :min(len(string), rest)],  sep='', end='')

    clc = clc + min(len(string), rest)
    strPos = min(len(string), rest)
    #print('clc=', clc)
    if clc >= every:
       print('')
       clc = 0

    if len(string) <= strPos:
       return
        
       
    # This means that length of string is greater than line length.
    numCompleteLines = len( string[strPos:] ) // every
    lastLineChars = len( string[strPos:] ) % every

    i = strPos
    s = 0
    e = strPos
    for k in range(numCompleteLines):
        s = strPos + k*every
        e = s + every
        print('\t',  prefix, string[s:e],  sep='')

    if lastLineChars == 0:
       clc = 0
    else:   
       print( '\t', prefix, string[e:], sep='', end='')
       clc = len(string[e:])

    return




#
# Format strings, but returns strings in a list.
# Uses global clc.
#
def fL(string,  every=57, prefix='', startOver=False):
    global clc

    lines = []
    if startOver:
       if clc != 0: 
          #print('')
          lines.append('') #add empty string to force newline at beginning
       clc = 0

       
    rest = every - clc
    if clc == 0:
       lines.append( '\t'+ prefix + string[ :min(len(string), rest)] )
    else:
       lines.append(    string[ :min(len(string), rest)]  )

    clc = clc + min(len(string), rest)
    strPos = min(len(string), rest)

    #print('clc=', clc, 'every=', every, 'strPos=', strPos, end='')
    if clc >= every:
       #lines.append('')
       clc = 0

    if len(string) <= strPos:
       #print('[' +'ppp'.join(lines) + ']')
       #print('returning without enter at end', end='')
       if clc==0: 
          return( '\n'.join(lines)+'\n' )
       else:
          return( '\n'.join(lines)) 
        
    
    # This means that length of string is greater than line length.
    numCompleteLines = len( string[strPos:] ) // every
    lastLineChars = len( string[strPos:] ) % every
    #print('numCom=', numCompleteLines, 'lastlineChars=', lastLineChars, end='')
    
    i = strPos
    s = 0
    e = strPos
    for k in range(numCompleteLines):
        s = strPos + k*every
        e = s + every
        lines.append('\t' +  prefix + string[s:e] )

    if lastLineChars == 0:
       #lines.append('\n') 
       clc = 0
       #print(lines)
       return( '\n'.join(lines)+ '\n' )
    else:   
       lines.append( '\t' + prefix + string[e:])
       clc = len(string[e:])
       return( '\n'.join(lines) )




