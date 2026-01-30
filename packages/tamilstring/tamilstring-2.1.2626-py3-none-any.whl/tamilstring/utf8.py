from .constant import SA_ROOT_LETTERS, TA_ROOT_CONSONENT, TAMIL_NUMURALS, TAMIL_SYMBOLS, TAMIL_VOWEL_CHARS, sanskrit_vowel_letters,tamil_consonent_letters, tamil_vowel_unicode_symbols,sanskrit_vowel_letters
import re


suffics = "ாிீுூெேைொோௌ"
vowel = "அஆஇஈஉஊஎஏஐஒஓஔ"
charector = "௦௧௨௩௪௫௬௭௮௯௰௱௲௳௴௵௶௷௹௺"
prefixs = "கஙசஞடணதநபமயரலவழளறனஶஜஷஸஹ"
clusters = "க்ஷ|ஶ்ர|ஸ்ர"
english = "\x00-\x7F"

def remove_non_ta_en(string):
    """
    it helps to remove any unicode other then english and tamil unicodes
    Args:
        string(str): you want app this function
    Return:
        string(str): removed unicode string
    eg:
    string1 = remove_non_ta_en("தைைமிாாழ்்ひらがな"))
    print(string1)
    "தைைமிாாழ்்"
    string2 = remove_non_ta_en("Hanzi汉字/漢字"))
    print(string2)
    "Hanzi/"
    string3 = remove_non_ta_en("Hindiहिन्दी"))
    print(string3)
    "Hindi"
    string4 = remove_non_ta_en("Tamilالتاميل")) 
    print(string4)
    "Tamil"
    string5 = remove_non_ta_en("Tamil,English")) 
    print(string5)
    "Tamil,English"
    string6 = remove_non_ta_en("تاميلی")) 
    print(string6)
    ""
    """
    return ''.join(re.findall(r'[\x00-\x7F\u0B80-\u0BFF]', string))

def get_letters(string,skip_en=False,only=None):
    """
    it helps to extract letters from the string
    Args:
        string(str): you want get letter from a perticular string
        skip_en(bool): you can skip extracting english letter, it helps if a string that contains tamil string only
        only(list): this helps you to extract only a specific kinf of letters
    Return:
        list
    eg:
    string1 = get_letters("தமிழ்")
    print(string1)
    ['த','மி','ழ்']
    string1 = get_letters("ஶ்ரீனி")
    print(string1)
    ['ஶ்ரீ','னி']
    string1 = get_letters("தமிழ் பலரின் தாய்மொழி ஆகும்")
    print(string1)
    ['த', 'மி', 'ழ்', ' ', 'ப', 'ல', 'ரி', 'ன்', ' ', 'தா', 'ய்', 'மொ', 'ழி', ' ', 'ஆ', 'கு', 'ம்']
    string1 = get_letters("செம்மொழி (Classical language)")
    print(string1)
    ['செ', 'ம்', 'மொ', 'ழி', ' ', '(', 'C', 'l', 'a', 's', 's', 'i', 'c', 'a', 'l', ' ', 'l', 'a', 'n', 'g', 'u', 'a', 'g', 'e', ')']
    string1 = get_letters("English")
    print(string1)
    ['E','n','g','l','i','s','h']
    # for sanskrit letters
    string1 = get_letters("ஜாபர்")
    print(string1)
    ['ஜா','ப','ர்']
    # skip en
    string1 = get_letters("செம்மொழி (Classical language)",skip_en=True)
    print(string1)
    ['செ', 'ம்', 'மொ', 'ழி']
    """
    if only != None:
        PATTERN = regex_generator(only)
    elif skip_en:
        PATTERN = rf"(?:(?:{clusters})[{suffics}்]?|[{prefixs}][{suffics}்]?|[{vowel}{charector}ஃ])"
    else:
        PATTERN = rf"(?:(?:{clusters})[{suffics}்]?|[{prefixs}][{suffics}்]?|[{vowel}{charector}ஃ{english}])"
    
    return re.findall(PATTERN, string)

