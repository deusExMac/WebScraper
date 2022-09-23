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
          self.debug = False


      # dv: debug value: True or False
      def setDebugMode(self, dv):
          self.debug = dv


        
      def render(self, url='', maxRetries = 3, timeout=5, requestCookies=[], userAgent=None, scrolldown=0, dynamicElements=[]):
          return( asyncio.get_event_loop().run_until_complete(self.fetchUrl(url, maxRetries, timeout, requestCookies, userAgent, scrolldown, dynamicElements)) )






      async def fetchUrl(self, url='', maxRetries = 3, timeout=5, requestCookies=[], userAgent=None, scrolldown=0, dynamicElements=[] ):

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
          #self.page.on('response', lambda res: asyncio.ensure_future(intercept_network_response(res)) )         
       else:
          print( utils.toString('\t[DEBUG] Reusing existing PAGE\n') if self.debug else '', sep='', end='' )
        
       if userAgent is not None:
          await self.page.setUserAgent(userAgent);
          
       for c in requestCookies:
            await self.page.setCookie( c )

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
              self.response = await self.page.goto(url, options={'timeout': int(timeout * 1000)})


              #try:
              #  print('>>> COOKIES:', await self.page.cookies() )  
              #except Exception as feee:
              #    print('ERROR', str(feee))
                  
              attemptEnd = time.perf_counter() 
              break
            
           except Exception as fetchException:
               print( utils.toString('\t\t[DEBUG] (', numTries, ') Excpetion ', str(fetchException), '\n' ) if self.debug else '', sep='', end='' )
               numTries += 1

       #print(origResponse.headers)
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

       # scroll entire browser page if required
       '''
       if scrolldown > 0:         
        for _ in range(scrolldown):          
          await self.scrollPageDown(self.page)

       await asyncio.sleep(3.4) # TODO: decrease sleep time?
       ''' 
            
       # Execute dynamic elements
       # TODO: changed order of operations (was: first scrolling then loading). NOT TESTED!
       if dynamicElements:
          for de in  dynamicElements:
              await self.executeDynamicElement(self.page, de)
              # This SEEMS to be required.
              # TODO: Investigate closer the execution dynamic of pyppeteer
              await asyncio.sleep(0.9)
       else:
             print( utils.toString('\t[DEBUG] No dynamic element on page to be executed\n') if self.debug else '', end='' )

       

       #'screenShot.png'
       print( utils.toString('\t[DEBUG] Saving screenshot to file:', utils.urlToPlainFilename('etc/', url), '\n' ) if self.debug else '', end='' )      
       await self.page.screenshot({'path': utils.urlToPlainFilename('etc/', url) + '.png' })
       content = await self.page.content()
                
       return( content )







      

      #
      # TODO: directive scroll does not work
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

            if dElem.dpcType == 'button':   
               await pg.click(dElem.dpcPageElement)
               await asyncio.sleep(2.5) # TODO: Remove me
            elif dElem.dpcType == 'js':
                result = await page.evaluate('''() =>''' + dElem.dpcPageElement + '''()''')
            elif dElem.dpcType.lower() == 'fill':
                 await pg.type(dElem.dpcPageElement, dElem.dpcFillContent)
            elif dElem.dpcType.lower() == 'scrollpage':
                 print( utils.toString(f'\t\t[DEBUG] Scrolling page down {dElem.dpcScrolldown} times\n') if self.debug else '', sep='', end='' )
                 for sn in range(dElem.dpcScrolldown):
                    #print( utils.toString(f'\t\t[DEBUG] Scroll: {sn}\n') if self.debug else '', sep='', end='' ) 
                    await self.scrollPageDown(pg)

                 await asyncio.sleep(2.4) # TODO: decrease sleep time?
                 
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
               await pg.waitForSelector(dElem.dpcWaitFor)
             
                   
            return(0)   
            



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


