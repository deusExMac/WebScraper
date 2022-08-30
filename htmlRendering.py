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

       # scroll entire browser page if required
       if scrolldown > 0:         
        for _ in range(scrolldown):
          #print('\t[DEBUG] Scrolling....', end='')
          await self.scrollPageDown(self.page)

       await asyncio.sleep(3.4) # TODO: decrease sleep time?

            
       # Execute dynamic elements
       # TODO: changed order of operations (was: first scrolling then loading). NOT TESTED!
       if dynamicElements:
          for de in  dynamicElements:
              await self.executeDynamicElement(self.page, de)
              # This SEEMS to be required.
              # TODO: Investigate closer the execution dynamic of pyppeteer
              await asyncio.sleep(2.1)
       else:
             print('\t[DEBUG] No dynamic element on page to be executed')

       

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
            print('\t\t[DEBUG] Chacking if element [', dElem.dpcPageElement, '] exists.....',  sep='', end='')
            if not await self.elementExists(pg, dElem.dpcPageElement):
               print(f'\t\t[DEBUG] Element {dElem.dpcPageElement} does not exist on page. Not executing any bahavior.')
               return(None) 

            print('YES.') 

            if dElem.dpcType == 'button':   
               await pg.click(dElem.dpcPageElement)
            elif dElem.dpcType == 'js':
                result = await page.evaluate('''() =>''' + dElem.dpcPageElement + '''()''')    
            elif dElem.dpcType == 'scroll':

                 print('\t\tGetting SCROLL PARENT of [', dElem.dpcPageElement, ']') 
                 scrP = await self.getScrollParent(pg, dElem.dpcPageElement)
                 print('\t\t===>SCROLL PARENT:[', scrP, ']')
                 
                 if not await self.elementIsScrollable(pg, dElem.dpcPageElement):
                    print(f'\t\t[DEBUG] Element {dElem.dpcPageElement} is not scrollable.')
                    return(-5)
                
                 selector = dElem.dpcPageElement
                 currentPosition = 0
                 for _ in range(dElem.dpcScrolldown):
                     #document.querySelectorAll

                     # TODO: check if this works somehow.
                     try:                        
                        #await pg.evaluate('{window.scrollTo(0, document.body.scrollHeight);}')
                        currentPosition= await pg.evaluate('''(selector, currentPosition) => {
                             
                             const element = document.querySelector(selector);
                             if ( element ) {
                                  scrollAmount = currentPosition + 70
                                  element.scroll(0, scrollAmount);
                                  console.error(`Scrolled to selector ${selector}`);
                                  return(scrollAmount)
                             } else {
                                       console.error(`cannot find selector ${selector}`);
                                       return(-4)
                             }
                               }''', selector, currentPosition)   
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




      async def  elementIsScrollable(self, pg, elem):
            print('\t\t[DEBUG] Checking if element [', elem, '] is scrollable..')
            selector = elem
            scrollable = await pg.evaluate(
                                 '''selector => {
                                                    const node = document.querySelector(selector);
                                                    if (!node){
                                                         return {vertical:False, horizontal:False}
                                                    }
                                                    const overflowY = window.getComputedStyle(node)['overflow-y'];
                                                    const overflowX = window.getComputedStyle(node)['overflow-x'];
                                                    return {
                                                        vertical: (overflowY === 'scroll' || overflowY === 'auto') && node.scrollHeight > node.clientHeight,
                                                        horizontal: (overflowX === 'scroll' || overflowX === 'auto') && node.scrollWidth > node.clientWidth,
                                                    };
                                  }''', selector
                                );


            #param = elem
            #scrollable = await pg.evaluate( '''(param) => {
            #                                 var res = isScrollable(param);
            #                                 return(res.vertical)
            #                              }''', param);

            print('\t\t[DEBUG] elementIsScrollable returned ', scrollable)
            return(scrollable['vertical'])



      async def  getScrollParent(self, pg, elem):
            #print('\t\t[DEBUG] Checking if element [', elem, '] is scrollable..')
            selector="div.r1are2x1"
            scrollableParent = await pg.evaluate(
                                 '''selector => {
                                    
                                    const element = document.querySelector(selector);
                                    if (!element) {
                                        return('?????') 
                                    }

                                    var includeHidden = true
                                    var style = getComputedStyle(element);
                                    var excludeStaticParent = style.position === "absolute";
                                    var overflowRegex = includeHidden ? /(auto|scroll|hidden)/ : /(auto|scroll)/;

                                    if (style.position === "fixed") return document.body;
                                    for (var parent = element; (parent = parent.parentElement);) {
                                        style = getComputedStyle(parent);
                                        if (excludeStaticParent && style.position === "static") {
                                            continue;
                                        }
                                        if (overflowRegex.test(style.overflow + style.overflowY + style.overflowX)) return parent;
                                    }

                                    return(document.body);
                                  
                                  
                                  }''', selector
                                );

            
            #param = elem
            #scrollableParent = await pg.evaluate( '''(param) => {
            #                                 var res = getScrollParent(param);
            #                                 return(res)
            #                              }''', param);
             
            print('\t\t[DEBUG] Scrollable parent element is [', scrollableParent, ']')
            return(scrollableParent)

        







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


