import os
import platform
import os.path
from urllib.parse import urlparse, urljoin, unquote
from pathlib import Path

import hashlib


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
       
