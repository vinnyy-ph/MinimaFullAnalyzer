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
            'params': 1,
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
        if isinstance(value, (list, str)):
            return len(value)
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
        Minima's sorted() function - equivalent to Python's sorted()
        Returns a sorted list from the items in the provided list or text
        """
        if not args:
            raise ValueError("sorted() requires 1 argument")
        
        value = args[0]
        if isinstance(value, list):
            # Sort the list
            try:
                return sorted(value)
            except TypeError:
                raise ValueError("Cannot sort list with mixed types")
        elif isinstance(value, str):
            # Sort the characters in the string and return as a list
            return sorted(value)
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
            raise ValueError(f"First argument of slice() must be a list or text: {collection}")
    
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
            raise ValueError(f"unique() argument must be a list or text: {value}")
        
    @staticmethod
    def _type(interpreter, args):
        """
        Minima's type() function
        Returns the type of a value as a string
        """
        if not args:
            raise ValueError("type() requires 1 argument")
        
        value = args[0]
        if isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "point"
        elif isinstance(value, str):
            if value in ["YES", "NO"]:
                return "state"
            return "text"
        elif isinstance(value, list):
            return "list"
        elif value is None:
            return "empty"
        else:
            return "unknown"