
import configparser
import argparse

#import sys, getopt
import os
import platform
import os.path
from pathlib import Path


import appConstants
import xRules
import commandShell


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
   cmdArgParser.add_argument('-M', '--mirror', action='store_true' )

   cmdArgParser.add_argument('-B', '--batch', action='store_true')
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

