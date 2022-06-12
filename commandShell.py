


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
from datetime import  timedelta 
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

#TODO: Does asyncio fix the "coroutine 'Launcher.killChrome' was never awaited" issue?
#import asyncio


# We define constants in this file
import appConstants
from commandHistory import commandHistory
import xRules

import utils
import urlQueue






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
            
          try:
              csvDF = pd.read_csv(oF, sep=';', header=0, quoting=csv.QUOTE_NONNUMERIC )
          except Exception as rEx:
                 print('Error.', str(rEx) )
                 return(False)
            
          print('ok. Total of ', csvDF.shape[0], ' rows', sep='')



          cPos = 0
          numProcessed = 0
          numUpdated = 0
          while(True):
            try:    
                if cPos >=csvDF.shape[0]:
                   print('Empty queue. Terminating')   
                   break

                targetUrl = csvDF.iloc[cPos]['url']  
                print('', cPos, ') [DEBUG] Doing [', targetUrl, ']', sep='' )
                cPos += 1 # Move to next... TODO: Is this correct here? Elsewhere?
                qData = uQ.getByUrl( targetUrl )
                if not qData:
                   print('\t\t[DEBUG] Url [', targetUrl, '] NOT FOUND! Adding to urlQueue')                   
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

                # Update extracted data
                print('\t[DEBUG] Updating csv...')
                storedRecord = csvDF[ csvDF['url'] ==targetUrl].to_dict(orient='records')[0]
                
                #csvDF.iloc[cPos]['url']
                if storedRecord is not None:
                   print('EXISTING DATA:', storedRecord)
                else:
                   print('!!!!!! NOT EXISTING DATA')

                   
                print('EXTRACTED DATA:', pageData)

                print('\t[DEBUG] Updating csv data...')
                pageData['dateaccessed'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')   
                for k in xR.csvLineFormat:
                    print('\t\t[DEBUG] Updating key', k)
                    print('\t\t\t[DEBUG] From [', csvDF.loc[ csvDF['url'] == targetUrl,  k ].values[0], ']', sep='')
                    print('\t\t\t[DEBUG] To [', pageData[k], ']', sep='')  
                    csvDF.loc[ csvDF['url'] == targetUrl,  k ] = pageData[k]

                csvDF.loc[ csvDF['url'] == targetUrl,  'dateaccessed' ] = pageData['dateaccessed']
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
          print('\t[DEBUG] Saving csv to [', oF, ']...', sep='') 
          csvDF.to_csv( oF, index=False, sep=';', quoting=csv.QUOTE_NONNUMERIC )
          print('ok')








      # TODO: IT's so ugly. Refactor me! 

      def crawl(self, a):

                    
          try:  
             cmdArgs = ThrowingArgumentParser()
             cmdArgs.add_argument('url',   nargs=argparse.REMAINDER, default=[] )
             cmdArgs.add_argument('-n', '--numpages', type=int, nargs='?' )
             cmdArgs.add_argument('-s', '--sleeptime', type=float, nargs='?' )
             cmdArgs.add_argument('-o', '--outputcsvfile', type=str, nargs='?', default='extracted' + datetime.datetime.now().strftime("%d-%m-%Y@%H-%M-%S") + '.csv' )
             cmdArgs.add_argument('-q', '--queuefile', type=str, default='.queue' )
             
             cmdArgs.add_argument('-M', '--mirror', action='store_true' )
             cmdArgs.add_argument('-r', '--rules',  nargs='?' )
             cmdArgs.add_argument('-H', '--humandelay', action='store_true' )
             cmdArgs.add_argument('-D', '--debugmode', action='store_true' )
             cmdArgs.add_argument('-C', '--continue', action='store_true' )
             
             
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
          #visitedQueue = []
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

          uQ = urlQueue.urlQueue(cmdConfigSettings.getint('Crawler', 'maxQueueSize', fallback=-1), startNewSession=not args['continue'], qF=args['queuefile'], sQ=True ) 
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

                 clrprint.clrprint('\n', (numProcessed + 1), ') >>> Doing [', currentUrl, '] Queue:', uQ.queueSize(), ' Pending:', uQ.pendingUrlsCount(),  ' Fetched:', uQ.fetchedUrlsCount(), ' Extracted:', numExtracted, clr='yellow')

                 tmStart = time.perf_counter() # start counting time
                 
                 while (True):
                  try:
                    pUrl = urlparse( unquote(currentUrl) )    
                    session = HTMLSession()
                    #print( '\t[DEBUG] ', session.headers['user-agent'])                    
                    response = session.get(currentUrl)
                    
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
                    continue


                 if utils.isText( response.headers.get('Content-Type', '')  ):
                    pHash = utils.txtHash( response.text )
                 else:
                    pHash = utils.byteHash( response.content )

                 print('\t[DEBUG] Hash:', pHash )
                 # Have we seen this content? If so, discard it; move to next
                 if uQ.hInQueue(pHash):
                    print('\t[DEBUG] Same hash [', pHash, '] seen. Url:', currentUrl, sep='')
                    continue

                 uQ.updatePageHash( currentUrl, pHash )
                 uQ.updateLastModified( currentUrl, response.headers.get('Last-Modified', '') )
                 
                 if exRules.renderPages:
                       try:   
                          print('\t[DEBUG] Rendering page...')    
                          response.html.render(timeout=250)
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
        

                     # Select part of the html specified by rule
                     #res = response.html.find(r.ruleCSSSelector, first=False)
                     if r.ruleName == 'getLinks':
                        # getLinks is a special rule that is treated differently...   
                        res = response.html.find(r.ruleCSSSelector, first=False)   
                        for lnk in res:   
                            canonicalLink = urljoin(args['url'][0], lnk.attrs.get(r.ruleTargetAttribute) )

                            #if canonicalLink                            
                            #if (canonicalLink in linkQueue) or (canonicalLink in visitedQueue):                               
                            #   continue
                            
                            # Does acquired content match content rule?
                            if re.search( r.ruleContentCondition, canonicalLink) is not None:  
                               uQ.add( canonicalLink )
                             
                     else:
                           # xData has the extracted data originating from a single (one) rule only.
                           xData = r.apply( response.html )
                           # Aggregate it. pageData aggregates all data extracted by
                           # all rules on one page. In the end, pageData will have 
                           pageData.update(xData)
                           

                        
                 print('\n\tExtracted page data:', pageData, '\n' )
                 
                 #ln = exRules.toCSVLine(pageData, ';')
                 #print('\t[DEBUG] csv line:', ln)


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
            cmdArgs.add_argument('-l', '--libfile',  nargs='?' )
            cmdArgs.add_argument('-R', '--rulename',  nargs='?' )
            #cmdArgs.add_argument('-D',  '--render', action='store_true')

            args = vars( cmdArgs.parse_args(a) )
          except Exception as argEx:
                 print('Error.', str(argEx) )
                 return(False)

          if args.get('libfile', '')  == '':
             print('No .exr file given.')
             return(False)

          try:
             print('Loading library file [', args['libfile'], ']...', end='')   
             with open(args['libfile'],  encoding='utf-8', errors='ignore', mode='r') as f:          
                  xLib = xRules.loadLibrary(f.read())
             print('ok')     
          except Exception as rFile:
                  print('Error reading rule file', args['libfile'])
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
                   response.html.render()
             
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
                   

                      
          print('\nExtracted data:', pageData)      

            
             
            


        
          
          




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
          i = 1
          for r in xLib.library:
              print('\t', 10*"+", i, 10*'+')
              print( "\tName:", r.ruleName   )
              print( "\tDescription:", r.ruleDescription   )
              print( "\tActivation:", r.ruleURLActivationCondition   )
              print( "\tCSS selector:", r.ruleCSSSelector   )
              print( "\tPrecondition type:", r.rulePreconditionType  )
              print( "\tNumber of preconditions:", len(r.rulePreconditions)   )
              print("\tUsage stats:")
              print( "\t\tApplied count:", r.ruleAppliedCount   )
              print( "\t\tMatch count:", r.ruleMatchCount   )
              i+=1

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

          

     


'''
#
# Class to execute commands given
# via the application's shell
#
class shellCommandExecutioner:

      def __init__(self, cfg):
          self.configuration = cfg
          self.totalCommands = 0
          self.commandsExecuted = 0


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

          


      
      def get(self, a):
          try:  
             cmdArgs = ThrowingArgumentParser()          
             cmdArgs.add_argument('tweetids',   nargs=argparse.REMAINDER, default=[] )
             cmdArgs.add_argument('-f', '--idfile',  nargs='?', default='' )
             cmdArgs.add_argument('-E',  '--showerrors', action='store_true')
             args = vars( cmdArgs.parse_args(a) )

          except Exception as gEx:
                print( str(gEx) )
                return(False)

          tAPI = twitterV2API.twitterSearchClient( self.configuration )
          if args['idfile'] == '':
             status = tAPI.getTweets( args['tweetids'], args['showerrors'] )
          else:
             if not os.path.exists( args['idfile'] ):
                print('Error. No such file [', args['idfile'], ']')
             else:
                idF = open( args['idfile'], 'r')
                #idList = idF.readlines()
                idList = mylist = idF.read().splitlines() 
                idF.close()
                print( 'File preview: ', idList[:5], '...\n', sep='' )
                status = tAPI.getTweets( idList + args['tweetids'], args['showerrors']  )   


          #if status is None:
          #   print('Error')
          
        



      
      def search(self, a):

          # Inner/nested function
          # Parses only arguments for search command ONLY.
          # Put in a different method in order not to bloat
          # the search method.
          def parseSearchArguments(cmdArgs):
        
            try:  
             parser = ThrowingArgumentParser()
          
             parser.add_argument('-f', '--from',   nargs='?', default= (datetime.now() - timedelta(days=2)).strftime("%d/%m/%Y") )
             parser.add_argument('-u', '--until', nargs='?', default=(datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y") )
             parser.add_argument('-t', '--timestep', nargs='?', default="" )
             parser.add_argument('-n', '--numtweets', type=int, nargs='?', default=0 )
             parser.add_argument('-o', '--outfile', type=str, nargs='?', default='' )
             parser.add_argument('-D',  '--debugmode', action='store_true')

             # IMPORTANT! The -S has been added to differentiate -in a quick and dirty manner-between period and simple queries.
             # if -S is present, this means a simple search will be conducted on the recent archive without any date constraints.
             # TODO: Get rid of -S and find some other way to differentiate these two type of queries 
             parser.add_argument('-S',  '--simple', action='store_true')

             # IMPORTANT! arguments -f, -u -t -n etc on the command line, MUST APPEAR BEFORE
             #            the remaining arguments. Otherwise, these arguments will not be parsed
             #            and will be interpreted as part of the remaining arguments i.e. parts of the query.
             parser.add_argument('keywords', nargs=argparse.REMAINDER)
          
          
             args = vars( parser.parse_args(cmdArgs) )

             # We make sure that no . spearator (separating seconds from ms at the end is present (as return by now())
             # this will destroy all our hypotheses about the formatting.
             # We also convert dates: Dates are always returned in isoformat.
             args['from'] = dateutil.parser.parse( args['from'].split('.')[0] , dayfirst=True).isoformat() + 'Z'        
             args['until'] = dateutil.parser.parse( args['until'].split('.')[0] , dayfirst=True).isoformat() + 'Z'    
             return(args)
    
            except Exception as argEx:
               print( str(argEx) )             
               return(None)
            
            return(None)


          ####################################
          #  outer method search starts here
          ####################################
          
          sParams = parseSearchArguments(a)
          if sParams is None:
             print("Usage: search [-f <from date>] [-u <to date>] [-n <number of tweets>] [-o <csv file>] [-S] [-D] <query>")
             return(False)

          
          # First, check if some configuration settings need to be overriden by
          # shell/command line arguments given by user. 
          # NOTE: We will make here a deep copy of the original configuration and make
          #       any change on that copy.
          # TODO: Check to see if Memento design pattern would be appropriate    


          
          # Before doing any change to the settings, make a deep copy of the current
          # config settings. This copy will be passed as
          # the search settings. Hence, any command shell arguments overrides the values
          # of the copy - not the original.
          # We consume a little bit of memory more, but
          # that's a static cost and is required memory is very, very low (i.e.
          # definitely within limits)
          # PS: We make a deep copy since we want to accommodate future modifications
          # where more complicate settings might be present in configurations. 
          cmdConfigSettings = copy.deepcopy( self.configuration )

         
          if sParams['numtweets'] != 0:
             cmdConfigSettings['General']['maxTweetsPerPeriod'] =  str(sParams['numtweets'])


          if sParams['outfile'] != '':
            if cmdConfigSettings.getboolean('Debug', 'debugMode', fallback=False):
               print("[DEBUG] Overriding setting csvFile from [", cmdConfigSettings['Storage']['csvFile'], "] to [", sParams['outfile'], "]")
             
            #cmdConfigSettings['Storage']['format'] =  'csv'
            cmdConfigSettings.set('Storage', 'format', 'csv')
            #cmdConfigSettings['Storage']['csvFile'] =  sParams['outfile']
            cmdConfigSettings.set('Storage', 'csvFile', sParams['outfile'])

          
        
          if sParams['debugmode']:
            #if configSettings.getboolean('Debug', 'debugMode', fallback=False):
            print("[DEBUG] Overriding setting debugMode from [", cmdConfigSettings['Debug']['debugMode'], "] to [", str(not cmdConfigSettings.getboolean('Debug', 'debugMode', fallback=False)), "]")
            # toggle debug setting
            cmdConfigSettings['Debug']['debugMode'] =  str( not cmdConfigSettings.getboolean('Debug', 'debugMode', fallback=False)) 

        

          # Perform actual search for tweets with the configuration. Instantiate an API object,
          tAPI = twitterV2API.twitterSearchClient( cmdConfigSettings )
          
          # Do we require a simple search on the recent archive, without any dates?
          if sParams['simple']:
             # Yes. This is a simple query without any dates. Call the appropriate method.   
             if cmdConfigSettings.getboolean('Debug', 'debugMode', fallback=False):
                print('[DEBUG] Initiating simple query on forced recent archive. No date constraints.')
                
             nFetched = tAPI.simpleQuery(  " ".join(sParams['keywords']).strip() )
          else:
             # This is a search based on dates. Call the appropriate method.   
             if cmdConfigSettings.getboolean('Debug', 'debugMode', fallback=False):
                print('[DEBUG] Initiating period query on specified archive. ')
                
             nFetched = tAPI.periodQuery( sParams['from'], sParams['until'], sParams['timestep'], " ".join(sParams['keywords']).strip() )

             
          if nFetched >= 0:
             print('\n\n\t[', datetime.now().strftime('%d/%m/%Y %H:%M:%S'), '] Fetched total of ', nFetched, ' tweets.', sep='')
          else:
             print('\n\n\t[', datetime.now().strftime('%d/%m/%Y %H:%M:%S'),  '] Error ', nFetched, ' encounterred.', sep='')   

                 
          return(False)
         




      


      
      def showcsv(self, a):
          try:  
           shellParser = ThrowingArgumentParser()           
           shellParser.add_argument('-s', '--separator', nargs='?',  default=self.configuration.get('Storage', 'csvSeparator', fallback=',') )
           shellParser.add_argument('-n', '--numrows', type=int, nargs='?',  default=15)
           #shellParser.add_argument('-R', '--rows', nargs='?',  default=':')
           shellParser.add_argument('-N',  '--noheader', action='store_true')
           shellParser.add_argument('-T','--tail', action='store_true')
           shellParser.add_argument('-F','--fields', nargs='+', default=['username', 'url'])

           shellParser.add_argument('csvfile', nargs=argparse.REMAINDER, default='')

           shellArgs = vars( shellParser.parse_args( a ) )
           #print(shellArgs)
           #print('>>>',  shellArgs['csvfile'])
           if not shellArgs['csvfile']:
              # Empty. Fill in with default value from config file
              # We do this, since the REMAINDER option seems
              # to ignore default values in add_argument.
              # TODO: check this in a more thorough way
            shellArgs['csvfile'] = self.configuration.get('Storage', 'csvFile', fallback="data.csv")     
           else:   
              shellArgs['csvfile'] =  shellArgs['csvfile'][0]


      
          except Exception as ex:
             print( str(ex) )
             print("Invalid argument. Usage: showcsv [-F <field list>] [-s <separator>] [-N] [-n <number of rows>] [-T] <csv file name>")
             return(False)


          if not os.path.exists( shellArgs['csvfile'] ):
             print('File ', shellArgs['csvfile'], ' does not exist.' )
             from pathlib import Path
             p = Path(shellArgs['csvfile'])
             #print('Parent dir is [', p.parent, ']')
             if os.path.isabs( str(p.parent) ) or str(p.parent) == '.' :
                target = str(p.parent)
             else:      
                target = os.path.join(os.path.dirname(__file__), str(p.parent))             
                
             if not os.path.exists( target ):                
                return(False)   
             
             csvFiles = utils.listDirectoryFiles( target, '.csv') 
             if len(csvFiles) != 0:                  
                print('\nFound the following csv files in the same directory [', str(p.parent), '] which may be of interest to you (newest appear higher in list):', sep='')
                for fn in csvFiles:
                    if fn == '':
                       continue
                  
                    print('\t', fn, sep='')  
             
             return(False)
                
          
          hdr = 0  
          if shellArgs['noheader']:
             hdr = None
             
          try:             
             tweetsDF = pd.read_csv(shellArgs['csvfile'], sep=shellArgs['separator'], header=hdr )
             print('')
             print('File: ', shellArgs['csvfile'] )
             print('Number of rows:', tweetsDF.shape[0], sep='' )
             print('Number of columns:', tweetsDF.shape[1], sep='' )
             print('Column names:', list(tweetsDF.columns) )
             #print('Number of duplicate rows:', ) # TODO: Complete me.
             
             if not shellArgs['tail']:
                print('First ', shellArgs['numrows'], ' rows:', sep='')
                print( tweetsDF.loc[ :, shellArgs['fields'] ].head(shellArgs['numrows']) )
             else:
                 print('Last ', shellArgs['numrows'], ' rows:', sep='')
                 print( tweetsDF.loc[:, shellArgs['fields'] ].tail(shellArgs['numrows']) )      
                   
          except Exception as dfREx:
                print('ERROR.',  str(dfREx) )

          return(False)
            




      

      # TODO: Sorry about this. It's a mess. Needs to be seriously refactored.
      #       This was done quickly.
      def help(self, a):

            # Inner/nested function. Move this to utils???
            def NLFormat(string, every=72):
                lines = []
                for i in range(0, len(string), every):
                  lines.append('\t' + string[i:i+every])
                return '\n'.join(lines)
            
            print("\n\tSupported commands and their syntax:")
            print("")

            print('\t' + 72*'-')
            print( NLFormat('get [-E] [-f <id file>] [< list of tweet ids>]', 72) )
            print('\t'+72*'-')
            print('\tAbout:')
            print( NLFormat('Downloads fields for specific tweets identified by their ids given as arguments.') )
            print("\tArguments:")            
            print( NLFormat('-f: path to local file containing list of tweet ids to fetch. Must contain each id in a separate line\n'))
            print( NLFormat('<list of tweet ids>: list of tweet ids to fetch, separated by whitespace.\n'))
            print( NLFormat('[-E]: Show errors. From the list of ids given to download, display the tweet ids that could not be downloaded (due to error or not existence)\n'))

            print("")
            

            
            print('\t' + 72*'-')
            print( NLFormat('search [-f <date>] [-u <date>] [-t <time step>] [-D] [-S] [-o <csv file>] [-n <number of tweets/period>] <query>', 72) )
            print('\t'+72*'-')
            print('\tAbout:')            
            print( NLFormat('Performs a simple or period search. Searches for tweets meeting conditions in <query>.\n'))
            print("\tArguments:")
            print( NLFormat('-n: Number of tweets to fetch. If a date query is conducted, -n specifies the number of tweets to download during each period.\n'))
            print( NLFormat( "-f, -u: Datetimes should be enterred as Day/Month/YearTHour:Minutes:Seconds. Datetimes are always in UTC. Example: search -f 29/12/2021T10:07:55 -u 31/12/2021T08:32:11 euro crisis\n" ))
            print( NLFormat( "-t: Time steps should be specified in the following manner: kDmHnMzS where k, m, n and z integer values. Example 3D10H5M8S. -t format specifies how the date range specified " +
                          " by -f and -u arguments will be divided into subperiods, in each of which a seperate search will be conducted for the same query. For example the query search -f 3/2/2008 -u 10/2/2008 -t 2D10H5M2S euro " +
                          " will break up the date range [3/2/2008, 10/2/2008] to subperiods of length 2 days, 10 hours, 5 minutes and 2seconds and conduct a search in each of these perids. In this example, search " +
                          "for the term euro in tweets will be conducted in the following periods separately:"))
            print( NLFormat('[ 03/02/2008 00:00:00 - 05/02/2008 10:05:02 ]'))
            print( NLFormat('[ 05/02/2008 10:05:02 - 07/02/2008 20:10:04 ]'))
            print( NLFormat('[ 07/02/2008 20:10:04 - 10/02/2008 00:00:00 ]\n'))
            print( NLFormat('-S: Conduct a simple search. Simple search means that the recent archive is searched and that no date constraints are enforced. -S option will make any option related to dates such as -f, -u -t obsolete.\n'))
            print( NLFormat('-D: Toggle debug mode (if true, set to false. If false, set to true).\n'))
            print( NLFormat('<query>: Query. For a list of supported query operators see https://developer.twitter.com/en/docs/twitter-api/tweets/search/integrate/build-a-query and https://developer.twitter.com/en/docs/twitter-api/v1/rules-and-filtering/search-operators \n'))
            print("")
            print('\t' + 72*'-')
            print( NLFormat('config') )
            print('\t' + 72*'-')
            print('\tAbout:')
            print( NLFormat('Displays currently loaded configuration settings.'))
            print("")
            print('\t' + 72*'-')
            print( NLFormat('reload [-c <path to configuration file>]') )
            print('\t' + 72*'-')
            print('\tAbout:')
            print( NLFormat('Allows loading a configuration file specified by the -c option. Relating file names are supported.'))
            print('\tArguments:')
            print( NLFormat('-c: Path (absolute or relative) to configuration file to load. In no -c option is provided, the same configuration file loaded during startup is reloaded'))
            print('')
            
            print('\t' + 72*'-')
            print( NLFormat('history (alternatively h) [-s] [<number of commands to display]' ) )
            print('\t' + 72*'-')
            print('\tAbout:')
            print( NLFormat('Displays a numbered list of the history of commands executed. Numbers can be used with ! (see below). Usefull to re-execute commands or copy-paste complicated commands'))
            print('\tArguments:')
            print( NLFormat('[<number of commands to display]: number of commands to display.\n'))
            print( NLFormat('-s: If present, specifies that the FIRST [<number of commands to display] commands in the command history list will be displayed. If not present, the LAST [<number of commands to display] commands (more recent) will be shown.'))
            print('')
            
            print('\t' + 72*'-')
            print( NLFormat('set [-G | --target <historic | recent>]' ) )
            print('\t' + 72*'-')
            print('\tAbout:')
            print( NLFormat('Specifies in which archive the search should be condicted.') )
            print('\tArguments:')
            print( NLFormat('-G: Specifies which archive to use. Allowed values are "recent" or "historic"'))            
            print('')
            
            print('\t' + 72*'-')
            print( NLFormat('!<index>' ) )
            print('\t' + 72*'-')
            print('\tAbout:')
            print( NLFormat('Execute command at the position <index> in the command history list (see history or h).'))
            print('')

            print( NLFormat('!<string>' ) )
            print('\t' + 72*'-')
            print('\tAbout:')
            print( NLFormat('Execute last command in the command history list starting with <string>.'))
            print('')

       
            print('\t' + 72*'-')
            print( NLFormat('!!' ) )
            print('\t' + 72*'-')
            print('\tAbout:')
            print( NLFormat('Re-executes last command.'))
            print('')
            print('')
            print('\t' + 72*'-')
            print( NLFormat('help' ) )
            print('\t' + 72*'-')
            print('\tAbout:')
            print( NLFormat('This screen.'))
            print('')
            print('\t' + 72*'-')
            print( NLFormat('quit or q' ) )
            print('\t' + 72*'-')
            print('\tAbout:')
            print( NLFormat('Terminates and quits the application.'))
            print('')

            print('\t' + 72*'-')
            print( NLFormat('github' ) )
            print('\t' + 72*'-')
            print('\tAbout:')
            print( NLFormat('Open TwitterSearch github page in browser.'))
            print('')
            print('')
            return(False)
      
            

      


      def set(self, a):
          shellParser = ThrowingArgumentParser()
          try:
           shellParser.add_argument('-G', '--target', nargs='?', required=True, default='recent')
           shellArgs = vars( shellParser.parse_args( a ) )
          except Exception as ex:
             print("Invalid argument. Usage: set [-G] value")
             return(False)

          if shellArgs['target'].lower() == "recent":
             if 'TwitterAPI' in self.configuration.sections(): 
              self.configuration['TwitterAPI']['apiEndPoint'] =  self.configuration['TwitterAPI']['recentApiEndPoint']
              self.configuration['TwitterAPI']['bearer'] =  self.configuration['TwitterAPI']['essentialBearer']
              self.configuration['TwitterAPI']['targetArchive'] = 'recent'
              print("Target archive set to recent.")
          elif  shellArgs['target'].lower() == "historic":
                self.configuration['TwitterAPI']['apiEndPoint'] =  self.configuration['TwitterAPI']['historicApiEndPoint']
                self.configuration['TwitterAPI']['bearer'] =  self.configuration['TwitterAPI']['academicBearer']
                self.configuration['TwitterAPI']['targetArchive'] = 'historic'
                print("Target archive set to historic.")
          else:
             print("Invalid target archive option [", shellArgs['target'], "]. Allowed values: historic, recent", sep='')
             return(False)

     
          
  
      def reload(self, a):

        # Inner/nested function
        def setTargetArchive(cfg, md):
          if md.lower() == "recent":
            if 'TwitterAPI' in self.configuration.sections(): 
              cfg['TwitterAPI']['apiEndPoint'] =  cfg['TwitterAPI']['recentApiEndPoint']
              cfg['TwitterAPI']['bearer'] =  cfg['TwitterAPI']['essentialBearer']
              cfg['TwitterAPI']['targetArchive'] = 'recent'
              print("Target archive set to recent.")
          elif  md.lower() == "historic":
             cfg['TwitterAPI']['apiEndPoint'] =  cfg['TwitterAPI']['historicApiEndPoint']
             cfg['TwitterAPI']['bearer'] =  cfg['TwitterAPI']['academicBearer']
             cfg['TwitterAPI']['targetArchive'] = 'historic'
             print("Target archive set to historic.")
          else:
             print("Invalid target archive option [", md, "]. Use historic or recent")


       ####################################
       #  outer method reload starts here
       ####################################
            
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

        # Make sure that the target and bearer agree
        setTargetArchive(self.configuration, self.configuration.get('TwitterAPI', 'targetArchive', fallback="recent") )




      def status(self, a):
          print('Status:')
          print('\tConfig file:', self.configuration.get('__Runtime', '__configSource', fallback="") )
          print('\tTarget search archive:', self.configuration.get('TwitterAPI', 'targetArchive', fallback="recent") )
          return(False)




      def encryptBearer(self, a):

          # Move this to utils?
          def NLFormat(string, every=72):
                lines = []
                for i in range(0, len(string), every):
                  lines.append('\t' + string[i:i+every])
                return '\n'.join(lines)


          try:
            parser = ThrowingArgumentParser()
            parser.add_argument('-V',  '--verify', action='store_true')
            args = vars( parser.parse_args(a) )

          except Exception as aEx:
                 print('ERROR!')
                 return(False)
            
          print( NLFormat('This command allows you to encrypt the bearer tokens (Essential and Academic) and use the encrypted tokens in configuration files.\n\n'))
          
          essB = input('\tGive the Essential bearer token to encrypt>>')
          acaB = input('\tGive the Academic bearer token to encrypt >>')
          
          encK, encEssB = utils.encrypt( essB )
          encAcaB = utils.encrypt2(encK, acaB)

          #print('Encrypting....')
          #print('Key:', encK, sep='')
          #print('Encoded Essential Bearer Token:', encEssB, sep='')
          #print('Encoded Academic Bearer Token:', encAcaB, sep='')

          while True:
             kF = input('\tGive the local file to store the encryption key >>')
             if kF.strip() != '':
                try:   
                  keyFile = open(kF, "wt")
                  n = keyFile.write(encK)
                  keyFile.close()
                  break
                except Exception as wEx:
                       print( str(wEx) )
                       print('Could not write file [', kF, ']')
                       continue
                
          print(NLFormat('\n\tPlease follow now the next step to complete the process:') )
          
          print(NLFormat('\n\tUpdate the configuration file with the following settings:') )
          print('')
          print(NLFormat('\t\tessentialBearer = ' + encEssB, every=1012) )
          print(NLFormat('\t\tacademicBearer = ' + encAcaB, every=1012))
          print(NLFormat('\t\tencryptionKeyFile = ' +  kF) )
          print(NLFormat('\t\tbearerEncrypted = true') )
          print('')
          print('')
          if args['verify']:
             print('\tVerifying:')   
             print('\t\tVerifying essential bearer....', end='')
             if utils.decrypt( encK, encEssB ) == essB:
                print('OK')
             else:
                print('ERROR')

             print('\t\tVerifying academic bearer....', end='')
             if utils.decrypt( encK, encAcaB ) == acaB:
                print('OK')
             else:
                print('ERROR')
             
          #print('\tDecoded Essential Bearer:', utils.decode( encK, encEssB ), sep='')
          #print('\tDecoded Academic Bearer:', utils.decode( encK, encAcaB ), sep='')

          
          return(False)



      def github(self, a):
          #self.configuration.get('General', 'githubURL', fallback='https://github.com/deusExMac/TwitterSearch')  
          webbrowser.open( self.configuration.get('General', 'githubURL', fallback='https://github.com/deusExMac/TwitterSearch') )  
          return( False )

          '''
