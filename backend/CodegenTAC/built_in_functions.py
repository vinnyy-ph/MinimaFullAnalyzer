class MinimaBultins:
    # Dictionary of all built-in functions with their metadata
    BUILTIN_FUNCTIONS = {
        'length': {
            'params': 1,
            'return_type': 'integer',
            'implementation': lambda interpreter, args: MinimaBultins._length(interpreter, args)
        }
        # Add more built-ins here following the same pattern:
        # 'function_name': {
        #     'params': number_of_params,
        #     'return_type': 'return_type',
        #     'implementation': lambda interpreter, args: MinimaBultins._function_name(interpreter, args)
        # }
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