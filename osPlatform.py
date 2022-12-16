import platform
import psutil
import configparser
import re

import utils


class OSPlatformFactory:

      def __init__(self, conf=None):
          self.config = conf

      def createPlatform(self):
          dbgMode = False
          if self.config is not None:
             dbgMode = self.config.getboolean('DEBUG', 'debugging', fallback=False)
             
          if   isWindows():   
                return( osPlatform(self.config.get('Crawler', 'windowsChrome', fallback=''), dbgMode ) ) 
          elif isMac():
                   return( osPlatform(self.config.get('Crawler', 'macosChrome', fallback=''), dbgMode) )  
          elif  isLinux():
                   return( osPlatform(self.config.get('Crawler', 'linuxChrome', fallback=''), dbgMode) )
          elif  isAndroid():
                   return( osPlatform(self.config.get('Crawler', 'androidChrome', fallback=''), dbgMode) )
          else:
                   return( osPlatform('', dbgMode) )
 



class osPlatform:

      def __init__(self, pName='', dbg=False):

          self.debug = dbg  
          self.nkilled = 0
          # A regular expression
          self.processName = ''
          if pName is not None:
             self.processName = pName.strip()


      def filterProcesses(self, nameRegex=''):
          ps = []
          for proc in psutil.process_iter():
              try:  
                pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])
              except psutil.NoSuchProcess:
                continue
              except psutil.ZombieProcess:
                continue

              if pinfo.get('name', '') is None:
                 continue
            
              
               
              if re.search(nameRegex, pinfo.get('name', '') ):      
                 ps.append( pinfo.get('name', '') )

          return(ps)


      def getProcessInfoByName(self, nameRegex=''): 
          pi = []
          for proc in psutil.process_iter():
              pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])
              try:
                 if pinfo.get('name', '') is None:
                    continue
               
                 if re.search(nameRegex, pinfo.get('name', '') ):
                    pi.append( pinfo )
                    
              except Exception as pinfoEx:
                    print(str(pinfoEx))
                    continue
                  
          return(pi)


      def getImageProcessesInfo(self):
          return( self.getProcessInfoByName(self.processName) )
                              

        
      def runningProcess(self, pName=''):
          if pName == '':
             if self.processName == '':
                return(False)
             pName = self.processName
              
          for proc in psutil.process_iter():
            try:    
              if re.search( pName, proc.name()):
                 return(proc)
            except Exception as rEx:
                 continue
            
          return(None)


        
      def processIsRunning(self, pName=''):
          p = self.runningProcess(pName)
          if not p:
             return(False)

          return(True)
        
          

          
      def killProcess(self, namePattern='', excludedPids=[]):

          targetPattern = ''
          if namePattern != '':
             targetPattern = namePattern
          else:
             targetPattern = self.processName

          
          print( utils.toString('\t[DEBUG] Process name target pattern:', targetPattern, '\n') if self.debug  else '', end='' )
          
          if targetPattern == '':
             return(False)

          
      
          for proc in psutil.process_iter():
           try:                 
             if re.search(targetPattern, proc.name()):
                  
                  pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])                  
                  print( utils.toString('\t[DEBUG] Checking if ', pinfo['pid'], ' in [', ', '.join( [str(m) for m in excludedPids]), ']...') if self.debug  else '', sep='', end='') 
                  
                  
                  if pinfo['pid'] not in excludedPids:
                     print( utils.toString(' NO. killing\n') if self.debug  else '', end='' )
                     proc.kill()
                     self.nkilled += 1
                  else:
                       print( utils.toString(' YES. NOT killing\n') if self.debug  else '', end='' )
                       
           except Exception as killEx:
                   #print( str(killEx) )
                   print(utils.toString( '\t[DEBUG] Caught exception... but ignoring. Zombie?', str(killEx), '\n') if self.debug  else '', sep='', end='' )
                   continue   
           
          return(True)


      




def getPlatformName():
    return( platform.system() )  


def isWindows():
    if 'windows' in getPlatformName().lower():
       return(True)
    return(False)



def isMac():
    if 'darwin' in getPlatformName().lower():
       return(True)
    return(False)

def isLinux():
    if 'linux' in getPlatformName().lower():
       return(True)
    return(False)


def isAndroid():
    if 'android' in getPlatformName().lower():
       return(True)
    return(False)