def unmatch_indeces(string,skip_en=False):
    """
    it retruns the unmatched letters indeces of the string, particularly it hepls to resolve the OCR texts
    Args:
        string(str): you want to find the unmatched indeces
    Return:
        list(list):where the unmatched indexes 
    eg:
    list1 = unmatch_indeces("தைைமிாாழ்்"))
    print(list1)
    [[2, 3], [5, 7], [9, 10]]
    list2 = unmatch_indeces("தைைமிாாழ்்"))
    print(list2)
    [[2, 5], [7, 9], [11, 12]]
    list3 = unmatch_indeces("தைைமிாாழ்்1#w)")
    print(list3)
    [[2, 3], [5, 7], [9, 14]]
    """
    PATTERN = "([{0}](?:[{1}்](?:[ஷர](?:[{1}்])?)?)?|[{2}{3}ஃ])".format(prefixs,suffics,vowel,charector)
    
    #REMOVE_NON_TAMIL = r"[\u0B80-\u0BFF]"
    
    PATTERN = f"[^\x00-\x7F]{PATTERN}" if skip_en == True else PATTERN 
     
    index_position, matches, unmatches = 0,[],[]
    for match in re.finditer(PATTERN, string):
        start, end = match.start(), match.end()
        if index_position < start: 
            unmatches.append([index_position,start])
        matches.append(string[start:end])
        index_position = end
    if index_position < len(string): 
        unmatches.append([index_position,len(string)])
    return unmatches
 
def unmatched_unicode(string,skip_en=False):
    """
    it retruns the unmatched unicode for getting letters of the given string, particularly it hepls to resolve the OCR texts
    Args:
        string(str): you want to find the unmatched unicode
    Return:
        list(list):where the unmatched unicodes
    eg:
    string1 = get_letters("தமிழ்்"))
    print(strin1)
    ['த','மி','ழ்']
    string2 = get_letters("்ா")) 
    print(strin2)
    [],
    string3 = get_letters("漢字")) 
    print(strin3)
    [],
    string4 = get_letters("க்ஷி்ாக்ஷு"))
    print(strin4)
    ['க்ஷி','க்ஷு']
    """
    indeces = unmatch_indeces(string,skip_en=False)
    return [string[index] for index in indeces ]

def regex_generator(only):

    if isinstance(only,bool) and only == True:
        return "([{0}](?:[{1}்])?|[{2}{3}ஃ])".format(prefixs,suffics,vowel,charector)
    else:
        
        #\x41–\x5A => A–Z
        #\x61–\x7A => a-z
        #\x30–\x39 => 1-9
        EN_LET = "\x41-\x5A\x61-\x7A\x30-\x39" if "EN_SYM" in only else ""

        #\x21–\x2F => ! " # $ % & ' ( ) * + , - . /
        #\x3A–\x40 => : ; < = > ? @
        #\x5B–\x60 => [ \ ] \ ^ _ 
        #\x7B–\x7E => `{ }
        EN_SYM = "\x21-\x2F\x3A-\x40\x5B-\x60\x7B-\x7E" if "EN_SYM" in only else ""

        # empty space
        EN_SPC = "\x20" if "EN_SYM" in only else ""

        IN_EN = EN_LET + EN_SYM + EN_SPC
        
        if "SA_LET" in only:
            PATTERN = "([{0}](?:[{1}்](?:[ஷர](?:[{1}்])?)?)?|[{2}{3}ஃ{4}])".format(prefixs,suffics,vowel,charector,english)
        else:
            PATTERN = "([{0}](?:[{1}்])?|[{2}{3}ஃ{4}])".format(prefixs,suffics,vowel,charector,english)
        # TODO for only getting english
        return PATTERN

