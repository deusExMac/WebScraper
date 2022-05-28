

from dataclasses import dataclass, field
from typing import List
import dataconf 

import re
import requests_html



@dataclass
class extractionRule:
    """Class for represeing a simple extraction rule."""
    ruleName: str = ''
    ruleDescription: str = ''
    # regular expression the URL has to match to make this rule fire
    ruleURLActivationCondition: List[str] = field(default_factory=lambda:[]) 

    # How to get/scrap the data (in regex or css selector form)
    ruleCSSSelector: str = ''
    ruleTargetAttribute: str = ''
    #ruleRegularExpression: str = ''
    # Regular expression that the extracted rule content must match
    # to be considered valid
    ruleContentCondition: str = ''
    
    ruleReturnsMore: bool  = False
    # If more than one value is returned, the next field tells us under what
    # key to store the extracted values (i.e. the text of each element)
    ruleReturnedValueNames: List[str] = field(default_factory=lambda:[])    
    ruleReturnedMatchPos: int  = 0    
    ruleReturningMoreIsError: bool  = False
    
    ruleRemoveChars: List[str] = field(default_factory=lambda:[' ', '$'])
    ruleAux1: str = ''
    ruleAux2: str = ''


     
    # Check if this rule should be activated for this url
    def ruleMatches(self, url) -> bool:
        # No condition means apply it
        if len(self.ruleURLActivationCondition) == 0:
           return(True)
            
        for regExp in self.ruleURLActivationCondition:
            if re.search( regExp, url) is not None:
               return(True)

        return(False)



    

    # TODO: Do we need this?
    def load(self, dictionary) -> int:
        self.ruleName = dictionary.get('name', '')
        self.ruleDescription = dictionary.get('decription', '')
        self.ruleRegularExpression = dictionary.get('regex', '')
        self.ruleReturnsMore = dictionary.get('more', False)
        self.ruleReturnedMatchPos = dictionary.get('matchpos', 0)
        self.ruleReturningMoreIsError = dictionary.get('reporterrors', False)
        return(0)
        


    # TODO: Complete me.
    
    def extract(self, text) -> list:
       print("[DEBUG] matching", self.ruleRegularExpression) 
       matches = re.findall(self.ruleRegularExpression, text)
       if self.ruleReturningMoreIsError and len(matches) > 1:
          raise Exception('Returned more than one matches (' + str(len(matches)) + ') while expected only one.')
        
       return(matches)


    

    def extractOne(self, text, pos = 0) -> str:
        matches = re.findall(self.ruleRegularExpression, text)
        if pos < len(matches):
           return( matches[pos] )
        else:
           return('') 


    
    # htmlContent must be html object from requests_html
    # TODO: Check this thoroughly. Also, refactor this
    def apply( self, htmlContent ) -> dict:

        exTractedData = {}
        
        res = htmlContent.find(self.ruleCSSSelector, first=False)
        if self.ruleTargetAttribute == "text":
           if not self.ruleReturnsMore: 
              if self.ruleContentCondition != '': 
                   res = [m for m in res if re.search(self.ruleContentCondition, m) is not None ]
              if len(res) <= 0:
                 print("\t\t[DEBUG] Empty. No match present")
                 exTractedData[self.ruleName] = ''
                 return(exTractedData)
              else:    
                 xVal = res[self.ruleReturnedMatchPos].text

                 # Replace characters
                 for c in self.ruleRemoveChars:
                     xVal = xVal.replace(c, '')
                     
                 exTractedData[self.ruleName] = xVal
                 return(exTractedData)

           else:
              if self.ruleContentCondition != '': 
                 res = [m for m in res if re.search(self.ruleContentCondition, m.text) is not None ]

              # TODO: Here, remove specified characters
              # something like this:
              #for i in range(len(res)):
              #     for c in self.ruleRemoveChars:                    
	      #         res[i] = res[i].replace(c, '')
	      # OR BETTER, USE maketrans!
	
              for e, name in zip(res, self.ruleReturnedValueNames):
                  exTractedData[name] = e.text

              return(exTractedData)
            
        else:
            
         numExtracted = 0   
         if self.ruleContentCondition != '': 
            res = [m for m in res if re.search(self.ruleContentCondition, m.attrs.get(self.ruleTargetAttribute)) is not None ]
                         
         if self.ruleReturnedMatchPos >= 0:
            print('>>>>> Got  [', res[self.ruleReturnedMatchPos].attrs.get(self.ruleTargetAttribute), ']', sep='' )
            exTractedData[self.ruleName] = res[self.ruleReturnedMatchPos].attrs.get(self.ruleTargetAttribute)
            numExtracted += 1
         else:
            print(len(res), ' matches found')
            lst = []
            for item in res:
                lst.append( item.text )

            exTractedData[self.ruleName] = lst    
            numExtracted += len(res)

         return(exTractedData)    







@dataclass
class ruleLibrary:
      libraryDescription: str = ''
      library: List[extractionRule] = field(default_factory=lambda:[])

      def get(self, ruleName) -> extractionRule:
          for r in self.library:
              if r.ruleName == ruleName:
                 return( r )

          return(None)      

      def numberOfRules(self):
          return( len(self.library) )

      def getPos(self, pos) -> extractionRule:
          if pos >= self.numberOfRules:
             return(None)
          else:
              return( self.library[pos] )




# Test!
def loadRule( r ):    
    rl = dataconf.loads(r, extractionRule)
    return(rl)

def loadLibrary(r):
    return( dataconf.loads(r, ruleLibrary) )
