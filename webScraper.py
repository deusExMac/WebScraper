
import configparser
import argparse

#import sys, getopt
import os
import os.path
from pathlib import Path


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
   cmdArgParser.add_argument('-r', '--rules', default="./default.exr")

   cmdArgParser.add_argument('-n', '--numpages', type=int, nargs='?' )
   cmdArgParser.add_argument('-t', '--sleeptime',  nargs='?' )
   cmdArgParser.add_argument('-M', '--mirror', action='store_true' )

   cmdArgParser.add_argument('-B', '--batch', action='store_true')
   cmdArgParser.add_argument('url', nargs=argparse.REMAINDER, default=[])
   

   
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
         config.add_section('__Runtime')
         config.set('__Runtime', '__configSource', configFile)
         print('ok.')
      except Exception as cfgEx:
             print("Error reading config file." + str(cfgEx))
   else:
    print("Error. Config file [", configFile, "] not found. Continuing with default settings.", sep="")    
    config.add_section('__Runtime')
    config.set('__Runtime', '__configSource', "")







   # Here, override any config parameter given via command line


   # Load rules file.
   config.set('Rules', 'ruleFile', args['rules'] )
   ruleLibrary = None
   print("Loading extraction rule library [", args.get('rules', ''), "]...", sep='', end='')
   try:
     with open(args['rules'],  encoding='utf-8', errors='ignore', mode='r') as f:          
          ruleLibrary = xRules.loadLibrary(f.read())
                    
     print('done')
     print('\tTotal of ', ruleLibrary.numberOfRules(), ' extraction rules loaded.')
   except Exception as readEx:
       print('Error.', str(readEx))



   # Check how to start: Interactive or batch mode

   if not args.get('batch', False):
      print("Starting interactive mode\n") 
      iShell = commandShell.commandShell( config, ruleLibrary )
      iShell.startShell()
   else:
      print('Entering Batch mode.')
      if len(args.get('url')) > 0:
         argumentList = []
         

         if args.get('mirror', False):
            argumentList.append('-M')

         if args.get('numpages') is not None :
            argumentList.append('-n')
            argumentList.append( str(args.get('numpages')))

                  
         if args.get('sleeptime') is not None :
            argumentList.append('-t')
            argumentList.append( str(args.get('sleeptime')))
            
         argumentList.append(args.get('url')[0])

         
         executioner = commandShell.commandImpl(config, ruleLibrary)
         executioner.crawl( argumentList )

         

   

  

if __name__ == '__main__':
   main() 

