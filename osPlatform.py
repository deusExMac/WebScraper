import platform
import psutil
import configparser

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

      def __init__(self, pName):
          self.nkilled = 0
          self.processName = pName


      def killProcess(self):
          if self.processName == '':
             return(False)
            
          for proc in psutil.process_iter():
             # check whether the process name matches
             if proc.name() == self.processName:
                proc.kill()
                self.nkilled += 1

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






