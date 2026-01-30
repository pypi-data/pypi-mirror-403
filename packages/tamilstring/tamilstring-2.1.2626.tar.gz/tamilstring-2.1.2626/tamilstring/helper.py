from . import utf8 
import math
import re


def is_numeric_regex(s):
    pattern = r'^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$'
    return bool(re.match(pattern, s))



class Tint:

    _instance = None  
    
    def __new__(cls, *args, **kwargs):

        singleton = kwargs.pop('singleton', False)
        if singleton:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = True
            return cls._instance
        else: 
            return super().__new__(cls)


    def __init__(self, *args, **kwargs):
        if not getattr(self, '_initialized', True):
            super().__init__(*args, **kwargs)
            self._initialized = True 
        if len(args) == 1:
            args1 = args[0]
            if not isinstance(args1, int):
                self.num = args1 if args1.isdigit() else utf8.ta_to_en_integer(args1)
        else:
            self.unicode = None
        # using the obj_output argument we can return object outputs particularly
        # for retrurning string concardination operations
        self.obj_output = kwargs.pop('obj', False)
        # it sensures self modification and does not retrun any value while concardination unicodes
        self.inplace = kwargs.pop('inplace',False)
        # we can disable automatic unicode corrections while adding but returns in as only in string 
        self.a_concad = kwargs.pop('concad',True)
        
        self.int_type = ""

        self.other = None

    def __repr__(self):
        try:
            char = chr(self.num)
        except ValueError:
            char = '?'
        return f"CharInt('{char}' | {self.num})"

    def __str__(self):
        try:
            return chr(self.num)
        except ValueError:
            return str(self.num)

    def __int__(self):
        return int(self.num)
    
    def __float__(self): 
        return float(self.num)
    
    #def __complex__(self): return complex(self.num)
    def __bool__(self): 
        return bool(int(self.num))
    
    def __index__(self): 
        return self.num

    def __round__(self, n=0): 
        return utf8.en_to_ta_integer(round(self.num, n))
    
    def __trunc__(self): 
        return utf8.en_to_ta_integer(math.trunc(float(self.num)))
    
    def __floor__(self): 
        return utf8.en_to_ta_integer(math.floor(float(self.num)))
    
    def __ceil__(self): 
        return utf8.en_to_ta_integer(math.ceil(float(self.num)))

    # Unary
    def __neg__(self): 
        return utf8.en_to_ta_integer(-self.num)
    
    def __pos__(self): 
        return utf8.en_to_ta_integer(+self.num)
    
    def __abs__(self): 
        return utf8.en_to_ta_integer(abs(int(self.num)))
    
    def __invert__(self): 
        return utf8.en_to_ta_integer(~int(self.num))

    def is_float(self):
        try:
            int( self.num )
            return False
        except ValueError:
            return True
            
    # Arithmetic
    def __add__(self, other): 
        self.other = other
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) + self.other )
    
    def __sub__(self, other):  
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) - self.other )
    
    
    def __mul__(self, other):
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) * self.other )
    
    
    def __matmul__(self, other): raise NotImplementedError("Matrix multiplication not supported")
    
    def __truediv__(self, other): 
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) / self.other )
    
    
    def __floordiv__(self, other):
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) // self.other )
    
    
    def __mod__(self, other):
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) % self.other )
    
    
    def __divmod__(self, other):
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) - self.other )
    
    

    def __pow__(self, other, modulo=None):
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) ** self.other )
    
        #return pow(self.num, int(other), modulo) if modulo else pow(self.num, int(other))

    # Bitwise
    def __lshift__(self, other):# return self.num << int(other)
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) << self.other )
    
    def __rshift__(self, other):# return self.num >> int(other)
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) >> self.other )
    
    def __and__(self, other):# return self.num & int(other)
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) & self.other )
    
    def __xor__(self, other):# return self.num ^ int(other)
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) ^ self.other )
    
    def __or__(self, other):# return self.num | int(other)
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return utf8.en_to_ta_integer( float(self.num) if self.is_float() else int(self.num) | self.other )
    
    # Reflected
    def __radd__(self, other): return int(other) + self.num
    def __rsub__(self, other): return int(other) - self.num
    def __rmul__(self, other): return int(other) * self.num
    def __rtruediv__(self, other): return int(other) / self.num
    def __rfloordiv__(self, other): return int(other) // self.num
    def __rmod__(self, other): return int(other) % self.num
    def __rdivmod__(self, other): return divmod(int(other), self.num)
    def __rpow__(self, other, modulo=None):
        return pow(int(other), self.num, modulo) if modulo else pow(int(other), self.num)
    def __rlshift__(self, other): return int(other) << self.num
    def __rrshift__(self, other): return int(other) >> self.num
    def __rand__(self, other): return int(other) & self.num
    def __rxor__(self, other): return int(other) ^ self.num
    def __ror__(self, other): return int(other) | self.num

    # In-place
    def __iadd__(self, other): 
        #self.num += int(other); return self
        return self.__add__(other)
       

    def __isub__(self, other): 
        return self.__sub__(other)
    def __imul__(self, other): 
        return self.__mul__(other)
    def __itruediv__(self, other): 
        return self.__truediv__(other)
    def __ifloordiv__(self, other): 
        return self.__floordiv__(other)
    def __imod__(self, other): 
        return self.__imod__(other)
        
    def __ipow__(self, other, modulo=None):
        self.num = pow(self.num, int(other), modulo) if modulo else pow(self.num, int(other)); return self
    def __ilshift__(self, other): self.num <<= int(other); return self
    def __irshift__(self, other): self.num >>= int(other); return self
    def __iand__(self, other): self.num &= int(other); return self
    def __ixor__(self, other): self.num ^= int(other); return self
    def __ior__(self, other): self.num |= int(other); return self

    # Comparison
    def __eq__(self, other):
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")
        return float(self.num) if self.is_float() else int(self.num) == self.other 
    

    def __ne__(self, other):
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return float(self.num) if self.is_float() else int(self.num) != self.other 
    
    def __lt__(self, other): 
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return float(self.num) if self.is_float() else int(self.num) < self.other
    
    def __le__(self, other):
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return float(self.num) if self.is_float() else int(self.num) <= self.other 
    
    def __gt__(self, other):      
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return float(self.num) if self.is_float() else int(self.num) > self.other 
    
    def __ge__(self, other):       
        self.other = None
        if isinstance(other,(int,float)):
            self.other = other 
        elif isinstance(other, (Tint)):
            self.other = float(other.num) if other.is_float() else int(other.num)
        elif isinstance(other, (str)):
            if is_numeric_regex(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            elif utf8.is_ta_numbers(other):
                other = Tint(other)
                self.other = float(other.num) if other.is_float() else int(other.num)
            else:
                #TODO
                raise ValueError("#TODO")
            # .isdigit() else utf8.ta_to_en_integer(args1)
        else:
            #TODO
            raise ValueError("#")

        return float(self.num) if self.is_float() else int(self.num) >= self.other 
    



class Letter:

    _instance = None  
    
    def __new__(cls, *args, **kwargs):

        singleton = kwargs.pop('singleton', False)
        if singleton:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = True
            return cls._instance
        else: 
            return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        '''
        
        eg:
        # with out using singleton
        from tamilString import Letter
        letter_ka = Letter('க')
        letter_va = Letter('வ')
        print(id(letter_ka)==id(letter_va))
        False
        #here both are not same, both variables uses different values
        letter_ka
        க
        letter_va
        வ

        # using singleton 
        letter_ka = Letter('க',singleton=True)
        letter_va = Letter('வ',singleton=True)
        print(id(letter_ka)==id(letter_va))
        True
        letter_ka
        வ
        letter_va
        வ
        # here both are same and both variable uses same instances
        when we modify any one of the singleton instances that reflect in both 
        variables becase both of them uses the same instances.
        letter_ka = அ
        letter_ka
        அ
        letter_va
        அ
        '''
        if not getattr(self, '_initialized', True):
            super().__init__(*args, **kwargs)
            self._initialized = True 
        if len(args) == 1:
            args1 = args[0]
            if isinstance(args1, str):
                args1 = str(args1)
            self.unicode = utf8.get_letters(args1)[0]
        else:
            self.unicode = None
        # using the obj_output argument we can return object outputs particularly
        # for retrurning string concardination operations
        self.obj_output = kwargs.pop('obj', False)
        # it sensures self modification and does not retrun any value while concardination unicodes
        self.inplace = kwargs.pop('inplace',False)
        # we can disable automatic unicode corrections while adding but returns in as only in string 
        self.auto_concad = kwargs.pop('concad',True)

        self.return_type = kwargs.pop('type',"obj")

        self.return_value = ""

        self.return_letters_len = 0

    def return_auto_concardination(self):
        if self.inplace == True:
            if self.return_letters_len > 1:
                self.string = self.return_value
                self.__class__(String)
        else:
            if self.return_type == "obj":
                return self.return_value
            elif self.return_letters_len > 1:
                return String(self.return_value)
            else:
                return Letter(self.return_value)

    def __add__(self,other):
        self.return_letters_len = 0
        if not isinstance(other,Letter):
            other_letters =  utf8.get_letters(other)
            if len(other_letters) < 1: 
                self.return_value = self.string
                return self.return_auto_concardination()
            elif len(other_letters) == 1:
                other = Letter(other)
            else:
                other = String(other)
                if other.singleton(0).is_vowel and self.is_consonent:
                    self.return_value = utf8.make_letter(self.unicode,other[0]) + other[1:]
                else:
                    self.return_value = self.letter + other.string
                return self.return_auto_concardination()

        if self.is_consonent and other.is_vowel: 
            self.return_value = utf8.make_letter(self.letter,other.letter)
        else:
            self.return_letters_len = 2
            self.return_value = self.letter + other.string

        return self.return_auto_concardination()

    def __iadd__(self,other):
        return self.__add__(other)

    def __radd__(self,other):
        self.return_letters_len = 0
        if not isinstance(other,Letter):
            other_letters =  utf8.get_letters(other)
            if len(other_letters) > 1: 
                self.return_value = self.letter + String(other)
                return self.return_auto_concardination()
            elif len(other_letters) == 1:
                other = Letter(other)
            else:
                other = String(other)
        
        if self.is_vowel and other.is_consonent: 
            self.return_value = utf8.make_letter(self.letter,other.letter)
        else:
            self.return_letters_len = 2
            self.return_value = other.string + self.letter 

        return self.return_auto_concardination()


    def __sub__(self,other):
        self.return_letters_len = 0
        if not isinstance(other,Letter):
            other_letters =  utf8.get_letters(other)
            if len(other_letters) > 1: 
                self.return_value = ""
                return self.self.return_auto_concardination()
            elif len(other_letters) == 1:
                other = Letter(other)
            else:
                # TODO
                raise ValueError("TODO")
        if self.is_composite and other.is_vowel or other.is_consonent:
            if other.is_vowel: 
                self.return_value = self.consonent
            elif other.is_consonent:
                self.return_value = self.vowel
            self.return_letters_len = 1
            return self.return_auto_concardination()
        else:
            #TODO
            raise ValueError("#TODO")

    def __rsub__(self,other):
        self.return_letters_len = 0
        if not isinstance(other,Letter):
            other_letters =  utf8.get_letters(other)
            if len(other_letters) > 1: 
                self.return_value = ""
                return self.return_auto_concardination()
            elif len(other_letters) == 1:
                other = Letter(other)
            else:
                # TODO
                raise ValueError("TODO")
        if self.is_vowel or self.is_consonent and other.is_composite:
            if self.is_vowel: 
                self.return_value = other.consonent
            elif self.is_consonent:
                self.return_value = other.vowel
            self.return_letters_len = 1
            return self.return_auto_concardination()
        else:
            #TODO
            raise ValueError("#TODO")


    def __isub__(self,other):
        return self.__sub__(other)


    def __contains__(self, item):
        if item == self.letter:
            return True
        else:
            return False

    def __str__(self):
        return self.letter
 
    @property
    def string(self): 
        '''
        it returns the current letter into the string formate .
        '''
        return self.unicode

    @string.setter
    def string(self, value):
        '''
        it helps to do perform setter
        '''
        if value != None:
            self.unicode = value
        else:
            self.unicode = None 

    @property
    def is_ta(self):
        return utf8.is_ta(self.letter)

    @property
    def is_sa(self):
        return utf8.is_sa(self.letter)
    
    @property
    def is_en(self):
        return utf8.is_en(self.unicode)
        
    @property
    def in_tamil(self):
        return utf8.in_tamil(self.unicode)

    @property
    def kind(self):
        '''
        it helps to findout current letter is what kind of representation. using this we can find does it is
        whether a numeric or perticular type letter or charecteristic representation.
        '''
        return utf8.kind(self.unicode)

    @property
    def letter(self):
        '''
        it return the current letter , works as getter method. both
        Letter.string and Letter.letter gives the same result.
        '''
        return self.unicode

    @letter.setter
    def letter(self, value):
        '''
        it acts as the setter for the letter 
        '''
        if value != None:
            self.unicode = value
        else:
            self.unicode = None 

    @property
    def is_vowel(self):
        '''
        it returens the current letter of the instance is vowel or not?
        eg:
        vowel = Letter('ஆ')
        consonent = Letter('வ்')
        composite = Letter('வா')
        vowel.is_vowel
        True
        composite.is_vowel
        False
        consonent.is_vowel
        False
        '''
        if utf8.is_vowel(self.letter):
            return True
        else:
            return False
        
    @property
    def is_consonent(self):
        '''
        it returens the current letter of the instance is consonent or not?
        eg:
        vowel = Letter('ஆ')
        consonent = Letter('வ்')
        composite = Letter('வா')
        vowel.is_consonent
        False
        composite.is_consonent
        True
        consonent.is_consonent
        False'''
        if utf8.is_consonent(self.letter):
            return True
        else:
            return False
        
    @property
    def is_composite(self): 
        '''
        it returens the current letter of the instance is composite or not?
        eg:
        vowel = Letter('ஆ')
        consonent = Letter('வ்')
        composite = Letter('வா')
        vowel.is_composite
        False
        composite.is_composite
        False
        consonent.is_composite
        True
        '''
        if utf8.is_composite(self.letter):
            return True
        else:
            return False
    

    @property
    def vowel(self):
        '''
        it returns the vowel letter only if our current letter is composite os vowel, otherwise
        it returns none.
        eg:
        vowel = Letter('ஆ')
        consonent = Letter('வ்')
        composite = Letter('வா')
        vowel.vowel
        "ஆ"
        composite.vowel
        'அ'
        consonent.vowel
        None
        '''
        if utf8.is_vowel(self.letter):
            return self.letter
        elif utf8.is_composite(self.letter):
            constant_ , vowel_ = utf8.split_letter(self.letter)
            return vowel_
        else:
            return None
    
    @vowel.setter
    def vowel(self, value):
        '''
        it acts as setter for make automatic in modifiying of one to another vowel letter 
        also it works in composite modifications.
        eg:
        vowel = Letter('ஆ')
        consonent = Letter('வ்')
        composite = Letter('வா')
        print(vowel)
        vowel.vowel
        "ஆ"
        vowel = "இ"
        vowel.letter
        "இ"
        vowel.vowel
        "இ"
        print(composite)
        வா

        composite.letter
        வா
        composite.vowel
        "ஆ"

        composite.vowel = 'ஔ'
        composite.letter
        வௌ
        composite.vowel
        'ஔ'
        consonent.vowel
        None
        consonent.letter
        consonent.consonent
        "வ்"
        
        consonent.vowel = "ஏ"
        consonent.letter
        வே
        consonent.consonent
        "வ்"
        consonent.vowel
        "ஏ"
        '''
        value =  utf8.get_letters(value)
        if len(value) != 1:
            raise ValueError("only tamil letter can be modify.")
        if utf8.is_vowel(value):
            #if utf8.is_vowel(self.letter):
            #    self.unicode = value
            if utf8.is_composite(self.letter):
                constant_ , vowel = utf8.split_letter(self.letter)
                self.unicode = utf8.make_letter(value,constant_)
            elif utf8.is_consonent(self.letter):
                self.unicode = utf8.make_letter(value,constant_)
            else:
                self.unicode = value
        
    @property
    def consonent(self):
        '''
        it returns the consonet letter only if our current letter is composite os consonent, otherwise
        it returns none.
        eg:
        vowel = Letter('ஆ')
        consonent = Letter('வ்')
        composite = Letter('வா')
        print(vowel)
        vowel.consonent
        None
        vowel = ""
        vowel.letter
        "இ"
        vowel.consonent
        "இ"
        print(composite)
        வா

        composite.letter
        வா
        composite.consonent
        'வ்'
        
        consonent.vowel
        None 
        consonent.consonent
        "ப்"

        '''
        if utf8.is_consonent(self.letter):
            return self.letter
        elif utf8.is_composite(self.letter):
            constant_ , vowel_ = utf8.split_letter(self.letter)
            return constant_
        else:
            return None

    @consonent.setter
    def consonent(self, value):
        '''
        it acts as setter for make automatic in modifiying of one to another consonent letter 
        also it works in composite modifications.
        eg:
        vowel = Letter('ஆ')
        consonent = Letter('வ்')
        composite = Letter('வா')
        print(vowel)
        vowel.consonent
        None
        vowel = ""
        vowel.letter
        "இ"
        vowel.consonent
        "இ"
        print(composite)
        வா

        composite.letter
        வா
        composite.consonent
        'வ்'

        composite.consonent = 'ப்'
        composite.letter
        பா
        composite.consonent
        'ப்'
        
        print(consonent)
        'வ்'
        consonent.consonent
        'வ்'
        
        consonent.letter
        'வ்'
        consonent.consonent = 'ம்'
        "ம்"
        
        consonent.vowel
        None 
        consonent.vowel = "ஊ"
        consonent.letter
        'பூ'
        consonent.consonent
        "ப்"
        consonent.vowel
        "ஊ"

        '''
        if utf8.is_consonent(value):
            if utf8.is_vowel(self.letter):
                self.unicode = utf8.make_letter(value,self.unicode)
            if utf8.is_composite(self.letter):
                constant_ , vowel_ = utf8.split_letter(self.letter)
                self.unicode = utf8.make_letter(value,vowel_)
            #elif utf8.is_consonent(self.letter):
            #    self.unicode = utf8.make_letter(value,constant_)
            else:
                self.unicode = value
        

    @property
    def composite(self):
        '''
        it simple return current letter only if it is composite, otherwise it returns none.
        eg:
        vowel = Letter('ஆ')
        consonent = Letter('வ்')
        composite = Letter('வா')
        vowel.vowel
        "ஆ"
        composite.vowel
        'அ'
        consonent.vowel
        None'''
        if utf8.is_composite(self.letter):
            return self.letter
        else:
            return None

    @composite.setter
    def composite(self, value):
        '''
        it acts as setter for make automatic in modifiying of one to another vowel letter 
        also it works in composite modifications.
        eg:
        vowel = Letter('ஆ')
        consonent = Letter('வ்')
        composite = Letter('வா')
        print(vowel)
        vowel.consonent
        None
        vowel = ""
        vowel.letter
        "இ"
        vowel.consonent
        "இ"
        print(composite)
        வா

        composite.letter
        வா
        composite.consonent
        'வ்'

        composite.consonent = 'ப்'
        composite.letter
        பா
        composite.consonent
        'ப்'
        
        print(consonent)
        'வ்'
        consonent.consonent
        'வ்'
        
        consonent.letter
        'வ்'
        consonent.consonent = 'ம்'
        "ம்"
        
        consonent.vowel
        None 
        consonent.vowel = "ஊ"
        consonent.letter
        'பூ'
        consonent.consonent
        "ப்"
        consonent.vowel
        "ஊ"
        '''
        if utf8.is_composite(value):
            self.unicode = value
    
    def remove(self,kind):
        '''
        in some sinearios we may need to remove consonent or vowel reprenentation unicode from 
        current compoiste letter, it helps to do those thing eaily
        eg:
        # it only going to work in composite letters
        
        composite = Letter('வா')

        print(composite)
        வா
        
        composite.remove("CON")
        print(composite)
        'ஆ'

        composite = Letter('கோ')
        
        composite.remove("VOL")
        print(composite)
        'க்'

        '''
        if self.is_composite:
            constant_ , vowel_ = utf8.split_letter(self.letter)
            if kind == "VOL":
                self.unicode = constant_
            elif kind == "CON":
                self.unicode = vowel_

    @property
    def split_letter(self):
        '''
        it returns the a spliter letter of the composite letter. 
        it only going to work for composite letters.
        eg:

        composite = Letter('வா')

        print(composite)
        வா
        
        splited_letters = composite.split_letter
        print(splited_letters)
        ('வ்','ஆ')

        composite = Letter('கோ')        
        splited_letters = composite.split_letter
        print(splited_letters)
        ('க்','ஓ')

        composite = Letter('க்ஷை')
        splited_letters = composite.split_letter
        print(splited_letters)
        ('க்ஷ்', 'ஐ')

        consonent = Letter('க்')
        splited_letters = consonent.split_letter
        print(splited_letters)
        (None,None)

        vowel = Letter('க்ஷை')
        splited_letters = vowel.split_letter
        print(splited_letters)
        (None,None)        
        '''
        return utf8.split_letter(self.letter)
    
    def is_contains(self, other):
        '''
        it helps to check a perticular letter does it container inside the letter.
        eg:
        '''
        if len(other) > 2:
            raise ValueError("it does not look like a seperate letter")
        if not isinstance(other, Letter):
            other = Letter(other)
        if other.letter == self.letter:
            return True
        elif (other.is_composite and not self.is_composite):
            return None
        elif (self.is_composite and not other.is_composite) :
            if other.letter in self.split_letter:
                return True
            else:
                return False

    def get_match(self, other, output=False):
        '''
        it returens similerar vowel or consonent having between the current letter and 
        giving input to current letters object method get_match().
        it only works if both letter is composite and it returns whether if it contains
        any similear consonent or vowel 
        eg:
        vowel = Letter('ஆ')
        consonent = Letter('வ்')
        composite = Letter('வா')
        print(vowel)
        vowel.consonent
        None
        vowel = ""
        vowel.letter
        "இ"
        vowel.consonent
        "இ"
        print(composite)
        வா

        composite.letter
        வா
        composite.consonent
        'வ்'

        '''
        if not isinstance(other,Letter):
            other = Letter(other)
        output_value = (False,None) 
        if self.letter == other.letter:
            output_value = (True,other.kind)
        elif (other.is_composite and not self.is_composite):
            if self.letter in other.split_letter[0]:
                output_value = (True,other.kind)
        elif (self.is_composite and not other.is_composite):
            if other.letter == self.split_letter[1]:
                output_value = (True,other.kind)
        if output:
            return output_value
        else:
            return output_value[0]


class String:       
    _instance = None  

    def __new__(cls, *args, **kwargs):
        singleton = kwargs.pop('singleton', False)
        if singleton:
            if cls._instance is None:
                cls._instance = super(String, cls).__new__(cls)
                cls._instance._initialized = True 
            return cls._instance
        else:
            return super(String, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        if not getattr(self, '_initialized', True):
            super(String, self).__init__(*args, **kwargs)
            self._initialized = True 
        if len(args) > 0:
            args1 = args[0]
            if not isinstance(args1, str):
                args1 = str(args1)
            self.unicodes_list = utf8.get_letters(args1)
        else:
            self.unicodes_list = None
        self.output = kwargs.pop('object', False)
        self.position = 0
        # it desides whether this object want to return a new instance or just a resulting string of the consardination operation
        # TODO
        # it helps to __getitem__ attribute to deside to return a instance of an lettter or just an index string letter 
        self.obj_output = kwargs.pop('obj', False)
        # it sensures self modification and does not retrun any value while concardination unicodes
        self.inplace = kwargs.pop('inplace',False)
        # we can disable automatic unicode corrections while adding but returns in as only in string 
        self.a_concad = kwargs.pop('concad',True)
        

    def __add__(self,other):
        '''
        it helps to automate concardinations in some specific places
        adding consonents ending letter of a words needs some automatic letter conversion with adding upcoming vowel letters
        eg:
        string1 = String("மெய்ம்மயக்கம்") 
        print(string1 + "அ")
        மெய்ம்மயக்கம
        suffix_string = String("அ")
        print(string1 + suffix_string)
        மெய்ம்மயக்கம
        suffix_letter = Letter("அ")
        print(string1+suffix_letter)
        மெய்ம்மயக்கம

        string2 = String("மெய்ம்ம்") 
        print(string2 + "அயக்கம்")
        மெய்ம்மயக்கம
        suffix_string =  String("அயக்கம்")
        print(string2 + suffix_string)
        மெய்ம்மயக்கம
        
        # un auto concardinating cases
        string3 = String("மெய்ம்") 
        print(string3 + "மயக்கம்")
        மெய்ம்மயக்கம
        suffix_string = String("மயக்கம்")
        print(string3 + suffix_string)
        மெய்ம்மயக்கம
        '''
        return_string_list = ""
        if not isinstance(other,String):
            other = String(other)
            
        if self.a_concad == True:
                
            if self.singleton(-1).is_consonent and other.singleton(0).is_vowel:
                return_string_list = self.letters[:-1] + [utf8.make_letter(self.letters[-1],other.letters[0])] + other.letters[1:] 
            else:
                return_string_list = self.letters + other.letters

        else:
            return self.string + other

        if self.output:
            return String("".join(return_string_list))
        else:
            if self.inplace:
                self.letters = return_string_list
            else:
                return "".join(return_string_list)


    def __sub__(self,other):
        '''
        in many places tamil letters needs to remove the ending vowel or consonents unicode charecters , removing vowel charecters
        does not need any complex changes but removing consonets needs do some complex chenges on that sinerios it will help more
        eg:
        string1 = String("மெய்ம்மயக்கம்") 
        print(string1 - "அ")
        மெய்ம்மயக்கம்
        suffix_string = String("அ")
        print(string1 - suffix_string)
        மெய்ம்மயக்கம்
        suffix_letter = Letter("அ")
        print(string1 - suffix_letter)
        மெய்ம்மயக்கம்
        '''
        return_string_list = None
        if not isinstance(other, Letter):
            other = Letter(other)
        if isinstance(other, Letter):
            if self.singleton(-1).is_composite and ( other.is_vowel or other.is_consonent): 
                final_letter = self.singleton(-1).consonent if other.kind == "VOL" else self.singleton(-1).vowel
                return_string_list = self.letters[:-1] + final_letter
            else:
                raise ValueError("can only subract string endings with voule or constant")        
        else:
            raise ValueError("can only subract string endings with voule or constant")

        if self.output:
            return String("".join(return_string_list))
        else:
            if self.inplace:
                self.letters = return_string_list
            else:
                return "".join(return_string_list)


    @property
    def letters(self):
        '''
        returns the letters in the given unicodes
        eg:
        tamilstring = String("தமிழ்")
        print(tamilstring.letters)
        ['த','மி','ழ்']
        tamilstring_sanskrit = "ஶ்ரீனி"
        print(tamilstring_sanskrit.letters)
        ['ஶ்ரீ','னி']
        '''
        return self.unicodes_list
 
    @property
    def string(self):
        '''
        it will return the given string, whenever needs to see the modified string it fecelitates that feature or it gives entir 
        letters of 
        eg:
        tamilstring = String("தமிழ்")
        print(tamilstring.string)
        'தமிழ்'
        tamilstring_sanskrit = "ஶ்ரீனி"
        print(tamilstring_sanskrit.string)
        'ஶ்ரீனி'

        '''
        return "".join(self.unicodes_list)

    @string.setter
    def string(self,value):
        '''
        eg:
        tamilstring = String("தமிழ்")
        print(tamilstring.string)
        'தமிழ்'
        tamilstring.string = "செந்தமிழ்"
        print(tamilstring.string)
        'செந்தமிழ்'
        tamilstring_sanskrit = "ஶ்ரீனி"
        print(tamilstring_sanskrit.string)
        tamilstring_sanskrit.string = "ஶ்ரீனிவாசன்"
        print(tamilstring_sanskrit.string)
        'ஶ்ரீனிவாசன்'        
        '''
        self.unicodes_list = utf8.get_letters(value)
       
    def has_contain(self, substring,):
        if isinstance(substring, String):
            subString = substring
        else:
            subString = String(substring)    
        matchValue, all_matches = [] ,[]       
        matchCount,tracer = 0,0
        letter = Letter('ஆ')
        for index , letter_ in enumerate(self.letters):
            letter.unicode = letter_
            if matchCount == len(subString.letters):
                subString.position,matchCount= 0,0
                all_matches.append((True,matchValue)) 
                matchValue = []
                tracer = index
            checkMatch =  letter.get_match(subString[subString.position],output=True )
            if checkMatch[0]:
                if self.letters[index] == subString[subString.position]: 
                    matchValue.append(letter_)
                    subString.position += 1 
                    matchCount += 1
                else:
                    constant,voule = letter.split_letter
                    if checkMatch[1] == "VOL":                       
                        matchValue.append(voule)
                        if len(all_matches) != 0:
                            if all_matches[-1][0] == True:
                                all_matches.append((False,constant))
                            else:
                                all_matches[-1] = (False,all_matches[-1][0]+[constant])
                        subString.position += 1  
                        matchCount += 1 
            else:
                if index == tracer:
                    all_matches.append( (False,[l for l in self.letters[tracer:index+1]]) )
                else:
                    all_matches[-1] = (False,[l for l in self.letters[tracer:index+1]])
            self.position = index
        return [(am[0],"".join(am[1]) ) for am in all_matches ]
         
    def object(self,index):
        return Letter(self.letters[index])

    def singleton(self,index):
        return Letter(self.letters[index],singleton = True)
     
    def __getitem__(self, index):
        return_value = None
        if isinstance(index, slice):
            if self.string:
                return_value = "".join(self.letters[index.start:index.stop:index.step])
            else:
                return_value = "".join(self.letters[index.start:index.stop:index.step])
        else:
            return_value = self.letters[index]

        if self.output:
            return String(return_value)
        else:
            if self.inplace:
                pass
            else:
                return return_value

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            start, stop, step =  index.indices(len(self.letters))   
            previous_value = self.letters
            if not isinstance(value, String):
                other = String(value,singleton = True)
            previous_value[start:stop:step] = other.letters
            self.string = "".join(previous_value)   
        else:
            previous_value = self.letters 
            previous_value[index] = value
            self.string = "".join(previous_value)  
           
    def __delattr__(self):
        del self

    def __iter__(self):
        return iter(self.letters)
    
    def __len__(self):
        return len(self.letters)

    def __contains__(self, other):        
        if not isinstance(other,str):
            other = str(other)
        if self. unicodes_list in other:
            return True
        else:
            return False

    def reverse(self):
        return self.letters[::-1]