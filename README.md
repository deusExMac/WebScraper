# WebScraper
 
A simple python program for scraping/extracting data from web pages. Specifications for how to extract data from individual web-pages is stored in .exr files. Each .exr file contains one or more extraction rules, collectively called a library, that are applied to a single web-page. .exr files are in json format. More information on how to author .exr files can be found below.


# Required python modules

Make sure you have the following python packages installed before running the application:

* dataconf (https://pypi.org/project/dataconf/)

* requests_html (https://requests.readthedocs.io/projects/requests-html/en/latest/)




# Specifying what data to extract using .exr files

.exr files are files in json format specifying what data to extract, what consditions the extracted data must meet, from which pages to extract the data and how to return them. These conditions 

Authoring .exr files requires basic knowledge of [css selectors] (https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors) and [regular expressions](https://www.regular-expressions.info/).

## Example .exr file

TODO: library extraction files have been  updated with new properties. Make changes here!

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
