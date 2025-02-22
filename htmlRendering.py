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
from datetime import datetime
import configparser

import utils
import xRules
import osPlatform

async def intercept_network_response2(response):
          
          
   
            
             print('==================================================')
             print("\t\tURL:", response.url)
             
             print("\t\tMethod:", response.request.method)
             print("\t\tResponse status:", response.status)
             print("\t\tResponse headers:", response.headers)
             print("\t\tRequest Headers:", response.request.headers)
             
             print('==================================================')
             

             



class htmlRenderer:



      def __init__(self):
          self.browser = None
          self.page = None
          self.headers = None
          
          # header used during request
          self.rqstHeader = {}
          
          self.response = None

          # TODO: Check me 
          self.interceptingUrl = ''


          self.cookiesSeen = []
          self.cookieIndex = {}
          
          self.interceptResponses = False
          
          # TODO: wait 
          self.waitTime = 1.2 # in seconds
          
          
          self.takePageScreenshot = True # in seconds
          self.screenShotStoragePath = './' # Where to store screenshots

          

          # Configuration options.
          # This is currently used to control how to terminate Chromium instances since there
          # is a bug in the .close() metho of pyppeteer and zombie Chromium instances remain.
          # 
          self.config = None
          
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
         
          
          cookie = SimpleCookie()
          cookie.load(cs)

          nC = 0
          knList = []
          for k, m in cookie.items():
              # add or update
              self.cookieIndex[k] = {'cookie':cookie, 'source': cs, 'url':url }
              knList.append( k )
              nC += 1
          




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

    
      # For intercepting http requests. Not used currently...
      ''' 
      async def interceptHttpRequest(req: Request):
            print(f'Original header: {req.headers}')
            req.headers.update({'Accept-Encoding': 'gzip'})
            await req.continue_(overrides={'headers': req.headers})
      '''

            
     # This captures responses by intercepting them
     # This is done when a page redirects.
      async def intercept_network_response(self, resp):

             # If reponse is a redirect i.e. response status is between
             # [300, 400), keep the destination of the redirect
             if 300 <= resp.status  and resp.status < 400:
                self.interceptingUrl =  urljoin( resp.url, resp.headers.get('location') )                
             else:
                 # If it's no redirect, just return
                 if self.interceptingUrl != resp.url:
                    return 
          
             # TODO: Is this correct? 
             # Store the new response header
             self.response = resp
             
             # Does the redirect have any cookie? 
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



      # TODO: Cleanup the parameter list of render as some parameters are obsolete.    
      def render(self, url='', maxRetries = 3, timeout=5, requestCookies=[], userAgent=None, scrolldown=0, dynamicElements=[], launchParams={}):
          return( asyncio.get_event_loop().run_until_complete(self.fetchUrl(url, maxRetries, timeout, requestCookies, userAgent, scrolldown, dynamicElements, launchParams)) )



      # fetchUrl method uses rendering engine to download page.
      # Returns html content. Headers are in .response instance variable.
      #
      # TODO: This method needs serious refactoring.
      #       Among others, scrolldown is now obsolete. 
      async def fetchUrl(self, url='', maxRetries = 3, timeout=5, requestCookies=[], userAgent=None, scrolldown=0, dynamicElements=[], launchParams={} ):

       #if self.interceptResponses:
       self.interceptingUrl = url
          
       if self.browser is None:
          print( utils.toString('\t[DEBUG] Creating new BROWSER\n') if self.debug else '', sep='', end=''  )
          
          # launches a browser in headless mode. Headless means WITHOUT UI.
          # NOTE: for default options add:
          #args=[
          #  '--no-sandbox',
          #  '--disable-setuid-sandbox',
          #  '--disable-dev-shm-usage',
          #  '--headless',
          #  '--disable-gpu',
          #  '--ignore-certificate-errors'
          #  ]

          if not launchParams:
             print( utils.toString('\t[DEBUG] Starting WITHOUT launch parameters\n') if self.debug else '', sep='', end='' ) 
             self.browser = await pyppeteer.launch()
          else: 
             # Next line seems to work properly for AIRBNB (previous line does not)
             # executablePath for MacOS: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
             # 'F:\\ProgramFiles\\Programs\\Google\\Chrome\\Application\\chrome.exe'
             # "C:\\Users\\Manolis\\AppData\\Local\\Google\\Chrome\\User Data"
             # For MacOS set executablePath to: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' and no userDataDir param
             print( utils.toString('\t[DEBUG] Starting WITH lauch parameters:[',launchParams.get('executablePath', ''), '] [', launchParams.get('userDataDir', ''), ']\n') if self.debug else '', sep='', end='' )
             self.browser = await pyppeteer.launch(headless=True, executablePath=launchParams.get('executablePath', ''), userDataDir=launchParams.get('userDataDir', ''))

          # for MacOS next like WORKED PERFECTLY!!!  
          #self.browser = await pyppeteer.launch(headless=True, executablePath='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', )
           
       else:
            print( utils.toString('\t[DEBUG] Reusing existing BROWSER\n') if self.debug else '', sep='', end='' )
            
       if self.page is None:
          print( utils.toString('\t[DEBUG] Creating new PAGE\n') if self.debug else '', sep='', end=''  )
          self.page = await self.browser.newPage()

          
          if self.interceptResponses:
             print( utils.toString('\t[DEBUG] INITIALIZING interception\n') if self.debug else '', sep='', end=''  ) 
             self.page.on('response', lambda res: asyncio.ensure_future(self.intercept_network_response(res)) )         
       else:
          print( utils.toString('\t[DEBUG] Reusing existing PAGE\n') if self.debug else '', sep='', end='' )


       if self.rqstHeader:
         print( utils.toString('\t[DEBUG] Setting extra headers to [', self.rqstHeader, ']\n') if self.debug else '', sep='', end='' ) 
         await self.page.setExtraHTTPHeaders( self.rqstHeader )

       # Set user agent 
       if userAgent is not None:
          print( utils.toString('\t[DEBUG] Setting user agent to [', userAgent, ']\n') if self.debug else '', sep='', end='' ) 
          await self.page.setUserAgent(userAgent);

       # Set request cookies
       print( utils.toString('\t[DEBUG] Setting request cookies ', requestCookies,'\n') if self.debug else '', sep='', end='' )
       for c in requestCookies:
            #print('[DEBUG] html rendering. Setting cookie', c)
            await self.page.setCookie( c )
            #await asyncio.sleep(self.waitTime/2)

      
         
      #TODO: Can we use .setExtraHTTPHEaders to change ANY header???
      # await self.page.setExtraHTTPHeaders({
      #  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
      #  'upgrade-insecure-requests': '1',
      #  'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
      #  'accept-encoding': 'gzip, deflate, br',
      #  'accept-language': 'en-US,en;q=0.9,en;q=0.8'
      # })

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
              print( utils.toString('\t[DEBUG] Fetching url. Timeout=', timeout, '\n') if self.debug else '', sep='', end='' )
              self.response = await self.page.goto(url, options={'waitUntil':'networkidle0', 'timeout': int(timeout * 1000)})
              
              # TODO: Do we REALLY need a sleep here??
              #await asyncio.sleep(1.4)

              # TODO: Add here a waitForSelector?
              #       Needs support in .exr files
              #await self.page.waitForSelector( 'div.t1bgcr6e') #'._11eqlma4')

              # TODO: Does this work??? 
              #await self.page.waitForNavigation()
              
              #self.page.on('response', lambda res: asyncio.ensure_future(intercept_network_response(res)) ) 
              print( utils.toString('\t[DEBUG] Fetching url DONE\n') if self.debug else '', sep='', end='' )
              if self.takePageScreenshot:
                 await self.page.screenshot({'path': utils.urlToPlainFilename(self.screenShotStoragePath, 'AFTER-LOADING-', url) + '.png' })

              
              
              attemptEnd = time.perf_counter() 
              break
            
           except Exception as fetchException:
               print( utils.toString('\t\t[DEBUG] (', numTries, ') Excpetion ', str(fetchException), '\n' ) if self.debug else '', sep='', end='' )
               numTries += 1

       
       # TODO: Remove me?
       self.headers = None #origResponse.headers
       
       print( utils.toString('\t\t\t[DEBUG] Successful attempt elapsed:', "{:.3f}".format(attemptEnd  - attemptStart), '\n' ) if self.debug else '', sep='', end='' )       
       print( utils.toString('\t\t\t[DEBUG] Total elapsed:', "{:.3f}".format(time.perf_counter() - startTm), '\n') if self.debug else '', sep='', end='' )    

              

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
           
           if self.debug and self.takePageScreenshot:
              # Next is for debugging purposes ONLY! 
              await self.page.screenshot({'path': utils.urlToPlainFilename(self.screenShotStoragePath, 'BEFORE-'+ de.dpcPageElement.replace(':', '-') + '-', url) + '.png' })


           await self.executeDynamicElement(self.page, de)
           if self.debug and self.takePageScreenshot:
              # Next is for debugging purposes ONLY! 
              await self.page.screenshot({'path': utils.urlToPlainFilename(self.screenShotStoragePath, 'AFTER-'+ de.dpcPageElement.replace(':', '-') + '-', url) + '.png' })


              
           # This SEEMS to be required.
           # TODO: Investigate closer the execution dynamic of pyppeteer
           await asyncio.sleep(self.waitTime)
       
              
       if self.takePageScreenshot:       
          print( utils.toString('\t[DEBUG] Saving screenshot to file:', utils.urlToPlainFilename(self.screenShotStoragePath, url), '\n' ) if self.debug else '', end='' )      
          await self.page.screenshot({'path': utils.urlToPlainFilename(self.screenShotStoragePath, '', url) + '.png' })

       
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
               print( utils.toString(f'NO. Element {dElem.dpcPageElement} does not exist on page. Not executing action on page.\n') if self.debug else '', sep='', end='' )
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
                     
            elif dElem.dpcType == 'scroll':

                 # Infinite scrolling not supported in this mode. That's because in
                 # this mode, no target element is defined hence not may to check
                 # if scrolling should stop.
                 
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
                                            
                     except Exception as scrEx:
                        print( utils.toString('\t[DEBUG] Error during element scrolling', str(scrEx), '\n') if self.debug else '', end='', sep='' ) 
                        return(None) 
                                          
            else:
                 print('[ERROR] Directive [', dElem.dpcType,  '] invalid.', sep='')
                 return(None) # not supported directive


                
            if dElem.dpcWaitFor != '':
               print( utils.toString('\t[DEBUG] Waiting for [', dElem.dpcWaitFor , ']\n') if self.debug else '', end='', sep='') 
               # increased default timeout 
               await pg.waitForSelector(dElem.dpcWaitFor, timeout=45000)
             
                   
            return(0)   
            



      # Infinite scrolling not supported in this mode.
      # That's because there is no way to check if scrolling
      # to stop, if no target element is defined.
      async def scrollPageDownNumberOfTimes(self, pg, nTimes, delta=20, sleepTime=0.3):

            if nTimes < 0:               
               return
        
            print( utils.toString(f'\t\t[DEBUG] Enterring number of time scroll mode {nTimes}\n') if self.debug else '', sep='', end='' )
            for i in range(nTimes):
                await self.scrollPageDown(pg)
                print( utils.toString(f'\t\t[DEBUG] Waiting for {self.waitTime} seconds\n') if self.debug else '', sep='', end='' )
                await asyncio.sleep(self.waitTime) # TODO: decrease sleep time?
        





      # mxTimes: maximum number of times to scroll when no change occurs. Safeguard.
      # if scrollTargetCount has negative value, this means scroll until end i.e. until
      # no change is happening on the page.
      # Infinite scrolling supported ONLY in this mode.
      async def scrollPageDownByElementCount(self, pg, scrollCondition, mxTimes=150, delta=20):

            #dpcScrollTargetElementCount
            try: 
              tSelector = scrollCondition.get('scrollTargetSelector', '')
            except Exception as iEx:
                   print('Exception during get scrollTargetSelector')
                   tSelector = ''
                   
            try:
              tSelectorCount = int( scrollCondition.get('scrollTargetCount', '-1') )
            except Exception as iEx:
                  print('Exception during get scrollTargetCount')
                  tSelectorCount = 3
                  
            print( utils.toString(f'\t\t[DEBUG] Enterring element count scroll mode {tSelectorCount}\n') if self.debug else '', sep='', end='' )

            lastElemCount = -1
            timesScrolled = 0
            timesScrolledNoChange = 0
            checkPoint = 0
            while True:
               await self.scrollPageDown(pg)
               timesScrolled += 1
               currElemCount = await self.pageElementCount(pg, tSelector)
               print( utils.toString(f'\t\t[DEBUG] Current element count {currElemCount} (min: {tSelectorCount} times scrolled without change: {timesScrolledNoChange})\n') if self.debug else '', sep='', end='' )
               if tSelectorCount > 0:
                  if currElemCount >= tSelectorCount:
                     break
               

               if currElemCount == lastElemCount:
                  timesScrolledNoChange += 1
                  if mxTimes > 0 and timesScrolledNoChange >= mxTimes:
                     return(False) 
               else:
                   timesScrolledNoChange = 0 # reset
                                   
               if currElemCount - checkPoint >= 100:
                  checkPoint =  currElemCount
                  now = datetime.now()
                  cDateTime = now.strftime("%d/%m/%Y %H:%M:%S")
                  print(f'\t[{cDateTime} INFINITE SCROLL] {currElemCount}')
            
               lastElemCount = currElemCount 

            return(True)




       

      


      # This scrolls the browser's window down.
      # Works on MacOS.
      # TODO: Does this also work on windows and other OSs?
      async def scrollPageDown(self, pg):
            await pg.evaluate('window.scrollBy(0, window.innerHeight)')

            return( await pg.evaluate('window.innerHeight') )



            

     
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

          # Auto behavior of forceBrowerCleanup is here. 
          if self.config is not None:
             if self.config.get('Crawler', 'forceBrowserCleanup', fallback='False').lower() == 'auto':

                excluded = self.config.get('__Runtime', '__runningChromeInstances', fallback=[])
                
                osP = osPlatform.OSPlatformFactory(self.config).createPlatform()
                osP.killProcess(excluded)
                print('Total of ', osP.nkilled, ' processes killed')
             
          self.browser = None
          self.page = None