def split_letter(letter):
    """
    it splits the composite letters into seperate consonent and vowel letters
    Args:
        letter(str)
    Return:
        typle()
    eg:
    print(split_letter("மா"))
    ('ம்','ஆ')
    print(split_letter("கோ"))
    ('க்','ஓ')
    print(split_letter("ணை"))
    ('ண்','ஐ')
    print(split_letter("க்ஷி")) 
    ("க்ஷ்","இ")
    print(split_letter("ஶ"))
    ('ஶ்', 'அ')
    print(split_letter("க்ஷை"))
    ('க்ஷ்', 'ஐ')
    print(split_letter("௵"))
    (None,None)
    print(split_letter("ழ்"))
    (None,None)
    print(split_letter("ஃ"))
    (None,None)
    """
    if is_composite(letter):
        for vowel_let, vowel_sym in zip(vowel[1:],suffics):
            if letter[-1] == vowel_sym:
                return (letter[:-1]+'்', vowel_let)
        else:
            return (letter+'்', "அ")
    else:
        return (None,None) 
    

def make_letter(letter1,letter2):
    """
    join consonent with vowel and return a sinle letter
    Args:
        letter1(str): 
        letter2(str): 
    Return:
        letter(str)
    eg:
    print(make_letter("ழ்","ஔ"))
    'ழௌ'
    print(make_letter("ப்","ஊ"))
    'பூ'
    print(make_letter("க்","ஐ"))
    'கை'
    print(make_letter("ம்","ஊ"))
    'மூ'
    print(make_letter("ச்","ஆ"))
    'சா'
    print(make_letter("ப்ப","ப்"))
    None
    print(make_letter("ச","ஆ"))
    None
    print(make_letter("ப்","ப"))
    None
    print(make_letter("ப்","ப்"))
    None
    """
    if is_vowel(letter1) and is_consonent(letter2):
        constant_ = letter2
        vowel_ = letter1
        for vowel_let, vowel_sym in zip(vowel[1:],suffics):
            if vowel_ == vowel_let:
                return constant_[:-1] + vowel_sym
        else:
            return constant_
    elif is_vowel(letter2) and is_consonent(letter1):
        constant_ = letter1
        vowel_ = letter2
        for vowel_let, vowel_sym in zip(vowel[1:],suffics):
            if vowel_ == vowel_let:
                return constant_[:-1] + vowel_sym
        else:
            return constant_[:-1] 
    else:
        # TODO rasie error
        return None


def is_vowel(unicodes):
    """
    it checks given letter is vowel or not?
    Args:
        letter(str): 
    Return:
        letter(str):
    eg:
    print(is_vowel("அ"))
    True
    print(is_vowel("ஔ"))
    True
    print(is_vowel("ஓ"))
    True
    print(is_vowel("இ"))
    True
    print(is_vowel("a"))
    False
    print(is_vowel("க்ஷ்"))
    False
    print(is_vowel("௩"))
    False
    print(is_vowel("௫"))
    False
    """
    letter = verify(unicodes)
    if letter: 
        if unicodes in vowel:
            return True
        else:
            return False


def is_consonent(unicodes):
    """
    it checks given letter is consonent or not?
    Args:
        letter(str): 
    Return:
        letter(str):
    eg:
    print(is_consonent("க்"))
    True
    print(is_consonent("ழ்"))
    True
    print(is_consonent("க்ஷ்"))
    True
    print(is_consonent("ஞ்"))
    True
    print(is_consonent("a"))
    False
    print(is_consonent("ஷி"))
    False
    print(is_consonent("௩"))
    False
    print(is_consonent("௫")) 
    False     
    """
    letter = verify(unicodes)
    if letter: 
        if (unicodes[:-1] in prefixs or unicodes[:-1] == "க்ஷ") and unicodes[-1] == "்":
            return True
        else:
            return False


