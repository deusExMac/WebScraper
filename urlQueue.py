
import pandas as pd
import numpy as np
import csv




class urlQueue:

      def __init__(self, qS=1000, startNewSession=True, qF='.queue',  csvSep=';'  ):
          
          self.qSize = qS
          self.qFile = qF

          self.queue = pd.DataFrame({'url': pd.Series(dtype='str'),
                                          'fetched': pd.Series(dtype='str'),
                                          'status': pd.Series(dtype='int'),
                                          'contenttype': pd.Series(dtype='str'),
                                          'lastmodified': pd.Series(dtype='str'),
                                          'hash': pd.Series(dtype='str')
                                         }
                                       )
          if not startNewSession:
              # We do it this way so that even if an error occurs, an empty data frame exists.
              # Also, we rely on the Python gb to do its job.
              print('[DEBUG] loading queue from [', self.qFile, ']')
              try:
                 self.queue = pd.read_csv(self.qFile, header=0, sep=csvSep, quoting=csv.QUOTE_NONNUMERIC)
              except Exception as rEx:
                 print('[DEBUG] Error loading queue from file ', self.qFile, ':', str(rEx), 'Continuing with empty queue.', sep='') 
              
          
          
          
          
          


      def uInQueue(self, u):
          if self.queue.loc[ self.queue['url'] == u ].shape[0] == 0:
             return(False)

          return(True)  



      def hInQueueH(self, h):
          if self.queue.loc[ self.queue['hash'] == u ].shape[0] == 0:
             return(False)

          return(True)
        



      def add(self, u, f=np.nan, s=-1, c=np.nan, l=np.nan, h=np.nan):

          if self.uInQueue(u):
             print('[DEBUG] url [', u, '] Already in queue. Not adding.', sep='') 
             return(False)


          if self.qSize > 0:
             if self.queueSize() >= self.qSize:
                return(False) 
          try:
            d = {'url':u, 'fetched':f, 'status':s, 'contenttype':c, 'lastmodified':l, 'hash':h}
            self.queue = self.queue.append(d, ignore_index = True)
            return(True)
          except Exception as ex:
             return(False) 


      def isEmpty(self):
          if self.queue is None:
             return(True)
            
          if self.queue.shape[0] == 0:
             return(True)

          return(False)  
          


      def getNext(self):
          try:
             return( self.queue.loc[ self.queue['status'] == -1, 'url' ].iloc[0] )
          except IndexError as iErr:              
              return( None )


       
      def queueSize(self):
          return( self.queue.shape[0] )

        
      def pendingUrlsCount(self):
          return( self.queue.loc[ self.queue['status'] == -1].shape[0] )


      def errorUrlsCount(self):
          return( self.queue[ (self.queue['status'] < 0 ) & (self.queue['status'] != -1) ].shape[0] )

       

      def updateStatus(self, u, sts):          
          self.queue.loc[ self.queue['url'] == u, 'status' ] = sts

          
      def updateLastModified(self, u, lm):          
          self.queue.loc[ self.queue['url'] == u, 'lastmodified' ] = lm


      def updateContentType(self, u, ct):          
          self.queue.loc[ self.queue['url'] == u, 'contenttype' ] = ct   


      def updatePageHash(self, u, ph):          
          self.queue.loc[ self.queue['url'] == u, 'hash' ] = ph   


          
      def showQ(self):
          print( self.queue )

      
          
      def saveQ(self, csvsep=';'):
          try:
             self.queue.to_csv( self.qFile, index=False, sep=csvsep, quoting=csv.QUOTE_NONNUMERIC )
          except Exception as svEx:
             print('[ERROR] Error saving queue to csv file [', self.qFile, '] ', str(svEx), sep='') 
