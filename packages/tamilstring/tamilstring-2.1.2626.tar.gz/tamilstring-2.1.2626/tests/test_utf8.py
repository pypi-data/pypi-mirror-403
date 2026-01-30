import unittest
from tamilstring.utf8 import get_letters, kind, split_letter , make_letter , \
    unmatch_indeces, is_composite ,is_vowel ,is_consonent, sa_composite, \
    sa_consonent, ta_consonent, ta_consonent, ta_composite, \
    is_sa, is_ta, is_en, in_tamil, trange,\
    remove_non_ta_en, verify, \
    add, subract, multiplay, divide, flore_division, power ,\
    english_specific, tamil_specific, sanskrit_specific,\
    en_to_ta_integer, ta_to_en_integer


class TestBaseWord(unittest.TestCase):

    def test_remove_non_ta_en(self):
        # true cases
        self.assertEqual("தைைமிாாழ்்",remove_non_ta_en("தைைமிாாழ்்ひらがな"))
        self.assertEqual("Hanzi/",remove_non_ta_en("Hanzi汉字/漢字")) 
        self.assertEqual("Hindi",remove_non_ta_en("Hindiहिन्दी"))
        self.assertEqual("Tamil",remove_non_ta_en("Tamilالتاميل")) 
        self.assertEqual("Tamil,English",remove_non_ta_en("Tamil,English"))
        self.assertEqual("",remove_non_ta_en("تاميلی")) 
        # false cases
        self.assertNotEqual("Hindiहिन्दी",remove_non_ta_en("Hindiहिन्दी"))
        self.assertNotEqual("Tamilالتاميل",remove_non_ta_en("Tamilالتاميل")) 
        

    def test_get_letters(self):
        # true cases
        self.assertEqual(['த','மி','ழ்'],get_letters("தமிழ்"))
        self.assertEqual(['க்ஷி','க்ஷு'],get_letters("க்ஷிக்ஷு"))
        self.assertEqual(['௵'],get_letters("௵"))
        self.assertEqual(['ஶ்ரீ','னி'],get_letters("ஶ்ரீனி")) 
        list1 = ['த', 'மி', 'ழ்', ' ', 'ப', 'ல', 'ரி', 'ன்', ' ', 'தா', 'ய்', 'மொ', 'ழி', ' ', 'ஆ', 'கு', 'ம்']
        self.assertEqual(list1,get_letters("தமிழ் பலரின் தாய்மொழி ஆகும்"))
        list2 =     ['செ', 'ம்', 'மொ', 'ழி', ' ', '(', 'C', 'l', 'a', 's', 's', 'i', 'c', 'a', 'l', ' ', 'l', 'a', 'n', 'g', 'u', 'a', 'g', 'e', ')']
        self.assertEqual(list2,get_letters("செம்மொழி (Classical language)"))
        self.assertEqual( ['E','n','g','l','i','s','h'],get_letters("English")) 
        self.assertEqual(['ஜா','ப','ர்'],get_letters("ஜாபர்"))
        self.assertEqual(['செ', 'ம்', 'மொ', 'ழி'],get_letters("செம்மொழி (Classical language)",skip_en=True))
        self.assertEqual(['௵'],get_letters("௵"))
        self.assertEqual(['ப்', 'ரீ'],get_letters('ப்ரீ'))
        self.assertEqual(['க்ஷ்', 'ரீ'], get_letters("க்ஷ்ரீ"))
        self.assertEqual(['ஜ்', 'ரீ'],get_letters('ஜ்ரீ'))
        self.assertEqual(['பெ','ரு'], get_letters("பெரு"))
        self.assertEqual(['இ', 'ரு'], get_letters("இரு"))
        self.assertEqual(['பூ','ரு'], get_letters("பூரு"))
        self.assertEqual(['பு','ரு'], get_letters("புரு"))
        self.assertEqual(['பொ','ரு'], get_letters("பொரு"))
        self.assertEqual(['போ','ரு'], get_letters("போரு"))
        self.assertEqual(['பௌ','ரு'], get_letters("பௌரு"))
        self.assertEqual(['பு','ரு'], get_letters("புரு"))

        # false cases
        self.assertNotEqual(['த','மி','ழ'],get_letters("தமிழ்"))
    
    def test_get_unmatch_indeces(self):
        self.assertEqual([[2, 3], [5, 7], [9, 10]],unmatch_indeces("தைைமிாாழ்்"))
        self.assertEqual([[2, 5], [7, 9], [11, 12]],unmatch_indeces("தைை漢字மிாாழ்்"))
        self.assertEqual([[2, 3], [5, 7], [9, 14]],unmatch_indeces("தைைமிாாழ்்1#w)"))

    def remove_wrong_unicode(self):
        self.assertEqual(['த','மி','ழ்'],get_letters("தமிழ்்"))
        self.assertEqual([],get_letters("்ா")) 
        self.assertEqual([],get_letters("漢字")) 
        self.assertEqual(['க்ஷி','க்ஷு'],get_letters("க்ஷி்ாக்ஷு"))

    def test_split_letter(self):
        # true cases
        self.assertEqual(('ம்','ஆ'),split_letter("மா"))
        self.assertEqual(('க்','ஓ'),split_letter("கோ"))
        self.assertEqual(('ண்','ஐ'),split_letter("ணை"))
        self.assertEqual(("க்ஷ்","இ"),split_letter("க்ஷி")) 
        self.assertEqual(('ஶ்', 'அ'),split_letter("ஶ"))
        self.assertEqual(('க்ஷ்', 'ஐ'),split_letter("க்ஷை"))
        # false cases
        self.assertEqual((None,None),split_letter("௵"))
        self.assertEqual((None,None),split_letter("ழ்"))
        self.assertEqual((None,None),split_letter("ஃ"))

    def test_make_letter(self):
        self.assertEqual('ழௌ',make_letter("ழ்","ஔ"))
        self.assertEqual('பூ',make_letter("ப்","ஊ"))
        self.assertEqual('கை',make_letter("க்","ஐ"))
        self.assertEqual('மூ',make_letter("ம்","ஊ"))
        self.assertEqual('சா',make_letter("ச்","ஆ"))
        self.assertEqual(None,make_letter("ப்ப","ப்"))        
        self.assertEqual(None,make_letter("ச","ஆ"))
        self.assertEqual(None,make_letter("ப்","ப"))
        self.assertEqual(None,make_letter("ப்","ப்"))
        

    def test_is_vowel (self):
        self.assertTrue(is_vowel("அ"))
        self.assertTrue(is_vowel("ஔ"))
        self.assertTrue(is_vowel("ஓ"))
        self.assertTrue(is_vowel("இ"))
        self.assertFalse(is_vowel("a"))
        self.assertFalse(is_vowel("க்ஷ்"))
        self.assertFalse(is_vowel("௩"))
        self.assertFalse(is_vowel("௫"))
        self.assertNotEqual(True,is_vowel("ஃ"))
        self.assertNotEqual(True,is_vowel("க"))
        self.assertNotEqual(True,is_vowel("க்"))
        self.assertEqual(True,is_vowel("உ"))
        self.assertEqual(True,is_vowel("இ"))
           
 
    def test_is_consonent (self):
        self.assertTrue(is_consonent("க்"))
        self.assertTrue(is_consonent("ழ்"))
        self.assertTrue(is_consonent("க்ஷ்"))
        self.assertTrue(is_consonent("ஞ்"))
        self.assertFalse(is_consonent("a"))
        self.assertFalse(is_consonent("ஷி"))
        self.assertFalse(is_consonent("௩"))
        self.assertFalse(is_consonent("௫")) 
        self.assertNotEqual(True,is_consonent("ஃ"))
        self.assertNotEqual(True,is_consonent("அ"))
        self.assertEqual(True,is_consonent("க்"))
        self.assertEqual(True,is_consonent("ப்"))
            
   
    def test_is_composite (self):
        self.assertTrue(is_composite("க"))
        self.assertTrue(is_composite("ழ"))
        self.assertTrue(is_composite("க்ஷ"))
        self.assertTrue(is_composite("க்ஷூ"))
        self.assertFalse(is_composite("a"))
        self.assertFalse(is_composite("ஶ்"))
        self.assertFalse(is_composite("௩"))
        self.assertFalse(is_composite("௫"))
        self.assertNotEqual(True,is_composite("ஃ"))
        self.assertNotEqual(True,is_composite("அ"))
        self.assertEqual(True,is_composite("க"))
        self.assertEqual(True,is_composite("மா"))

    def test_verify(self):
        self.assertTrue(verify("க"))
        self.assertTrue(verify("ழ"))
        self.assertTrue(verify("a"))
        self.assertTrue(verify("௩"))
        self.assertTrue(verify("௫"))
        self.assertTrue(verify("க்ஷ"))
        self.assertTrue(verify("க்ஷூ"))
        self.assertTrue(verify("க்ஷ்"))
        self.assertFalse(verify("English"))
        self.assertFalse(verify("தமிழ்"))
        self.assertFalse(verify("Hi"))

    def test_is_sa(self):
        self.assertFalse(is_sa("a"))
        self.assertFalse(is_sa("B"))
        self.assertFalse(is_sa("3"))
        self.assertFalse(is_sa("?"))
        self.assertFalse(is_sa("ஃ"))
        self.assertFalse(is_sa("௹"))
        self.assertTrue(is_sa("க்ஷ்"))
        self.assertTrue(is_sa("ஷி"))
        self.assertTrue(is_sa("ஶ்ரீ"))
        self.assertFalse(is_sa("我"))
        self.assertFalse(is_sa("ക"))

    def test_is_ta(self):
        self.assertTrue(is_ta("ஃ"))
        self.assertTrue(is_ta("கை"))
        self.assertTrue(is_ta("௩"))
        self.assertTrue(is_ta("௹"))
        self.assertTrue(is_ta("அ"))
        self.assertTrue(is_ta("௹"))
        self.assertFalse(is_ta("a"))
        self.assertFalse(is_ta("B"))
        self.assertFalse(is_ta("3"))
        self.assertFalse(is_ta("?"))
        self.assertFalse(is_ta("க்ஷ்"))
        self.assertFalse(is_ta("ஷி"))
        self.assertFalse(is_ta("ஶ்ரீ"))
        self.assertFalse(is_ta("我"))
        self.assertFalse(is_ta("ക"))


    def test_is_en(self):
        self.assertTrue(is_en("a"))
        self.assertTrue(is_en("B"))
        self.assertTrue(is_en("3"))
        self.assertTrue(is_en("?"))
        self.assertFalse(is_en("ஃ"))
        self.assertFalse(is_en("கை"))
        self.assertFalse(is_en("௩"))
        self.assertFalse(is_en("௹"))
        self.assertFalse(is_en("அ"))
        self.assertFalse(is_en("௹"))
        self.assertFalse(is_en("க்ஷ்"))
        self.assertFalse(is_en("ஷி"))
        self.assertFalse(is_en("ஶ்ரீ"))
        self.assertFalse(is_en("我"))
        self.assertFalse(is_en("ക"))


    def test_in_tamil(self):
        self.assertTrue(in_tamil("ஃ"))
        self.assertTrue(in_tamil("கை"))
        self.assertTrue(in_tamil("௩"))
        self.assertTrue(in_tamil("௹"))
        self.assertTrue(in_tamil("அ"))
        self.assertTrue(in_tamil("௹"))
        self.assertTrue(in_tamil("க்ஷ்"))
        self.assertTrue(in_tamil("ஷி"))
        self.assertTrue(in_tamil("ஶ்ரீ"))
        self.assertFalse(in_tamil("我"))
        self.assertFalse(in_tamil("ക"))
        self.assertFalse(in_tamil("a"))
        self.assertFalse(in_tamil("B"))
        self.assertFalse(in_tamil("3"))
        self.assertFalse(in_tamil("?"))

    def english_specific(self):
        self.assertEqual('EN-LOW',english_specific("a"))
        self.assertEqual('EN-UPP',english_specific("B"))
        self.assertEqual('EN-NUM',english_specific("3"))
        self.assertEqual('TA-SYM',english_specific("?"))
        self.assertEqual('EN-SYM',english_specific("+"))
        self.assertEqual(None,english_specific("ஃ"))
        self.assertEqual(None,english_specific("௹"))

    def test_tamil_specific(self):
        self.assertEqual('TA-VOL',tamil_specific("அ"))
        self.assertEqual('TA-VOL',tamil_specific("ஔ"))
        self.assertEqual('TA-NUM',tamil_specific("௩"))
        self.assertEqual('TA-CON',tamil_specific("ப்"))
        self.assertEqual('TA-COM',tamil_specific("கை"))
        self.assertEqual('TA-AUT',tamil_specific("ஃ"))
        self.assertEqual('TA-SYM',tamil_specific("௹"))
        self.assertEqual(None,tamil_specific("க்ஷ்"))
        self.assertEqual(None,tamil_specific("ஷி"))
        self.assertEqual(None,tamil_specific("ஶ்ரீ"))
        self.assertEqual(None,tamil_specific("我"))
        self.assertEqual(None,tamil_specific("ക"))

    def test_sanskrit_specific(self):
        self.assertEqual('SA-CON',sanskrit_specific("க்ஷ்"))
        self.assertEqual('SA-COM',sanskrit_specific("ஷி"))
        self.assertEqual('SA-SYM',sanskrit_specific("ஶ்ரீ"))
        self.assertEqual(None,sanskrit_specific("我"))
        self.assertEqual(None,sanskrit_specific("ക"))

    def test_ta_consonent(self):
        self.assertTrue(ta_consonent("க்"))
        self.assertTrue(ta_consonent("ழ்"))
        self.assertFalse(ta_consonent("க்ஷ"))
        self.assertFalse(ta_consonent("க்ஷூ"))
        self.assertFalse(ta_consonent("a"))
        self.assertFalse(ta_consonent("ஶ்"))
        self.assertFalse(ta_consonent("௩"))
        self.assertFalse(ta_consonent("௫"))
        

    def test_ta_composite(self):
        self.assertTrue(ta_composite("க"))
        self.assertTrue(ta_composite("ழ"))
        self.assertFalse(ta_composite("க்ஷ"))
        self.assertFalse(ta_composite("க்ஷூ"))
        self.assertFalse(ta_composite("a"))
        self.assertFalse(ta_composite("ஶ்"))
        self.assertFalse(ta_composite("௩"))
        self.assertFalse(ta_composite("௫"))
        
    def test_sa_consonent(self):
        self.assertTrue(sa_consonent("க்ஷ்"))
        self.assertTrue(sa_consonent("ஷ்"))
        self.assertTrue(sa_consonent("ஶ்"))
        self.assertFalse(sa_consonent("க"))
        self.assertFalse(sa_consonent("ழ"))
        self.assertFalse(sa_consonent("a"))
        self.assertFalse(sa_consonent("௩"))
        self.assertFalse(sa_consonent("௫"))
        
    def test_sa_composite(self):
        self.assertFalse(sa_composite("க"))
        self.assertFalse(sa_composite("ழ"))
        self.assertTrue(sa_composite("க்ஷ"))
        self.assertTrue(sa_composite("க்ஷூ"))
        self.assertFalse(sa_composite("a"))
        self.assertFalse(sa_composite("ஶ்"))
        self.assertFalse(sa_composite("௩"))
        self.assertFalse(sa_composite("௫"))

    def test_kind(self):
        self.assertEqual("TA-CON",kind("க"))
        self.assertEqual("TA-CON",kind("ழ"))
        self.assertEqual("EN-LOW",kind("a"))
        self.assertEqual("TA-NUM",kind("௩"))
        self.assertEqual("TA-NUM",kind("௫"))
        self.assertEqual("SA-COM",kind("க்ஷ"))
        self.assertEqual("SA-COM",kind("க்ஷூ"))
        self.assertEqual("SA-CON",kind("க்ஷ்"))

    def test_en_to_ta_integer(self):     
        self.assertEqual('௧௧',en_to_ta_integer(11))
        self.assertEqual('-௦',en_to_ta_integer(0))
        self.assertEqual('-௪௦',en_to_ta_integer(-40))
        self.assertEqual('௨௪௯',en_to_ta_integer(249))
        self.assertEqual('௮௧',en_to_ta_integer(81))
        self.assertEqual('-௨',en_to_ta_integer(-2))

    def test_ta_to_en_integer(self):
        self.assertEqual(11,ta_to_en_integer('௧௧'))
        self.assertEqual(0,ta_to_en_integer('-௦'))
        self.assertEqual(-40,ta_to_en_integer('-௪௦'))
        self.assertEqual(249,ta_to_en_integer('௨௪௯'))
        self.assertEqual(81,ta_to_en_integer('௮௧'))
        self.assertEqual(-2,ta_to_en_integer('-௨'))
        self.assertEqual(4.1,ta_to_en_integer('௪.௧'))


    def test_add(self):
        self.assertEqual('௨௨',add('௧௧','௧௧',))
        self.assertEqual('-௦',add('-௦','-௦',))
        self.assertEqual('-௮௦',add('-௪௦','-௪௦',))
        self.assertEqual('௯௮',add('௪௯','௪௯',))
        self.assertEqual('௧௬௨',add('௮௧','௮௧',))
        self.assertEqual('-௪',add('-௨','-௨',))



    def test_subract(self):
        self.assertEqual('-௦',subract('௧௧','௧௧',))
        self.assertEqual('-௦',subract('-௨','-௨',))
        self.assertEqual('-௦',subract('-௪௦','-௪௦',))
        self.assertEqual('-௦',subract('௪௯','௪௯',))
        self.assertEqual('-௦',subract('௮௧','௮௧',))
        self.assertEqual('-௦',subract('-௨','-௨',))
        # #TODO Zero division error

    def test_multiplay(self):
        self.assertEqual('௧௨௧',multiplay('௧௧','௧௧',))
        self.assertEqual('௪',multiplay('-௨','-௨',))
        self.assertEqual('௧௬௦௦',multiplay('-௪௦','-௪௦',))
        self.assertEqual('௨௪௦௧',multiplay('௪௯','௪௯',))
        self.assertEqual('௬௫௬௧',multiplay('௮௧','௮௧',))
        self.assertEqual('௪',multiplay('-௨','-௨',))

    def test_divide(self):
        self.assertEqual('௧',divide('௧௧','௧௧',))
        self.assertEqual('௧',divide('-௨','-௨',))
        self.assertEqual('௧',divide('-௪௦','-௪௦',))
        self.assertEqual('௧',divide('௪௯','௪௯',))
        self.assertEqual('௧',divide('௮௧','௮௧',))
        self.assertEqual('௧',divide('-௨','-௨',))

    def test_flore_division(self):
        self.assertEqual('௧.௦',flore_division('௧௧','௧௧',))
        self.assertEqual('௧.௦',flore_division('-௨','-௨',))
        self.assertEqual('௧.௦',flore_division('-௪௦','-௪௦',))
        self.assertEqual('௧.௦',flore_division('௪௯','௪௯',))
        self.assertEqual('௧.௦',flore_division('௮௧','௮௧',))
        self.assertEqual('௧.௦',flore_division('-௨','-௨',))

    def test_power(self):
        self.assertEqual('௧',power('௧','௧',))
        self.assertEqual('௪',power('௨','௨',))
        self.assertEqual('௨௫௬',power('௪','௪',))
        self.assertEqual('௬௫௬௧',power('௯','௪',))
        self.assertEqual('௧',power('௧','௮',))
        self.assertEqual('௧௬',power('௪','௨',))

