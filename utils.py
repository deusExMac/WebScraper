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
    if re.search('(?i)(text?|rss\+xml)', contentType) is None:
       return(False)

    return(True)  




def isHTML(contentType):
    pass


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
        cookieList.append( ck + '=' + d[ck] ) 
    
    return( ';'.join(cookieList) )
    
              


