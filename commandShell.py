


"""

Module containing the implementation of the application
command shell.
Implementation of the supported commands is also in this module.



Author: mmt
Version: 20/04/2022

"""



import os
import os.path
#import psutil # killing processes

import configparser

# For parsing the dates received from twitter in readable formats
import datetime
import dateutil.parser
#from datetime import  timedelta 
import time
import re
import statistics

import argparse
import copy

import pandas as pd
import webbrowser

import json, requests 
from urllib.parse import urlparse, urljoin, unquote
from bs4 import BeautifulSoup
from bs4.element import Comment
from requests_html import HTMLSession, HTML

from pathlib import Path
import hashlib

import numpy as np
import csv

import clrprint

import pyppdf.patch_pyppeteer



# We define constants in this file
import appConstants
from commandHistory import commandHistory
import xRules

import utils
import urlQueue
import extractedDataSource

import htmlRendering
import osPlatform


# The following two classes are used to parse
# arguments on the shell 'scommand line
class ArgumentParserError(Exception): pass
  
class ThrowingArgumentParser(argparse.ArgumentParser):
      def error(self, message):
          raise ArgumentParserError(message)






class commandShell:

      def __init__(self, cfg, xRls=None):

          # Command synonyms.
          # Add here any command you would like to expand
          self.cmdExpansions = [{"c":"config", "jk":"joke"} ]

          self.cmdExecutioner = commandImpl(cfg, xRls)
          self.cmdHistory = commandHistory(cfg.getint('Shell', 'historySize', fallback=10), True)

          





      
      # Check if the command given needs to be expanded
      #
      # TODO: expansion works ONLY for commands with no arguments.
      # Fix this. And add h for history here!
      def expandCommand( self, cmd ):

          # Is it in our manual expansion list?
          for c in self.cmdExpansions:
            if c.get(cmd) is not None:
               return( c.get(cmd) )

            
                
          if cmd == '!!':
             return( self.cmdHistory.getLast() )
                  
          if cmd.startswith('!'):
             try:
               hIdx = int(cmd[1:])
               return( self.cmdHistory.get(hIdx) )
               
             except Exception as nmbrEx:
                 #print('Executing last command starting with [', command[1:], ']', sep='')
                 return( self.cmdHistory.getLastContaining(cmd[1:] ) )
                   
          if cmd.startswith('^'):
             tokens = cmd.split('^')
             lcmd = self.cmdHistory.getLast()
             if lcmd == '':
                return('')
            
             #print('>>>', cmd.replace(tokens[1], tokens[2]))
             if len(tokens) < 3:
                return('')
            
             return( lcmd.replace(tokens[1], tokens[2]) )

          return(cmd)  




      def displayCommandHistory(self, n, fromBegin=False, containingStr=''):
          
          if n > len(self.cmdHistory.commandHistory):
             n = len(self.cmdHistory.commandHistory)
          elif n <= 0:
               return
                               
          cList = self.cmdHistory.getN(n, fromBegin)
          #  counting commands
          if fromBegin:
             pos = 1
          else:   
             pos = len(self.cmdHistory.commandHistory)  - n + 1
             
          for c in cList:
              if containingStr == '':
                 print('\t', pos, '.   ', c, sep='')   
              else:
                try:    
                  if re.search(containingStr, c):  
                     print('\t', pos, '.   ', c, sep='')
                except Exception as reExc:
                     print('Error during regular expression:', str(reExc))
                     return
                  
                   
                #if containingStr.lower() in c.lower():
                #   print('\t', pos, '.   ', c, sep='')   
              
              pos += 1

                     



      def startShell(self):

          # To infinity and beyond...
          
          while True:                
             try:
              command = input('(v' + appConstants.APPVERSION + ')' +'{' + str(self.cmdExecutioner.commandsExecuted) + '}' + self.cmdExecutioner.configuration.get('Shell', 'commandPrompt', fallback="(default conf) >>> ") )
              command = command.strip()
     
              # Check if we need to expand the command i.e. the command is either !!, ! or ^.
              # If so, expand it and return the expanded form.
              command = self.expandCommand(command)
              
              
              if len(command) == 0:
                 continue
              else:
                   print(command)  
                           
              cParts = command.split()

              
              # Don't add history and quit commands to command history list
              # It will clog it.
              # TODO: Add h and q in expanded command list i.e. in self.cmdExpansions
              if cParts[0].lower() not in ['history', 'h', 'quit', 'q']:           
                 self.cmdHistory.addCommand( command )



              # NOTE: history/h command is the only command handled here!
              #       That's because the cHistory object is instantiated here
              # TODO: Check if there is a better design?
              if cParts[0] == 'history' or   cParts[0] == 'h':
                try:    
                 hArgs = ThrowingArgumentParser()
                 hArgs.add_argument('ncommands', nargs=argparse.REMAINDER, default='-1')
                 hArgs.add_argument('-s',  '--start', action='store_true')
                 args = vars( hArgs.parse_args(cParts[1:]) )
                except Exception as aEx:
                       print(str(aEx))
                       continue

                strFilter = ''
                
                if len(args['ncommands']) == 0:
                    n = len(self.cmdHistory.commandHistory) 
                else:
                      try:
                         n = int( args['ncommands'][0] )
                         if n > len(self.cmdHistory.commandHistory):
                            n = len(self.cmdHistory.commandHistory)
                         elif n <= 0:
                              continue
                        
                      except Exception as convEx:
                            n = len(self.cmdHistory.commandHistory)
                            if type( args['ncommands'][0] ) == str:
                               # assume string filter.
                               # TODO: Here we assume first argument
                               # is a complete regular expression.
                               strFilter = args['ncommands'][0]
                               
                               # The next is more correct one; TODO: Test it
                               #strFilter = ''.join(args['ncommands']) #[0]
                               

                
                if len( args['ncommands'] ) >= 2:
                   strFilter = args['ncommands'][1]
                   
                self.displayCommandHistory(n, args['start'], strFilter)
                continue 



              # Execute command
              # If executeCommand returns True, quit shell and terminate
              if self.cmdExecutioner.executeCommand( cParts ):                 
                 break
             
             except KeyboardInterrupt:
                 print("\nKeyboard interrupt seen.")


          # Save history 
          sts = self.cmdHistory.save()
          if sts != 0:
              print('Error', str(sts), 'writing .history file.')

          # kill any Chrome zombie process that remained when pyppeteer was used to download and process pages
          if self.cmdExecutioner.configuration.get('Crawler', 'forceBrowserCleanup', fallback='False').lower() == 'true':
             osP = osPlatform.OSPlatformFactory(self.cmdExecutioner.configuration).createPlatform()             
             if not osP.processIsRunning():
                print( utils.toString('Not running.\n') if self.cmdExecutioner.configuration.getboolean('DEBUG', 'debugging', fallback=False) else '', end='' )
             else:
                #print('Process running. Killing it...')
                print( utils.toString('\t[DEBUG] Chrome/Chromium processes running. Checking and killing...\n') if self.cmdExecutioner.configuration.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')
                # We kill all Chrome instances but excluding all these that were running
                # before start of WebScraper. These are in runningChromeInstances
                osP.killProcess(excludedPids=self.cmdExecutioner.runningChromeInstances)
             
             
          return





class httpResponse:
      
      def __init__(self, fm='static'):
            
          self.fetchMethod = fm
          self.status = -999          
          self.__requestResponse = None

          # We need a separate header dict since
          # the dicts returned by the 2 different calls fetching pages (and inside the __requestResponse)
          # are of different kind with regard to letter case. 
          # Here we make sure that all keys are lower case in any way
          # they appear in the original dicts.
          self.__headers = None
          
          self.html = None
          self.text = None

      # two values supported: static and dynamic
      def setFetchMethod(self, fm='static'):
          self.fetchMethod = fm


      def getFetchMethod(self):
          return(self.fetchMethod)  


      # normalizeCookies: if True this makes sure that
      # the format of cookies is a proper one to be parsed
      # by SimpleCookie class.
      # In particular, if more than one cookies are present in a response i.e. cookies in the form:
      #   <cookie-name>=<cookie-value>; expires=XXX, YYYYY ZZZZ GMT; Max-Age=NNN; path=OOO; domain=MMM; secure
      # then in some cases these are separated by a comma and in other situations by a newline.
      # If these cookies are separated by a comma, these cannot be parsed by the SimpleCookie class.
      # What normalizeCookies does is that it replaces the comma separating the coockies with a  newline character (\n)
      # so that they can be parsed by SimpleCookie.
      def setResponse(self, resp, normalizeCookies=False):
          if resp is None:
             return
            
          self.__requestResponse = resp
          self.setHeaders( resp.headers, normalizeCookies )



      def getResponse(self):
          return( self.__requestResponse )  



          
      def setHeaders(self, hdr, normalizeCookies=False):
            
          #for i,j in hdr.items():
          #    if i.lower() == 'set-cookie':
          #       print('\t', i, '=', j)
                 
          self.__headers = {k.lower(): v for k, v in hdr.items()}
          
          # Normalizing cookies: We use a regular expression to
          # replace only commas that are not part of the date.
          # TODO: This does not guarantee correctness. Need to make sure
          # that commmas are not as cookie values.
          if normalizeCookies:
             if not 'set-cookie' in self.__headers:
                # this means there is no set-cookie directive.   
                return
            
             self.__headers['set-cookie'] =  re.sub('(?<!Mon|Tue|Wed|Thu|Fri|Sat|Sun),', '\n', self.__headers['set-cookie'])  


          
      def printHeaders(self):
          print(self.__headers)
 
            
      def get(self, key, default=''):
          if  self.__headers is None:
              return(default)
            
          return( self.__headers.get(key.lower(), default) )


      # TODO: REmove me!
      def getText(self):
          if self.fetchMethod == 'static':
             return(self.text)
          elif self.fetchMethod == 'dynamic':
               return(self.text) 
          else:
               return('') 

      
      """  
      # During normalization we store the header key/value pairs in a
      # different dictionary as requestResponse.headers attribute can;t be set
      def normalizeHeaders(self):
          print('NORMALIZING HEADERS!')  
          self.headers = {k.lower(): v for k, v in self.requestResponse.headers.items()}
      """




# Was previously shellCommandExecutioner
class commandImpl:

      def __init__(self, cfg, rules = None):
          self.configuration = cfg
          self.totalCommands = 0
          self.commandsExecuted = 0
          self.extractionRules = rules

          # Here we gather all the ids of Chrome processes
          # that are *currently* running that we assume
          # are caused by a Chrome browser executed by the user.
          # We do this so that these ids are ignored when WebScraper
          # is configured to kill manually all Chromium instances when
          # pyppeteer is used to download/process a page.
          # Chromium seems to have a bug when closing and zombie processes
          # still remain.
          # These pids are passed to htmlRendering (by adding them to the
          # config settings object) so that these should be ignored when forceBrowserCleanup
          # is set to auto.
          # Notice that:
          # When forceBrowserCleanup is set to True, cleanup is carried out when the shell terminates (in commandShell)
          # When forceBrowserCleanup is set to Auto, cleanup is carried out when the download/processing
          # task terminates (in htmlRendering)
          self.runningChromeInstances = []
          if cfg.getboolean('Crawler', 'guardRunningChromeInstances', fallback=False):
             osP = osPlatform.OSPlatformFactory(cfg).createPlatform()
             rcI = osP.getImageProcessesInfo()
             for p in rcI:
                self.runningChromeInstances.append(p['pid'])    

          #print( self.runningChromeInstances )


      
      # Main entry point. Call this to execute commands given via the apps command line shell.
      # commandParts: a list of tokens comprising the command given, spearated by 
      #               whitespaces at the command line.
      #               For example, when the following is entered:
      #               (v0.1a){0}WebScraper >> crawl -M -n -1 -r rules/example5-en.wikipedia.exr -o csv/STATSORALG.csv  -C https://en.wikipedia.org/wiki/Statistics
      #               commandParts will contain all tokens separated by whitespaces i.e.
      #               commandParts = ['crawl', '-M', '-n', '-1', '-r', 'rules/example5-en.wikipedia.exr', '-o', 'csv/STATSORALG.csv', '-C', 'https://en.wikipedia.org/wiki/Statistics']
      #               First item commandParts[0] is always the command and is used to call the method with the same
      #               name in this class.
      #               
      def executeCommand( self, commandPartsList):
          
          self.totalCommands += 1  
          if not hasattr(self, commandPartsList[0]):
             self.defaultF(commandPartsList[0])
             return(False)
          
          self.commandsExecuted += 1
          return getattr(self, commandPartsList[0])(commandPartsList[1:])  





      # Executes a command given as a string
      # TODO: This has not been tested at all.
      
      def executeCommandS( self, commandString ):
          # Split command at whitespace  
          return( self.executeCommand(commandString.split()) )
            



      # What to execute when no relevant method is found. 
      # I.e. command is not supported
      # NOTE: s is a string; NOT A LIST
      
      def defaultF(self, s):
          print('Invalid command', s)
          return(False)



      def updateRunningChromeInstances(self):
          # TODO: This has to be moved out of here.  
          if not self.configuration.getboolean('Crawler', 'guardRunningChromeInstances', fallback=False):
             return(False)

          osP = osPlatform.OSPlatformFactory(self.configuration).createPlatform()
          rcI = osP.getImageProcessesInfo()
          # reset
          self.runningChromeInstances = []
          for p in rcI:
              self.runningChromeInstances.append(p['pid'])
              
          return(True)  



      ###############################################################################
      #
      # This next section contains the implementation of ths supported shell
      # commands. All methods below are application specific as they implement the
      # behavior of various commands. I.e. the config method implements the
      # behavior of the config command given at the shell prompt.
      #
      # TODO: The methods below should be put in a different class based
      # on some behavioral (command???, strategy???) design pattern???
      # 
      ###############################################################################  



      def q(self, a):
          return( True )
      
      def quit(self, a):
          return( True )
      



      def config(self, a):

          #Inline/nested function  
          def displayConfigSettings(cfg):
             if cfg is None:
                print('No configuration.')
                return          
          
             print("Configuration settings")
             for s in cfg.sections():
                 print("Section [", s, "]", sep="")
                 for key, value in cfg[s].items():
                     print( "\t-", key, "=", value)

          ####################################
          #  outer method config starts here
          ####################################
          
          print('Executing config >>>>>')
          displayConfigSettings(self.configuration)
          return(False)


      
      
      def joke(self, a):
          try:
            import pyjokes
            import random
            # value twister although mentioned in the docs, not supported (?) 
            rjk = pyjokes.get_joke(language="en", category=random.choice(['neutral',  'all']) )   
            print('"', rjk, '"', sep='')
            
            # Remove package
            # For testing purposes only; to see if/how this works. 
            del pyjokes
            
            return(False)
      
          except Exception as jkEx:
                 return(False)

     


      
      def updateBasedOnCSV(self, qF, csvF, xR, conf=None):

          #if not os.path.exists(qF):
          #   print('')   

          uQ = urlQueue.urlQueue(startNewSession=False, qF=qF, sQ=True)
          
          if not os.path.exists(csvF):
             print('CSV file [', csvF, '] not found. This is fatal in CSV mode. Terminating')
             return(False)

          uS = extractedDataSource.extractedDataFileCSVReader(csvF, sep=';')


          numProcessed = 0
          numUpdated = 0
          previousHost = ''
          while(True):
                try:

                   extractedData = uS.getNext()
                   if extractedData is None:
                      print('\nEmpty data. Terminating. Updated/processed:', numUpdated, '/', numProcessed)
                      break

                   targetUrl = extractedData['url']
                   pUrl = urlparse( unquote(targetUrl) )
                   
                   clrprint.clrprint( (numProcessed+1), '/', uS.getNumRows(), ') Updating [', targetUrl, '] last time accessed:[', extractedData['dateaccessed'], ']...', clr='yellow', sep=''  )

                   queueInfo = uQ.getByUrl( targetUrl )
                   if not queueInfo:
                      print('\t\t[DEBUG] Url [', targetUrl, '] NOT FOUND IN QUEUE! Adding to urlQueue')                   
                      uQ.add( targetUrl )
                   else:
                      print('\t\t[DEBUG] Url [', targetUrl, '] found in queue.')

                   
                   
                   if previousHost == pUrl.netloc:
                      delayValue = 0.5 #some value   
                      if conf.get('Crawler', 'delayModel', fallback='c') == 'h':
                         delayValue = abs( float( np.random.normal(conf.getfloat('Crawler', 'humanSleepTimeAvg', fallback='3.78'), conf.getfloat('Crawler', 'humanSleepTimeSigma', fallback='0.43'), 1)[0]))
                      else:
                         delayValue = conf.getfloat('Crawler', 'sleepTime', fallback='0.3') # TODO: Check fallback!
                       
                      #print('Sleeping for', delayValue)
                      time.sleep( delayValue )

                   previousHost = pUrl.netloc
                   
                   
                   numProcessed += 1
                   response = self.downloadURL(dUrl=targetUrl, rCookies = xR.requestCookies, uAgent=xR.requestUserAgent if xR.requestUserAgent != '' else None, renderPage=xR.renderPages, dynamicElem = xR.ruleDynamicElements, cfg = conf )
                   
                   if response.status != 200:
                      continue   

                   if response.get('Last-Modified', '') != '':
                      print('\t\t[DEBUG] Date comparison: NEW=(', response.get('Last-Modified', ''), ') OLD=(', queueInfo['lastmodified'], ')')   
                      if response.get('Last-Modified', '') == queueInfo.get('lastmodified', ''):
                         #print('\t\t[DEBUG] Date comparison: Not modified (', response.get('Last-Modified', ''), ') (', queueInfo['lastmodified'], ')')                      
                         print('\t\t[DEBUG] No change.')
                         continue # Not changed

                   newHash = utils.txtHash( response.text )
                   print('\t\t[DEBUG] oldHash=[', queueInfo.get('hash', ''), '] newHash=[', newHash,']', sep='')
                   if newHash == queueInfo.get('hash', ''):
                      print('\t\t[DEBUG] No change.')   
                      continue # Not changed


                   print('\t\t[DEBUG] Change detected [', targetUrl, ']', sep='')
                   
                   # There was a change. Extract data now.
                   pageData = xR.applyAllRules(targetUrl, response.html, conf.getboolean('DEBUG', 'debugging', fallback=False))
                   clrprint.clrprint(extractedData, clr='red')
                   #print( pageData )

                   uQ.updateTimeFetched(targetUrl)
                   uQ.updateStatus( targetUrl, response.status )
                   uQ.updateLastModified(targetUrl, response.get('Last-Modified', ''))
                   uQ.updatePageHash( targetUrl, newHash )

                   # Update csv file
                   if xRules.isRecordData(pageData):
                      xdt = xR.CSVFields(pageData)
                      xdt['dateaccessed'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S') 
                      xdt['url'] = targetUrl
                      clrprint.clrprint('\t[DEBUG] Adding ', xdt, clr='green', sep='')  
                      uS.updateExtractedData(targetUrl, xdt)
                      
                   else:
                     # Since this returned a recordList, iterate over
                     # the individual records and add then to the data frame
                     xdtList = pageData[xRules.getRecordListFieldName(pageData)]
                     #print('\t[DEBUG] Removing all rows with URL [', targetUrl, ']',  sep='')
                     uS.removeExtractedData( targetUrl )
                     for xdt in xdtList:
                         xdt['dateaccessed'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                         xdt['url'] = targetUrl  
                         clrprint.clrprint('\t[DEBUG] Adding ', xdt, clr='green', sep='')
                         uS.insertDataAtCurrentPosition(xdt)   

                   numUpdated += 1 

                    
                         
                except KeyboardInterrupt:
                      print('Control-C seen. Terminating. Updated/Processed:', numUpdated, '/', numProcessed , sep='')
                      break
                  
          print('Saving queue.....')
          uQ.saveQ()
          print('Saving csv.....')
          uS.save()
          return(True)            
            




      #
      # TODO: add cookie parameters also. These here are hardcoded
      #       and valid only for youtube
      #
      def prepareCookies(self, url, d):
          cookieList = []  
          for k,v in d.items():
            c={}
            c['name'] = k
            c['value'] = v
            c['url'] = url
            c['domain'] = '.youtube.com'
            c['path'] = '/'
            dtTime = datetime.datetime.strptime('2023-07-28T06:24:39.000Z', '%Y-%m-%dT%H:%M:%S.000Z')
        
            c['expires'] = datetime.datetime.timestamp(dtTime) #'2023-07-28T06:24:39.000Z'
            c['httpOnly'] = True
            c['secure'] = True
            c['samesite'] = 'None'
            cookieList.append( c )

          return(cookieList)   




      def htmlToText(self, html):
            
         def tag_visible(element):
             if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
                return False
             if isinstance(element, Comment):
                return False

             return True
            

         try:   
          soup = BeautifulSoup(html, 'html.parser')
          texts = soup.findAll(text=True)
          visible_texts = filter(tag_visible, texts)
          return u" ".join(t.strip() for t in visible_texts)
         except Exception as bsEx:
                print('\t[DEBUG] Error parsing with BS:', str(bsEx) )
                return('')

      #
      # Main method to download an URL.
      #
      # TODO: THIS HAS BECOME A SHAME. Needs to be seriously refactored!
      #
      def downloadURL(self, dUrl, rCookies={}, uAgent=None, renderPage=False, dynamicElem=[], cfg=None, launchPar={}, rHeader={}):
          print( utils.toString('\t[DEBUG] renderPages is [', renderPage, ']\n') if cfg.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='')  
          r = httpResponse()  
          if not renderPage:
             r.setFetchMethod('static')
             session = HTMLSession()
             #print('\t[DEBUG] Cookies:', rCookies)
             #cJar = utils.cookieJarFromDict(rCookies, dUrl)
             #print('\t[DEBUG] Request cookies:')
             #for cookie in cJar:
             #    print ( cookie.name, cookie.value, cookie.domain)

             # TODO: check if cfg is None
             '''
             if not rCookies:
                print( utils.toString('\t[DEBUG] No request cookies for this request\n') if cfg.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='')
             else:    
                print( utils.toString('\t[DEBUG] Using as cookies:', utils.cookieJarFromDict(rCookies, dUrl), '\n' ) if cfg.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='' )    
             '''
             
             h = rHeader
             if uAgent is not None and uAgent != '':
                h['User-Agent'] = uAgent

             if not rCookies:
                print( utils.toString('\t[DEBUG] No request cookies for this request\n') if cfg.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='')
             else:   
                # We include cookies in the header.
                # Tried to pass cookies using the cookies parameter of session.get() but
                # could not find appropriate way to set up the arguments.
                # TODO: Need to read the manual again and lookup source code to see how
                # to pass cookies to session.get()
                h['Cookie'] = utils.dictToCookieString(rCookies) 
                print( utils.toString('\t[DEBUG] Using as REQUEST cookies:', h['Cookie'], '\n' ) if cfg.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='' )

             
             #print( utils.toString('\t[DEBUG] Using as HEADER:', h, '\n' ) if cfg.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='' )
             #cks = utils.cookieJarFromDict(rCookies, dUrl)
                
             response = session.get(dUrl, cookies = {}, headers=h  )
             
             # The cookies will be separated by a comma ,. Hence we normalize these by replacing
             # this comma with a newline character.
             r.setResponse(response, normalizeCookies=True)
             try:
                r.status = int(response.status_code)
             except Exception as statusEx:
                    r.status = -5

                                 
             r.html = response.html
             r.text = response.text
             
          else:
                r.setFetchMethod('dynamic') 
                cks = {}
                if rCookies:
                   print( utils.toString('\t[DEBUG] Preparing cookies...\n') if cfg.getboolean('DEBUG', 'debugging', fallback=False) else '', end=''  )
                   #cks = self.prepareCookies(dUrl, rCookies)
                   cks = utils.cookiesFromDict(rCookies, dUrl)
                   print( utils.toString('\t[DEBUG] Cookies:', cks, '\n') if cfg.getboolean('DEBUG', 'debugging', fallback=False) else '', end='' )
                   
                htmlRndr = htmlRendering.htmlRenderer()
                
                # Set the configuarion file.
                # TODO: This make some arguments and instance variables of
                # htmlRendering OBSOLETE! REFACTOR THIS!!!
                htmlRndr.config = cfg
                htmlRndr.setDebugMode( cfg.getboolean('DEBUG', 'debugging', fallback=False) )
                #htmlRndr.asyncWaitTime = cfg.getfloat('Crawler', 'asyncWaitTime', fallback=1.4)
                htmlRndr.waitTime = cfg.getfloat('Crawler', 'asyncWaitTime', fallback=1.4)
                htmlRndr.takePageScreenshot = cfg.getboolean('Crawler', 'takePageScreenShot', fallback=False)
                htmlRndr.screenShotStoragePath = cfg.get('Storage', 'screenShotPath', fallback='.')

                # set additional or update headers
                htmlRndr.rqstHeader = rHeader

                # How to cleanup/close browser
                htmlRndr.forceBrowserCleanup = cfg.get('Crawler', 'forceBrowserCleanup', fallback='False')
                

                
                # Fetch url
                # TODO: timeout must be a setting
                rHTML = htmlRndr.render(url=dUrl, timeout=45, requestCookies=cks, userAgent=uAgent, scrolldown=4, maxRetries=5, dynamicElements=dynamicElem, launchParams=launchPar)                
                if rHTML is None:
                   r.status = -666
                   return(r)

                
                r.setResponse(htmlRndr.response, normalizeCookies=True) 
                                   
                try:   
                   r.status = int( htmlRndr.response._status )
                except Exception as statusEx:
                   r.status = -6
                      
                r.html = HTML( html=rHTML )
                r.text = rHTML
                
                                
                htmlRndr.cleanUp() # Not needed anymore
                

          
          return( r )


                





      
      #  
      # 
      #
      # 
      # Main crawl method!
      # Starts crawling from an initial URL.
      #
      # TODO: This method has become so ugly. Has to be refactored. Like seriously. 
      #
      #
      #
      #
      
     
      def crawl(self, a):
                
          try:
             # Supported arguments of crawl commans    
             cmdArgs = ThrowingArgumentParser()
             cmdArgs.add_argument('url',   nargs=argparse.REMAINDER, default=[] )
             cmdArgs.add_argument('-n', '--numpages', type=int, nargs='?' )
             cmdArgs.add_argument('-s', '--sleeptime', type=float, nargs='?' )
             cmdArgs.add_argument('-o', '--outputcsvfile', type=str, nargs='?', default='extracted' + datetime.datetime.now().strftime("%d-%m-%Y@%H-%M-%S") + '.csv' )
             cmdArgs.add_argument('-q', '--queuefile', type=str, default='.queue' )
             
             cmdArgs.add_argument('-M', '--mirror', action='store_true' )
             cmdArgs.add_argument('-r', '--rules',  nargs='?' )
             cmdArgs.add_argument('-H', '--humandelay', action='store_true' )             
             cmdArgs.add_argument('-C', '--continue', action='store_true' )
             cmdArgs.add_argument('-D', '--dfs', action='store_true' )
             # minimum hit rate
             cmdArgs.add_argument('-HR', '--minhitrate', type=float, nargs='?' )

             # content type
             cmdArgs.add_argument('-CT', '--contenttype', type=str, nargs='?' )

             # Use page pyppeteer to download page  
             cmdArgs.add_argument('-R', '--render', action='store_true' )
             cmdArgs.add_argument('-ST', '--screenshot', action='store_true' )
             
             cmdArgs.add_argument('-U', '--update', action='store_true' )
             cmdArgs.add_argument('-p', '--startposition', type=int, nargs='?', default=0 )

             # Mute library i.e. don't print out library description when starting
             cmdArgs.add_argument('-ML', '--mutelib', action='store_true' )
             
             cmdArgs.add_argument('-G', '--debug', action='store_true' )
             
             args = vars( cmdArgs.parse_args(a) )

          except Exception as gEx:
                print( str(gEx) )
                return(False)    

          

          # We copy the existing configuration file in order to not
          # modify original settings with arguments given by the shell
          cmdConfigSettings = copy.deepcopy( self.configuration )


          # We add here all currently running chrome instances process ids. This is used when using Chromium (pyppeteer) to
          # download/render pages.
          # This is done so that during auto mode, no Chrome browser used by the HUMAN USER is killed.
          # TODO: Move down? Just before calling render?
          cmdConfigSettings.set('__Runtime', '__runningChromeInstances', self.runningChromeInstances)

          

          #
          # Override now any configuration setting with the command line arguments given to crawl.
          #

          # We first update this option to make sure that calls will work properly.
          if args['debug']:
             cmdConfigSettings.set('DEBUG', 'debugging', 'True' )

          # Override settings with shell arguments
          if args.get('numpages') is not None:
             cmdConfigSettings.set('Crawler', 'maxpages', args.get('numpages'))


          if args.get('sleeptime') is not None:             
             cmdConfigSettings.set('Crawler', 'sleepTime', args.get('sleeptime') )
             cmdConfigSettings.set('Crawler', 'delayModel', 'c' )   

                          
          if args.get('humandelay'):
             cmdConfigSettings.set('Crawler', 'delayModel', 'h' )
          else:
             cmdConfigSettings.set('Crawler', 'delayModel', 'c' )   
                

          if args.get('dfs'):
             cmdConfigSettings.set('Crawler', 'traversalStrategy', 'dfs' )
          else:
             cmdConfigSettings.set('Crawler', 'traversalStrategy', 'bfs' )     

          if args.get('rules') is None:
             exRules = self.extractionRules
          else:
                print( utils.toString('\t[DEBUG] Loading extraction rules from [', args['rules'], ']...') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='')
                try:
                  with open(args['rules'],  encoding='utf-8', errors='ignore', mode='r') as f:
                     exRules = xRules.loadLibrary(f.read())
                     print( utils.toString('ok.\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='')

                     
                     
                except Exception as flEx:
                       print(str(flEx) )
                       return(False)

          if args['render']:
             exRules.renderPages = True   

          if args['screenshot']: 
             cmdConfigSettings.set('Crawler', 'takePageScreenShot', 'True')
            
          if args.get('minhitrate'):
             cmdConfigSettings.set('Crawler', 'minHitRate', args.get('minhitrate') )   

          if args.get('contenttype'):
             cmdConfigSettings.set('Crawler', 'allowedContentTypes', args.get('contenttype') )
          

          
          #exRules.libraryDescription
          if not args['mutelib']:   
             #clrprint.clrprint('\nUsing library:[', exRules.libraryDescription, ']', clr='purple', sep='')   
             print('')
             clrprint.clrprint( utils.fL('Using library:[' +  exRules.libraryDescription + ']\n', every=60,  startOver=True), clr='purple', sep='' )

          #
          # We update the pid of running Chrome instances
          # started by the user, in order to avoid killing them
          # during browser cleanup processes.
          #
          self.updateRunningChromeInstances()

          print( utils.toString('\t[DEBUG] crawl params [', ' '.join(a), ']...') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='')

          if args['update']:
             print("")
             print("")   
             print("#######################################################################")
             print("#")
             print("#")
             print("#")
             print("#       Entering UPDATE MODE - USING OLD MODEL!")   
             print("#       NOT TESTED WITH NEW CRAWL MODEL")
             print("#       Execute on your own responsibility")
             print("#")
             print("#######################################################################")
             print("")
             print("")
             #time.sleep( delayValue )

             self.updateBasedOnCSV( args['queuefile'], args['outputcsvfile'], exRules, cmdConfigSettings)

             #self.__updateCrawl( args['queuefile'], args['outputcsvfile'], cmdConfigSettings, exRules, args.get('numpages'), args['mirror'] )
             return(False)


          

          if exRules is None or exRules.library is None:
             print('[WARNING] Not extraction library found.')
             
          
          #linkQueue = []
          #linkQueue.append( args['url'][0] )
          #visitedPageHashes = []
          pageHandlingTimes = []

          # used to determine if a delay should be in order
          previousHost = ''

          # number of pages processed
          numProcessed = 0
          
          numprocessingErrors = 0
          numHTTPErrors = 0
          numNetErrors = 0

          numExtracted = 0 # Number of matches found/extracted
          # Bytes downloaded 
          totalBytes = 0

          xDataDF = None
          if exRules is not None and len( exRules.csvLineFormat ) > 0:
             # Create a new, empty data.frame that will store all extracted data.
             # The data.frame will have as columns the url and datetime the url was accessed
             # (these are always and everytime added) as well as the fields specified in the
             # field csvLineFormat of the library.
             xDataDF =  pd.DataFrame(columns= (['dateaccessed', 'url'] + exRules.csvLineFormat) )  

          if args['continue']:
             if os.path.exists( args['outputcsvfile'] ):
               print( utils.toString('\t[DEBUG] Loading existing csv file [', args['outputcsvfile'], ']\n') if self.configuration.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='')    
               xDataDF = pd.read_csv( args['outputcsvfile'], sep=';', header=0, quoting=csv.QUOTE_NONNUMERIC)

          # Create URLqueue object   
          uQ = urlQueue.urlQueue(qSz=cmdConfigSettings.getint('Crawler', 'maxQueueSize', fallback=-1),
                                 qMemSz=cmdConfigSettings.get('Crawler', 'maxQueueMemorySize', fallback='-1'),
                                 startNewSession=not args['continue'],
                                 qF=args['queuefile'], sQ=True, tS=cmdConfigSettings.get('Crawler', 'traversalStrategy', fallback='bfs') ) 



           

          if not args['url']:
             print('No starting URL given. Terminating.')
             return(False)


          # Process now the seed url given.
          # This might be a file though containing urls to be loaded into
          # the queue, so check this first.
          
          absolutePath = os.path.abspath( args['url'][0] )
          print( utils.toString('\t[DEBUG] Checking if: [', absolutePath, '] is file...\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='' )  
          if os.path.exists( absolutePath ):
             # yes, it was a file. Read lines and add these
             # into the queue. We assume that every line is a
             # separate URL.
             with open(absolutePath) as f:
                   urls = f.read().splitlines()
                   
             for u in urls:
                 print( utils.toString('\t[DEBUG] Adding to queue url from file: [', u, ']\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='' )  
                 uQ.add(u)  
          else:      
              # Is probably url. I.e. one url given in command line. Add it to queue
              print( utils.toString('\t[DEBUG] Adding to queue url: [', args['url'][0], ']\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='' )   
              uQ.add( args['url'][0] )


          # Allowed protocol prefixes.  
          allowedNetworkSchemes = [v.strip().lower() for v in cmdConfigSettings.get('Crawler', 'allowedSchemes', fallback='http,https').split(',')]

          lastAutosave = time.perf_counter()
          crawlStarted  = time.perf_counter()

          # counts how many times we reached below minimum hit rate
          # NOT USED YET.
          belowMinHitRateCount = 0
          
          # Main loop starts here
          # Processing URLs starts from here.
          try:
                
            while (True):
                  
                 try:                                                        
                  currentUrl = uQ.getNext()
                  if currentUrl is None:
                     #print( '\t[DEBUG] Empty Queue' if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '')
                     print('\n\nQueue empty. Terminating...\n\n')
                     break
                  
                 except Exception as popEx:
                   print('Error:', str(popEx))   
                   break    

                 # transform average seconds/page to pages/second
                 pgsPerSec = '---'
                 if len(pageHandlingTimes) > 0:
                    pgsPerSec = '{:.2}'.format( 1/statistics.mean(pageHandlingTimes) )

                 kBPerSec = -1
                 elapsed = float('{:.0}'.format(time.perf_counter() - crawlStarted))
                 if elapsed > 0:
                    kBPerSec = float('{:.0}'.format(totalBytes / elapsed) ) / 1024
                    
                 exHitRate = 0.00 # extraction hit rate: percentage of pages processed from which data was actually extracted (i.e. hits)
                 if uQ.fetchedUrlsCount() != 0:
                    exHitRate = numExtracted/uQ.fetchedUrlsCount()
                    
                 clrprint.clrprint('\n', (numProcessed + 1), ') >>> Doing [', currentUrl, '] Queue:', uQ.queueSize(), ' (mem: ', uQ.queueMemorySize(), 'B/', "{:.2f}".format(uQ.queueMemorySize()/(1024*1024)), 'M/', uQ.qMemorySize ,') Pending:', uQ.pendingUrlsCount(),  ' Fetched:', uQ.fetchedUrlsCount(), ' Extracted:', numExtracted, '  [Avg pps:', pgsPerSec, ' (', '{:.3f}'.format(kBPerSec),  'KB/sec) Hit rate:', "{:.4f}".format(exHitRate) , ' (min:', "{:.4f}".format( cmdConfigSettings.getfloat('Crawler', 'minHitRate', fallback=-1.0) ) , ')]', clr='yellow', sep='')

                 tmStart = time.perf_counter() # start counting time

                 # Download URL. We'll try a number of times if
                 # network errors occur - hence the loop.
                 while (True):
                  try:
                    pUrl = urlparse( unquote(currentUrl) )    
                    
                    # Is the protocol prefix supported? Default supported are http and https                    
                    if pUrl.scheme.lower() not in allowedNetworkSchemes:
                       #print( '\t>>>>>>>>>>>>>> [DEBUG] Unsupported network scheme: [', pUrl.scheme.lower(), ']')      
                       print( utils.toString('\t[DEBUG] Unsupported network scheme: [', pUrl.scheme.lower(), ']\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '',  end='' )   
                       response = httpResponse()
                       response.status = -11
                       break
                    
                    uA = None
                    if exRules.requestUserAgent.strip() != "":
                       uA = exRules.requestUserAgent

                    
                    response = self.downloadURL(dUrl=currentUrl, rCookies = exRules.requestCookies, uAgent=uA, renderPage=exRules.renderPages, dynamicElem = exRules.ruleDynamicElements, cfg = cmdConfigSettings, launchPar=exRules.launchParameters, rHeader=exRules.requestHeader )

                    # TODO: FIX ME
                    if response is None:
                       pass   
                     
                    print( utils.toString('\t[DEBUG] Response Cookies: ', response.get('Set-Cookie', ''), '\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='' )                    


                     


                    # Get response cookies and parse them into
                    # a dictionary where each key/value pair
                    # is a separate cookie in the form <cookie-name>:<cookie-value>
                    #
                    # TODO: This has to be moved out of here because cookies of ignored resources (e.g. due to their content-type)
                    # should not be stored. This has to be checked.
                    cDict = utils.cookieStringToDict(response.get('Set-Cookie', ''))                    

                    if not cmdConfigSettings.getboolean('Crawler', 'ignoreResponseCookies', fallback=True):
                       if cDict:                          
                          icL = [ckn.strip() for ckn in cmdConfigSettings.get('Crawler', 'ignoredCookies', fallback='').lower().split(',')]
                          for k,v in cDict.items():

                              if k.lower() in icL:
                                 print( utils.toString('\t[DEBUG] Ignoring cookie ', k, '. In ignoredCookie list\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='' )                                
                                 continue
                              
                              if k not in exRules.requestCookies:
                                   print( utils.toString('\t[DEBUG] ADDING cookie ', k, '.\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='' ) 
                                   exRules.requestCookies[k] = v
                                   
                          print( utils.toString('\t[DEBUG] Response Cookies UPDATED: ', exRules.requestCookies, '\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='' )                             
                                        
                    break
                  
                  except requests.exceptions.SSLError as sslErr :
                         # That's an SSL error. This is handled differently as there won't be
                         # any more retries and the process is stopped with an
                         # special error. 
                         print('[DEBUG] SSL error:', str(sslErr) )
                         # Create a httpResponse object with an appropriate status
                         # so that the url will be updated.
                         response = httpResponse()
                         response.status = -9                         
                         break 

                  except requests.exceptions.Timeout as tmErr:
                         print('[DEBUG] Timeout error:', str(tmErr) )
                         response = httpResponse()
                         response.status = -7
                         break

                  except requests.exceptions.TooManyRedirects as tmrErr:
                         print('[DEBUG] Redirect error:', str(tmrErr) )
                         response = httpResponse()
                         response.status = -8
                         break
                        
                  except requests.exceptions.ConnectionError as cErr:
                         # We could not connect
                         print('[DEBUG] General connection error:', str(cErr) )
                         response = httpResponse()
                         response.status = -4
                         break
                         
                  except Exception as netEx:
                        # Another exception happened. Usually this
                        # means a network error. In such cases
                        # the same url will be tried a number of
                        # times. If all retries fail, the process is stopped
                        # as this may mean a serious error.
                        print('[DEBUG] Network error:', str(netEx) )
                        numNetErrors += 1
                        if numNetErrors >= 3:
                           # Exceeded maximum number of tries without
                           # sucess. Save the queue and extracted data
                           # and terminate the crawl.
                           #
                           # TODO: a break here would be more appropriate...   
                           uQ.saveQ()
                           if xDataDF is not None:
                              xDataDF.to_csv( args['outputcsvfile'], index=False, sep=';', quoting=csv.QUOTE_NONNUMERIC )
                              
                           uQ.updateStatus( currentUrl, -667 )
                           print('[DEBUG] Too many errors. Stopping.')   
                           return(False)   



                 #
                 #
                 # Url has been fetched.
                 # Process the response and the page content.
                 #
                 #

                 

                 # Update the URL in the URLQueue with the data
                 # from the response
                 uQ.updateTimeFetched(currentUrl)
                 uQ.updateStatus( currentUrl, response.status )
                 uQ.updateContentType( currentUrl, response.get('Content-Type', '') )
                 uQ.updateLastModified( currentUrl, response.get('Last-Modified', '') )



                 # Check if status is ok.
                 # If not, continue to next url.
                 if response.status != 200:
                    numHTTPErrors += 1
                    print( utils.toString('\t[DEBUG] Http status [', response.status, ']\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='' )
                    continue # Get next url

                          

                 # Check if content-type is ok.
                 # If not, continue to next url settings the status to a very specific value to indicate
                 # that this resource was in essence ignored.
                 if re.search( cmdConfigSettings.get('Crawler', 'allowedContentTypes', fallback=''), response.get('Content-Type', '') ) is not None:
                    clrprint.clrprint( utils.toString('[DEBUG] Content type [', response.get('Content-Type', ''), '] MATCHED this pattern [',  cmdConfigSettings.get('Crawler', 'allowedContentTypes', fallback=''),']\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='', sep='', clr='green')
                 else:   
                     uQ.updateStatus( currentUrl, -700 )  
                     clrprint.clrprint( utils.toString('[DEBUG] Content type [', response.get('Content-Type', ''), '] DID NOT MATCH pattern [',  cmdConfigSettings.get('Crawler', 'allowedContentTypes', fallback=''),']\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='', sep='', clr='red')
                     continue # next URL from queue
                 
                     

                                  
                 # Calculating Content length.
                 # If no Content-Length is present in the response header, content length is
                 # calculated by the data received.
                 # NOTE: Content-length for textual data is calculated differently from
                 #       binary data.
                 pHash = ''
                 #TODO: Check WTF .get() is cast to int?????? What  were i thinking???
                 pageContentLength = int( response.get('Content-Length', '-2') )      
                 if utils.isText( response.get('Content-Type', '')  ):
                    # This is text data.
                    if pageContentLength < 0:
                       # Since this is text data, len() on the received data can be used.   
                       pageContentLength = len( response.text )

                    pHash = utils.txtHash( response.text )   
                 else:
                     # TODO: If this was fetched using dynamic method,
                     # the next does not work. There is a bug with pyppeteer when using the
                     # default Chromium browser.                     
                     if pageContentLength < 0:
                        try:   
                           pageContentLength = len( response.getResponse().content )
                        except Exception as pclEx:
                           pageContentLength = -56   

                     pHash = utils.byteHash(response.getResponse().content)
                        
                 #   print('\t[DEBUG] Incompatible content type', response.get('Content-Type', '') )
                 #   continue
                    
                     
                 uQ.updateContentLength( currentUrl, pageContentLength )
                 if pageContentLength <= 0 :
                    print( utils.toString('\t[DEBUG] Zero content length! (wtf???)\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')   
                    uQ.updateStatus( currentUrl, -999 )
                    continue
                      
                 clrprint.clrprint( utils.toString('\t[DEBUG] HttpStatus: [', response.status, '] ContentType: [', response.get('Content-Type', ''), '] ContentEncoding: [', response.get('Content-Encoding', '????') ,'] ContentLength: [', pageContentLength,']\n'  ) if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='', clr='purple' ) 
                 #clrprint.clrprint( utils.toString('[DEBUG] Content type [', response.get('Content-Type', ''), '] MATCHED this pattern [',  cmdConfigSettings.get('Crawler', 'allowedContentTypes', fallback=''),']\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='', sep='', clr='green')
                 print(utils.toString('\t[DEBUG] Hash: ', pHash, '\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='' )

                 # Have we aleadt seen this content (NOTE: not url)?
                 # If so, discard it; move to next
                 if uQ.hInQueue(pHash):
                    print( utils.toString('\t[DEBUG] Same hash [', pHash, '] seen. Url:', currentUrl, '\n') if self.configuration.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='')
                    continue

                 uQ.updatePageHash( currentUrl, pHash )
                 
                                   
                 # Save to file if so required
                 # TODO: Refactor this. This is awfull....
                 # TODO: has a bug when saving files with extension e.g.:https://www.econ.upatras.gr/sites/default/files/attachments/tmima_politiki_poiotitas_toe_v3.pdf
                 #       does not 
                 if args['mirror']:
                    if not utils.saveWebPageToLocalFile(currentUrl, response, args['mirror'], cmdConfigSettings.get('Storage', 'mirrorRoot', fallback='')):
                       print( utils.toString('\t[DEBUG] Error saving file\n') if self.configuration.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')   
                    

                 totalBytes += pageContentLength

                 

                 # As reference, deciding html content is based 
                 # on the following chart: https://www.iana.org/assignments/media-types/media-types.xhtml 
                 if not utils.isHTML( response.get('Content-Type', '') ):                    
                    continue   

                 
                 
                 ###############################################################################
                 #
                 # This url is valid and urlqueue has been updated with the respective
                 # data.
                 # Now, apply all rules of the loaded library to the downloaded content.
                 #
                 ###############################################################################
                 
                 if exRules is None or exRules.library is None:
                    print(utils.toString('\t[DEBUG] No library present. Skipping extraction.\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')   
                    continue
                 else:
                      print(utils.toString('\t[DEBUG] Extracting using library: ', exRules.libraryDescription, '\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')  


      
                 # pageData will contain all the extracted/scraped data from the page after
                 # all rules have been applied.
                 # pageData will have the extracted data in the form of <key, value> pairs where
                 # key is the rule name and value the extracted value by that rule.
                 #
                 # The data extracted by each rule, updates this dictionary.
                 #
                 # NOTE: pageData may contain a single record or a list of records (recordlist) originating
                 #       from the page extraction. This will determine how pageData will be
                 #       processed/stored later.

                 #pageData = {}

                 pageData = exRules.applyAllRules(currentUrl, response.html, cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False))
                 
                 extractedLinks = pageData.get('getLinks', [])
                 
                 print( utils.toString('\t[DEBUG] Total of [', str(len(extractedLinks)), '] links extracted\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')
                 getLinksRule = exRules.get('getLinks')
                 tB = time.perf_counter()
                 # Process all links now and add them
                 # to the queue.
                 for lnk in extractedLinks:
                       
                     if lnk.startswith('#'):
                        continue
                  
                     absoluteUrl = urljoin( currentUrl, lnk )
                     cUrl = utils.canonicalURL( absoluteUrl )
                     # Does URL match condition? If so, add it to the queue. 
                     # TODO: move the next check inside .apply()???
                     if getLinksRule:
                        if re.search( getLinksRule.ruleContentCondition, cUrl) is not None:  
                           uQ.add( cUrl ) # Add it to the URL queue
                        
                 print( utils.toString('\t[DEBUG] All links done in ', time.perf_counter() - tB, ' sec\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end=''  ) 

                 




                        
                 print(utils.toString('\nExtracted page data:', pageData, '\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end=''  )
                                  


                 #   
                 # Store extracted data
                 #
                 # TODO: handle differently recordlist and record types of extractions.
                 #

                 # Extract fields required by csv

                 print(utils.toString('\t[DEBUG] Extracted data is record:', xRules.isRecordData(pageData), '\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')
                 print( utils.toString('\t[DEBUG] Extracted data is recordlist:', xRules.isRecordListData(pageData), '\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')
                 if xRules.isRecordData(pageData):
                    # Get extracted data to generate csv line.
                    # We generate a line only if a minimum percentage of
                    # extracted keys in pageData do have a value i.e. are non empty.
                    xdt = exRules.CSVFields(pageData, debug=cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False), reqFilled=exRules.requiredFilledFields, minFilled=exRules.allowedMinimumFilled)
                    if xdt:
                       xdt['dateaccessed'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')  
                       xdt['url'] = currentUrl
                       clrprint.clrprint('\t\t[DEBUG] Adding [', xdt, ']',  clr='green')
                       # Append extracted data to data frame.
                       xDataDF = pd.concat([xDataDF, pd.DataFrame.from_records([ xdt ])])
                    #else:
                    #     print('NOT ADDING!') 
                       
                 else:
                       recordList = pageData[xRules.getRecordListFieldName(pageData)]
                       for r in recordList:
                           # Extract from dict fields that should be written to csv file  
                           csvr = exRules.CSVFields(r, debug=cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False), reqFilled=exRules.requiredFilledFields, minFilled=exRules.allowedMinimumFilled)
                           # TODO: check here is csvr is kinda empty
                           if not csvr:
                              print(utils.toString('\t[DEBUG] Recordlist/ csvFields returned empty dictionary.\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')   
                              continue   
                                 
                           csvr['dateaccessed'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                           csvr['url'] = currentUrl
                           clrprint.clrprint('\t\t[DEBUG] (record list) Adding [', csvr, ']', clr='green')
                           xDataDF = pd.concat([xDataDF, pd.DataFrame.from_records([ csvr ])])
                       
                                           
                 
                 numProcessed += 1

                 if xDataDF is not None:
                    numExtracted = xDataDF.shape[0]
                 else:
                    numExtracted = 0

                 # Check if some limits have been reached

                 # MaxPages
                 if cmdConfigSettings.getint('Crawler', 'maxPages', fallback=-1) > 0:
                    if numProcessed >= cmdConfigSettings.getint('Crawler', 'maxPages', fallback=-1):
                       print('\nTerminating. Reached page limit of [', cmdConfigSettings.getint('Crawler', 'maxPages', fallback=-1), ']', sep='' ) 
                       break

                 # MinHitRate
                 # if cmdConfigSettings.getfloat('Crawler', 'minHitRate', fallback=-1.0) > 0:
                       
                 if exHitRate < cmdConfigSettings.getfloat('Crawler', 'minHitRate', fallback=-1.0):
                       belowMinHitRateCount += 1
                       # if we go below hit rate more than minHitRateSamples consecutive times,
                       # the process terminates.
                       if belowMinHitRateCount >= cmdConfigSettings.getint('Crawler', 'minHitRateSamples', fallback=50):
                          print('\nTerminating. Reached below minimum hit rate', cmdConfigSettings.getfloat('Crawler', 'minHitRate', fallback=-1.0), ' more than', cmdConfigSettings.getint('Crawler', 'minHitRateSamples', fallback=50), 'consecutive times.\n' )   
                          break
                 else:
                          belowMinHitRateCount = 0 # reset
                          

                 tmEnd = time.perf_counter()
                 pageHandlingTimes.append( tmEnd - tmStart )
                 print( utils.toString('\t[DEBUG] Average page handling time: ', '{:.4}'.format( statistics.mean(pageHandlingTimes) ), ' seconds\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='' )
                 if len(pageHandlingTimes) >= cmdConfigSettings.getint('Crawler', 'maxTPPSamples', fallback=50):
                    print( utils.toString('\t[DEBUG] Cleaning timing list (', len(pageHandlingTimes), ')\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='')   
                    pageHandlingTimes.clear()


                 # Should we autosave?
                 if cmdConfigSettings.getboolean('Crawler', 'autoSave', fallback=False):
                  if (time.perf_counter() - lastAutosave) >= cmdConfigSettings.getint('Crawler', 'autoSaveInterval', fallback=200):   
                    print( utils.toString('\t[DEBUG] Autosaving...(elapsed:', (time.perf_counter() - lastAutosave), ' seconds)\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')    
                    try:
                        uQ.saveQ()
                        if xDataDF is not None:
                           xDataDF.to_csv( args['outputcsvfile'], index=False, sep=';', quoting=csv.QUOTE_NONNUMERIC )

                        lastAutosave = time.perf_counter()
                    except Exception as asEx:
                           print('\t[DEBUG] Error autosaving!', str(asEx) )
                           

                    
                 # Sleep only if previous request was on the same server
                 if previousHost == pUrl.netloc:
                    if cmdConfigSettings.get('Crawler', 'delayModel', fallback='c') == 'h':
                       delayValue = abs( float( np.random.normal(cmdConfigSettings.getfloat('Crawler', 'humanSleepTimeAvg', fallback='3.78'), cmdConfigSettings.getfloat('Crawler', 'humanSleepTimeSigma', fallback='0.43'), 1)[0]))
                    else:
                       delayValue = cmdConfigSettings.getfloat('Crawler', 'sleepTime', fallback='0.3') # TODO: Check fallback!
                       
                    print( utils.toString('\t[DEBUG] Sleeping for ', delayValue, ' seconds\n') if cmdConfigSettings.getboolean('DEBUG', 'debugging', fallback=False) else '', sep='', end='')   
                    time.sleep( delayValue )

                 previousHost = pUrl.netloc
                 
                   
          except KeyboardInterrupt:
                 print('Control-C seen. Terminating. Processed ', numProcessed)
                 #return(False)
                 #break


          print('\nSaving extracted data to [', args['outputcsvfile'], '] (# rows:', xDataDF.shape[0] if xDataDF is not None else '???',')...', sep='', end='')
          if xDataDF is None:
             print('done (empty data frame)')   
          else:      
            try:    
             xDataDF.to_csv( args['outputcsvfile'], index=False, sep=';', quoting=csv.QUOTE_NONNUMERIC )
             print( 'done.')
            except Exception as scsvEx:
                  print('Error:', str(scsvEx),)
          
          if uQ.qSave: 
             print( utils.toString('[DEBUG] Saving queue...') if self.configuration.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')       
             uQ.saveQ()
             print( utils.toString('done.\n') if self.configuration.getboolean('DEBUG', 'debugging', fallback=False) else '', end='')


          # Display some statistics 
          exRules.libStats()
          
          print('\nFinished in (h:m:s) ', str(datetime.timedelta(seconds= float('{:.0}'.format(time.perf_counter() - crawlStarted)))) )
          return(False)


      def ps(self, a):
         try:
            cmdArgs = ThrowingArgumentParser()
            cmdArgs.add_argument('pimagename',   nargs=argparse.REMAINDER, default=[] )
            cmdArgs.add_argument('-r', '--rules',  nargs='?' )
            cmdArgs.add_argument('-R', '--rulename',  nargs='?' )
            
            args = vars( cmdArgs.parse_args(a) )
         except Exception as argEx:
                 print('Error.', str(argEx) )
                 return(False)


         osP = osPlatform.OSPlatformFactory(self.configuration).createPlatform()
         tp = ''
         if args['pimagename']:
            pList = osP.getProcessInfoByName( args['pimagename'][0] )
            tp = args['pimagename'][0]
         else:
            pList = osP.getImageProcessesInfo()
            tp = osP.processName

         print('Querying for [', tp, '] Total of ', len(pList), sep='')
         for p in pList:
              if p['pid'] in self.runningChromeInstances: 
                 print('\t', p['pid'], p['name'], p['create_time'], '(IN running chrome list)')
              else:
                 print('\t', p['pid'], p['name'], p['create_time'], '(NOT IN running chrome list)')   
                    

         return(False)    




      def killChrome(self, a):
          try:
            cmdArgs = ThrowingArgumentParser()    
            cmdArgs.add_argument('-A', '--allprocs',  action='store_true' )
            args = vars( cmdArgs.parse_args(a) )
          except Exception as argEx:
                print(str(argEx))
                return(False)
            
          osP = osPlatform.OSPlatformFactory(self.configuration).createPlatform()
          #pList = osP.filterProcesses( '(?i)chrome' )
          #print( pList )
          if not osP.processIsRunning():
             print('Not running.')
          else:
                #print('Process running. Killing it...')
                print( utils.toString('[DEBUG] Chrome/Chromium processes running. Checking and killing...') if self.configuration.getboolean('DEBUG', 'debugging', fallback=False) else '')
                if args['allprocs']:
                   osP.killProcess()
                else:   
                   osP.killProcess(excludedPids=self.runningChromeInstances)   

          return(False)


      def rcpids( self, a):
          print( self.runningChromeInstances)
          return(False)

      def urcpids(self, a):
          osP = osPlatform.OSPlatformFactory(self.configuration).createPlatform()
          rcI = osP.getImageProcessesInfo()
          self.runningChromeInstances = []
          for p in rcI:
              self.runningChromeInstances.append(p['pid'])

          return(False)    
            

      #
      # TODO: What to do with this method? Keep, remove, refactor???
      #
      def loadResource( self, resource, xL=xRules.ruleLibrary() ):
          # Is this a file?  
          if os.path.exists(resource):
             with open(resource,mode='r') as f:
                fcnt = f.read()

             h = HTML(html=fcnt) 
             return(None, h)

          rsp =self.downloadURL( dUrl=resource, rCookies=xL.requestCookies, uAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0", renderPage=xL.renderPages, cfg=self.configuration)
          return(rsp, rsp.html)
      
          '''
          s = HTMLSession()
          response = s.get(resource)
          return( response, response.html )
          '''






      def applyRules(self, a): 

          pageData = {}  
          try:
            cmdArgs = ThrowingArgumentParser()
            cmdArgs.add_argument('url',   nargs=argparse.REMAINDER, default=[] )
            cmdArgs.add_argument('-r', '--rules',  nargs='?' )
            cmdArgs.add_argument('-R', '--rulename',  nargs='?' )

            # Start in batch or interactive mode of applyRules
            cmdArgs.add_argument('-B',  '--batchmode', action='store_true')
            
            cmdArgs.add_argument('-T', '--extracttext',  action='store_true' )

            args = vars( cmdArgs.parse_args(a) )
          except Exception as argEx:
                 print('Error.', str(argEx) )
                 return(False)

          if args.get('rules', '')  == '':
             print('No .exr file given.')
             return(False)

          try:
             print('Loading library file [', args['rules'], ']...', end='')   
             with open(args['rules'],  encoding='utf-8', errors='ignore', mode='r') as f:          
                  xLib = xRules.loadLibrary(f.read())
             print('ok')     
          except Exception as rFile:
                  print('Error reading rule file', args['rules'])
                  return(False)  

          print('\tLibrary description:', xLib.libraryDescription)
          print('\tNumber of rules :', len(xLib.library) )
          targetRule = None
          if args.get('rulename') is None:
             print('\tRule: Applying all rules in library')   
          else:      
             #print('Checking if rule [', args.get('rulename', ''), '] exists...')   
             allRNames = []   
             for r in xLib.library:
                 allRNames.append( r.ruleName )  
                 if r.ruleName == args.get('rulename'):
                    targetRule = r
                    break
                  
             if targetRule is None:
                print('\tRule:', args.get('rulename', ''), ' not found in library (', allRNames, ')')
                return(False)
             else: 
                 print('\tRule: Found in library (', targetRule.ruleName, ')')

          
          if len(args.get('url', [])) == 0:
             print('No url given.')
             return(False)


          if targetRule is not None and not targetRule.ruleMatches(args['url'][0]):
             print('Cannot apply rule to this url. URl does not match')
             return(False)

          try:
             # Fetch url
             response, responseHtml = self.loadResource(args['url'][0], xL = xLib)
             
          except Exception as readEx:
                  print('ERROR.', str(readEx))
                  return(False)
          
          #return(False)

          
             
          if targetRule is not None:
             print('* Applying rule', targetRule.ruleName)   
             xData = targetRule.apply( responseHtml )
             pageData.update(xData)
          else:
               '''   
               print('Rule list:') 
               for r in xLib.library:
                   if not r.ruleMatches(args['url'][0]):
                      print('* Rule ', r.ruleName, ' not applying. Does not meet URLActivation criteria.')
                      continue

                   print('* Applying rule', r.ruleName)    
                   xData = r.apply( responseHtml )
                   pageData.update(xData)
               '''
               pageData = xLib.applyAllRules(args['url'][0], responseHtml, self.configuration.getboolean('DEBUG', 'debugging', fallback=False))


          if not pageData:
             print('\t[DEBUG] Nothing extracted.')
             return(False)
                
          #print('\nExtracted data:', pageData)
          print('\nExtracted data from page:', )
          print('\tData type:', pageData.get('datatype', '???'))
          if pageData.get('datatype', '???') == 'record':                
            for k in pageData.keys():
              print('\t',k, ':[', pageData[k],']', sep='')
          else:
               i = 0 # just a counter 
               recordList = pageData[xRules.getRecordListFieldName(pageData)]
               for ex in recordList:
                   i += 1  
                   print('\t\tExtracted data ', i, ')', sep='')  
                   for k in ex.keys():
                       print('\t\t\t',k, ':[', ex[k],']', sep='')  
          
                  
          return(False)   



 
      def cssSelector(self, a):
         try:
            cmdArgs = ThrowingArgumentParser()
            cmdArgs.add_argument('url',   nargs=argparse.REMAINDER, default=[] )
            
            # Start in batch or interactive mode of applyRules
            cmdArgs.add_argument('-B',  '--batchmode', action='store_true')
            
            cmdArgs.add_argument('-T', '--extracttext',  action='store_true' )
            args = vars( cmdArgs.parse_args(a) )
         except Exception as argEx:
                 print('Error.', str(argEx) )
                 return(False)  


         try:
             # Fetch url
             response, responseHtml = self.loadResource(args['url'][0])             
         except Exception as readEx:
                  print('ERROR.', str(readEx))
                  return(False)

          
         if args['batchmode']:
             print('Sorry, batch mode not yet supported. Entering interactive mode')  
               
         while (True):
                   try:
                     clrprint.clrprint('CSS selector (type -- to exit)::', end='', clr='purple')
                     cssSel = input('')
                     if cssSel == '':
                        continue

                     if cssSel == '--':
                        print('exiting....')   
                        break   

                     matchedElements = responseHtml.find(cssSel, first=False)
                     print( 'Found', len(matchedElements), ' matching elemens' )
                     if args['extracttext']:
                        for e in  matchedElements:
                            clrprint.clrprint('\t', e.text, clr='green')  
                     
                   except KeyboardInterrupt:
                     print('Control-C seen...')    
                     return(False)    
                     #break
          
          
          




      def library(self, a):

          cmdArgs = ThrowingArgumentParser()          
          cmdArgs.add_argument('exrfile', nargs=argparse.REMAINDER, default=[] )
          args = vars( cmdArgs.parse_args(a) )
          
          #print('file:', args.get('exrfile'))
          if len(args['exrfile']) > 0:
           print('Showing library in file ', args['exrfile'][0], sep='')     
           #print('Rule file given:', args['exrfile'][0])     
           try:     
             with open(args['exrfile'][0],  encoding='utf-8', errors='ignore', mode='r') as f:          
                  xLib = xRules.loadLibrary(f.read())
           except Exception as rFile:
                  print('Error reading rule file', args['exrfile'], str(rFile))
                  return(False)
          else:
                  print('Showing loaded library')
                  xLib =  self.extractionRules
 
          if  xLib is None:
              print('No library loaded.')
              return
              
          print('Description: ', xLib.libraryDescription, sep='')
          print('Total of ', len(xLib.library), ' extraction rules in library', sep='')
          #i = 1
          for i,r in enumerate(xLib.library):
              print('\t', 10*"+", (i+1), 10*'+')
              print( "\tName:", r.ruleName   )
              print( "\tDescription:", r.ruleDescription   )
              print( "\tActivation:", r.ruleURLActivationCondition   )
              print( "\tNumber of PAGE preconditions:", len(r.rulePreconditions)   )
              print( "\tPAGE Precondition type:", r.rulePreconditionType  )
              for idx, rP in enumerate(r.rulePreconditions):
                  print("\t\tPrecondition selector:", rP.ecCSSSelector)
                  print("\t\tPrecondition text condition:", rP.ecTextCondition)
                  print("\t\tPrecondition RULE selector:", rP.ecRuleCSSSelector)
                  print('')
                  

              print( "\tCSS selector:", r.ruleCSSSelector   )
              print("\t** Usage stats:")
              print( "\t\tApplied count:", r.ruleAppliedCount   )
              print( "\t\tMatch count:", r.ruleMatchCount   )
              #i+=1

          return(False)





          
          
      def rules(self, a):
          print('\tTotal of ', self.extractionRules.numberOfRules(), ' rules', sep='')
          i = 1
          for r in self.extractionRules.library:
              print('\t', 10*"+", i, 10*'+')
              print( "\tName:", r.ruleName   )
              print( "\tDescription:", r.ruleDescription   )
              print( "\tActivation:", r.ruleURLActivationCondition   )
              print( "\tCSS selector:", r.ruleCSSSelector   )
              i+=1

          return(False)






      def addRule(self, a):
          newExtractionRule = xRules.extractionRule()  
          newExtractionRule.ruleName = input('Rule name? ')
          newExtractionRule.ruleURLActivationCondition = input('Rule URL activation condition? ')
          newExtractionRule.ruleDescription = input('Rule description? ')
          newExtractionRule.ruleCSSSelector = input('Rule css selector? ')
          newExtractionRule.ruleTargetAttribute = input('Rule target attribute? ')
          newExtractionRule.ruleContentCondition = input('Rule content condition? ')

          self.extractionRules.library.append( newExtractionRule )
          return(False)






      def reload(self, a):
            
        shellParser = ThrowingArgumentParser()         
        try:
           shellParser.add_argument('-c', '--config',   nargs='?', default='')
           shellArgs = vars( shellParser.parse_args( a ) )
        except Exception as ex:
             print("Invalid argument. Usage: reload [-c config_file]")
             return(False)


        if shellArgs['config'] is None:
            print("Invalid argument. Usage: reload [-c config_file]")
            return(False)  
                      
        if  shellArgs['config'] == '':
            configFile = self.configuration['__Runtime']['__configSource']
        else:
            configFile = shellArgs['config']
             
         
        if configFile == '':
          print('No configuration file. No configuration loaded.')   
          return(False)

        if not os.path.exists(configFile):
          print('Configuration file [', configFile ,'] not found', sep='')
          print('No configuration file loaded.')
          return(False)

        print('Loading configuration file: [', configFile, ']', sep="")
        self.configuration = configparser.RawConfigParser(allow_no_value=True)
        self.configuration.read(configFile)
        self.configuration.add_section('__Runtime')
        self.configuration['__Runtime']['__configSource'] = configFile
        print("Configuration file [", configFile, "] successfully loaded.", sep="")
        return(False)
      
        # Make sure that the target and bearer agree
        # setTargetArchive(self.configuration, self.configuration.get('TwitterAPI', 'targetArchive', fallback="recent") )






      def cdf(self, a):
          cmdArgs = ThrowingArgumentParser()          
          cmdArgs.add_argument('exrfile', nargs=argparse.REMAINDER, default=[] )
          args = vars( cmdArgs.parse_args(a) )

          try:     
             with open(args['exrfile'][0],  encoding='utf-8', errors='ignore', mode='r') as f:          
                  exl = xRules.loadLibrary(f.read())
          except Exception as rFile:
                  print('Error reading rule file', args['exrfile'])
                  return(False)

          print(exl.libraryDescription)

          xDF = pd.DataFrame(columns= exl.csvLineFormat )
          print(xDF)
          return(False)

          


      # Load a queue csv file.
      # TODO:  Has bugs
      def loadq(self, a):
          cmdArgs = ThrowingArgumentParser()          
          cmdArgs.add_argument('queuefile', nargs=argparse.REMAINDER, default=['.queue'] )
          args = vars( cmdArgs.parse_args(a) )

          try:
             # TODO: test if no queue file is given.   
             print('Loading queue file [', args['queuefile'][0], ']')   
             qD = pd.read_csv(args['queuefile'][0], sep=';', header=0, quoting=csv.QUOTE_NONNUMERIC )   
             print(qD) 
          except Exception as rFile:
                  print('Error reading queue file', args['queuefile'], str(rFile))
                  return(False)

          return(False)    




      
      def download(self, a):
          cmdArgs = ThrowingArgumentParser()
          cmdArgs.add_argument('-r', '--rules', type=str, nargs='?', default='' )
          cmdArgs.add_argument('url', nargs=argparse.REMAINDER, default=[''] )
          args = vars( cmdArgs.parse_args(a) )

          exRules = None
          if args['rules'] != '':
             print('Loading rules file', args['rules'])   
             with open(args['rules'],  encoding='utf-8', errors='ignore', mode='r') as f:          
                  exRules = xRules.loadLibrary(f.read())

          ccc = {}
          if exRules is not None:
             ccc = exRules.requestCookies

             
          try:
            #print('Downloading', args['url'], '...')
            print('>>>> SESSTION', args['url'][0])
            respS = self.downloadURL( dUrl=args['url'][0], rCookies=ccc, uAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0", renderPage=False, cfg=self.configuration)
            print('\tSession: Status=', respS.status)
            print('\tSession: content-type=', respS.get('Content-tYpe', '????') )
            print('\tSession: content-length=', respS.get('content-length', '-1') )
            print('\t\tData-type:', type(respS.get('content-length')))
            print('\tSession: Last-Modified=', respS.get('Last-Modified', '-1') )
            print('\tSession: Date=', respS.get('date', '-1') )
            print('\tSession: Set-Cookie=', respS.get('Set-Cookie', '-1') )
            
            print('>>>> RENDERED ', args['url'][0])
            
            respR = self.downloadURL( dUrl=args['url'][0], rCookies=ccc, uAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0", renderPage=True, cfg=self.configuration)
            if respR is None:
               print('\t[ERROR] Error downloading url')
            else:   
               print('\tRendered: Status', respR.status)
               print('\tRendered: content-type', respR.get('content-TYPE', '????') )
               print('\tRendered: content-length', respR.get('conTeNt-Length', '-1') )
               print('\tRendered: Last-Modified', respR.get('Last-Modified', '-1') )
               print('\tRendered: Date', respR.get('date', '-1') )
               print('\tRendered: Set-Cookie', respR.get('Set-Cookie', '-1') )
               
            
          except Exception as dEx:
                 print('Error downloading url ', args['url'], str(dEx))
                 return(False)
            
      

      



