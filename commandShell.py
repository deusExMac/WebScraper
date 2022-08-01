


"""

Module containing the implementation of the application
command shell.
Implementation of the supported commands is also in this module.



Author: mmt
Version: 20/04/2022

"""



import os
import os.path

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
from requests_html import HTMLSession, HTML

from pathlib import Path
import hashlib

import numpy as np
import csv

import clrprint

import pyppdf.patch_pyppeteer

#TODO: Does asyncio fix the "coroutine 'Launcher.killChrome' was never awaited" issue?
#import asyncio


# We define constants in this file
import appConstants
from commandHistory import commandHistory
import xRules

import utils
import urlQueue
import extractedDataSource

import htmlRendering



# The following two classes are used to parse
# arguments on the shell 'scommand line
class ArgumentParserError(Exception): pass
  
class ThrowingArgumentParser(argparse.ArgumentParser):
      def error(self, message):
          raise ArgumentParserError(message)






class commandShell:

      def __init__(self, cfg, xRls=None):

          # add here any command you would like to expand
          self.cmdExpansions = [{"c":"config"} ]

          '''
          #print("Loading extraction rule library [", args['rules'], "]...", sep='', end='')

          try:
           with open(args['rules'],  encoding='utf-8', errors='ignore', mode='r') as f:          
             ruleLibrary = xRules.loadLibrary(f.read())
                    
           #print('done')
           #print('\tTotal of ', ruleLibrary.numberOfRules(), ' extraction rules loaded.')
          except Exception as readEx:
             print('Error.', str(readEx))
          '''
          
          self.cmdExecutioner = commandImpl(cfg, xRls)
          self.cmdHistory = commandHistory(cfg.getint('Shell', 'historySize', fallback=10), True)

          





      #
      # Check if the command given needs to be expanded
      #
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
                 return( self.cmdHistory.getLastStartingWith(cmd[1:] ) )
                   
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




      def displayCommandHistory(self, n, fromBegin=False):
          
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
              print(pos, '. ', c, sep='')
              pos += 1

                     



      def startShell(self):

                    
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
              # It clogs it.
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
                            n = 0


                self.displayCommandHistory(n, args['start'])
                continue 



              # Execute command
              if self.cmdExecutioner.executeCommand( cParts ):                 
                 break

              

             except KeyboardInterrupt:
                 print("\nKeyboard interrupt seen.")


          # Save history 
          sts = self.cmdHistory.save()
          if sts != 0:
              print('Error', str(sts), 'writing .history file.')

          return





