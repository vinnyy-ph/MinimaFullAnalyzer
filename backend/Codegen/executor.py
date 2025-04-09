# executor.py
import sys
import io
from contextlib import redirect_stdout

class CodeExecutor:
    def __init__(self):
        self.output_buffer = io.StringIO()
        
    def execute(self, code):
        """Execute the generated Python code safely and capture output"""
        # Redirect stdout to our buffer
        with redirect_stdout(self.output_buffer):
            try:
                # Execute the code in a restricted environment
                # For now, just execute the code directly - in a real system,
                # you might want to use a sandboxed environment
                exec(code, {"__builtins__": __builtins__})
                execution_result = True
                error_message = None
            except Exception as e:
                execution_result = False
                error_message = f"Runtime Error: {type(e).__name__}: {str(e)}"
                print(error_message)
        
        # Get the captured output
        output = self.output_buffer.getvalue()
        self.output_buffer = io.StringIO()  # Reset buffer for next execution
        
        return {
            "success": execution_result,
            "output": output,
            "error": error_message
        }