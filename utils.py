import os
import os.path
from urllib.parse import urlparse, urljoin, unquote
from pathlib import Path

import hashlib


# Calculates sha256 checksum for textual data.
# Cuts it in sizes of 4K and calculates sha256
# TODO: Not yet used.           
def pageContentHash( txt, chnunkSize=4096 ):
        
       chunks = [txt[i:i+chnunkSize] for i in range(0, len(txt), chnunkSize)]
       sha256Hash = hashlib.sha256()
       for c in chunks:
           sha256Hash.update( str.encode(c) )

       return(sha256Hash.hexdigest()) 



def urlToFilename( root, u ):
                
            parsedUrl = urlparse(unquote(u))
            prefix = root + '/' + parsedUrl.netloc
            if os.path.splitext( os.path.basename(parsedUrl.path))[-1].lower() != '':
               print( os.path.splitext( os.path.basename(parsedUrl.path))[-1].lower() )
               return(prefix + parsedUrl.path)
            else:
               qParams =  parsedUrl.query.replace('&', 'X').replace('!', 'X').replace('@','X') 
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

