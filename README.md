# Earnings Calls Transcript Scraper

This repository contains a Python file with a script with functions used to search for transcripts of earnings calls given the ticker symbol for a company's stock. Using a combination of the `selenium` and `beautifulSoup` library, a automatic webdriver searches for the links for each transcript from the Motley Fool website, and then stores all the responses from the earnings call in a list of strings.

There are three functions in this script. The first searches for the transcripts' links, the second filters the responses from the page's content given a bs4 tag object, and the third uses the first two to create a dictionary with dates, links and contents for each ticker symbol. 

> This code is not necessarily optmized, there is still a lot of space for improvements. Sometimes, there are different offer pop-ups that show up, so it needs constant updates.