def is_composite(unicodes):
    """
    it checks given letter is composite or not?
    Args:
        letter(str): 
    Return:
        letter(str):
    eg:
    print(is_composite("க"))
    True
    print(is_composite("ழ"))
    True
    print(is_composite("க்ஷ"))
    True
    print(is_composite("க்ஷூ"))
    True
    print(is_composite("a"))
    False
    print(is_composite("ஶ்"))
    False
    print(is_composite("௩"))
    False
    print(is_composite("௫"))
    False
    """
    letter = verify(unicodes)
    if letter:
        if (unicodes[:-1] in prefixs or unicodes[:-1] == "க்ஷ") and unicodes[-1] in suffics:
            return True
        elif unicodes in prefixs or unicodes == "க்ஷ":
            return True
        else:
            return False


def verify(unicodes):
    """
    it checks the letter has length one or not
    Args:
        letter(str): 
    Return:
        letter(str):
    eg:
    print(verify("க"))
    True
    print(verify("ழ"))
    True
    print(verify("a"))
    True
    print(verify("௩"))
    True
    print(verify("௫"))
    True
    print(verify("க்ஷ"))
    True
    print(verify("க்ஷூ"))
    True
    print(verify("க்ஷ்"))
    True
    print(verify("English"))
    False
    print(verify("தமிழ்"))
    False
    print(verify("Hi"))
    False
    """
    letter_list = get_letters(unicodes)
    if len(letter_list) != 1:
        return False
    else:
        return True

def is_sa(letter):
    """
    it checks the given letter is belongs to sanskrit letters or not
    Args:
        letter(int): 
    Return:
        bool:
    eg
    print(in_tamil("a"))
    False
    print(in_tamil("B"))
    False
    print(in_tamil("3"))
    False
    print(in_tamil("?"))
    False:
    print(in_tamil("ஃ")
    False
    print(in_tamil("௹"))
    False
    print(in_tamil("க்ஷ்")
    True
    print(in_tamil("ஷி"))
    True
    print(in_tamil("ஶ்ரீ")
    True
    print(in_tamil("我"))
    False
    print(in_tamil("ക")
    False
    """
    #check_tamil = tamil_specific(letter) if tamil_specific(letter) != None else ""
    if sa_composite(letter) or sa_consonent(letter) or letter == 'ஶ்ரீ':
        return True
    else:
        return False
    
def is_ta(letter):
    """
    it checks the given letter is belongs to tamil letters or not?
    Args:
        letter(int): 
    Return:
        bool:
    eg:
    print(in_tamil("a"))
    False
    print(in_tamil("B"))
    False
    print(in_tamil("3"))
    False
    print(in_tamil("?"))
    False
    print(in_tamil("ஃ"))
    True
    print(in_tamil("௹"))
    True
    print(in_tamil("அ"))
    True
    print(in_tamil("௩"))
    True
    print(in_tamil("ப்"))
    True
    print(in_tamil("கை"))
    True
    print(in_tamil("ஃ"))
    True
    print(in_tamil("௹"))
    True
    print(in_tamil("க்ஷ்"))
    False
    print(in_tamil("ஷி"))
    False
    print(in_tamil("ஶ்ரீ"))
    False
    print(in_tamil("我"))
    False
    print(in_tamil("ക"))
    False
    """
    check_tamil = tamil_specific(letter) if tamil_specific(letter) != None else ""
    if check_tamil.startswith("TA-"):
        return True
    return False

def is_en(char):
    """
    it checks the given letter is belongs to english letters or not
        Args:ஶ்ரீ
        letter(int): 
    Return:
        bool:
    eg:
    print(in_tamil("a"))
    True
    print(in_tamil("B"))
    True
    print(in_tamil("3"))
    True
    print(in_tamil("?"))
    True
    print(in_tamil("ஃ"))
    True
    False
    print(in_tamil("௹"))
    False
    print(in_tamil("அ"))
    False
    print(in_tamil("௩"))
    False
    print(in_tamil("ப்"))
    False
    print(in_tamil("கை"))
    False
    print(in_tamil("ஃ"))
    False
    print(in_tamil("௹"))
    False
    print(in_tamil("க்ஷ்"))
    False
    print(in_tamil("ஷி"))
    False
    print(in_tamil("ஶ்ரீ"))
    False
    print(in_tamil("我"))
    False
    print(in_tamil("ക"))
    False
    """
    if len(char) == 1:
        code = ord(char)
        if 0x0000 <= code <= 0x007E:
            return True
        else:
            return False
        
