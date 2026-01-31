import tokenize
from io import BytesIO
import sys
import os

class TamilPythonCompiler:
    def __init__(self):
        # Mapping Tamil keywords to Python keywords
        self.translation_map = {
            # --- Control Flow ---
            'எனில்': 'if',
            'ஆனால்': 'elif',
            'இல்லை': 'else',
            'சுற்று': 'for',
            'வரை': 'while',
            'இல்': 'in',
            'நிறுத்து': 'break',
            'தொடர்': 'continue',
            'விடு': 'pass',
            'திருப்பு': 'return',

            # --- Operators ---
            'மற்றும்': 'and',
            'அல்லது': 'or',
            'இல்லாத': 'not',
            'ஆக': 'as',
            'என்பது': 'is',

            # --- Data & Types ---
            'உண்மை': 'True',
            'பொய்': 'False',
            'ஏதுமில்லை': 'None',
            'உலகளாவிய': 'global',

            # --- Structure ---
            'செயல்': 'def',
            'வகுப்பு': 'class',
            'சுயம்': 'self',
            'இருந்து': 'from',
            'இறக்குமதி': 'import',

            # --- Error Handling ---
            'முயற்சி': 'try',
            'பிழை': 'except',
            'இறுதியாக': 'finally',
            'எழுப்': 'raise',

            # --- Built-ins ---
            'பதி': 'print',
            'உள்ளிடு': 'input',
            'தொடர்வெளியீடு': 'range',
            'நீளம்': 'len',
            'முழுஎண்': 'int',
            'சரம்': 'str',
            'பட்டியல்': 'list'
        }

    def translate_and_run(self, tamil_code):
        # 1. Convert string to byte stream for tokenizer
        tokens = list(tokenize.tokenize(BytesIO(tamil_code.encode('utf-8')).readline))
        
        new_tokens = []
        for token in tokens:
            # FIX: If the user types 'அமை', we simply skip it. 
            # This turns "அமை x = 10" into "x = 10" automatically.
            if token.string == 'அமை':
                continue

            if token.type == tokenize.NAME:
                if token.string in self.translation_map:
                    new_token = (token.type, self.translation_map[token.string])
                else:
                    new_token = (token.type, token.string)
            else:
                new_token = (token.type, token.string)
            
            new_tokens.append(new_token)

        # 2. Reconstruct the code
        python_code = tokenize.untokenize(new_tokens).decode('utf-8')
        
        # 3. Execute
        try:
            # We pass globals() to ensure imports (like math) work correctly
            exec(python_code, globals())
        except Exception as e:
            print(f"\n❌ பிழை (Error): {e}")

# --- MAIN RUNNER ---
# ... (Keep the TamilPythonCompiler class exactly as it is) ...

def main():
    import sys
    import os

    # 1. Check arguments
    if len(sys.argv) < 2:
        print("ℹ️  Usage: tamilpp <filename.tpp>")
        sys.exit(1)

    filename = sys.argv[1]
    compiler = TamilPythonCompiler()

    # 2. Check file existence
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                code = f.read()
            # Optional: Don't show the translation when running professionally
            print(f"📂 Running file: {filename} ...") 
            compiler.translate_and_run(code)
        except Exception as e:
            print(f"❌ Error reading file: {e}")
    else:
        print(f"❌ பிழை: The file '{filename}' was not found.")

if __name__ == "__main__":
    main()