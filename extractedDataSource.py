import os
import os.path

import csv
import pandas as pd



class extractedDataFileCSVReader:

      def __init__(self, csvFile, sep=';'):

          # We do this in order to surpress warnings generated
          # during execution of insertDataAtCurrentPosition method
          pd.options.mode.chained_assignment = None

          
          self.currPos = 0
          self.csvFileName = csvFile
          self.xData = None
          #self.tempBuffer = None # We may opt to add newly added data here. 
          if os.path.exists( csvFile ):          
              self.xData = pd.read_csv( csvFile, sep=sep, header=0, quoting=csv.QUOTE_NONNUMERIC)
              

           


      # TODO: Fixme/complete me
      '''  
      def addExtractedData(self, newData, target='buffer' ):
            
          if self.xData is None:
             return(False)

          #self.tempBuffer = self.xData.iloc[:0,:].copy()
          try:  
             self.xData = pd.concat([self.xData, pd.DataFrame.from_records([ newData ])])             
             return(True)
          except Exception as addEx:
                 print('\t\t[DEBUG]Error adding.', str(addEx) )
                 return(False)
      '''
      def insertDataAtCurrentPosition(self,  newData):
           # Slice the upper half of the dataframe
           df1 = self.xData[0:self.currPos]
  
           # Store the result of lower half of the dataframe
           df2 = self.xData[self.currPos:]
  
           # Insert the row in the upper half dataframe
           df1.loc[self.currPos]=newData
  
           # Concat the two dataframes
           dfResult = pd.concat([df1, df2])
  
           # Reassign the index labels
           dfResult.index = [*range(dfResult.shape[0])]
  
           # Return the updated dataframe
           self.xData = dfResult

           self.currPos += 1 # advance since we added one new row
           



      
      def updateExtractedData(self, url, newData):

          if self.xData is None:
             return  
          
          for k in newData.keys():
              print('\t\t[DEBUG] Updating', k)
              if k not in self.xData.columns:
                 print('\t\t\t[DEBUG] field ', k, 'not found in extracted data')
                 continue
            
              self.xData.loc[self.xData.url == url, k] = newData[k]  



        

      def removeExtractedData(self, url):
          if self.xData is None:
             return
            
          self.xData = self.xData[self.xData.url != url]  
          
      
      def getNext(self):
          if self.xData is None:
             return(None)

          if self.currPos >= self.xData.shape[0]:
             return(None)

          xd = self.xData.iloc[self.currPos].to_dict()
          self.currPos += 1
          return( xd )

        
      def moveBy(self, n):
          self.currPos += n
          
            

      def getNumRows(self):
          if self.xData is None:
             return(0)

          return(  self.xData.shape[0] )





      def save(self, fn='', fs=';'):
       try:    
         if fn == '':   
            self.xData.to_csv( self.csvFileName, index=False, sep=fs, quoting=csv.QUOTE_NONNUMERIC )
         else:
            self.xData.to_csv( fn, index=False, sep=fs, quoting=csv.QUOTE_NONNUMERIC )

         return(True)   
       except Exception as scsvEx:
            print('\t[DEBUG] Error saving csv file.', str(scsvEx) )
            return(False)
      
