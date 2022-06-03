# WebScraper
 
A simple python program for scraping/extracting data from web pages. Specifications for how to extract data from individual web-pages is stored in .exr files. Each .exr file contains one or more extraction rules, collectively called a library, that are applied to a single web-page. .exr files are in json format. More information on how to author .exr files can be found below.


# Required python modules

Make sure you have the following python packages installed before running the application:

* dataconf (https://pypi.org/project/dataconf/)

* requests_html (https://requests.readthedocs.io/projects/requests-html/en/latest/)




# Specifying what data to extract using .exr files

.exr files are files in json format specifying what data to extract, what consditions the extracted data must meet, from which pages to extract the data and how to return them. Such specfications are referred to as 'extraction rules' and the the extraction rules inside the same .exr file is called a library. .exr files contain one or more rules. All rules inside the .exr files are applied to each individual page.

During startup the preferred .exr file can be specified. The specified .exr file and all the rules it contains are applied to each individual page that the application downloads.  

Authoring .exr files requires basic knowledge of [css selectors] (https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors) and [regular expressions](https://www.regular-expressions.info/).

## Example .exr file

.exr files, when applied to content (web-page) downloaded from the WWW, attempt to express the following conditions and actions:

*"For each rule inside the .exr file, do the following: If the web-page URL matches the conditions, check if the web-page's content matches zero or more preconditions. If all these conditions hold, extract the data from the web-page specified by a CSS selector. Check if the extracted data meets a contition. If so, return it as the scraped value. If not, return empty extracted data."*   


TODO: library extraction files have been  updated with new properties. Make changes here!
Below is an example of a .exr file that is used to extract data related to football teams from wikipedia pages. It contains 4 rules that will be applied to all wikipedia pages downloaded.

```
#
# json format of 
# 
# version 0.01@18/05/2022
#
#


{
"libraryDescription": "Library to extract data from english wikipedia pages",
"csvLineFormat": ["teamFullName", "clubPresident"],

"library": [

{
 "ruleName": "teamFullName"
 "ruleDescription": "Get full name of clubs from infoboxes"
 "ruleURLActivationCondition": ["en\.wikipedia\.org"]
 
 "rulePreconditionType": "Any"
 "rulePreconditions" : [ 
                            {
                              "ecCSSSelector" : "tr:nth-child(2) .infobox-label" 
                              "ecTextCondition" : "Full name"
                              "ecRuleCSSSelector" : ""
                            }                       
                       ]
 "ruleCSSSelector": "tr:nth-child(2) .infobox-data"
 "ruleTargetAttribute": "text"
 "ruleContentCondition": ""
 "ruleReturnsMore": False
 "ruleReturnedMatchPos": 0
 "ruleReturningMoreIsError": False
 "ruleRemoveChars": []
},

{
 "ruleName": "articleTitle"
 "ruleDescription": "2nd rule"
 "ruleURLActivationCondition": ["en\.wikipedia\.org/wiki"]
 "rulePreconditionType": "Any"
 "rulePreconditions" :  [ 
                             {
                               "ecCSSSelector" : "tr:nth-child(2) .infobox-label" 
                               "ecTextCondition" : "Full name"
                             },
                             {
			        "ecCSSSelector" : "tr:nth-child(3) .infobox-label" 
			        "ecTextCondition" : "Full name"
                             }
                          ]
                       
 "ruleCSSSelector": "#content h1.firstHeading"
 "ruleTargetAttribute": "text"
 "ruleContentCondition": ""
 "ruleReturnsMore": False
 "ruleReturnedMatchPos": 0
 "ruleReturningMoreIsError": False
 "ruleRemoveChars": []
},


{
 "ruleName": "clubPresident"
 "ruleDescription": "Get football club president from infobox"
 "ruleURLActivationCondition": ["en\.wikipedia\.org/wiki"]
 "rulePreconditionType": "Any"
 "rulePreconditions" :   [ 
                             {
			      "ecCSSSelector" : "tr:nth-child(5) .infobox-label" 
			      "ecTextCondition": "President"
			      "ecRuleCSSSelector" : "tr:nth-child(5) .agent"			      			      
                             },
                             
                             {
			      "ecCSSSelector" : "tr:nth-child(6) .infobox-label" 
			      "ecTextCondition": "President"
			      "ecRuleCSSSelector" : "tr:nth-child(6) .agent"			      			      
                             },
                             
                             {
			      "ecCSSSelector" : "tr:nth-child(7) .infobox-label" 
			      "ecTextCondition": "President"
			      "ecRuleCSSSelector" : "tr:nth-child(7) .agent"			      			      
                             },
                             
                             {
                               "ecCSSSelector" : "tr:nth-child(8) .infobox-label" 
                               "ecTextCondition": "President"
                               "ecRuleCSSSelector" : "tr:nth-child(8) .agent"
                             },
                             
                             {
			       "ecCSSSelector" : "tr:nth-child(9) .infobox-label" 
			       "ecTextCondition": "President"
			       "ecRuleCSSSelector" : "tr:nth-child(9) .agent"
                             },
                             
                             {
			       "ecCSSSelector" : "tr:nth-child(8) .infobox-label" 
			       "ecTextCondition": "Chairman"
			       "ecRuleCSSSelector" : "tr:nth-child(8) .agent"
                             },
                             
                             {
			     	"ecCSSSelector" : "style+ .vcard tr:nth-child(9) .infobox-label" 
			     	"ecTextCondition": "Chairman"
			     	"ecRuleCSSSelector" : "tr:nth-child(9) .agent"
                             }
                             
                             
                             
                          ]                       
 "ruleCSSSelector": "#content h1.firstHeading"
 "ruleTargetAttribute": "text"
 "ruleContentCondition": ""
 "ruleReturnsMore": False
 "ruleReturnedMatchPos": 0
 "ruleReturningMoreIsError": False
 "ruleRemoveChars": ["\n", "\t"]
},




{
 "ruleName": "getLinks"
 "ruleDescription": "Extracting links rule"
 "ruleURLActivationCondition": ["en\.wikipedia\.org.*$"]
 
 "rulePreconditionType": "Any"
 "rulePreconditions" : []
 
 "ruleCSSSelector": "a[href]"
 "ruleTargetAttribute": "href"
 "ruleContentCondition": "en\.wikipedia\.org/.*$"
 "ruleReturnsMore": True
 "ruleReturnedMatchPos": -1
 "ruleReturningMoreIsError": False
 
 # other parameters needed
}

]


}

```

## Structure of rules in .exr file

-``[libraryDescription]``: A human readable description of the .exr file. What it is used for etc.

-``[library]``: list of rules defining this library.

Rule attributes/properties:

- ``[ruleName]``: String. Name of the rule. In the current version, rule names should not contain spaces. Rule names are important as these names are used to store extracted values, by that rule, with these keys in python dictionaries.
- ``[ruleDescription]``: String. A human readable description of the rule's aim i.e. what it does. 
- ``[ruleURLActivationCondition]``: List of regular expressions.  List of regular expression that the URL of the web page must match. Rule is applied if ANY of the regular expressions in this list is matched. If no regular expression is matched, rule if not applied. If this list is empty, rule is applied. Example: ruleURLActivationCondition: ["en\.wikipedia\.org", "C://downloadedPages//"] meaning if URL matches en.wikipedia.org or C://downloadedPages//, then apply this rule. If URL (or file name) does not match any of regular expressions in this list rule will not applied. NOTE . is escaped as 



# Related projects

To make life easier, you may use the following extensions to extract the relevant css selectors that are required in .ecr files:

* Chrome extension SelectorGadget to specify CSS seslectors used in .exr files. See: https://chrome.google.com/webstore/detail/selectorgadget/mhjhnkcfbdhnjickkkdbjoemdmbfginb?hl=en and   https://selectorgadget.com/   

* Firefox extension ScrapeMate. See https://addons.mozilla.org/en-US/firefox/addon/scrapemate/
