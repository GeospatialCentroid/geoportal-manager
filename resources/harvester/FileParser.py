"""
The super class FileParser looks through the loaded data and extracts the relevant information
Helper function are included to assist with automatically populating certain fields

"""

from html.parser import HTMLParser
import re
from datetime import datetime
import csv


class FileParser:
    def __init__(self,props):
        for p in props:
            setattr(self,p, props[p])

        # make sure the year is reasonable - get the current for comparison
        self.curr_year = datetime.today().year


        print("A file parser is born")

    def get_categories(self, r):


        """

        :param r:
        :return:
        """
        if 'categories' in r:
            categories = r["categories"] # most likely an empty list
        else:
            categories=[]
        text = r['description']
        # append the keywords

        if 'tags' in r:
            text += ', '.join(r['tags'])

        if 'title' in r:
            text += ' '+r["title"]

        text = text.lower()

        match={}

        print(" looking for categories-------------",text)
        if len(categories)==0 and text is not None:

            # look through the description and pull out and matches
            # we want to know what keywords are selected from each to assist with improving the keywords being used
            for c in self.categories:
                for k in c.category_keywords_set.all():
                    if k.name in text:
                        if c.name not in match:
                            match[c.name]=[]
                        match[c.name].append(k.name)

            print("match",match)
            r['match'] = match
            # choose the category with the highest number
            count=0
            for m in match:
                new_count = len(match[m])
                if new_count>count:
                    categories=[m]
                    count=new_count

        return categories

    def get_year(self, r):
        """

        :param r:
        :return:
        """
        # -- get the year --
        text = r['description']

        year = ""

        if text is not None:
            # try to get the year from the description
            regex = "\d{4}"
            match = re.findall(regex, text)

            if len(match) > 0:
                for m in match:
                    if int(m) <= self.curr_year and int(m) > 1500:
                        # loop through look for a reasonable year
                        solrYear = m
            # if still not set - take the year from the modified date
        if year == "" and "modified" in r:
            if isinstance(r["modified"], str):
                year = self.get_utc_from_unix(r["modified"])[:4]

        return year


    def get_utc_from_unix(self,ts):
        """

        :param ts:
        :return:
        """
        print("get_utc_from_unix",ts)
        if isinstance(ts, int):
            # if the string is only 8 characters it's likely in the yyyymmdd format
            if len(str(ts))==8:
                return ts
            return datetime.utcfromtimestamp(ts/1000).strftime('%Y%m%d')
        elif isinstance(ts, str):
            return datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y%m%d')

    def get_results(self,report):
        """

        :param report:
        :return:
        """
        with open(report, 'w', newline='', encoding='utf-8') as outfile:
            csvout = csv.writer(outfile)
            csvout.writerow(self.cols)
            for r in self.rows:
                all_values=[]
                for v in self.vals:
                    if v != "" and v in r:
                        all_values.append(r[v])
                    else:
                        all_values.append("")
                csvout.writerow(all_values)

    def get_places(self,r):
        '''
        Look through the places file and see if there are any matches with the tags lists
        todo - make this more robust
        :param r:
        :return:
        '''
        places=[]
        tags =[]
        if 'tags' in r:
            tags=r['tags']
            print('tags',tags)
        for t in tags:
            # look for a match
            for p in self.places:
                if t.lower() == p.name.lower() or t.lower() == p.name_lsad.lower():
                    val = p.name.lower()+"|"+p.name_lsad
                    if val not in places and t.lower() not in ["trail","basin","wells","hydro","forest"]:
                        # so that we can map to the same place - use both the name and lsad
                        places.append(val)

        return places

# https://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    if html is None:
        return ""
    s = MLStripper()
    s.feed(html)
    d = s.get_data()
    d = re.sub(r'[\n]+|[\r\n]+', ' ', d, flags=re.S)
    d = re.sub(r'\s{2,}', ' ', d)
    d = d.replace(u"\u2019", "'").replace(u"\u201c", "\"").replace(u"\u201d", "\"").replace(
        u"\u00a0", "").replace(u"\u00b7", "").replace(u"\u2022", "").replace(u"\u2013", "-").replace(u"\u200b", "")
    return d