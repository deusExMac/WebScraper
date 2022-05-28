# WebScraper
 
A simple python program for scraping speficied data from web pages. Specifications for scraped data is stored in .exr files.



# exr files

exr files are files in json format specifying what data to extract, on which pages and how to return them.

```
{
"libraryDescription": "Default rule library. Library to extract data from econ.upatras.gr pages",
"library": [

{
 "ruleName": "efficiencyPerDay"
 "ruleDescription": "A simple example of a rule"
 "ruleURLActivationCondition": ["/miners/"]
 
 "ruleCSSSelector": "div.rentabilitylabel > span:not(.hidden-xs)"
 "ruleTargetAttribute": "text"
 "ruleContentCondition": ""
 "ruleReturnsMore": False
 "ruleReturnedMatchPos": 0
 "ruleReturningMoreIsError": False
 "ruleRemoveChars": ["$"]
},

{
 "ruleName": "costPerDay"
 "ruleDescription": "2nd rule"
 "ruleURLActivationCondition": []
 "ruleCSSSelector": "div.rentabilitylabel > span:not(.hidden-xs)"
 "ruleTargetAttribute": "text"
 "ruleContentCondition": ""
 "ruleReturnsMore": False
 "ruleReturnedMatchPos": 0
 "ruleReturningMoreIsError": False
 
 # other parameters needed
}

]
}



```



# Related projects

To make life easier, you may use the following extensions to extract the relevant css selectors that are required in .ecr files:

* Chrome extension SelectorGadget to specify CSS seslectors used in .exr files. See: https://chrome.google.com/webstore/detail/selectorgadget/mhjhnkcfbdhnjickkkdbjoemdmbfginb?hl=en and   https://selectorgadget.com/   

* Firefox extension ScrapeMate. See https://addons.mozilla.org/en-US/firefox/addon/scrapemate/