def in_tamil(unicodes):
    """
    it checks the given letter is used in tamil or not(it say true for both tamil and 
    sanskrit, it helps to avoid other langaule letters)
    Args:
        letter(int): 
    Return:
        bool:
    eg:
    print(in_tamil("a"))
    False
    print(in_tamil("B"))
    False
    print(in_tamil("3"))
    False
    print(in_tamil("?"))
    False
    print(in_tamil("ஃ"))
    True
    print(in_tamil("௹"))
    True
    print(in_tamil("அ"))
    True
    print(in_tamil("ஔ"))
    True
    print(in_tamil("௩"))
    True
    print(in_tamil("ப்"))
    True
    print(in_tamil("கை"))
    True
    print(in_tamil("ஃ"))
    True
    print(in_tamil("௹"))
    True
    print(in_tamil("க்ஷ்"))
    True
    print(in_tamil("ஷி"))
    True
    print(in_tamil("ஶ்ரீ"))
    True
    print(in_tamil("我"))
    True
    print(in_tamil("ക"))
    True
    """
    in_tamil_range = all(0x0B80 <= ord(char) <= 0x0BFF for char in unicodes)
    if in_tamil_range:
        return True
    else:
        return False

def english_specific(char):
    """
    it gives which kind in given letter is in tamil
    Args:
        letter(int): 
    Return:
        bool:
    eg:
    print(english_specific("a"))
    'EN-LOW'
    print(english_specific("B"))
    'EN-UPP'
    print(english_specific("3"))
    'EN-NUM'
    print(english_specific("?"))
    'TA-SYM'
    print(english_specific("+"))
    'EN-SYM'
    print(english_specific("ஃ"))
    None
    print(english_specific("௹"))
    None
    """
    letter = None
    code = ord(char)
    if 0x41 <= code <= 0x5A:
        letter = "EN-UPP" 
    elif 0x61 <= code <= 0x7A:
        letter = "EN-LOW"
    elif 0x30 <= code <= 0x39:
        letter = "EN-NUM"
    elif code < 0x80: 
        letter = "EN-SYM"
    else:
        letter = None
    return letter

def tamil_specific(unicodes):
    """
    it gives which kind in given letter is in tamil
    Args:
        letter(int): 
    Return:
        bool:
    eg:

    print(tamil_specific("அ"))
    'TA-VOL'
    print(tamil_specific("ஔ"))
    'TA-VOL'
    print(tamil_specific("௩"))
    'TA-NUM'
    print(tamil_specific("ப்"))
    'TA-CON'
    print(tamil_specific("கை"))
    'TA-COM'
    print(tamil_specific("ஃ"))
    'TA-AUT'
    print(tamil_specific("௹"))
    'TA-SYM'
    print(tamil_specific("க்ஷ்"))
    None
    print(tamil_specific("ஷி"))
    None
    print(tamil_specific("ஶ்ரீ"))
    None
    print(tamil_specific("我"))
    None
    print(tamil_specific("ക"))
    None
    """
    letter = None
    if len(unicodes) == 1:
        if is_vowel(unicodes):
            return "TA-VOL"
        elif unicodes in TA_ROOT_CONSONENT:
            return "TA-CON"
        elif 0x0BE6 <= ord(unicodes) <= 0x0BEF:
            letter = "TA-NUM"
        elif unicodes == "ஃ":
            letter = "TA-AUT"
        elif unicodes in TAMIL_SYMBOLS:
            letter = "TA-SYM"
        else:
            letter = None
        # Tamil Symbols
    elif ta_consonent(unicodes):
        return "TA-CON"
    elif ta_composite(unicodes):
        return "TA-COM"
    else:
        return None
    return letter

