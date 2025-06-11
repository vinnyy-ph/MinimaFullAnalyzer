// Utility to fetch and cache built-in functions
import { API_BASE_URL } from '../config/api';

let cachedBuiltinFunctions = null;

export const fetchBuiltinFunctions = async () => {
  if (!cachedBuiltinFunctions) {
    try {
      // Try with the configured API URL
      let response = await fetch(`${API_BASE_URL}/api/builtin-functions`);
      
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