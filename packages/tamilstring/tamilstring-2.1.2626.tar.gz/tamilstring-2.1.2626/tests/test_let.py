import unittest
from tamilstring import Letter


class TestTamil(unittest.TestCase):

    def test_without_letter(self):
        none_letter = Letter()

    def test_singelton(self):
        l1 = Letter("க்",singleton = True)
        l2 = Letter("வா",singleton = True)
        self.assertEqual(id(l1),id(l2))

    def test(self):
        volue = Letter('ஆ')
        constant = Letter('வ்')
        compound = Letter('வா')
        self.assertEqual( "வா",constant+volue )

        self.assertEqual( "வா",constant+"ஆ")
        self.assertEqual( "ஆவ்",volue+constant)
        self.assertEqual( "ஆவ்",volue+"வ்")

        tha = Letter("த")
        self.assertEqual( "தமிழ்", tha+"மிழ்" )
        ith = Letter("த்")
        
        self.assertEqual( "தமிழ்", ith+"அமிழ்")
        self.assertNotEqual( "தமிழ்", tha+"த்மிழ்")
        self.assertEqual("வ்",compound-volue)
        self.assertEqual("வ்",compound-"ஆ") 
        self.assertEqual("ஆ",compound-constant)
        self.assertEqual("ஆ",compound-"வ்") 

        self.assertEqual("வ்","வா"-volue)
        self.assertEqual("ஆ","வா"-constant)
        with self.assertRaises(ValueError) as context:
            "வ்"-compound
        self.assertEqual(str(context.exception),"#TODO" )
        with self.assertRaises(ValueError) as context:
            "வ்"-compound
        self.assertEqual(str(context.exception),"#TODO" )
        with self.assertRaises(ValueError) as context:
            "ஆ"-compound
        self.assertEqual(str(context.exception),"#TODO" )
        with self.assertRaises(ValueError) as context:
            "ஆ"-compound
        self.assertEqual(str(context.exception),"#TODO" )


    def test_inplace_methods(self):
        vowel = Letter('ஆ')
        consonent = Letter('ஜ்')
        composite = Letter('வா')

        add_inplace_letter = vowel
        add_inplace_letter += consonent
        self.assertEqual( "ஆஜ்", add_inplace_letter )

        add_inplace_letter = consonent
        add_inplace_letter += vowel
        self.assertEqual( "ஜா", add_inplace_letter )
