import unittest 
from tamilstring.helper import Tint

class Test_Tint(unittest.TestCase):


    def test_int(self):
        self.assertEqual(1, int(Tint('௧')) )
        self.assertEqual(55, int(Tint('௫௫')) )
        self.assertEqual(4, int(Tint('௪.௧')) )
        self.assertEqual(-10, int(Tint('-௧௦')) )
        self.assertEqual(0, int(Tint('௦')) )

    def test_float(self):
        self.assertEqual(1.0, float(Tint('௧')) )
        self.assertEqual(55.0, float(Tint('௫௫')) )
        self.assertEqual(4.1, float(Tint('௪.௧')) )
        self.assertEqual(-10.0, float(Tint('-௧௦')) )
        self.assertEqual(0.0, float(Tint('௦')) )


    def test_bool(self):
        self.assertEqual(True, bool(Tint('௧')) )
        self.assertEqual(True, bool(Tint('௫௫')) )
        self.assertEqual(True, bool(Tint('௪.௧')) )
        self.assertEqual(True, bool(Tint('-௧௦')) )
        self.assertEqual(False, bool(Tint('௦')) )




    def test_add(self):
        self.assertEqual('௨௨', Tint('௧௧')+Tint('௧௧'))
        self.assertEqual('-௦',   Tint('-௦')+Tint('-௦'))
        self.assertEqual('-௮௦', Tint('-௪௦')+Tint('-௪௦'))
        self.assertEqual('௯௮', Tint('௪௯')+Tint('௪௯'))
        self.assertEqual('௧௬௨',Tint('௮௧')+Tint('௮௧'))
        self.assertEqual('-௪',  Tint('-௨')+Tint('-௨'))


    def test_subract(self):
        self.assertEqual('-௦',Tint('௧௧')-Tint('௧௧'))
        self.assertEqual('-௦',Tint('-௨')-Tint('-௨'))
        self.assertEqual('-௦',Tint('-௪௦')-Tint('-௪௦'))
        self.assertEqual('-௦',Tint('௪௯')-Tint('௪௯'))
        self.assertEqual('-௦',Tint('௮௧')-Tint('௮௧'))
        self.assertEqual('-௦',Tint('-௨')-Tint('-௨'))
        # #TODO Zero division error


    def test_multiplay(self):
        self.assertEqual('௧௨௧',Tint('௧௧')* Tint('௧௧'))
        self.assertEqual('௪',Tint('-௨')* Tint('-௨'))
        self.assertEqual('௧௬௦௦',Tint('-௪௦')* Tint('-௪௦'))
        self.assertEqual('௨௪௦௧',Tint('௪௯')* Tint('௪௯'))
        self.assertEqual('௬௫௬௧',Tint('௮௧')* Tint('௮௧'))
        self.assertEqual('௪',Tint('-௨')* Tint('-௨'))


    def test_divide(self):
        self.assertEqual('௧',Tint('௧௧')//Tint('௧௧'))
        self.assertEqual('௧',Tint('-௨')//Tint('-௨'))
        self.assertEqual('௧',Tint('-௪௦')//Tint('-௪௦'))
        self.assertEqual('௧',Tint('௪௯')//Tint('௪௯'))
        self.assertEqual('௧',Tint('௮௧')//Tint('௮௧'))
        self.assertEqual('௧',Tint('-௨')//Tint('-௨'))

    def test_flore_division(self):
        self.assertEqual('௧.௦',Tint('௧௧')/Tint('௧௧'))
        self.assertEqual('௧.௦',Tint('-௨')/Tint('-௨'))
        self.assertEqual('௧.௦',Tint('-௪௦')/Tint('-௪௦'))
        self.assertEqual('௧.௦',Tint('௪௯')/Tint('௪௯'))
        self.assertEqual('௧.௦',Tint('௮௧')/Tint('௮௧'))
        self.assertEqual('௧.௦',Tint('-௨')/Tint('-௨'))

    def test_power(self):
        self.assertEqual('௧',Tint('௧')**Tint('௧',))
        self.assertEqual('௪',Tint('௨')**Tint('௨',))
        self.assertEqual('௨௫௬',Tint('௪')**Tint('௪',))
        self.assertEqual('௬௫௬௧',Tint('௯')**Tint('௪',))
        self.assertEqual('௧',Tint('௧')**Tint('௮',))
        self.assertEqual('௧௬',Tint('௪')**Tint('௨',))

    def test_lshift(self):
        self.assertEqual(12, 6 << 1)
        self.assertEqual(Tint("௧௨"), Tint("௬") << Tint("௧"))
        

        self.assertEqual(24, 6 << 2)
        self.assertEqual(Tint("௨௪"), Tint("௬") << Tint("௨") )
        
    
    def test_lshift(self):
        self.assertEqual(6,12 >> 1 )
        self.assertEqual(Tint("௬"), Tint("௧௨") >> Tint("௧"))

        self.assertEqual(3,12 >> 2)
        self.assertEqual(Tint("௩"), Tint("௧௨") >> Tint("௨"))
        

    def test_and(self):
        self.assertEqual(1,5  & 3)
        self.assertEqual(Tint("௧"), Tint("௫") & Tint("௩"))
        
        self.assertEqual(2, 6 & 3 )
        self.assertEqual(Tint("௨"), Tint("௬") & Tint("௩"))
        
        self.assertEqual(1, 9 & 5)
        self.assertEqual(Tint("௧"), Tint("௯") & Tint("௫"))

        self.assertEqual(3, 3 & 3)
        self.assertEqual(Tint("௩"), Tint("௩") & Tint("௩"))


    def test_or(self):
        self.assertEqual(7, 5 | 3 )
        self.assertEqual(Tint("௭"), Tint("௫") | Tint("௩"))
        
        self.assertEqual(7, 6 | 3)
        self.assertEqual(Tint("௭"), Tint("௬") | Tint("௩"))
        
        self.assertEqual(5, 4 | 1)
        self.assertEqual(Tint("௫"), Tint("௪")  | Tint("௧"))
        


    def test_xor(self):
        self.assertEqual(6,5 ^ 3 )
        self.assertEqual(Tint("௬"), Tint("௫") ^ Tint("௩"))

        self.assertEqual(5, 6 ^ 3)
        self.assertEqual(Tint("௫"), Tint("௬") ^ Tint("௩"))
        
        self.assertEqual(5, 4 ^ 1)
        self.assertEqual(Tint("௫"), Tint("௪") ^ Tint("௧"))
        

        
    def test_inplace_add(self):
        letter =  Tint('௧௧')
        letter += '௧௧'
        self.assertEqual('௨௨', letter)
        letter =  Tint('௨௨')
        letter -= '௧௧'
        self.assertEqual('௧௧', letter)
        letter =  Tint('௧௧')
        letter *= '௧௧'
        self.assertEqual('௧௨௧', letter)
        #letter =  Tint('௧௧')
        #letter += '௧௧'
        #self.assertEqual('௨௨', letter)
        #letter =  Tint('௧௧')
        #letter += '௧௧'
        #self.assertEqual('௨௨', letter)
        #letter =  Tint('௧௧')
        #letter += '௧௧'
        #self.assertEqual('௨௨', letter)
        #letter =  Tint('௧௧')
        #letter += '௧௧'
        #self.assertEqual('௨௨', letter)
        

    def test_equal(self):
        self.assertTrue(Tint("௧") == Tint("௧"))
        self.assertTrue(Tint("1") == Tint("௧"))
        self.assertTrue(Tint("௧") == Tint("1"))
        self.assertTrue(1 == Tint("௧"))
        self.assertTrue(Tint("௧") == 1)
        #False cases
        self.assertFalse(Tint("௧") == Tint("௨"))
        self.assertFalse(Tint("1") == Tint("௨"))
        self.assertFalse(Tint("௨") == Tint("1"))
        self.assertFalse(1 == Tint("௨"))
        self.assertFalse(Tint("௨") == 1)

    def test_not_equal(self):
        self.assertFalse(Tint("௧") != Tint("௧"))
        self.assertFalse(Tint("1") != Tint("௧"))
        self.assertFalse(Tint("௧") != Tint("1"))
        self.assertFalse(1 != Tint("௧"))
        self.assertFalse(Tint("௧") != 1)
        #False cases
        self.assertTrue(Tint("௧") != Tint("௨"))
        self.assertTrue(Tint("1") != Tint("௨"))
        self.assertTrue(Tint("௨") != Tint("1"))
        self.assertTrue(1 != Tint("௨"))
        self.assertTrue(Tint("௨") != 1)


    def test_lessthen(self):
        self.assertTrue(Tint("௧") < Tint("௨"))
        self.assertTrue(Tint("1") < Tint("௨"))
        self.assertTrue(Tint("1") < Tint("2"))
        self.assertTrue(Tint("௧") < Tint("2"))
        self.assertFalse(Tint("௨") < Tint("௧") )
        self.assertFalse(Tint("௨") < Tint("1") )
        self.assertFalse(Tint("2") < Tint("1") )
        self.assertFalse(Tint("2") < Tint("௧") )


    def test_graterthen(self):
        self.assertTrue(   Tint("௨") > Tint("௧")  )
        self.assertTrue(   Tint("௨") > Tint("1")  )
        self.assertTrue(   Tint("2") > Tint("1")  )
        self.assertTrue(   Tint("2") > Tint("௧")  )
        self.assertFalse(  Tint("௧") > Tint("௨")  )
        self.assertFalse(  Tint("1") > Tint("௨")  )
        self.assertFalse(  Tint("1") > Tint("2")  )
        self.assertFalse(  Tint("௧") > Tint("2") ) 


    def test_lessthen_or_eq(self):
        self.assertTrue(Tint("௧") <= Tint("௧"))
        self.assertTrue(Tint("1") <= Tint("௧"))
        self.assertTrue(Tint("௧") <= Tint("1"))
        self.assertTrue(Tint("௧") <= Tint("௨"))
        self.assertTrue(Tint("1") <= Tint("௨"))
        self.assertTrue(Tint("1") <= Tint("2"))
        self.assertTrue(Tint("௧") <= Tint("2"))
        self.assertFalse(Tint("௨") <= Tint("௧") )
        self.assertFalse(Tint("௨") <= Tint("1") )
        self.assertFalse(Tint("2") <= Tint("1") )
        self.assertFalse(Tint("2") <= Tint("௧") )

    def test_graterthen(self):
        self.assertTrue(Tint("௧") >= Tint("௧"))
        self.assertTrue(Tint("1") >= Tint("௧"))
        self.assertTrue(Tint("௧") >= Tint("1"))
        self.assertTrue(   Tint("௨") >= Tint("௧")  )
        self.assertTrue(   Tint("௨") >= Tint("1")  )
        self.assertTrue(   Tint("2") >= Tint("1")  )
        self.assertTrue(   Tint("2") >= Tint("௧")  )
        self.assertFalse(  Tint("௧") >= Tint("௨")  )
        self.assertFalse(  Tint("1") >= Tint("௨")  )
        self.assertFalse(  Tint("1") >= Tint("2")  )
        self.assertFalse(  Tint("௧") >= Tint("2") ) 


    # inplace operations