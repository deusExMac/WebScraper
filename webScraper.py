
import configparser
import argparse

import sys, getopt
import os
import os.path
from pathlib import Path
import dateutil.parser


import json, requests, datetime
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
#from urllib  import  urljoin

from requests_html import HTMLSession

import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import math
from random import seed
from random import randint




import xRules
import commandShell





def main():
    


   #
   # TODO: Fix the config and arg stuff. Or at least use a consistent model.
   # MODEL:
   #    1) Load config file
   #    2) Command line arguments override loaded config settings
   #

   cmdArgParser = argparse.ArgumentParser(description='Command line arguments', add_help=False)
   cmdArgParser.add_argument('-c', '--config', default="./webscraper.conf")
   cmdArgParser.add_argument('-u', '--url')
   cmdArgParser.add_argument('-r', '--rules', default="./default.exr")

   cmdArgParser.add_argument('-B', '--batch', action='store_true')
   #cmdArgParser.add_argument('-I', '--interactive', action='store_true')

   args = vars( cmdArgParser.parse_args() )

   # Config file that will be used
   configFile = args['config']


    
   # Initialize some important parameters.
   # NOTE: command line arguments can override them

   config = configparser.RawConfigParser(allow_no_value=True)

   print("\n\nLoading config settings from [", configFile, "]....", end='')
   # Check if config file exists
   cFile = Path(configFile)
   if cFile.exists():
    try:
      config.read(configFile)
      config.add_section('Runtime')
      config.set('Runtime', '__configurationFile', configFile)
      print('ok.')
    except Exception as cfgEx:
           print("Error reading config file." + str(cfgEx))
   else:
    print("Error. Config file [", configFile, "] not found. Continuing with default settings.", sep="")
    #sys.exit("Cannot continue")
    config.add_section('Runtime')
    config.set('Runtime', '__configurationFile', "")



   # Here, override any config parameter given via command line
   
   config.set('Rules', 'ruleFile', args['rules'] )


   ruleLibrary = None
   print("Loading extraction rule library [", args['rules'], "]...", sep='', end='')
   try:
     with open(args['rules'],  encoding='utf-8', errors='ignore', mode='r') as f:          
          ruleLibrary = xRules.loadLibrary(f.read())
                    
     print('done')
     print('\tTotal of ', ruleLibrary.numberOfRules(), ' extraction rules loaded.')
   except Exception as readEx:
       print('Error.', str(readEx))



   



   if not args.get('batch', False):
      print("Starting interactive mode\n") 
      iShell = commandShell.commandShell( config, ruleLibrary )
      iShell.startShell()

   else:
      print('Entering Batch mode.')
      if args.get('url') is not None:
         session = HTMLSession()
         r = session.get(args['url'])
         rL = ruleLibrary.get('getLinks')
         #res = soup.select( rL.ruleCSSSelector )
         res = r.html.find(rL.ruleCSSSelector, first=False)
         for l in res:
            print(l.attrs.get('href'))
      

   

      '''   
       if rL.ruleTargetProperty == 'text':
          print("::: [", item.contents[0], ']')
       else:
           print("::: [", urljoin(urlBase, item.get(rL.ruleTargetProperty) ), ']')
       '''    
      
'''
   if args.get('url') is not None:
      print('Downloading ', args['url'], '...')
      reqResponse = requests.get(args['url'])
      #print( htmlContent.text )
      with open('page.html', 'w') as f:
        f.write(reqResponse.text)

      htmlContent = reqResponse.text  
   
   else:
    print('Reading from file')
    with open('page.html',  encoding='utf-8', errors='ignore', mode='r') as f:
          htmlContent = f.read()


   print("Loading rules...")
   with open('ruleExample.conf',  encoding='utf-8', errors='ignore', mode='r') as f:
          rSpec = f.read()
          rule = xRules.loadRule(rSpec)


   soup = BeautifulSoup(htmlContent, features="html.parser")

   rL = ruleLibrary.get('efficiencyPerDay')
   if rL is not None:
      print(">>> applying ", rL.ruleCSSSelector) 
      res = soup.select( rL.ruleCSSSelector )
      for item in res:
       if rL.ruleTargetProperty == 'text':
          print("::: [", item.contents[0], ']')
       else:
           print("::: [", item.get(rL.ruleTargetProperty), ']')


   urlBase = 'https://www.asicminervalue.com/'
   rL = ruleLibrary.get('getLinks')
   if rL is not None:
    print(">>> applying ", rL.ruleCSSSelector)
    res = soup.select( rL.ruleCSSSelector )
    for item in res:
       if rL.ruleTargetProperty == 'text':
          print("::: [", item.contents[0], ']')
       else:
           print("::: [", urljoin(urlBase, item.get(rL.ruleTargetProperty) ), ']') 

'''     



#config.getint('Default', 'maxArticlesXXX', fallback=80)


if __name__ == '__main__':
   main() 

