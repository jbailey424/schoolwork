Here is the code and finished dataset for the web scraping task of our Network Science group project. To initialize the scraping, simply run datamaker.py. This script uses a collection of functions, some created by myself (Jeff Bailey) and some provided by our professor, to initialize or add to a .jsonl dataset of directors and their credited crew. There are three modifiable parameters to this script, which at this time can be modified by altering the code manually. These are: 
1. your director data, which currently comes from the provided 100_film_directors.csv. 
2. your dataset file name, currently new_credits.jsonl
3. a list of valid roles to record credits from, currenly set to the list ['direct', 'writ', 'produce', 'cinematography', 'casting by', 'editing', 'music by']

The script loads the csv into a pandas df and then, for each director listed in the dataframe, checks the jsonl if the director is already recorded and if not it runs scraping functions to record every crew member credited with a role in the valid list for each of the director's feature film credits. 
