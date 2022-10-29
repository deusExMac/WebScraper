import sys
import configparser
import argparse

#import sys, getopt
import os
import datetime

import platform
import os.path
from pathlib import Path


import appConstants
import xRules
import commandShell
#import utils

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

   cmdArgParser.add_argument('-n', '--numpages', type=int, nargs='?' )
   cmdArgParser.add_argument('-s', '--sleeptime',  nargs='?' )
   cmdArgParser.add_argument('-o', '--outputcsvfile', type=str, nargs='?', default='extracted' + datetime.datetime.now().strftime("%d-%m-%Y@%H-%M-%S") + '.csv' )
   cmdArgParser.add_argument('-q', '--queuefile', type=str, default='.queue' )
 
   cmdArgParser.add_argument('-M', '--mirror', action='store_true' )
   #cmdArgParser.add_argument('-r', '--rules',  nargs='?' )
   cmdArgParser.add_argument('-H', '--humandelay', action='store_true' )             
   cmdArgParser.add_argument('-C', '--continue', action='store_true' )
   cmdArgParser.add_argument('-D', '--dfs', action='store_true' )

   cmdArgParser.add_argument('-R', '--render', action='store_true' )
             
   cmdArgParser.add_argument('-U', '--update', action='store_true' )
   cmdArgParser.add_argument('-p', '--startposition', type=int, nargs='?', default=0 )
             
   cmdArgParser.add_argument('-G', '--debug', action='store_true' )
             

   cmdArgParser.add_argument('-B', '--batch', action='store_true')
   cmdArgParser.add_argument('-J', '--joke',  default='neutral')
   cmdArgParser.add_argument('url', nargs=argparse.REMAINDER, default=[])
   
   args = vars( cmdArgParser.parse_args() )
   
   
   
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

   # Update the rules file in the configuration, given in the command line
   config.set('Rules', 'ruleFile', args['rules'] )


   # Load the extraction rules from a library file.
   # If no library file is specified, load the default
   # library file.
   ruleLibrary = None
   print("Loading extraction rule library [", args.get('rules', ''), "]...", sep='', end='')
   try:
     # Check if .exr file is in UTF-8.
     #u = utils.fileIsUTF8(args['rules'])
     #if not u:
     #   print('[WARNING] file does not seem to be utf-8.')
        
     
     
     with open(args['rules'],  encoding='utf-8',  mode='r', errors='ignore') as f:          
          ruleLibrary = xRules.loadLibrary(f.read())
                    
     print('done')
     print('\tTotal of ', ruleLibrary.numberOfRules(), ' extraction rules loaded.')
     
   except Exception as readEx:
       print('Error.', str(readEx))

   

   # Check how to start: Interactive or batch mode

   if not args.get('batch', False):
      print("Starting interactive mode\n")

      
      # Start the interactive shell. This shell
      # allows the user to issue and execute a specified set
      # of commands.
      iShell = commandShell.commandShell( config, ruleLibrary )
      iShell.startShell()
   else:
      print('Entering Batch mode.')
      if len(args.get('url')) <= 0:
         print('No url given. Terminating.') 
      else:
         inputArgs = sys.argv
         argumentList = inputArgs[1:]
         
         # make sure -B is not in argument list. It's an
         # argument valid only in command line args.
         argumentList.remove('-B')
         
         
         executioner = commandShell.commandImpl(config, ruleLibrary)
         executioner.crawl( argumentList )
         #executioner.crawl( args )

         

   

  

if __name__ == '__main__':
   main() 