def sanskrit_specific(unicodes):
    """
    it gives which kind in given letter is in sanskrit
    Args:
        letter(int): 
    Return:
        bool:
    eg:
    print(sanskrit_specific("க்ஷ்"))
    'SA-CON'
    print(sanskrit_specific("ஷி"))
    'SA-COM'
    print(sanskrit_specific("ஶ்ரீ"))
    'TA-SYM'
    print(sanskrit_specific("我"))
    None
    print(sanskrit_specific("ക"))
    None
    """
    letter_type = None
    if sa_consonent(unicodes):
        letter_type = "SA-CON"
    elif sa_composite(unicodes):
        letter_type = "SA-COM"
    elif unicodes == "ஶ்ரீ" :#TODO
        letter_type = "SA-SYM"
    else:
        return None
    return letter_type

def ta_consonent(unicodes):
    """
    it checks the given input is sanskrit composite?
    Args:
        letter(int): 
    Return:
        bool:
    eg:
    print(ta_consonent("ப்"))
    True
    print(ta_consonent("க்ஷூ"))
    False
    print(ta_consonent("க்"))
    True
    print(ta_consonent("a"))
    False
    print(ta_consonent("ஶ்"))
    False
    print(ta_consonent("அ"))
    False
    """
    if verify(unicodes):
        if unicodes[-1] == "்" and unicodes[:-1] in TA_ROOT_CONSONENT:
            return True
        else:
            return False
    else:
        return False

def ta_composite(unicodes):
    """
    it checks the given input is sanskrit composite?
    Args:
        letter(int): 
    Return:
        bool:
    eg:
    print(ta_composite("பூ"))
    True
    print(ta_composite("க்ஷூ"))
    False
    print(ta_composite("க"))
    True
    print(ta_composite("a"))
    False
    print(ta_composite("ஶ்"))
    True
    print(ta_composite("அ"))
    False
    """
    if verify(unicodes):
        if unicodes[-1] in TAMIL_VOWEL_CHARS and unicodes[:-1] in TA_ROOT_CONSONENT or unicodes in TA_ROOT_CONSONENT:
            return True
        else:
            return False
    else:
        return False


def sa_consonent(unicodes):
    """
    it checks the given input is sanskrit composite?
    Args:
        letter(int): 
    Return:
        bool:
    eg:
    print(sa_consonent("க்ஷ்"))
    True
    print(sa_consonent("க்ஷூ"))
    False
    print(sa_consonent("க"))
    False
    print(sa_consonent("a"))
    False
    print(sa_consonent("ஶ்"))
    True
    print(sa_consonent("அ"))
    False
    """
    if verify(unicodes):
        if unicodes[-1] == "்" and unicodes[:-1] in SA_ROOT_LETTERS:
            return True
        else:
            return False
    else:
        return False


def sa_composite(unicodes):
    """
    it checks the given input is sanskrit composite?
    Args:
        letter(int): 
    Return:
        bool:
    eg:
    print(sa_composite("க்ஷ"))
    True
    print(sa_composite("க்ஷூ"))
    True
    print(sa_composite("க"))
    False
    print(sa_composite("a"))
    False
    print(sa_composite("ஶ்"))
    False
    print(sa_composite("அ"))
    False
    """
    if verify(unicodes):
        if unicodes[-1] != "்": 
            if unicodes[-1] in TAMIL_VOWEL_CHARS and unicodes[:-1] in SA_ROOT_LETTERS or unicodes in SA_ROOT_LETTERS:
                return True
            else:
                return False
        elif unicodes in SA_ROOT_LETTERS:
            return True
    else:
        return False


