# WebScraper
 
A simple python program for scraping speficied data from web pages. Specifications for scraped data is stored in .exr files.



# Specifying what data to extract using .exr files

.exr files are files in json format specifying what data to extract, what consditions the extracted data must meet, from which pages to extract the data and how to return them. 

Authoring .exr files requires basic knowledge of [css selectors] (https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors) and [regular expressions](https://www.regular-expressions.info/).

## Example .exr file

TODO: library extraction files have been  updated with new properties.

```
{
"libraryDescription": "Default rule library. Library to extract data from econ.upatras.gr pages",
"library": [

{
 "ruleName": "efficiencyPerDay"
 "ruleDescription": "A simple example of a rule"
 "ruleURLActivationCondition": ["econ.upatras.gr"]
 "ruleCSSSelector": "div.rentabilitylabel > span:not(.hidden-xs)"
 "ruleTargetAttribute": "text"
 "ruleContentCondition": ""
 "ruleReturnsMore": False
 "ruleReturnedValueNames": []
 "ruleReturnedMatchPos": 0
 "ruleReturningMoreIsError": False
 "ruleRemoveChars": ["$"]
 "ruleAux1": ''
 "ruleAux2": ''
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
}

]
}



```



# Related projects

To make life easier, you may use the following extensions to extract the relevant css selectors that are required in .ecr files:

* Chrome extension SelectorGadget to specify CSS seslectors used in .exr files. See: https://chrome.google.com/webstore/detail/selectorgadget/mhjhnkcfbdhnjickkkdbjoemdmbfginb?hl=en and   https://selectorgadget.com/   

* Firefox extension ScrapeMate. See https://addons.mozilla.org/en-US/firefox/addon/scrapemate/
