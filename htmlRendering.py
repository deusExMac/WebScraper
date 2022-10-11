import sys
import time
import re
import copy

#from datetime import datetime
#import json
import asyncio
import pyppeteer

from http.cookies import SimpleCookie
from urllib.parse import urlparse, urljoin

import utils
import xRules


async def intercept_network_response2(response):
          # In this example, we only care about HTML responses!
          #if "text/html" in response.headers.get("content-type", ""):
             # Print some info about the responses

             
            
             print('==================================================')
             print("\t\tURL:", response.url)
             
             print("\t\tMethod:", response.request.method)
             print("\t\tResponse status:", response.status)
             print("\t\tResponse headers:", response.headers)
             print("\t\tRequest Headers:", response.request.headers)
             
             print('==================================================')
             

             # Print the content of the response
             #print("Content: ", await response.text())
             # NOTE: Use await response.json() if you want to get the JSON directly



class htmlRenderer:



      def __init__(self):
          self.browser = None
          self.page = None
          self.headers = None
          self.response = None

          # TODO: Check me 
          self.interceptingUrl = ''


          self.cookiesSeen = []
          self.cookieIndex = {}
          
          self.interceptResponses = False
          
          self.waitTime = 1.2 # in seconds
          self.takePageScreenshot = True # in seconds
          self.screenShotStoragePath = './' # Where to store screenshots

          self.debug = False


      # dv: debug value: True or False
      def setDebugMode(self, dv):
          self.debug = dv



      # TODO: Do we need this?
      def getCookie(self, cs):
          pass





      # cs: a set-cookie line from http response
      def addResponseCookie2(self, cs):

          if cs is None or cs == '':
             return

          #cs = cs.replace('\n', ',')  
          cookie = SimpleCookie()
          cookie.load(cs)
                    
          for k, m in cookie.items():
              # add or update
              self.cookieIndex[k] = cs

          #self.cookieIndex[]
          #c=utils.cookieStringToDict(ck)
          #if self.cookieList[c
          #for c in self.cookieList:
          #    pass




      def addResponseCookie(self, cs, url=''):

          if cs is None or cs == '':
             return

          #print('\n++++++++++++++++++++++++++++++++++++++++++')
          #print(cs)
          #print('++++++++++++++++++++++++++++++++++++++++++\n')
          
          cookie = SimpleCookie()
          cookie.load(cs)

          nC = 0
          knList = []
          for k, m in cookie.items():
              # add or update
              self.cookieIndex[k] = {'cookie':cookie, 'source': cs, 'url':url }
              knList.append( k )
              nC += 1

          #print('################### ADDED [', nC, '] COOKIES.', knList)




      def filterCookies(self, targetUrl):
       cookieString = ''
       pUrl = urlparse(targetUrl)
       for k, m in self.cookieIndex.items():
           ck = m['cookie'].get(k)
           if ck['path'] != '':
              if not pUrl.path.startswith(ck['path']):
                 #print('\t\t>>>>Skipping cookie [', k, ']') 
                 continue 

           domain = ''   
           if ck['domain'] != '':
              domain =  ck['domain']
           else:
              domain =  urlparse(m['url']).netloc

           if not domain in pUrl.netloc:
               #print('\t\t>>>>Skipping cookie [', k, ']') 
               continue

           # Seems ok. Append it
           if cookieString == '':
              cookieString =  m['source']
           else:
               cookieString =  cookieString + '\n' + m['source']

       #print('RETURNING', cookieString)
       return( cookieString ) 

    


              
          
      async def intercept_network_response(self, resp):

             # In this example, we only care about responses from specific urls!

             #print('================= INTERCEPTING ========================')
             #print("URL:[", resp.url, '] HTTP Status:[', resp.status,'] LOCATION:[', urljoin( resp.url, resp.headers.get('location', '') ) if 300<=resp.status<400 else 'xxxx', '] COOKIE:', resp.headers.get('set-cookie', 'xxxx') )
             #return
            
             #print('>>>GOT:', 'Response status:', resp.status)
                   
             #if self.interceptingUrl != resp.url:
             #   return


             if 300 <= resp.status  and resp.status < 400:
                self.interceptingUrl =  urljoin( resp.url, resp.headers.get('location') )
                #print('\tIntercepting url set to [', self.interceptingUrl, ']')
             else:
                 if self.interceptingUrl != resp.url:
                    return 

             #print('200 or REDIRECT as response for:', resp.url)
             
             #if not self.interceptResponses:
             #   return
            
             # TODO: Is this correct? 
             
             self.response = resp
             
             
             # is this a redirect request?  
             #if 300 <= resp.status  < 400:
                #print("INTERCEPT: Setting target to [", response.headers.get('location'), "]")
                # This might be a  relative URL. Make it absolute                 
                #self.interceptingUrl =  urljoin( resp.url, resp.headers.get('location', '') )
                #print('>>>Redirect from [', resp.url, '] to [', urljoin( resp.url, resp.headers.get('location', '') ),'] Cookie:[', resp.headers.get('set-cookie', 'xxx'), ']')



             if resp.headers.get('set-cookie', None) is not None:
                # Do we already have this cookie? If not, add it.
                '''
                print('URL:[', resp.url,'] GOT Cookie:', resp.headers.get('set-cookie', None))
                if  resp.headers.get('set-cookie', '') not in self.cookiesSeen:
                    self.cookiesSeen.append( resp.headers.get('set-cookie', None) )
                    print('$$$$$$\n', self.cookiesSeen, '$$$$$\n' )
                '''
                self.addResponseCookie(resp.headers.get('set-cookie', None), resp.url )
             else:
                 # Do we have a cookie from some previous request? If yes
                 # add it to existing response header in order to be returned
                 # to caller.
                 if self.cookieIndex:
                    ckString = self.filterCookies( resp.url )
                    #print('!!!!!!! filterCookies returned:', ckString)
                    if ckString != '':
                       self.response.headers['set-cookie'] = ckString
                       #print('-------------------------------', self.response.headers['set-cookie'] )
                    

             '''       
             print('================INTERCEPT================')
             print("\t\tURL:", resp.url)
             
             print("\t\tMethod:", resp.request.method)
             print("\t\tResponse status:", resp.status)
             print("\t\tResponse headers:", resp.headers)
             print("\t\tRequest Headers:", resp.request.headers)
             
             print('==================================================')
             ''' 
             
             
             
             # NOTE: Use await response.json() if you want to get the JSON directly



  
      def render(self, url='', maxRetries = 3, timeout=5, requestCookies=[], userAgent=None, scrolldown=0, dynamicElements=[]):
          return( asyncio.get_event_loop().run_until_complete(self.fetchUrl(url, maxRetries, timeout, requestCookies, userAgent, scrolldown, dynamicElements)) )




      # TODO: This method needs serious refactoring.
      #       Among others, scrolldown is now obsolete. 
      async def fetchUrl(self, url='', maxRetries = 3, timeout=5, requestCookies=[], userAgent=None, scrolldown=0, dynamicElements=[] ):

       #if self.interceptResponses:
       self.interceptingUrl = url
          
       if self.browser is None:
          print( utils.toString('\t[DEBUG] Creating new BROWSER\n') if self.debug else '', sep='', end=''  )
          # launches a browser in headless mode. Headless means WITHOUT UI.
          self.browser = await pyppeteer.launch()
       else:
            print( utils.toString('\t[DEBUG] Reusing existing BROWSER\n') if self.debug else '', sep='', end='' )
            
       if self.page is None:
          print( utils.toString('\t[DEBUG] Creating new PAGE\n') if self.debug else '', sep='', end=''  )
          self.page = await self.browser.newPage()

          # Uncomment next line if you would like to intercept responses
          if self.interceptResponses:
             print( utils.toString('\t[DEBUG] INITIALIZING interception\n') if self.debug else '', sep='', end=''  ) 
             self.page.on('response', lambda res: asyncio.ensure_future(self.intercept_network_response(res)) )         
       else:
          print( utils.toString('\t[DEBUG] Reusing existing PAGE\n') if self.debug else '', sep='', end='' )
        
       if userAgent is not None:
          await self.page.setUserAgent(userAgent);

       # Set request cookies
       print( utils.toString('\t[DEBUG] Setting request cookies ', requestCookies,'\n') if self.debug else '', sep='', end='' )
       for c in requestCookies:
            #print('[DEBUG] html rendering. Setting cookie', c)
            await self.page.setCookie( c )
            #await asyncio.sleep(self.waitTime/2)

       #print('\t[DEBUG] Loading URL', url)
       await self.page.setViewport( {'width':1920, 'height':1080} )
       await self.page.setJavaScriptEnabled(enabled=True)

       
       numTries = 0
       startTm = time.perf_counter() # Start counting total time.
       while True:

           if numTries >= maxRetries:
              print( utils.toString(f'\t\t[DEBUG] Reached maximum number of retries {maxRetries}. Giving up.\n') if self.debug else '', sep='', end=''     )
              return(None)
            
           try:
              attemptStart = time.perf_counter() # start counting request time
              self.response = await self.page.goto(url, options={'waitUntil':'load', 'timeout': int(timeout * 1000)})
              #self.page.on('response', lambda res: asyncio.ensure_future(intercept_network_response(res)) ) 

              #try:
              #  print('>>> COOKIES:', await self.page.cookies() )  
              #except Exception as feee:
              #    print('ERROR', str(feee))
                  
              attemptEnd = time.perf_counter() 
              break
            
           except Exception as fetchException:
               print( utils.toString('\t\t[DEBUG] (', numTries, ') Excpetion ', str(fetchException), '\n' ) if self.debug else '', sep='', end='' )
               numTries += 1

       
       # TODO: Remove me?
       self.headers = None #origResponse.headers
       
       print( utils.toString('\t\t\t[DEBUG] Successful attempt elapsed:', "{:.3f}".format(attemptEnd  - attemptStart), '\n' ) if self.debug else '', sep='', end='' )       
       print( utils.toString('\t\t\t[DEBUG] Total elapsed:', "{:.3f}".format(time.perf_counter() - startTm), '\n') if self.debug else '', sep='', end='' )    

       
       '''
          if utils.isMac():
               # TODO: Check if .scrollPageDown works also for all other OSs 
               #print('\t\t[DEBUG] MacOS detected') 
               await self.scrollPageDown(self.page)
          else:
               # On windows and linux, PageDown key works
               # Replaced method .down with .press 
               #await self.page._keyboard.press('PageDown')
               await self.scrollPageDown(self.page) # test!
       '''     

       
       


       
       
       # Check if dynamic elements should be executed. If yes, do it.
       # TODO: changed order of operations (was: first scrolling then loading). NOT TESTED!
       '''
       applyDynamicElements = True
       
       if not dynamicElements:
          print( utils.toString('\t[DEBUG] No dynamic element on page to be executed\n') if self.debug else '', end='' ) 
       else:    

          # First element may be a check or checkurl element. See if this is the case.
          # If it is, see the page meets conditions. If not, do not apply dynamic elements
          # to the page.
          elem = dynamicElements[0]
          if elem.dpcType.lower() == 'checkurl':
             print( utils.toString('\t[DEBUG] Found checkurl constraint\n' ) if self.debug else '', end='' )       
             if (elem.dpcFillContent.strip() != '') and (re.search( elem.dpcFillContent, url) is None):
                 print( utils.toString(f'\t[DEBUG] Url {url} does not match constraints. Not applying dynamic elements to page\n' ) if self.debug else '', end='' )
                 applyDynamicElements = False
             
          
       ''' 
       #if applyDynamicElements:

       # Iterate over all dynamic element and first check if they should
       # be applied (based on url pattern) to the page and if so, apply it.
       for de in  dynamicElements:
             
           #if de.dpcType.lower() == 'checkurl':
           #   continue # ignore. Has already been processed.

           # Should the dynamic element be applied to this page?
           # Check url pattern to see if it should be applied.
           # However, we get the current page's url. This is because some
           # dynamic element may have executed a submit and hence the url may have changed.
           currentUrl = await self.page.evaluate("() => window.location.href")
           if (de.dpcURLActivationCondition != '') and (re.search( de.dpcURLActivationCondition, currentUrl) is None):
              print( utils.toString(f'\t[DEBUG] Url {currentUrl} does NOT MATCH dynamic element url pattern. NOT APPLYING\n' ) if self.debug else '', end='' ) 
              continue

           print( utils.toString(f'\t[DEBUG] Url {currentUrl} does MATCH dynamic element url pattern. APPLYING\n' ) if self.debug else '', end='' )   
           await self.executeDynamicElement(self.page, de)
           # This SEEMS to be required.
           # TODO: Investigate closer the execution dynamic of pyppeteer
           await asyncio.sleep(self.waitTime)
       
              
       if self.takePageScreenshot:       
          print( utils.toString('\t[DEBUG] Saving screenshot to file:', utils.urlToPlainFilename('etc/', url), '\n' ) if self.debug else '', end='' )      
          await self.page.screenshot({'path': utils.urlToPlainFilename(self.screenShotStoragePath, url) + '.png' })

       
       content = await self.page.content()
       return( content )




   

      #
      # 
      #
      async def executeDynamicElement(self, pg, dElem):

            if dElem is None:
               return(None)

            print( utils.toString('\t\t[DEBUG] Executing dynamic content: type=',dElem.dpcType, ' element=', dElem.dpcPageElement, '\n') if self.debug else '', sep='', end='')
            print( utils.toString('\t\t[DEBUG] Checking if element [', dElem.dpcPageElement, '] exists.....') if self.debug else '',  sep='', end='')
            if not await self.elementExists(pg, dElem.dpcPageElement):
               print( utils.toString(f'\t\t[DEBUG] Element {dElem.dpcPageElement} does not exist on page. Not dynamic element.\n') if self.debug else '', sep='', end='' )
               return(None) 

            print( utils.toString('YES (NOTE: empty selector element will return true).\n') if self.debug else '', end='') 

            if dElem.dpcType == 'click':
                
               if dElem.dpcIsSubmit:
                  #self.interceptingUrl = '' 
                  f = await self.getFormContaining(pg, dElem.dpcPageElement)
                  if f is not None:
                     print( utils.toString('\t\t[DEBUG] Submit detected. Form element found.\n') if self.debug else '', end='') 
                     m = await pg.evaluate("(el) => el.getAttribute('action')", f)
                     formAction = urljoin( await pg.evaluate("() => window.location.href"), m )
                     self.interceptResponses = dElem.dpcRedirects
                     if self.interceptResponses:
                        self.interceptingUrl = formAction                     
                        #self.interceptResponses = True
                        self.page.on('response', lambda res: asyncio.ensure_future(self.intercept_network_response(res)) )
                        print( utils.toString('\t\t[DEBUG] Redirection detected. Intercepted url set to [', self.interceptingUrl,']\n') if self.debug else '', end='')
                     
               await pg.click(dElem.dpcPageElement)
               await asyncio.sleep(self.waitTime) # TODO: Remove me

            elif dElem.dpcType == 'js':
                result = await pg.evaluate('''() =>''' + dElem.dpcPageElement + '''()''')
            elif dElem.dpcType.lower() == 'fill':
                 await pg.type(dElem.dpcPageElement, dElem.dpcFillContent)
            elif dElem.dpcType.lower() == 'scrollpage':
                 if dElem.dpcScrollTargetElementCount:
                    await self.scrollPageDownByElementCount(pg, dElem.dpcScrollTargetElementCount)
                 else:
                     await self.scrollPageDownNumberOfTimes(pg, dElem.dpcScrolldown)
                     
                 '''
                 print( utils.toString(f'\t\t[DEBUG] Scrolling page down {dElem.dpcScrolldown} times\n') if self.debug else '', sep='', end='' )
                 for sn in range(dElem.dpcScrolldown):                 
                    await self.scrollPageDown(pg)
                    print( utils.toString(f'\t\t[DEBUG] Waiting for {self.waitTime} seconds\n') if self.debug else '', sep='', end='' )
                    await asyncio.sleep(self.waitTime) # TODO: decrease sleep time?
                 '''


                 #dElem.dpcScrollTargetSelector
                 #dElem.dpcScrollTargetSelectorCount
                 
                 #nElem = await self.pageElementCount(pg, ".ytd-comment-renderer")
                 #print( utils.toString(f'\t\t[DEBUG] Element count {nElem}\n') if self.debug else '', sep='', end='' )
                 #if await self.pageElementCount(pg, '#author-text .ytd-comment-renderer') >=10:
                 #   break 
                 
            elif dElem.dpcType == 'scroll':

                 # Check if element is scrollable
                 if not await self.elementIsScrollable(pg, dElem.dpcPageElement):
                    print( utils.toString(f'\t\t[DEBUG] Element {dElem.dpcPageElement} is NOT scrollable.\n') if self.debug else '', sep='', end='' )
                    return(-5)
                
                 selector = dElem.dpcPageElement
                 currentPosition = 0
                 for _ in range(dElem.dpcScrolldown):
                                          
                     try:                        
                        currentPosition = await self.scrollElement(pg, dElem.dpcPageElement, currentPosition, 203  )
                        if currentPosition < 0:
                           print( utils.toString('Error [', currentPosition,  '] during scrolling of element [', dElem.dpcPageElement, ']. Stopping\n') if self.debug else '', sep='')
                           break

                      #  currentPosition= await pg.evaluate('''(selector, currentPosition) => {
                      #       const element = document.querySelector(selector);
                      #       if ( element ) {
                      #            scrollAmount = currentPosition + 70
                      #            element.scroll(0, scrollAmount);
                      #            console.error(`Scrolled to selector ${selector}`);
                      #            return(scrollAmount)
                      #       } else {
                      #                 console.error(`cannot find selector ${selector}`);
                      #                 return(-4)
                      #       }
                      #         }''', selector, currentPosition)
                      
                     except Exception as scrEx:
                        print( utils.toString('\t[DEBUG] Error during element scrolling', str(scrEx), '\n') if self.debug else '', end='', sep='' ) 
                        return(None) 
                     
                     #await pg.evaluate('''selector => {
                     #        
                     #        const element = document.querySelector(selector);
                     #        if ( element ) {
                     #             //document.getElementById(selector).scrollTop += 100;
                     #             element.scrollTop += 10;
                     #             console.error(`Scrolled to selector ${selector}`);
                     #        } else {
                     #                  console.error(`cannot find selector ${selector}`);
                     #        }
                     #          }''', selector);
            else:
                 print('[ERROR] Directive [', dElem.dpcType,  '] invalid.', sep='')
                 return(None) # not supported directive


                
            if dElem.dpcWaitFor != '':
               print( utils.toString('\t[DEBUG] Waiting for', dElem.dpcWaitFor , '\n') if self.debug else '', end='', sep='') 
               await pg.waitForSelector(dElem.dpcWaitFor)
             
                   
            return(0)   
            



      # sleepTime is currently obsolete
      async def scrollPageDownNumberOfTimes(self, pg, nTimes, delta=20, sleepTime=0.3):

            if nTimes < 0:
               # if nTimes is negative this means scroll to end of page.
               # NOTE: scrollPageEnd DOES NOT WORK
               await self.scrollPageEnd(pg)
               return
        
            print( utils.toString(f'\t\t[DEBUG] Enterring number of time scroll mode {nTimes}\n') if self.debug else '', sep='', end='' )
            for i in range(nTimes):
                await self.scrollPageDown(pg)
                print( utils.toString(f'\t\t[DEBUG] Waiting for {self.waitTime} seconds\n') if self.debug else '', sep='', end='' )
                await asyncio.sleep(self.waitTime) # TODO: decrease sleep time?
        





      # mxTimes: maximum number of times to scroll. Safeguard
      async def scrollPageDownByElementCount(self, pg, scrollCondition, mxTimes=300, delta=20):

            #dpcScrollTargetElementCount
            tSelector = scrollCondition.get('scrollTargetSelector', '')
            try:
              tSelectorCount = int( scrollCondition.get('scrollTargetCount', '-1') )
            except Exception as iEx:
                  tSelectorCount = 3
                  
            print( utils.toString(f'\t\t[DEBUG] Enterring element count scroll mode {tSelectorCount}\n') if self.debug else '', sep='', end='' )
            timesScrolled = 0
            while True:
               await self.scrollPageDown(pg)
               timesScrolled += 1
               currElemCount = await self.pageElementCount(pg, tSelector)
               print( utils.toString(f'\t\t[DEBUG] Current element count {currElemCount} min {tSelectorCount}\n') if self.debug else '', sep='', end='' )
               if currElemCount >= tSelectorCount:
                  break
                
               if mxTimes > 0: 
                  if timesScrolled >= mxTimes:
                     return(False) 

            return(True)
       

      # Scroll page until end i.e. cannot scroll anymore
      # TODO: Does not work.
      async def scrollPageEnd(self, pg):
          print( utils.toString(f'\t\t[DEBUG] Scrolling to page end\n') if self.debug else '', sep='', end='' )
          while(True):
            try:
              
              #previousHeight = await pg.evaluate('document.body.scrollHeight')
              
              elemList = await pg.querySelectorAll('body')
              if elemList is None:
                 print( utils.toString(f"\t\t[DEBUG] Zeor list? Retrying....\n") if self.debug else '', sep='', end='' ) 
                 continue

              
              try:  
                 prevBox = elemList[0]
              except Exception as eEx:
                  print('Error getting first element. ', elemList)

              
              boundingBox = await prevBox.boundingBox();
              print( utils.toString(f"\t\t[DEBUG] BEFORE Current scroll height {boundingBox['height']}\n") if self.debug else '', sep='', end='' )
              
              #print( utils.toString(f'\t\t[DEBUG] Current scroll height {previousHeight}\n') if self.debug else '', sep='', end='' )
              await self.scrollPageDown(pg)
              await asyncio.sleep(2)

              try:
                
                elemList = await pg.querySelectorAll('body')
                afterBox = elemList[0]
                boundingBoxAfter = await afterBox.boundingBox();
                print( utils.toString(f"\t\t[DEBUG] AFTER Current scroll height {boundingBoxAfter['height']}\n") if self.debug else '', sep='', end='' )
              except Exception as eEx:
                  print('Error HERE ', elemList)

              
              if boundingBox['height'] == 0 and boundingBoxAfter['height'] == 0:
                   break
              
                
              #currHeight = await pg.evaluate('document.body.scrollHeight')
              #if currHeight == previousHeight:
              #   break


              
              #print( utils.toString(f'\t\t[DEBUG] Current scroll height {previousHeight}\n') if self.debug else '', sep='', end='' )
              #await pg.evaluate('window.scrollTo(0, document.body.scrollHeight)')
              #status = await pg.evaluate('''(previousHeight) => { if (document.body.scrollHeight > previousHeight) {
              #                                                return(0)
              #                                           } else {
              #                                                 return(-1)
              #                                             }
              #                                             }''', previousHeight)
              #if status < 0:
              #   print( utils.toString(f'\t\t[DEBUG] No more scrolling possible\n') if self.debug else '', sep='', end='' ) 
              #   break
                
            except Exception as scrEx:
                   print( utils.toString(f'\t\t[DEBUG] Exception during scrolling to page end: {str(scrEx)}\n') if self.debug else '', sep='', end='' )
                   return





      # This scrolls the browser's window down.
      # Works on MacOS.
      # TODO: Does this also work on windows and other OSs?
      async def scrollPageDown(self, pg):
            await pg.evaluate('window.scrollBy(0,window.innerHeight)')
            #document.body.scrollHeight
            #window.innerHeight
            '''
            await pg.keyboard.down('Fn')
            await pg.keyboard.down('Shift')
            await pg.keyboard.press('ArrowDown')
            await pg.keyboard.up('Shift')
            await pg.keyboard.up('fn')
            '''

     
      # This scrolls the content of an html element down.
      # E.g. a scrollable div
      # This method assumes that element exists and is actually
      # scrollable (see elementExists() and elementIsScrollable())             
      async def scrollElement(self, pg, elem, currentPos, scrollBy=30):
          
                return ( await pg.evaluate('''(elem, currentPos, scrollBy) => {
                             
                             const element = document.querySelector(elem);
                             if ( element ) {
                                  scrollAmount = currentPos + scrollBy
                                  element.scroll(0, scrollAmount);
                                  console.error(`Scrolled to selector ${elem}`);
                                  return(scrollAmount)
                             } else {
                                       console.error(`cannot find selector ${elem}`);
                                       return(-4)
                             }
                               }''', elem, currentPos, scrollBy)
                        ) 
          


      # Check if element exists on page
      async def elementExists(self, pg, elemSel):

          if elemSel.strip() == '':
             return(True) # Some dynamic types may not need an element. E.g. page scrolldowns
            
          selector = elemSel
          value = await pg.evaluate('''selector => {
                                            const element = document.querySelector(selector);
                                            if ( element ) {
                                                 return(0)
                                            } else {
                                                 return(-1) 
                                            }
                                            }''', selector)          
          if value < 0:
             return(False)

          return(True)  




      async def  elementIsScrollable(self, pg, elem):
            print( utils.toString('\t\t[DEBUG] Checking if element [', elem, '] is scrollable....\n') if self.debug else '', end='')            
            scrollable = await pg.evaluate(
                                 '''elem => {
                                                    const node = document.querySelector(elem);
                                                    if (!node){
                                                         return {vertical:False, horizontal:False}
                                                    }
                                                    const overflowY = window.getComputedStyle(node)['overflow-y'];
                                                    const overflowX = window.getComputedStyle(node)['overflow-x'];
                                                    return {
                                                        vertical: (overflowY === 'scroll' || overflowY === 'auto') && node.scrollHeight > node.clientHeight,
                                                        horizontal: (overflowX === 'scroll' || overflowX === 'auto') && node.scrollWidth > node.clientWidth,
                                                    };
                                  }''', elem
                                );

            

            print('', 'YES' if scrollable and self.debug else 'NO' if not scrollable and self.debug else '')
            return(scrollable['vertical'])


        
      ##############################################
        
      async def getFormContaining(self, pg, targetElemSelector):
         e = await self.getElementContaining(pg, 'form', targetElemSelector)
         return(e) 


      # innerMost not yet working
      async def getElementContaining(self, pg, parentElemSelector, targetElemSelector, innerMost=False):
         
         allCandidateElements = await pg.querySelectorAll(parentElemSelector)
         print(allCandidateElements)
         for cel in allCandidateElements:
             if await self.elementContains(cel, targetElemSelector):
                   return( cel ) # return the first element containing targetElem
                 
         return(None) # Not found  




      # Used when asking the deepest element containing targetElemSelector
      # TODO: Not yet used/completed/tested
      async def getContainingElement( self, pElem, parentElemSelector, targetElemSelector ):
       
         if  not await self.elementContains(pElem, targetElem):
             return(None)

         allCandidateElements = await elem.querySelectorAll(parentElemSelector)
         for cel in allCandidateElements:
             if await self.elementContains(cel, targetElem):
                return( self.getContainingElement(cel, parentElemSelctor, targetElemSelector) )
             else:   
                return(cel)   

         return(None)     


         
      async def elementContains(self, elem, containedElemSelector):

         try:
           e = await elem.querySelectorEval(containedElemSelector, "(el)=>(el)")
           return(True)
         except Exception as sErr:
              return(False)
            
         return(False) # Obsolete. TODO: Should be removed  


      # Count how many elements matching elemSelector exists on page
      async def pageElementCount(self, pg, elemSelector):

            #if not self.elementExists(pg, elemSelector):
            #   return(False)
            
            return( len(await pg.querySelectorAll(elemSelector)) ) 

      #####################################


      def cleanUp(self):
          asyncio.get_event_loop().run_until_complete( self.__close() )  
          
          
      async def __close(self):
          print( utils.toString('\t[DEBUG] Freeing resources\n')  if self.debug else '', end='', sep='' )
          try:
            await self.browser.close()
          except Exception as cEx:
                 print( utils.toString('\t[DEBUG] Exception during closing of browser.\n')  if self.debug else '', end='', sep='' )
                 
          self.browser = None
          self.page = None


