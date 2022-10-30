import sys
import configparser
import argparse

#import sys, getopt
import os
import random


import platform
import os.path
from pathlib import Path


import appConstants
import xRules
import commandShell
import pyjokes






# Generate an empty configuration setting, with only the sections.
# Used when no valid configuration file is given or found.
def generateDefaultConfiguration():
    cS = configparser.RawConfigParser(allow_no_value=True)
    cS.add_section('Rules')
    cS.add_section('Crawler')
    cS.add_section('Storage')
    cS.add_section('Shell')
    return(cS)






def main():
    
   #
   # The steps are as follows:
   #    1) Load config file
   #    2) Command line arguments override loaded config settings
   #

   # Prepare command line arguments
   cmdArgParser = argparse.ArgumentParser(description='Command line arguments', add_help=False)
   cmdArgParser.add_argument('-c', '--config', default="./webscraper.conf")
   cmdArgParser.add_argument('-r', '--rules', default="./default.exr")
   
   cmdArgParser.add_argument('-B', '--batch', action='store_true')
   cmdArgParser.add_argument('-J', '--joke',  action='store_true')
   cmdArgParser.add_argument('url', nargs=argparse.REMAINDER, default=[])
   
   # We only parse known arguments (see previous lines) i.e. arguments
   # that make sense in starting WebScraper. On the command line, more
   # arguments can be present that are used for batch processing.
   # These are not handled via ArgumentParser.
   knownArgs, unknownArgs = cmdArgParser.parse_known_args()
   args = vars( knownArgs )
   
   
   
   # Config file that will be used.
   # NOTE: This will at least have the default value
   configFile = args['config']

   print('\n\n[v', appConstants.APPVERSION, ' ', appConstants.VERSIONRELEASEDATE, ']', sep='') 
   print('Execution started on ', platform.system(), ' release ', platform.release(), ' (', os.name, ')', sep='')
   print("\nLoading configuration settings from [", configFile, "]....", end='')
   # Check if config file exists
   cFile = Path(configFile)
   if not cFile.exists():
      # No, does not exists. Continue with default values

      # Generate an empty configuration file, containing only the required sections   
      config = generateDefaultConfiguration() 
      print("Error. Config file [", configFile, "] not found. Continuing with default settings.", sep="")    
      config.add_section('__Runtime')
      config.set('__Runtime', '__configSource', "")
   else:   
      try:
         # Read configuration file
         config = configparser.RawConfigParser(allow_no_value=True)
         config.read(configFile)
         # Add special section to indicate which file was loaded.
         # Used to support reloading the same configuration file
         config.add_section('__Runtime')
         config.set('__Runtime', '__configSource', configFile)
         print('ok.')
      except Exception as cfgEx:
             print("Error reading config file." + str(cfgEx))
   
     
   # Here, override any config parameter given in the command line

   # Update the rules file in the configuration, if one is given in the command line
   config.set('Rules', 'ruleFile', args['rules'] )


   # Load the extraction rules from a library file.
   # If no library file is specified, load the default
   # library file.
   ruleLibrary = None
   print("Loading extraction rule library [", args.get('rules', ''), "]...", sep='', end='')
   try:   
     with open(args['rules'],  encoding='utf-8',  mode='r', errors='ignore') as f:          
          ruleLibrary = xRules.loadLibrary(f.read())
                    
     print('done')
     print('\tTotal of ', ruleLibrary.numberOfRules(), ' extraction rules loaded.')
     
   except Exception as readEx:
       print('Error.', str(readEx))


   rjk = ''
   if args['joke']:
      try:   
        rjk = pyjokes.get_joke(language="en", category=random.choice(['neutral',  'all']) ) 
      except Exception as jkEx:
             pass


   # Check how to start: In interactive or in batch mode

   if not args.get('batch', False):
      print("\nStarting INTERACTIVE mode", ' ("' + rjk +'")' if rjk != '' else '', "\n", sep='')

      # Start the interactive shell. This shell
      # allows the user to issue and execute a specified set
      # of commands.
      iShell = commandShell.commandShell( config, ruleLibrary )
      iShell.startShell()
   else:

      # We start in batch mode. This means that no shell is executed
      # and crawling is immediately initiated.
      
      print("\nStarting BATCH mode", ' ("' + rjk +'")' if rjk != '' else '', "\n", sep='')
      if len(args.get('url')) <= 0:
         print('No url given. Terminating.')
         return(-2)
      else:
         # We collect any argument that was given at the command line (sys.argv) as
         # a list and pass it to crawl. These arguments will be handled there.
         inputArgs = sys.argv
         argumentList = inputArgs[1:]
         
         # make sure -B is not in argument list. It's an
         # argument valid only at this level; not during crawling.
         argumentList.remove('-B')
                
         executioner = commandShell.commandImpl(config, ruleLibrary)
         executioner.crawl( argumentList )
         
   return(0)
         

   

  

if __name__ == '__main__':
   main() 

