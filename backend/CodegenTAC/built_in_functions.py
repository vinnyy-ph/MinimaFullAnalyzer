class MinimaBultins:
    BUILTIN_FUNCTIONS = {
        'length': {
            'params': 1,
            'return_type': 'integer',
            'implementation': lambda interpreter, args: MinimaBultins._length(interpreter, args)
        },
        'uppercase': {
            'params': 1,
            'return_type': 'text',
            'implementation': lambda interpreter, args: MinimaBultins._uppercase(interpreter, args)
        },
        'lowercase': {
            'params': 1,
            'return_type': 'text',
            'implementation': lambda interpreter, args: MinimaBultins._lowercase(interpreter, args)
        },
        'max': {
            'params': 1,
            'return_type': 'unknown',
            'implementation': lambda interpreter, args: MinimaBultins._max(interpreter, args)
        },
        'min': {
            'params': 1,
            'return_type': 'unknown',
            'implementation': lambda interpreter, args: MinimaBultins._min(interpreter, args)
        },
        'sorted': {
            'params': -1,  # -1 indicates variable arguments (1 or 2 parameters)
            'return_type': 'list',
            'implementation': lambda interpreter, args: MinimaBultins._sorted(interpreter, args)
        },
        'reverse': {
            'params': 1,
            'return_type': 'unknown',
            'implementation': lambda interpreter, args: MinimaBultins._reverse(interpreter, args)
        },
        'abs': {
            'params': 1,
            'return_type': 'unknown',
            'implementation': lambda interpreter, args: MinimaBultins._abs(interpreter, args)
        },
        'sum': {
            'params': 1,
            'return_type': 'unknown',
            'implementation': lambda interpreter, args: MinimaBultins._sum(interpreter, args)
        },
        'contains': {
            'params': 2,
            'return_type': 'state',
            'implementation': lambda interpreter, args: MinimaBultins._contains(interpreter, args)
        },
        'indexOf': {
            'params': 2,
            'return_type': 'integer',
            'implementation': lambda interpreter, args: MinimaBultins._indexOf(interpreter, args)
        },
        'join': {
            'params': 2,
            'return_type': 'text',
            'implementation': lambda interpreter, args: MinimaBultins._join(interpreter, args)
        },
        'slice': {
            'params': 3,
            'return_type': 'list',
            'implementation': lambda interpreter, args: MinimaBultins._slice(interpreter, args)
        },
        'unique': {
            'params': 1,
            'return_type': 'list',
            'implementation': lambda interpreter, args: MinimaBultins._unique(interpreter, args)
        },
        'type': {
            'params': 1,
            'return_type': 'text',
            'implementation': lambda interpreter, args: MinimaBultins._type(interpreter, args)
        },
        'isqrt': {
            'params': 1,
            'return_type': 'integer',
            'implementation': lambda interpreter, args: MinimaBultins._isqrt(interpreter, args)
        },
        'pow': {
            'params': 2,
            'return_type': 'unknown',
            'implementation': lambda interpreter, args: MinimaBultins._pow(interpreter, args)
        },
        'factorial': {
            'params': 1,
            'return_type': 'integer',
            'implementation': lambda interpreter, args: MinimaBultins._factorial(interpreter, args)
        },
        'ceil': {
            'params': 1,
            'return_type': 'integer',
            'implementation': lambda interpreter, args: MinimaBultins._ceil(interpreter, args)
        },
        'floor': {
            'params': 1,
            'return_type': 'integer',
            'implementation': lambda interpreter, args: MinimaBultins._floor(interpreter, args)
        },
        'round': {
            'params': -1,  # -1 indicates variable arguments (1 or 2 parameters)
            'return_type': 'unknown',
            'implementation': lambda interpreter, args: MinimaBultins._round(interpreter, args)
        },
    }
    
    @staticmethod
    def get_builtin_functions():
        """
        Returns the dictionary of built-in functions.
        Used by both the semantic analyzer and interpreter.
        """
        return MinimaBultins.BUILTIN_FUNCTIONS
    
    @staticmethod
    def get_builtin_implementations():
        """
        Returns a dictionary mapping function names to their implementations.
        Used by the interpreter.
        """
        return {name: func['implementation'] 
                for name, func in MinimaBultins.BUILTIN_FUNCTIONS.items()}
    
    @staticmethod
    def get_builtin_metadata():
        """
        Returns a dictionary mapping function names to their metadata.
        Used by the semantic analyzer.
        """
        return {name: {'params': func['params'], 'return_type': func['return_type']}
                for name, func in MinimaBultins.BUILTIN_FUNCTIONS.items()}
    
    @staticmethod
    def _length(interpreter, args):
        """
        Minima's length() function - equivalent to Python's len()
        Returns the length of a list or string
        """
        if not args:
            raise ValueError("length() requires 1 argument")
        
        value = args[0]
        if isinstance(value, list):
            return len(value)
        elif isinstance(value, str):
            return len(value)
        elif isinstance(value, (int, float)):
            # Convert numeric values to strings to get their length
            return len(str(value))
        else:
            raise ValueError(f"Cannot get length of non-sequence: {value}")
        
    @staticmethod
    def _uppercase(interpreter, args):
        """
        Minima's uppercase() function - converts text to uppercase
        """
        if not args:
            raise ValueError("uppercase() requires 1 argument")
        
        value = args[0]
        if isinstance(value, str):
            return value.upper()
        else:
            return str(value).upper()

    @staticmethod
    def _lowercase(interpreter, args):
        """
        Minima's lowercase() function - converts text to lowercase
        """
        if not args:
            raise ValueError("lowercase() requires 1 argument")
        
        value = args[0]
        if isinstance(value, str):
            return value.lower()
        else:
            return str(value).lower()
    
    @staticmethod
    def _max(interpreter, args):
        """
        Minima's max() function - equivalent to Python's max()
        Returns the largest item in a list or text
        """
        if not args:
            raise ValueError("max() requires at least 1 argument")
        
        value = args[0]
        if isinstance(value, list):
            if not value:
                raise ValueError("max() argument is an empty list")
            
            # Handle lists of numbers or text
            return max(value)
        elif isinstance(value, str):
            if not value:
                raise ValueError("max() argument is an empty string")
            return max(value)
        elif isinstance(value, (int, float)):
            # If a single number is provided, return it
            return value
        else:
            raise ValueError(f"max() argument must be a list, text, or number: {value}")
    
    @staticmethod
    def _min(interpreter, args):
        """
        Minima's min() function - equivalent to Python's min()
        Returns the smallest item in a list or text
        """
        if not args:
            raise ValueError("min() requires at least 1 argument")
        
        value = args[0]
        if isinstance(value, list):
            if not value:
                raise ValueError("min() argument is an empty list")
            
            # Handle lists of numbers or text
            return min(value)
        elif isinstance(value, str):
            if not value:
                raise ValueError("min() argument is an empty string")
            return min(value)
        elif isinstance(value, (int, float)):
            # If a single number is provided, return it
            return value
        else:
            raise ValueError(f"min() argument must be a list, text, or number: {value}")
    
    @staticmethod
    def _sorted(interpreter, args):
        """
        Minima's sorted() function with optional direction
        Returns a sorted list from the items in the provided list or text
        
        sorted(collection) - sorts in ascending order
        sorted(collection, YES/NO) - sorts in ascending (YES) or descending (NO) order
        """
        if not args or len(args) < 1 or len(args) > 2:
            raise ValueError("sorted() requires 1 or 2 arguments: collection and optional direction (YES/NO)")
        
        value = args[0]
        
        # Default to ascending (reverse=False)
        reverse = False
        
        # If second argument is provided, check for various representations of boolean values
        if len(args) == 2:
            direction = args[1]
            
            # Accept YES/NO, 1/0, and True/False as valid direction indicators
            if direction in ["YES", True, 1]:
                reverse = False  # Ascending
            elif direction in ["NO", False, 0]:
                reverse = True   # Descending
            else:
                raise ValueError("Second argument of sorted() must be YES/NO (or equivalent boolean/integer value)")
        
        if isinstance(value, list):
            # Sort the list with the specified direction
            try:
                return sorted(value, reverse=reverse)
            except TypeError:
                raise ValueError("Cannot sort list with mixed types")
        elif isinstance(value, str):
            # Sort the characters in the string and return as a list
            return sorted(value, reverse=reverse)
        else:
            raise ValueError(f"sorted() argument must be a list or text: {value}")
    
    @staticmethod
    def _reverse(interpreter, args):
        """
        Minima's reverse() function
        Returns a reversed version of the list or text
        """
        if not args:
            raise ValueError("reverse() requires 1 argument")
        
        value = args[0]
        if isinstance(value, list):
            # Return a reversed copy of the list
            return list(reversed(value))
        elif isinstance(value, str):
            # Reverse the string
            return value[::-1]
        else:
            raise ValueError(f"reverse() argument must be a list or text: {value}")
    
    @staticmethod
    def _abs(interpreter, args):
        """
        Minima's abs() function - equivalent to Python's abs()
        Returns the absolute value of a number
        """
        if not args:
            raise ValueError("abs() requires 1 argument")
        
        value = args[0]
        if isinstance(value, (int, float)):
            return abs(value)
        else:
            raise ValueError(f"abs() argument must be a number: {value}")
        
    @staticmethod
    def _sum(interpreter, args):
        """
        Minima's sum() function - equivalent to Python's sum()
        Returns the sum of all numbers in a list
        """
        if not args:
            raise ValueError("sum() requires 1 argument")
        
        value = args[0]
        if isinstance(value, list):
            if not value:
                return 0
            
            try:
                # Only sum numeric values
                numeric_values = [v for v in value if isinstance(v, (int, float))]
                return sum(numeric_values)
            except TypeError:
                raise ValueError("Cannot sum non-numeric values in list")
        elif isinstance(value, (int, float)):
            return value
        else:
            raise ValueError(f"sum() argument must be a list or number: {value}")
    
    @staticmethod
    def _contains(interpreter, args):
        """
        Minima's contains() function 
        Check if an item exists in a list or text
        Returns YES or NO
        """
        if len(args) != 2:
            raise ValueError("contains() requires 2 arguments: collection and item")
        
        collection = args[0]
        item = args[1]
        
        if isinstance(collection, list):
            result = item in collection
        elif isinstance(collection, str):
            result = str(item) in collection
        else:
            raise ValueError(f"First argument of contains() must be a list or text: {collection}")
        
        return "YES" if result else "NO"
    
    @staticmethod
    def _indexOf(interpreter, args):
        """
        Minima's indexOf() function
        Find the index of an item in a list or text
        Returns the index or -1 if not found
        """
        if len(args) != 2:
            raise ValueError("indexOf() requires 2 arguments: collection and item")
        
        collection = args[0]
        item = args[1]
        
        try:
            if isinstance(collection, list):
                return collection.index(item) if item in collection else -1
            elif isinstance(collection, str):
                return collection.find(str(item))
            else:
                raise ValueError(f"First argument of indexOf() must be a list or text: {collection}")
        except ValueError:
            return -1
    
    @staticmethod
    def _join(interpreter, args):
        """
        Minima's join() function
        Join a list of items into a string with a specified separator
        """
        if len(args) != 2:
            raise ValueError("join() requires 2 arguments: separator and list")
        
        separator = args[0]
        collection = args[1]
        
        if not isinstance(separator, str):
            separator = str(separator)
            
        if isinstance(collection, list):
            # Convert all items to strings
            string_items = [str(item) for item in collection]
            return separator.join(string_items)
        else:
            raise ValueError(f"Second argument of join() must be a list: {collection}")
    
    @staticmethod
    def _slice(interpreter, args):
        """
        Minima's slice() function
        Extract a portion of a list or text
        slice(collection, start, end) - end is exclusive
        """
        if len(args) != 3:
            raise ValueError("slice() requires 3 arguments: collection, start, end")
        
        collection = args[0]
        start = args[1]
        end = args[2]
        
        if not isinstance(start, int):
            raise ValueError(f"Start index must be an integer: {start}")
        if not isinstance(end, int):
            raise ValueError(f"End index must be an integer: {end}")
        
        if isinstance(collection, list):
            return collection[start:end]
        elif isinstance(collection, str):
            return collection[start:end]
        else:
            raise ValueValueError(f"First argument of slice() must be a list or text: {collection}")
    
    @staticmethod
    def _unique(interpreter, args):
        """
        Minima's unique() function
        Return a list of unique elements from a list, preserving order
        """
        if not args:
            raise ValueError("unique() requires 1 argument")
        
        value = args[0]
        if isinstance(value, list):
            # Use dict.fromkeys to preserve order in Python 3.7+
            return list(dict.fromkeys(value))
        elif isinstance(value, str):
            # For strings, return list of unique characters
            return list(dict.fromkeys(value))
        else:
            raise ValueValueError(f"unique() argument must be a list or text: {value}")
        
    @staticmethod
    def _type(interpreter, args):
        """
        Minima's type() function
        Returns the type of a value as a string
        """
        if not args:
            raise ValueError("type() requires 1 argument")
        
        value = args[0]
        
        # Special handling for state literals and their numeric equivalents
        if value == "YES" or value == "NO" or value is True or value is False:
            return "state"
        # Integer 1 and 0 might be from state literals, but only identify as state if explicitly YES/NO
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "point"
        elif isinstance(value, str):
            return "text"
        elif isinstance(value, list):
            return "list"
        elif value is None:
            return "empty"
        else:
            return "unknown"

    @staticmethod
    def _isqrt(interpreter, args):
        """
        Minima's isqrt() function
        Returns the integer square root of a number (largest integer i such that i*i ≤ n)
        """
        if not args:
            raise ValueError("isqrt() requires 1 argument")
        
        value = args[0]
        if not isinstance(value, (int, float)):
            raise ValueError(f"isqrt() argument must be a number: {value}")
            
        if value < 0:
            raise ValueError(f"isqrt() cannot compute square root of negative number: {value}")
            
        # Convert to integer and use integer square root algorithm
        import math
        return int(math.isqrt(int(value))) if isinstance(value, int) else int(math.sqrt(value))
    
    @staticmethod
    def _pow(interpreter, args):
        """
        Minima's pow() function
        Raises first argument to the power of the second argument
        """
        if len(args) != 2:
            raise ValueError("pow() requires 2 arguments: base and exponent")
        
        base = args[0]
        exponent = args[1]
        
        if not isinstance(base, (int, float)):
            raise ValueError(f"First argument of pow() must be a number: {base}")
            
        if not isinstance(exponent, (int, float)):
            raise ValueError(f"Second argument of pow() must be a number: {exponent}")
        
        try:
            result = base ** exponent
            # Validate the result fits within Minima's range
            return interpreter.validate_number(result)
        except OverflowError:
            raise ValueError(f"pow() result is too large: {base}^{exponent}")
    
    @staticmethod
    def _factorial(interpreter, args):
        """
        Minima's factorial() function
        Returns the factorial of a non-negative integer
        """
        if not args:
            raise ValueError("factorial() requires 1 argument")
        
        value = args[0]
        if not isinstance(value, (int, float)):
            raise ValueError(f"factorial() argument must be a number: {value}")
            
        if isinstance(value, float) and not value.is_integer():
            raise ValueError(f"factorial() argument must be an integer: {value}")
            
        n = int(value)
        if n < 0:
            raise ValueError(f"factorial() argument must be non-negative: {n}")
            
        if n > 20:  # Safeguard against extremely large factorials
            raise ValueError(f"factorial() argument is too large: {n}")
        
        result = 1
        for i in range(2, n + 1):
            result *= i
            
        # Validate the result fits within Minima's range
        return interpreter.validate_number(result)
    
    @staticmethod
    def _ceil(interpreter, args):
        """
        Minima's ceil() function
        Returns the smallest integer greater than or equal to the argument
        """
        if not args:
            raise ValueError("ceil() requires 1 argument")
        
        value = args[0]
        if not isinstance(value, (int, float)):
            raise ValueError(f"ceil() argument must be a number: {value}")
            
        import math
        return math.ceil(value)
    
    @staticmethod
    def _floor(interpreter, args):
        """
        Minima's floor() function
        Returns the largest integer less than or equal to the argument
        """
        if not args:
            raise ValueError("floor() requires 1 argument")
        
        value = args[0]
        if not isinstance(value, (int, float)):
            raise ValueError(f"floor() argument must be a number: {value}")
            
        import math
        return math.floor(value)
    
    @staticmethod
    def _round(interpreter, args):
        """
        Minima's round() function
        Rounds a number to the nearest integer or to specified decimal places
        
        round(number) - rounds to nearest integer
        round(number, places) - rounds to specified number of decimal places
        """
        if not args or len(args) < 1 or len(args) > 2:
            raise ValueError("round() requires 1 or 2 arguments: number and optional decimal places")
        
        value = args[0]
        if not isinstance(value, (int, float)):
            raise ValueError(f"First argument of round() must be a number: {value}")
        
        decimal_places = 0
        if len(args) == 2:
            places = args[1]
            if not isinstance(places, int):
                raise ValueError(f"Second argument of round() must be an integer: {places}")
            decimal_places = places
        
        # If decimal_places is 0, return an integer
        if decimal_places == 0:
            return round(value)
        
        # Otherwise, return a point (float) with specified decimal places
        rounded = round(value, decimal_places)
        
        # Ensure the result is within Minima's range
        return interpreter.validate_number(rounded)