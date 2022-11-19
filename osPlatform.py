import platform
import psutil
import configparser
import re

import utils


class OSPlatformFactory:

      def __init__(self, conf=None):
          self.config = conf

      def createPlatform(self):
          if   isWindows():   
                return( osPlatform(self.config.get('Crawler', 'windowsChrome', fallback='')) ) 
          elif isMac():
                   print('Instatiating MacOS platform object')
                   return( osPlatform(self.config.get('Crawler', 'macosChrome', fallback='')) )  
          elif  isLinux():
                   return( osPlatform(self.config.get('Crawler', 'linuxChrome', fallback='')) )
          elif  isAndroid():
                   return( osPlatform(self.config.get('Crawler', 'androidChrome', fallback='')) )
          else:
                   return( osPlatform('') )
 



class osPlatform:

      def __init__(self, pName=''):
          self.nkilled = 0
          # A regular expression
          self.processName = ''
          if pName is not None:
             self.processName = pName.strip()


      def filterProcesses(self, nameRegex=''):
          ps = []
          for proc in psutil.process_iter():
              if re.search(nameRegex, proc.name() ):
                 ps.append( proc.name() )

          return(ps)


      def getProcessInfoByName(self, nameRegex=''):
          pi = []
          for proc in psutil.process_iter():
              pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])  
              if re.search(nameRegex, pinfo['name'] ):
                 pi.append( pinfo )

          return(pi)


      def getImageProcessesInfo(self):
          return( self.getProcessInfoByName(self.processName) )
                              

        
      def runningProcess(self, pName=''):
          if pName == '':
             if self.processName == '':
                return(False)
             pName = self.processName
              
          for proc in psutil.process_iter():
              if re.search( pName, proc.name()):
                 return(proc)

          return(None)


        
      def processIsRunning(self, pName=''):
          p = self.runningProcess(pName)
          if not p:
             return(False)

          return(True)
        
          

          
      def killProcess(self, excludedPids=[]):
          if self.processName == '':
             return(False)

          pf = self.filterProcesses( self.processName )
          print('Matching processes:', pf)
          if len(pf) <= 0:
             return(False)
            
          for proc in psutil.process_iter():
           try:                 
             if re.search(self.processName, proc.name()):
                  #if not proc.
                  pinfo = proc.as_dict(attrs=['pid', 'name', 'create_time'])
                  print('>>> Checking if', pinfo['pid'], 'in', excludedPids, end='')
                  if pinfo['pid'] not in excludedPids:
                     print('NO. killing')    
                     proc.kill()
                     self.nkilled += 1
                  else:
                       print('YES. NOT killing') 
           except Exception as killEx:
                   print('Caught exception... but ignoring.')
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