class httpResponse:
      
      def __init__(self):
            
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


      def setResponse(self, resp):
          if resp is None:
             return
            
          self.__requestResponse = resp
          self.setHeaders( resp.headers )



          
      def setHeaders(self, hdr):
          self.__headers = {k.lower(): v for k, v in hdr.items()}


          

      def get(self, key, default=''):
          #print('Calling get with key [', key, ']', sep='')
          #print( type(self.requestResponse.headers ) )
          #print( self.requestResponse.headers )
          if  self.__headers is None:
              return(default)
            
          return( self.__headers.get(key.lower(), default) )


      
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


      # Main entry point. Call this to execute commands given via the apps command line shell.
      # commandParts: a list of tokens comprising the command given, spearated by 
      #               whitespaces at the command line.
      #               For example, when the following is entered:
      #               TwitterAPI v2 >> search -t 1/1/1970 -u 2/1/1970 -t 0D12H5M3S -n 7 mmmmm
      #               commandParts will contain all tokens separated by whitespaces i.e.
      #               commandParts = ['search', '-t', '1/1/1970', '-u', '2/1/1970', '-t', '0D12H5M3S', '-n', '7', 'mmmmm']
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


      
      '''
      #
      #
      # TODO: Do we need this method?
      #
      def extract(self, a):


          def loadResource( resource ):
              if os.path.exists(resource):
                 with open(resource,mode='r') as f:
                      fcnt = f.read()

                 h = HTML(html=fcnt) 
                 return(None, h)

              s = HTMLSession()
              rsp = s.get(resource)
              return( rsp, rsp.html )



          def matchesAny( regexpList, txt):
              if len(regexpList) == 0:
                 return(True)
            
              for regExp in regexpList:
                  if re.search( regExp, txt) is not None:
                     return(True)

              return(False)



          ####################################
          #  outer method config starts here
          ####################################
          
          try:  
             cmdArgs = ThrowingArgumentParser()          
             cmdArgs.add_argument('url',   nargs=argparse.REMAINDER, default=[] )
             cmdArgs.add_argument('-s', '--savetofile',  nargs='?' )
             cmdArgs.add_argument('-r', '--rules',  nargs='?' )
             #cmdArgs.add_argument('-E',  '--showerrors', action='store_true')
             args = vars( cmdArgs.parse_args(a) )

          except Exception as gEx:
                print( str(gEx) )
                return(False)  

          if args.get('rules') is None:
             exRules = self.extractionRules
          else:
                print('Loading extraction rules from [', args['rules'], ']...', sep='', end='')
                with open(args['rules'],  encoding='utf-8', errors='ignore', mode='r') as f:
                     exRules = xRules.loadLibrary(f.read())
                     print('ok.')


          try:
            
            rresponse, html = loadResource( args['url'][0] )
            if rresponse is not None:
               if rresponse.status_code != 200:
                  print('ERROR. Got status code:', rresponse.status_code )
                  return(False)


                  
            if args.get('savetofile') is not None:
               with open(args['savetofile'], 'w') as f:
                  f.write(rresponse.text)
                  
          except Exception as fetchEx:
                 print('ERROR.', str(fetchEx) )
                 return(False)
                
          print('ok. done')

          # Extracted data is stored here
          exTractedData = {}
          
          # Check which extraction rules should be activated 
          for r in exRules.library:
              if not matchesAny( r.ruleURLActivationCondition, args['url'][0]) :
                 print("IGNORING Rule: ", r.ruleName)
                 continue
              else:
                 print("APPLYING Rule: ", r.ruleName)
                 res = html.find(r.ruleCSSSelector, first=False)
                 
                 if r.ruleTargetAttribute == "text":
                       
                       if r.ruleContentCondition != '': 
                          res = [m for m in res if re.search(r.ruleContentCondition, m) is not None ]

                       print('Total of ', len(res))
                       if len(res) > 0:

                          xVal = res[r.ruleReturnedMatchPos].text   

                          # Replace characters
                          for c in r.ruleRemoveChars:
                              xVal = xVal.replace(c, '')  
                                
                          #print('\n>>>>> Got MATCH [', res[r.ruleReturnedMatchPos].text, ']\n', sep='' )
                          print('\n>>>>> Got MATCH [', xVal, ']\n', sep='' )
                          exTractedData[r.ruleName] = xVal
                       else:
                          print('\tNothing exrtracted.')   
                 else:
                      
                      if r.ruleContentCondition != '': 
                         res = [m for m in res if re.search(r.ruleContentCondition, m.attrs.get(r.ruleTargetAttribute)) is not None ]
                    
                      if r.ruleReturnedMatchPos >= 0:
                         print('>>>>> Got  [', res[r.ruleReturnedMatchPos].attrs.get(r.ruleTargetAttribute), ']', sep='' )
                         #numExtracted += 1
                      else:
                          print(len(res), ' matches found')
                          #numExtracted += len(res)


          print('\n\nExtracted data:', exTractedData )
          return(False)
      '''  
      



      # TODO: Change what parameters are passed
      def __updateCrawl(self, qF, oF, cfg, xR, nU, mr=False ):

          print('\t[DEBUG] Loading queue file [', qF, ']...', end='')
          uQ = urlQueue.urlQueue(startNewSession=False, qF=qF, sQ=True)
          
          print('\t[DEBUG] Loading csvfile file [', oF, ']...', end='')
          if not os.path.exists(oF):
             print('No such file. Terminating')
             return(False)


          uS = extractedDataSource.extractedDataFileCSVReader(oF, sep=';')

           
          print('ok. Total of ', uS.getNumRows(), ' rows', sep='')


          
          cPos = 0
          numProcessed = 0
          numUpdated = 0
          while(True):
            try:
               
                exData = uS.getNext()
                if exData is None:
                   print('\t[DEBUG] No URLs found. Exiting.')
                   break
                  
                targetUrl = exData['url']
                clrprint.clrprint( (numProcessed+1), '/', uS.getNumRows(), ') Doing [', targetUrl, ']', clr='yellow', sep=''  )
                qData = uQ.getByUrl( targetUrl )
                if not qData:
                   print('\t\t[DEBUG] Url [', targetUrl, '] NOT FOUND IN QUEUE! Adding to urlQueue')                   
                   uQ.add( targetUrl )
                else:
                   print('\t\t[DEBUG] Url [', targetUrl, '] FOUND IN QUEUE!')   
                
                # TODO: Try block here...      
                pUrl = urlparse( unquote(targetUrl) )    
                session = HTMLSession()                
                response = session.get(targetUrl)

                numProcessed += 1

                print('\t\t[DEBUG] Compaing last modification dates (', response.headers.get('Last-Modified', '???'), ') (', qData.get('lastmodified', '???'), ')')  
                if response.headers.get('Last-Modified', '') != '':
                   if response.headers.get('Last-Modified', '') == qData.get('lastmodified', ''):
                      print('\t\t[DEBUG] Date comparison: Not modified (', response.headers.get('Last-Modified', ''), ') (', qData['lastmodified'], ')')                      
                      continue

                if xR.renderPages:
                   print('\t\tRendering page....')   
                   response.html.render(timeout=250, scrolldown=12)

                   
                # Check hashes
                newHash = utils.txtHash( response.text )
                print('\t\t[DEBUG] oldHash=[', qData.get('hash', ''), '] newHash=[', newHash,']', sep='')
                if newHash == qData.get('hash', ''):
                   print('\t\t[DEBUG] Hash comparison: Not modified.')                   
                   continue
                else:
                   print('[\t\t[DEBUG] Hash does not match. Modified')   

                print('\t\t[DEBUG] Modified.')

                if mr:
                    if not utils.saveWebPageToLocalFile(targetUrl, response, True, cfg.get('Storage', 'mirrorRoot', fallback='')):
                       print('\t[DEBUG] Error saving file')   



                exTractedData = {}
                pageData = {}
                for r in xR.library:
                      
                    print('\t[DEBUG] Checking if rule ', r.ruleName,'should be applied...', end='')
                    if not r.ruleMatches(targetUrl):
                        print('No.')
                        continue
                  
                    print('yes')

                    if r.ruleName == 'getLinks':
                       print('\t[DEBUG] Skipping getLinks rule')   
                       continue

                    print('\t[DEBUG] Applying rule [', r.ruleName, ']', sep='') 
                    xData = r.apply( response.html )
                    pageData.update(xData)

                 
                    
                # Update url queue
                print('\t[DEBUG] Updating queue...')
                uQ.updateTimeFetched(targetUrl)
                uQ.updateStatus( targetUrl, response.status_code )
                uQ.updateLastModified(targetUrl, response.headers.get('Last-Modified', ''))
                uQ.updatePageHash( targetUrl, newHash )
                
                   
                print('\t[DEBUG] Extracted:', pageData)

                # TODO: check/expand this.
                
                if xRules.isRecordData(pageData):
                   print('\t[DEBUG] Record data..')   
                   xdt = xR.CSVFields(pageData)
                   xdt['dateaccessed'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S') 
                   xdt['url'] = targetUrl
                   clrprint.clrprint('\t[DEBUG] Adding ', xdt, clr='green', sep='')  
                   uS.updateExtractedData(targetUrl, xdt)
                else:
                     # Since this returned a recordList, iterate over
                     # the individual records and add then to the data frame
                     xdtList = pageData[xRules.getRecordListFieldName(pageData)]
                     print('\t[DEBUG] Removing all rows with URL [', targetUrl, ']',  sep='')
                     uS.removeExtractedData( targetUrl )
                     for xdt in xdtList:
                         xdt['dateaccessed'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                         xdt['url'] = targetUrl  
                         clrprint.clrprint('\t[DEBUG] Adding ', xdt, clr='green', sep='')
                         uS.insertDataAtCurrentPosition(xdt)
                         

                     # Move the current position forward because more than one 
                     #uS.moveBy( len(xdtList) )
                   
                

                
                numUpdated += 1
                
                
                if nU is None:
                   maxU = cfg.getint('Crawler', 'maxPages', fallback=-1)
                else:
                   maxU = nU

                      
                if maxU > 0:
                   if (cPos -1) >= maxU:   
                      print('\t\tLimit of', maxU, 'reached. Terminating')
                      return(False)

                delayValue = 0.5  
                if cfg.get('Crawler', 'delayModel', fallback='c') == 'h':
                   delayValue = abs( float( np.random.normal(cfg.getfloat('Crawler', 'humanSleepTimeAvg', fallback='3.78'), cfg.getfloat('Crawler', 'humanSleepTimeSigma', fallback='0.43'), 1)[0]))
                else:
                   delayValue = cfg.getfloat('Crawler', 'sleepTime', fallback='0.3') # TODO: Check fallback!
                       
                print('\t[DEBUG] Sleeping for ', delayValue, ' seconds', sep='')   
                time.sleep( delayValue )  

            except KeyboardInterrupt:
                   print('Control-C seen. Terminating. Processed/Updated:', numProcessed, '/', numUpdated, sep='')
                   break
                
          #print('\t[DEBUG] Saving url queue...', end='')
          uQ.saveQ()
          #print('ok.')
          print('\t[DEBUG] Saving csv to [', oF, ']...', sep='', end='')
          uS.save()
          #csvDF.to_csv( oF, index=False, sep=';', quoting=csv.QUOTE_NONNUMERIC )
          print('ok')









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



      def downloadURL(self, dUrl, rCookies=[], userAgent=None, renderPage=False):
          r = httpResponse()  
          if not renderPage:
             session = HTMLSession()
             response = session.get(dUrl, cookies = rCookies )             
             r.setResponse(response)
             try:
                r.status = int(response.status_code)
             except Exception as statusEx:
                    r.status = -5

                                 
             r.html = response.html
             r.text = response.text
             
          else:
                htmlRndr = htmlRendering.htmlRenderer()
                rHTML = htmlRndr.render(url=dUrl, timeout=25, requestCookies=rCookies, scrolldown=0, maxRetries=3)                
                if rHTML is None:
                   return(None)
                  
                r.setResponse(htmlRndr.response) 
                #if r.requestResponse is not None:                   
                try:   
                   r.status = int( htmlRndr.response._status )
                except Exception as statusEx:
                   r.status = -6
                      
                r.html = rHTML
                r.text = '' # Fix me
                   
          
          return( r )
                



      # Starts crawling from an initial URL.
      # TODO: This method is so ugly. Has to be refactored seriously. 

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
             #cmdArgs.add_argument('-B', '--bfs', action='store_true' )
             
             
             cmdArgs.add_argument('-U', '--update', action='store_true' )
             #cmdArgs.add_argument('-Q', '--updateQueue', action='store_true' )
             cmdArgs.add_argument('-p', '--startposition', type=int, nargs='?', default=0 )
             
             args = vars( cmdArgs.parse_args(a) )

          except Exception as gEx:
                print( str(gEx) )
                return(False)    

          

          # We copy the existing configuration file in order to not
          # modify original settings with arguments given by the shell
          cmdConfigSettings = copy.deepcopy( self.configuration )




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
                print('\t[DEBUG] Loading extraction rules from [', args['rules'], ']...', sep='', end='')
                try:
                  with open(args['rules'],  encoding='utf-8', errors='ignore', mode='r') as f:
                     exRules = xRules.loadLibrary(f.read())
                     print('ok.')
                     
                except Exception as flEx:
                       print(str(flEx) )
                       return(False)



          if args['update']:
             print("")
             print("")   
             print("######################################")
             print("#")
             print("#")
             print("#")
             print("#       Entering UPDATE MODE")   
             print("#")
             print("#")
             print("#")
             print("######################################")
             print("")
             print("")   
             self.__updateCrawl( args['queuefile'], args['outputcsvfile'], cmdConfigSettings, exRules, args.get('numpages'), args['mirror'] )
             return(False)


          '''
          if exRules is None or exRules.library is None:
             print('[WARNING] Not extraction library found.')
          else:    
             print('\t[DEBUG] Using extraction library: ', exRules.libraryDescription)            

          '''

          if exRules is None or exRules.library is None:
             print('[WARNING] Not extraction library found.')
             
          
          linkQueue = []
          linkQueue.append( args['url'][0] )
          visitedPageHashes = []
          pageHandlingTimes = []

          previousHost = ''
          
          numProcessed = 0
          numprocessingErrors = 0
          numHTTPErrors = 0
          numNetErrors = 0

          numExtracted = 0 # Number of matches found/extracted

          xDataDF = None
          if exRules is not None and len( exRules.csvLineFormat ) > 0: 
             xDataDF =  pd.DataFrame(columns= (['dateaccessed', 'url'] + exRules.csvLineFormat) )  

          if args['continue']:
             if os.path.exists( args['outputcsvfile'] ):
               print('\t[DEBUG] Loading existing csv file [', args['outputcsvfile'], ']', sep='')    
               xDataDF = pd.read_csv( args['outputcsvfile'], sep=';', header=0, quoting=csv.QUOTE_NONNUMERIC)
              
          uQ = urlQueue.urlQueue(qSz=cmdConfigSettings.getint('Crawler', 'maxQueueSize', fallback=-1),
                                 qMemSz=cmdConfigSettings.get('Crawler', 'maxQueueMemorySize', fallback='-1'),
                                 startNewSession=not args['continue'],
                                 qF=args['queuefile'], sQ=True, tS=cmdConfigSettings.get('Crawler', 'traversalStrategy', fallback='bfs') ) 
          uQ.add( args['url'][0] )

          lastAutosave = time.perf_counter()
          crawlStarted  = time.perf_counter()
          
          try:
            while (True):
                 try:
                                                          
                  currentUrl = uQ.getNext()
                  if currentUrl is None:
                     print('\t[DEBUG] Empty Queue')
                     break
                  
                 except Exception as popEx:
                   print('Error:', str(popEx))   
                   break    

                 clrprint.clrprint('\n', (numProcessed + 1), ') >>> Doing [', currentUrl, '] Queue:', uQ.queueSize(), '(mem: ', uQ.queueMemorySize(), 'B/', "{:.2f}".format(uQ.queueMemorySize()/(1024*1024)), 'M/', uQ.qMemorySize ,') Pending:', uQ.pendingUrlsCount(),  ' Fetched:', uQ.fetchedUrlsCount(), ' Extracted:', numExtracted, clr='yellow')

                 tmStart = time.perf_counter() # start counting time
                 
                 while (True):
                  try:
                    pUrl = urlparse( unquote(currentUrl) )    
                    session = HTMLSession()
                    #print( '\t[DEBUG] ', session.headers['user-agent'])
                    headers = {}
                    if exRules.requestUserAgent.strip() != "":
                       headers = {'User-Agent': exRules.requestUserAgent}

                    #ccc = self.prepareCookies(pUrl, exRules.requestCookies)
                    
                    #response = session.get(currentUrl, cookies = exRules.requestCookies)                    
                    response = session.get(currentUrl, cookies = exRules.requestCookies   )
                    
                    print('\t[DEBUG] Cookies: ', response.cookies.get_dict() ) 
                    #visitedQueue.append( currentUrl )
                    break
                  
                  except Exception as netEx:
                        print('[DEBUG] Network error:', str(netEx) )
                        numNetErrors += 1
                        if numNetErrors >= 3:
                           # TODO: a break here would be more appropriate...   
                           uQ.saveQ()
                           if xDataDF is not None:
                              xDataDF.to_csv( args['outputcsvfile'], index=False, sep=';', quoting=csv.QUOTE_NONNUMERIC )
                              
                           print('[DEBUG] Too many errors. Stopping.')   
                           return(False)   

                 uQ.updateTimeFetched(currentUrl)
                 uQ.updateStatus( currentUrl, response.status_code )
                 uQ.updateContentType( currentUrl, response.headers.get('Content-Type', '') )
                 
                 if response.status_code != 200:
                    numHTTPErrors += 1
                    print('\t[DEBUG] Http status [', response.status_code, ']' )
                    continue

                 #if response.headers.get('Content-Length', -2):
                 pageContentLength = int( response.headers.get('Content-Length', '-2') )      

                 # TODO: Check if content was actually received i.e. content-length is not zero.

                 if utils.isText( response.headers.get('Content-Type', '')  ):
                    pHash = utils.txtHash( response.text )
                    if pageContentLength < 0:
                       pageContentLength = len( response.text )
                 else:
                    pHash = utils.byteHash( response.content )
                    if pageContentLength < 0:
                       pageContentLength = len( response.content )

                 uQ.updateContentLength( currentUrl, pageContentLength )
                 if pageContentLength == 0 :
                    print('\t[DEBUG] Zero content length')   
                    uQ.updateStatus( currentUrl, -999 )
                    continue
                       

                 print('\t[DEBUG] Hash:', pHash )
                 # Have we seen this content? If so, discard it; move to next
                 if uQ.hInQueue(pHash):
                    print('\t[DEBUG] Same hash [', pHash, '] seen. Url:', currentUrl, sep='')
                    continue

                 uQ.updatePageHash( currentUrl, pHash )
                 uQ.updateLastModified( currentUrl, response.headers.get('Last-Modified', '') )

                 # We keep the html object in a separate variable that will be the subject of css selectors
                 # and regular expression found in rules.
                 # We do this because rendering the html page may result in changing the html.
                 # This is because we do not rely on response.html.render() to do the rendering, as
                 # it seems to be not working/buggy. Instead a separate class has been developed
                 # rendering html pages, which however has the sideeffect that the same page needs
                 # to be fetched again. Sorry for this.
                 #
                 # TODO: This needs more thorough testing.
                 htmlObject = response.html
                 
                 if exRules.renderPages:
                       try:   
                          print('\t[DEBUG] Rendering page...')    
                          htmlRndr = htmlRendering.htmlRenderer()
                          rHTML = htmlRndr.render(url=currentUrl, timeout=10, requestCookies=self.prepareCookies(currentUrl, exRules.requestCookies), scrolldown=10, maxRetries=5)
                          #response.html.render(timeout=250, cookies= exRules.requestCookies, scrolldown=5)
                          htmlObject = HTML( html=rHTML )
                          #htmlObject = response.html.html # TODO: This must leave if abover .render is replaced.
                          #TODO: Update hash, content type/length etc.
                       except KeyboardInterrupt:
                              print('\t[DEBUG] *** ', sep='')
                              raise KeyboardInterrupt
                              break
                       except Exception as rtmEx:
                              print('\t[DEBUG] Exception during rendering.', str(rtmEx) )
                              break
                              #raise KeyboardInterrupt
                        
                 
                 # Save to file if so required
                 # TODO: Refactor this. This is awfull....
                 # TODO: has a bug when saving files with extension e.g.:https://www.econ.upatras.gr/sites/default/files/attachments/tmima_politiki_poiotitas_toe_v3.pdf
                 #       does not 
                 if args['mirror']:
                    if not utils.saveWebPageToLocalFile(currentUrl, response, args['mirror'], cmdConfigSettings.get('Storage', 'mirrorRoot', fallback='')):
                       print('\t[DEBUG] Error saving file')   
                    
                  
                 if 'html' not in response.headers.get('Content-Type', ''):
                    print('\t\tignoring ', response.headers.get('Content-Type', 'xxx'))   
                    continue
                 
                 if exRules is None or exRules.library is None:
                    print('\t[DEBUG] No library present. Skipping extraction.')   
                    continue
                 else:
                      print('\t[DEBUG] Extracting using library: ', exRules.libraryDescription)  

      
                 #exTractedData = {} 
                 pageData = {}
                 for r in exRules.library: #self.extractionRules.library:
                       
                     # should we apply this rule to the URL?
                     print('\t[DEBUG] Checking if rule ', r.ruleName,'should be applied...', end='')
                     if not r.ruleMatches(currentUrl):
                        print('No.')
                        continue
                  
                     print('yes')
        

                     # getLings are handled a little bit different than other rules.
                     #  TODO: Refactor this.                     
                     if r.ruleName == 'getLinks':                        
                        xData = r.apply(htmlObject)
                        #print('GETLINKS:', xData)
                        xLinks = xData.get('getLinks', [])
                        print('\t[DEBUG] Total of [', len(xLinks), '] links extracted')
                        # TODO: Seems that the loop below takes too long.
                        #       Check it/measure it.
                        tB = time.perf_counter()
                        for lnk in xLinks:
                            absoluteUrl = urljoin(args['url'][0], lnk )
                            cUrl = utils.canonicalURL( absoluteUrl )
                            # TODO: move the next check inside .apply()???
                            if re.search( r.ruleContentCondition, cUrl) is not None:  
                               uQ.add( cUrl ) # Add it to the URL queue
                               
                        print('\t\t[DEBUG] All links done in', time.perf_counter() - tB )   
                             
                     else:
                           # xData has the extracted data originating from a single (one) rule only.
                           xData = r.apply( htmlObject )
                           # Aggregate it. pageData aggregates all data extracted by
                           # all rules on one page. In the end, pageData will have 
                           pageData.update(xData)
                           

                        
                 print('\n\tExtracted page data:', pageData, '\n' )
                                  


                 #   
                 # Store extracted data
                 #
                 # TODO: handle differently recordlist and record types of extractions.
                 #

                 # Extract fields required by csv

                 print('\t[DEBUG] Extracted data is record:', xRules.isRecordData(pageData) )
                 print('\t[DEBUG] Extracted data is recordlist:', xRules.isRecordListData(pageData) )
                 if xRules.isRecordData(pageData):
                    xdt = exRules.CSVFields(pageData)
                    if xdt:
                       xdt['dateaccessed'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')  
                       xdt['url'] = currentUrl
                       clrprint.clrprint('\t\t[DEBUG] Adding [', xdt, ']',  clr='green')
                       #xDataDF = xDataDF.append( xdt, ignore_index = True )
                       xDataDF = pd.concat([xDataDF, pd.DataFrame.from_records([ xdt ])])
                       #df = pd.concat([df, pd.DataFrame.from_records([{ 'a': 1, 'b': 2 }])])
                       #print(xDataDF)
                 else:
                       recordList = pageData[xRules.getRecordListFieldName(pageData)]
                       for r in recordList:
                           csvr = exRules.CSVFields(r)  
                           csvr['dateaccessed'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                           csvr['url'] = currentUrl
                           clrprint.clrprint('\t\t[DEBUG] (record list) Adding [', csvr, ']', clr='green')
                           xDataDF = pd.concat([xDataDF, pd.DataFrame.from_records([ csvr ])])
                       
                                           
                 
                 numProcessed += 1

                 if xDataDF is not None:
                    numExtracted = xDataDF.shape[0]
                 else:
                    numExtracted = -1
                    
                 if cmdConfigSettings.getint('Crawler', 'maxPages', fallback=-1) > 0:
                    if numProcessed >= cmdConfigSettings.getint('Crawler', 'maxPages', fallback=-1):
                       print('Terminating. Reached page limit ', cmdConfigSettings.getint('Crawler', 'maxPages', fallback=-1) ) 
                       break


                 tmEnd = time.perf_counter()
                 pageHandlingTimes.append( tmEnd - tmStart )
                 print('\t[DEBUG] Average page handling time: ', '{:.4}'.format( statistics.mean(pageHandlingTimes) ), ' seconds', sep='' )
                 if len(pageHandlingTimes) > 5:
                    print('\t[DEBUG] Cleaning timing list (', len(pageHandlingTimes), ')', sep='')   
                    pageHandlingTimes.clear()


                 # Should we autosave?
                 if cmdConfigSettings.getboolean('Crawler', 'autoSave', fallback=False):
                  if (time.perf_counter() - lastAutosave) >= cmdConfigSettings.getint('Crawler', 'autoSaveInterval', fallback=200):   
                    print('\t[DEBUG] Autosaving...(elapsed:', (time.perf_counter() - lastAutosave), ' seconds)')    
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
                       
                    print('\t[DEBUG] Sleeping for ', delayValue, ' seconds', sep='')   
                    time.sleep( delayValue )

                 previousHost = pUrl.netloc
                 
                   
          except KeyboardInterrupt:
                 print('Control-C seen. Terminating. Processed ', numProcessed)
                 #return(False)
                 #break


          print('[DEBUG] Saving extracted data to [', args['outputcsvfile'], ']...', end='')
          if xDataDF is not None:
            try:    
             xDataDF.to_csv( args['outputcsvfile'], index=False, sep=';', quoting=csv.QUOTE_NONNUMERIC )
             print('ok')
            except Exception as scsvEx:
                  print('Error.', str(scsvEx))
          
          if uQ.qSave: 
             print('[DEBUG] Saving queue...', end='')       
             uQ.saveQ()
             print('done.')


          # Display some statistics 
          exRules.libStats()
          
          return(False)







      #
      # TODO: What to do with this method? Keep, remove, refactor???
      #
      def loadResource( self, resource ):
          if os.path.exists(resource):
             with open(resource,mode='r') as f:
                fcnt = f.read()

             h = HTML(html=fcnt) 
             return(None, h)

          s = HTMLSession()
          response = s.get(resource)
          return( response, response.html )






      def applyRules(self, a): 

          pageData = {}  
          try:
            cmdArgs = ThrowingArgumentParser()
            cmdArgs.add_argument('url',   nargs=argparse.REMAINDER, default=[] )
            cmdArgs.add_argument('-r', '--rules',  nargs='?' )
            cmdArgs.add_argument('-R', '--rulename',  nargs='?' )
            #cmdArgs.add_argument('-D',  '--render', action='store_true')

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
             response, responseHtml = self.loadResource(args['url'][0])
             if response is not None:
                if xLib.renderPages:
                   print('\tRendering page...')
                   response.html.render(timeout=220)
             
          except Exception as readEx:
                  print('ERROR.', str(readEx))
                  return(False)
          '''  
          try:
             print('Fetching url [', args['url'][0], ']...', end='')  
             session = HTMLSession()
             response = session.get(args['url'][0])
             print('ok.')
          except Exception as netEx:
                 print('Error.', str(netEx))
                 return(False)
          '''
          #return(False)

          
             
          if targetRule is not None:
             print('* Applying rule', targetRule.ruleName)   
             xData = targetRule.apply( responseHtml )
             pageData.update(xData)
          else:
               print('Rule list:') 
               for r in xLib.library:
                   if not r.ruleMatches(args['url'][0]):
                      print('* Rule ', r.ruleName, ' not applying. Does not meet URLActivation criteria.')
                      continue

                   print('* Applying rule', r.ruleName)    
                   xData = r.apply( responseHtml )
                   pageData.update(xData)
                   

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
             print('Loading queue file [', args['queuefile'][0], ']')   
             qD = pd.read_csv(args['queuefile'][0], sep=';', header=0, quoting=csv.QUOTE_NONNUMERIC )   
             print(qD) 
          except Exception as rFile:
                  print('Error reading queue file', args['queuefile'], str(rFile))
                  return(False)

          return(False)    

      #def downloadURL(self, url, rCookies=None, userAgent=None, renderPage=False, **options)
      def download(self, a):
          cmdArgs = ThrowingArgumentParser()          
          cmdArgs.add_argument('url', nargs=argparse.REMAINDER, default=[''] )
          args = vars( cmdArgs.parse_args(a) )
          try:
            #print('Downloading', args['url'], '...')
            print('>>>> SESSTION', args['url'][0])
            respS = self.downloadURL( dUrl=args['url'][0], rCookies=[], userAgent=None, renderPage=False)
            print('\tSession: Status=', respS.status)
            print('\tSession: content-type=', respS.get('Content-tYpe', '????') )
            print('\tSession: content-length=', respS.get('content-length', '-1') )
            
            print('>>>> RENDERED ', args['url'][0])
            
            respR = self.downloadURL( dUrl=args['url'][0], rCookies=[], userAgent=None, renderPage=True)
            if respR is None:
               print('\t[ERROR] Error downloading url')
            else:   
               print('\tRendered: Status', respR.status)
               print('\tRendered: content-type', respR.get('content-TYPE', '????') )
               print('\tRendered: content-length', respR.get('conTeNt-Length', '-1') )
            
          except Exception as dEx:
                 print('Error downloading url ', args['url'], str(dEx))
                 return(False)
            
      
     