def kind(unicodes):
    """
    it find's the give inputs kind it only works on only in tamil, english and sanskrit 
    Args:
        letter(str): 
    Return:
        letter(str):
    eg:
    print(kind("அ"))
    'TA-VOL'
    print(kind("ஔ"))
    'TA-VOL'
    print(kind("௩"))
    'TA-NUM'
    print(kind("ப்"))
    'TA-CON'
    print(kind("கை"))
    'TA-COM'
    print(kind("ஃ"))
    'TA-AUT'
    print(kind("௹"))
    'TA-SYM'
    print(kind("க்ஷ்"))
    'SA-CON'
    print(kind("ஷி"))
    'SA-COM'
    print(kind("ஶ்ரீ"))
    'TA-SYM'
    print(kind("我"))
    'UN-LAN'
    print(kind("ക"))
    'UN-LAN'
    """
    letter = None
    if is_en(unicodes):
        letter = english_specific(unicodes)
    elif in_tamil(unicodes):
        tamil_kind = tamil_specific(unicodes)
        if tamil_kind != None:
            letter = tamil_kind
        else:
            letter = sanskrit_specific(unicodes)
    else:
        return "UN-LAN"
    return letter




# numbers

en_to_ta_digit_dict = {
    '0': "௦", 
    '1': "௧", 
    '2': "௨", 
    '3': "௩", 
    '4': "௪",
    '5': "௫", 
    '6': "௬", 
    '7': "௭", 
    '8': "௮", 
    '9': "௯",
    ".":'.'
}

def en_to_ta_integer(integer):
    """
    it convert's english numerical into tamil numericals
    Args:
        letter(int): 
    Return:
        letter(str):
    eg:
    print(en_to_ta_integer(0))
    '௧௧'
    print(en_to_ta_integer(11))
    '-௦'
    print(en_to_ta_integer(-40))
    '-௪௦'
    print(en_to_ta_integer(249))
    '௨௪௯'
    print(en_to_ta_integer(81))
    '௮௧'
    print(en_to_ta_integer(-2))
    '-௨'

    """
    sign = "" if integer > 0 else '-'  
    ta_num = ''.join(en_to_ta_digit_dict[d] for d in str(integer) if d in en_to_ta_digit_dict)
    return sign + ta_num

ta_to_en_digit_dict = {
    "௦": '0', 
    "௧": '1', 
    "௨": '2', 
    "௩": '3', 
    "௪": '4',
    "௫": '5', 
    "௬": '6', 
    "௭": '7', 
    "௮": '8', 
    "௯": '9',
    ".":'.'
}

def ta_to_en_integer(integer):
    """
    it convert's tamil numerical into english numericals
    Args:
        letter(str): 
    Return:
        letter(int):
    eg:
    print(en_to_ta_integer('௧௧'))
    11
    print(en_to_ta_integer('-௦'))
    0
    print(en_to_ta_integer('-௪௦'))
    -40
    print(en_to_ta_integer('௨௪௯'))
    249
    print(en_to_ta_integer('௮௧'))
    81
    print(en_to_ta_integer('-௨'))
    -2
    """
    if is_ta_numbers(integer):
        sign = -1 if integer.startswith('-') > 0 else 1  
        en_num = ''.join(ta_to_en_digit_dict[d] for d in str(integer) if d in ta_to_en_digit_dict)
        if '.' in integer:
            return sign * float(en_num)
        else:
            return sign * int(en_num)
    else:
        raise ValueError("unexpected character in tamil numurals")

def is_ta_numbers(integer):
    """
    it convert's tamil numerical into english numericals
    Args:
        letter(str): 
    Return:
        letter(int):
    eg:
    """
    sign = slice(1,None) if integer.startswith('-') > 0 else slice(None,None)  
    return_bool = all([num in TAMIL_NUMURALS or num == "." for num in str(integer)[sign]])
    return return_bool

