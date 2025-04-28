// Utility to fetch and cache built-in functions
let cachedBuiltinFunctions = null;

export const fetchBuiltinFunctions = async () => {
  if (!cachedBuiltinFunctions) {
    try {
      // Try with relative URL first
      let response = await fetch('/api/builtin-functions');
      
      // If that fails, try with absolute URL
      if (!response.ok) {
        response = await fetch('http://127.0.0.1:5000/api/builtin-functions');
      }
      
      if (response.ok) {
        cachedBuiltinFunctions = await response.json();
        console.log('Loaded built-in functions:', cachedBuiltinFunctions);
      } else {
        console.error('Failed to fetch built-in functions');
        cachedBuiltinFunctions = [];
      }
    } catch (error) {
      console.error('Error fetching built-in functions:', error);
      // Fallback to hardcoded list of built-ins if API fails
      cachedBuiltinFunctions = [
        'length', 'uppercase', 'lowercase', 'max', 'min', 'sorted', 
        'reverse', 'abs', 'sum', 'contains', 'indexOf', 'join', 
        'slice', 'unique', 'type','isqrt', 'pow', 'factorial', 'ceil', 'floor', 'round'
      ];
    }
  }
  return cachedBuiltinFunctions || [];
};