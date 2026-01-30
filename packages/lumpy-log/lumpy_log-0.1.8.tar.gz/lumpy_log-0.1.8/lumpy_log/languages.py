#!/usr/bin/python3
import yaml

class Languages(object):
    def __init__(self, LANGUAGES_PATH = "languages.yml"):
        self.LANGUAGES_PATH = LANGUAGES_PATH
        with open(self.LANGUAGES_PATH, 'r') as file:
            #self.LANGUAGES = [Language(sLang, oLang) for sLang, oLang in yaml.safe_load(file).items()]
            self.LANGUAGES = yaml.safe_load(file)

    # TODO : Cache the fetched language objects

    @property
    def list(self):
        return self.LANGUAGES.keys()

    @property
    def all(self):
        return [self.getLanguage(Lang) for Lang in self.LANGUAGES.keys() if Lang is not None] 
        
    def getByExtension(self, ext):
        Lang = self._getByExtension(ext)
        if(Lang is None):
            return Language(ext[1:],{"type":"data"})
        return self.getLanguage(Lang)

    def getLanguage(self, Lang):
        if Lang in  self.LANGUAGES:
            newLang = Language(Lang, self.LANGUAGES[Lang])
            if(newLang.lexer_name):
                newLang.lexer = self.getLanguage(newLang.lexer_name)
            
            if(newLang.group_name):
                newLang.group = self.getLanguage(newLang.group_name)

            if(newLang.comment_family != newLang.name):
                newLang.comment_lang = self.getLanguage(newLang.comment_family)

            return newLang
        return None

    def _getByExtension(self, ext):
        primary = [Lang for Lang in self.LANGUAGES if self.LANGUAGES[Lang]['primary_extension'] == ext] 
        
        if (len(primary)):
            return primary[0]#
            
        secondary = [Lang for Lang in self.LANGUAGES if 'extensions' in self.LANGUAGES[Lang] and ext in self.LANGUAGES[Lang]['extensions']] 
        
        if (len(secondary)):
            return secondary[0]#['lang'].lower()
        
        return None

class Language(object):
    name = str
    oLang = object
    group = None
    lexer = None
    comment_lang = None
    _comment_structure = None

    def __init__(self, sLang, oLang):
        self.name = sLang
        self.oLang = oLang
        
    
    @property
    def lexer_name(self):
        if("lexer" in self.oLang and self.oLang["lexer"] and self.oLang["lexer"] != self.name):
            return self.oLang["lexer"]
        return None

    @property
    def group_name(self):
        if("group" in self.oLang and self.oLang["group"] and self.oLang["group"] != self.name):
            return self.oLang["group"]
        return None

    @property
    def mdname(self):
        if "ace_mode" in self.oLang and self.oLang["ace_mode"]:
            return self.oLang["ace_mode"]
        return self.name.lower()
        
    @property
    def comment_family(self):
        #comment: C,  lexer: ActionScript 3, group: Shell
        commentType =  self.name
        
        if("comment_type" in self.oLang and self.oLang["comment_type"]):
            commentType = self.oLang["comment_type"]
        elif(self.lexer):
            commentType = self.lexer.comment_family
        elif(self.group):
            commentType = self.group.comment_family
        return commentType
    
    @property
    def comment_structure(self):
        #if self._comment_structure :
        #    return self._comment_structure
        if "comments" in self.oLang and self.oLang["comments"]:
            comments = self.oLang["comments"]
            #self._comment_structure = {
            #    "single": comments["single"],
            #    "begin": comments["begin"].split(",") if comments["begin"] else None,
            #    "end": comments["end"].split(",") if comments["end"] else None
            #}
            
            #return self._comment_structure
            return comments

        if self.comment_lang is not None:
            return self.comment_lang.comment_structure
        
        return None
      
if __name__ == "__main__":
    languages = Languages()
    
    comments = list(set([ lang.comment_family for lang in languages.all if lang.comment_structure]))
    #comment_searches.sort()
    print( comments)
    for langname in comments:
        print(langname, languages.getLanguage(langname).comment_structure)