def add(int1,int2):
    """
    it convert's tamil numerical into english numericals
    Args:
        letter(str): 
    Return:
        letter(int):
    eg:
    print(add('௧௧','௧௧',))
    '௨௨'
    print(add('-௦','-௦',))
    '-௦'
    print(add('-௪௦','-௪௦',))
    '-௮௦'
    print(add('௪௯','௪௯',))
    '௯௮'
    print(add('௮௧','௮௧',))
    '௧௬௨'
    print(add('-௨','-௨',))
    '-௪'
    """
    return en_to_ta_integer( int(ta_to_en_integer(int1)) + int(ta_to_en_integer(int2)) )

def subract(int1,int2):
    """
    it convert's tamil numerical into english numericals
    Args:
        letter(str): 
    Return:
        letter(int):
    eg:
    print(subract('௧௧','௧௧',))
    '-௦'
    print(subract('-௨','-௨',))
    '-௦'
    print(subract('-௪௦','-௪௦',))
    '-௦'
    print(subract('௪௯','௪௯',))
    '-௦'
    print(subract('௮௧','௮௧',))
    '-௦'
    print(subract('-௨','-௨',))
    '-௦'
    """
    return en_to_ta_integer( int(ta_to_en_integer(int1)) - int(ta_to_en_integer(int2)) )

def multiplay(int1,int2):
    """
    it convert's tamil numerical into english numericals
    Args:
        letter(str): 
    Return:
        letter(int):
    eg:
    print(multiplay('௧௧','௧௧',))
    '௧௨௧'
    print(multiplay('-௨','-௨',))
    '௪'
    print(multiplay('-௪௦','-௪௦',))
    '௧௬௦௦'
    print(multiplay('௪௯','௪௯',))
    '௨௪௦௧'
    print(multiplay('௮௧','௮௧',))
    '௬௫௬௧'
    print(multiplay('-௨','-௨',))
    '௪'
    """
    return en_to_ta_integer( int(ta_to_en_integer(int1)) * int(ta_to_en_integer(int2)) )

def divide(int1,int2):
    """
    it convert's tamil numerical into english numericals
    Args:
        letter(str): 
    Return:
        letter(int):
    eg:
    print(divide('௧௧','௧௧',))
    '௧'
    print(divide('-௨','-௨',))
    '௧'
    print(divide('-௪௦','-௪௦',))
    '௧'
    print(divide('௪௯','௪௯',))
    '௧'
    print(divide('௮௧','௮௧',))
    '௧'
    print(divide('-௨','-௨',))
    '௧'

    """
    value = int(ta_to_en_integer(int1)) // int(ta_to_en_integer(int2))
    return en_to_ta_integer( value )

def flore_division(int1,int2):
    """
    it convert's tamil numerical into english numericals
    Args:
        letter(str): 
    Return:
        letter(int):
    eg:
    print(flore_division('௧௧','௧௧',))
    '௧௦'
    print(flore_division('-௨','-௨',))
    '௧௦'
    print(flore_division('-௪௦','-௪௦',))
    '௧௦'
    print(flore_division('௪௯','௪௯',))
    '௧௦'
    print(flore_division('௮௧','௮௧',))
    '௧௦'
    print(flore_division('-௨','-௨',))
    '௧௦'

    """
    return en_to_ta_integer( int(ta_to_en_integer(int1)) / int(ta_to_en_integer(int2)) )

def power(int1,int2):
    """
    it convert's tamil numerical into english numericals
    Args:
        letter(str): 
    Return:
        letter(int):
    eg:
    print(power('௧','௧',))
    '௧'
    print(power('௨','௨',))
    '௪'
    print(power('௪','௪',))
    '௨௫௬'
    print(power('௯','௪',))
    '௬௫௬௧'
    print(power('௧','௮',))
    '௧'
    print(power('௪','௨',))
    '௧௬'
    """
    return en_to_ta_integer( int(ta_to_en_integer(int1)) ** int(ta_to_en_integer(int2)) )

def trange(start, stop=None, step=1):
    # If only one argument is given, it's the stop
    if stop is None:
        start, stop = 0, start

    return [en_to_ta_integer(r) for r in range(start, stop, step)]
