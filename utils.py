import os
import platform
import os.path
from urllib.parse import urlparse, urljoin, unquote
from pathlib import Path

import hashlib
import http.cookies


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
               print( os.path.splitext( os.path.basename(parsedUrl.path))[-1].lower() )
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



def urlToPlainFilename( root, u ):
       
    toReplace = {'/': '-', '&': '-','|': '-', '@':'-', '\\':'-', '*':'-', '<':'-', '>':'-', ':':'-', '?':'-', '=':'-'}
    
    if root=='' or root.endswith('/'):
       return( root + u.translate(str.maketrans(toReplace)) )
    else:
       return( root + '/' + u.translate(str.maketrans(toReplace)) )    
    



# TODO: change this.
def isText(contentType):             
    textCT = ['text/html', 'text/css', 'text/csv', 'text/javascript', 'text/plain ', 'text/xml', 'application/rss+xml']
    #print("\tChecking", contentType)
    for ct in textCT:
        if ct in contentType.lower():  
           return(True)
              
    return(False)



def saveWebPageToLocalFile(u, rsp,  m=False, mRoot='.'):
    try:
       targetName = urlToFilename(mRoot, u)
       print('\t[DEBUG] [mirror] Saving to ', targetName)
       targetName = targetName.replace(':', '').replace('*', '').replace('?', '').replace('<', '').replace('>', '').replace('|', '').replace('"', '').replace("'", '')
       targetDir = os.path.dirname(targetName)
       Path(targetDir).mkdir(parents=True, exist_ok=True)
       print('\t[DEBUG] Content-type:', rsp.get('Content-Type', '') )
       if isText( rsp.get('Content-Type', '') ):
          print('\t[DEBUG] Writing text')
          # TODO: What about encoding?
          with open(targetName, 'w', errors='ignore') as f:
               f.write( rsp.text )
       else:
           # TODO: Is this correct???   
           print('\t[DEBUG] Writing binary')     
           with open(targetName, 'wb') as f:
                f.write( rsp.html )   

       return(True)                  
    except Exception as pcEx:
           print('\tERROR creating directories or creating file ', targetName, str(pcEx))
           return(False)




def strToBool(s):
       
    if s.lower().strip() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']:
       return(True)

    return(False)




def getDomain(url):
    return(urlparse(url).netloc)


def getPlatformName():
    return( platform.system() )  


       
def isWindows():
    if getPlatformName().lower() == 'windows':
       return(True)
    return(False)



def isMac():
    if getPlatformName().lower() == 'darwin':
       return(True)
    return(False)

def isLinux():
    if getPlatformName().lower() == 'linux':
       return(True)
    return(False)



       

#####################################
#
# http cookie related stuff
#
#####################################




# This function takes as input a dictionary which contains the cookie names
# and values as well as the COMMON cookie parameters like domain, path, expires etc.
# for each cookie.
# The function first separates the parameters from the dict which  is then used to
# configure all cookies.
# Returns a list of dictionaries, one dict for each cookie.
def cookiesFromDict( d, url ):
    
    cookieList = []
    for k, v in d.items():
        c = {'name':k, 'value':v, 'domain':getDomain(url) }
        cookieList.append(c)

    return(cookieList)

        #c['name'] = k
        #c['value'] = v
        
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
        




      
def cookieFromString( s, url ):
    print('String cookie:', s, '\n\n')  
    
    polishedCookie = {'url': url}
    cks = http.cookies.SimpleCookie()
    cks.load(s)
    for k, m in cks.items():
        # SimpleCookie returns a key and a Morsel (m)
        polishedCookie['name'] = k
        polishedCookie['value'] = m.value
        polishedCookie['domain'] = utils.getDomain(url)
        polishedCookie['path'] = m['path']
        polishedCookie['expires'] = ''
        if m['expires'] != '':
           polishedCookie['expires'] = datetime.timestamp(datetime.strptime(m['expires'], '%d-%m-%YT%H:%M:%S.000Z')) 
        polishedCookie['httponly'] = utils.strToBool(m['httponly'])
        polishedCookie['secure'] = utils.strToBool(m['secure'])
        polishedCookie['samesite'] = m['samesite']
        return(polishedCookie) 
    


              
# Takes as input a list of strings, whare each string in the form:
#    cookieName=cookieValue;domain=xxx;path=yyy;expires=zzz etc
# and returns a dictionary for of the cookie with the keys mentioned.
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
        





    
              


