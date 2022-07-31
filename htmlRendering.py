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


      
        
      def render(self, url='', timeout=5, requestCookies=[], scrolldown=0, maxRetries = 3):
          return( asyncio.get_event_loop().run_until_complete(self.fetchUrl(url, timeout, requestCookies, scrolldown, maxRetries)) )



      async def fetchUrl(self, url='', timeout=5, requestCookies=[], scrolldown=0, maxRetries = 3):

       if self.browser is None:
          print('\t[DEBUG] Creating new BROWSER') 
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
              await self.page.goto(url, options={'timeout': int(timeout * 1000)})
              attemptEnd = time.perf_counter() 
              break
           except Exception as fetchException:
               print('\t\t[DEBUG] (', numTries, ') Excpetion ', str(fetchException), sep='' )
               numTries += 1

               
       print('\t\t\t[DEBUG] Successful attempt elapsed:', "{:.3f}".format(attemptEnd  - attemptStart))       
       print('\t\t\t[DEBUG] Total elapsed:', "{:.3f}".format(time.perf_counter() - startTm))    

       if scrolldown > 0:         
        for _ in range(scrolldown):
          print('\t[DEBUG] Scrolling....', end='')
             
          if utils.isMac():
               # TODO: Check if .scrollPageDown works also for all other OSs 
               print('\t\t[DEBUG] MacOS detected') 
               await self.scrollPageDown(self.page)
          else:
               # On windows and linux, PageDown key works
               # Replaced method .down with .press 
               await self.page._keyboard.press('PageDown') 
               
            
          print('done')
          print('\t[DEBUG] Sleeping....', end='')  
          await asyncio.sleep(1.4)
          print('done')

       await self.page.screenshot({'path': 'screenShot.png'})
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





      def cleanUp(self):
          asyncio.get_event_loop().run_until_complete( self.__close() )  
          
          
      async def __close(self):
          print('[DEBUG] Freeing resources')
          try:
            await self.browser.close()
          except Exception as cEx:
                 print('\t[DEBUG] Exception during closing of browser.')
                 
          self.browser = None
          self.page = None


