import sys
import time
#from datetime import datetime
#import json
import asyncio
import pyppeteer

import utils



async def intercept_network_response(response):
          # In this example, we only care about HTML responses!
          #if "text/html" in response.headers.get("content-type", ""):
             # Print some info about the responses
             print("URL:", response.url)
             print("Method:", response.request.method)
             print("Response headers:", response.headers)
             print("Request Headers:", response.request.headers)
             print("Response status:", response.status)
             # Print the content of the response
             #print("Content: ", await response.text())
             # NOTE: Use await response.json() if you want to get the JSON directly



class htmlRenderer:



      def __init__(self):
          self.browser = None
          self.page = None
          self.headers = None
          self.response = None



      
        
      def render(self, url='', maxRetries = 3, timeout=5, requestCookies=[], userAgent=None, scrolldown=0, dynamicElements=[]):
          return( asyncio.get_event_loop().run_until_complete(self.fetchUrl(url, maxRetries, timeout, requestCookies, userAgent, scrolldown, dynamicElements)) )






      async def fetchUrl(self, url='', maxRetries = 3, timeout=5, requestCookies=[], userAgent=None, scrolldown=0, dynamicElements=[] ):

       if self.browser is None:
          print('\t[DEBUG] Creating new BROWSER')
          # launches a browser in headless mode. Headless means WITHOUT UI.
          self.browser = await pyppeteer.launch()
       else:
            print('\t[DEBUG] Reusing existing BROWSER')
            
       if self.page is None:
          print('\t[DEBUG] Creating new PAGE') 
          self.page = await self.browser.newPage()
          # Uncomment next line if you would like to intercept responses
          #self.page.on('response', lambda res: asyncio.ensure_future(intercept_network_response(res)) )         
       else:
          print('\t[DEBUG] Reusing existing PAGE') 
        
       if userAgent is not None:
          await self.page.setUserAgent(userAgent);
          
       for c in requestCookies:
            await self.page.setCookie( c )

       print('\t[DEBUG] Loading URL', url)
       await self.page.setViewport( {'width':1920, 'height':1080} )
       await self.page.setJavaScriptEnabled(enabled=True)

       
       numTries = 0
       startTm = time.perf_counter() # Start counting total time.
       while True:

           if numTries >= maxRetries:
              print(f'\t\t[DEBUG] Reached maximum number of retries {maxRetries}. Giving up.')      
              return(None)
            
           try:
              attemptStart = time.perf_counter() # start counting request time
              self.response = await self.page.goto(url, options={'timeout': int(timeout * 1000)})
              attemptEnd = time.perf_counter() 
              break
           except Exception as fetchException:
               print('\t\t[DEBUG] (', numTries, ') Excpetion ', str(fetchException), sep='' )
               numTries += 1

       #print(origResponse.headers)
       # TODO: Remove me?
       self.headers = None #origResponse.headers
       
       print('\t\t\t[DEBUG] Successful attempt elapsed:', "{:.3f}".format(attemptEnd  - attemptStart))       
       print('\t\t\t[DEBUG] Total elapsed:', "{:.3f}".format(time.perf_counter() - startTm))    

       
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
            
       # Execute dynamic elements
       # TODO: changed order of operations (was: first scrolling then loading). NOT TESTED!
       if dynamicElements:
          for de in  dynamicElements:
              await self.executeDynamicElement(self.page, de)
       else:
             print('\t[DEBUG] No dynamic element on page to be executed')

       # scroll entire browser page if required
       if scrolldown > 0:         
        for _ in range(scrolldown):
          #print('\t[DEBUG] Scrolling....', end='')
          await self.scrollPageDown(self.page)

       await asyncio.sleep(1.4) # TODO: decrease sleep time?

       #'screenShot.png'
       print('\t[DEBUG] Saving screenshot to file:', utils.urlToPlainFilename('etc/', url))      
       await self.page.screenshot({'path': utils.urlToPlainFilename('etc/', url) + '.png' })
       content = await self.page.content()
                
       return( content )







      # This is a different implementation for scrolling down the
      # page. This works on MacOS.
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


      #
      # TODO: directive scroll does not work
      #
      async def executeDynamicElement(self, pg, dElem):

            if dElem is None:
               return(None)

            print('\t\t[DEBUG] Executing dynamic content: type=',dElem.dpcType, ' element=', dElem.dpcPageElement, sep='')
            if not await self.elementExists(pg, dElem.dpcPageElement):
               print(f'\t\t[DEBUG] Element {dElem.dpcPageElement} does not exist on page. Not executing any bahavior.')
               return(None) 


            if dElem.dpcType == 'button':   
               await pg.click(dElem.dpcPageElement)
            elif dElem.dpcType == 'js':
                result = await page.evaluate('''() =>''' + dElem.dpcPageElement + '''()''')    
            elif dElem.dpcType == 'scroll':
                 selector = dElem.dpcPageElement
                 for _ in range(dElem.dpcScrolldown):
                     #document.querySelectorAll

                     # TODO: check if this works somehow.
                     try:                        
                        await pg.evaluate('{window.scrollTo(0, document.body.scrollHeight);}')
                        await pg.evaluate('''selector => {
                             
                             const element = document.querySelector(selector);
                             if ( element ) {                                  
                                  element.scroll(50, 0);
                                  console.error(`Scrolled to selector ${selector}`);
                             } else {
                                       console.error(`cannot find selector ${selector}`);
                             }
                               }''', selector)   
                     except Exception as scrEx:
                        print('\t[DEBUG] Error during element scrolling', str(scrEx)) 
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
                 return(None) # not supported directive


                
            if dElem.dpcWaitFor != '':
               await pg.waitForSelector(dElem.dpcWaitFor)
             
                   
            return(0)   
            


      # Check if element exists on page
      async def elementExists(self, pg, elemSel):          
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





      def cleanUp(self):
          asyncio.get_event_loop().run_until_complete( self.__close() )  
          
          
      async def __close(self):
          print('\t[DEBUG] Freeing resources')
          try:
            await self.browser.close()
          except Exception as cEx:
                 print('\t[DEBUG] Exception during closing of browser.')
                 
          self.browser = None
          self.page = None


