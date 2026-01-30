import re
from lumpy_log.list1 import list1

class ChangeLump(object):
    def __init__(self, lang, lines, start=None, end=None, func=None, verbose=False):
        self.verbose = False and verbose
        self.lang = lang
        self.lines = list1(lines)
        self.commentStart = None
        self.multiLineStart = None
        self.multiLine = False
        self.source = None

        if len(lines) == 0:
            self.start = None
            self.end = None
            return
        
        if (start is not None and end is not None and (start < 1 or end > len(lines))):
            self.start = None
            self.end = None
            return
        

        if func is not None:
            self.source = "Function" 
            self.func = func
            # func line numbers are 1-indexed, store them directly
            self.start = func["start_line"]
            self.end = func["end_line"]
        else:
            if(start is None):
                self.start = 1  # 1-indexed: first line
            else:
                self.source = "Line Changed" 
                self.start = start
                
            if(end is None):
                self.end = self.start
            else:
                self.end = max(self.start, end)

        # Clamp to valid 1-indexed range [1, len(lines)]
        if self.start is not None:
            self.start = max(1, min(self.start, len(self.lines)))
        if self.end is not None:
            self.end = max(1, min(self.end, len(self.lines)))

        if self.verbose:
            print("ChangeLump", "self.start", self.start, "self.end", self.end, "len(self.lines)", len(self.lines))
        
    def extendOverText(self):
        j = self.start - 1  # Go to previous line (in 1-indexed terms)
        try:
            while( j >= 1 and len(self.lines[j].strip())):
                self.start = j
                j -= 1
        except Exception as e:
            print("extendOverText", type(e), e, "j", j, "len(self.lines)", len(self.lines))
        
        k = self.end + 1  # Go to next line (in 1-indexed terms)
        while( k <= len(self.lines) and len(self.lines[k].strip())):
            self.end = k
            k += 1
        
        if self.verbose:
            print("extendOverText", "self.start", self.start, "j", j, "self.end", self.end, "k", k, "len(self.lines)", len(self.lines))
        
        
    def inLump(self, i):
        """Check if 1-indexed line i is within the lump bounds."""
        inLump = (self.start is not None and self.end is not None and self.start <= i and i <= self.end)
    
        if self.verbose:
            print("inLump", "self.start", self.start,"i", i, "inLump",inLump)
        return inLump
        
    def extendOverComments(self):
        if self.verbose:
            print("extendOverComments", "self.start", self.start)
        j = self.start - 1  # Go to previous line (in 1-indexed terms)
        while(j >= 1 and self.lineIsComment(j)):
            j -= 1
            self.commentStart = j + 1  # Store as 1-indexed
            
            
    @property
    def code(self):    
        if self.start is None or self.end is None:
            return ""
        
        start = self.start 
        if(self.commentStart is not None):
            start = self.commentStart     

        #code = ""self.source+"\n"+
        # Use 1-indexed slicing with list1: [start:end+1] includes lines from start to end inclusive
        code = ("\n".join(self.lines[start:self.end+1]))
        if self.verbose:
            print("code", code)
        return code
    
    def lineIsComment(self, i):
        blineIsComment = self._lineIsComment(i)
        if self.verbose:
            print("lineIsComment", blineIsComment, self.lines[i])
        return blineIsComment

    # Abstracts out lineIsComment so we can  print the results
    def _lineIsComment(self, i):
        line = self.lines[i]
        if(self.verbose):
            print(self.lang.name, "self.lang.comment_structure",self.lang.comment_structure)
        comment_structure = self.lang.comment_structure

        begin = comment_structure.get("begin")
        end = comment_structure.get("end")
        single = comment_structure.get("single")

        # Multiline comments: treat lines with both begin and end as comment,
        # and any line inside unmatched begin/end pairs as comment.
        if begin:
            try:
                beginmatches = re.findall(begin, line)
                endmatches = re.findall(end, line)

                # If both markers appear on the same line, it's a comment line.
                if len(beginmatches) and len(endmatches):
                    return True
                
                # If this line is inside an open multiline comment, it's a comment.
                if self._in_multiline_comment(i, begin, end):
                    return True
            except Exception as Err:
                print(type(Err), Err)
                print(self.lang.comment_family, comment_structure)

        # Single-line comments
        if single:
            try:
                if re.search(single, line.strip()):
                    return True
            except Exception as Err:
                print("Single", type(Err), Err)
                print(self.lang.comment_family, comment_structure["single"])

        return False

    def _in_multiline_comment(self, i, begin_re, end_re):
        """Return True if line i is inside an unmatched multiline comment block."""
        try:
            # Check if begin and end delimiters are the same (symmetric like """)
            # Strip common regex anchors to compare the actual delimiter strings
            begin_stripped = begin_re.strip('^$\\s')
            end_stripped = end_re.strip('^$\\s')
            symmetric = (begin_stripped == end_stripped)
            
            in_comment = False
            for idx in range(0, i + 1):
                s = self.lines[idx]
                
                if symmetric:
                    # For symmetric delimiters (like """ in Python), each occurrence
                    # toggles the comment state: first one opens, second one closes, etc.
                    # Example: """comment""" means we enter on first """, exit on second
                    matches = re.findall(begin_re, s)
                    for _ in matches:
                        in_comment = not in_comment  # Flip True->False or False->True
                else:
                    # For asymmetric delimiters, track depth
                    begins = len(re.findall(begin_re, s))
                    ends = len(re.findall(end_re, s))
                    
                    # Process begins first, then ends
                    if not in_comment and begins > 0:
                        in_comment = True
                    if in_comment and ends > 0:
                        in_comment = False
                    
            
            return in_comment
        except Exception as Err:
            if self.verbose:
                print("_in_multiline_comment error", type(Err), Err)
            return False

