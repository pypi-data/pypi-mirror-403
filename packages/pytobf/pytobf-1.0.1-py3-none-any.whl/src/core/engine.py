from ..compiler.lexer import Lexer
from ..compiler.parser import Parser
from ..compiler.generator import Generator

class PyToBFEngine:
    def __init__(self):
        self.lexer = Lexer()
        self.parser = Parser()
        self.generator = Generator()

    def compile(self, source_code):
        tokens = self.lexer.tokenize(source_code)
        ast = self.parser.parse(tokens)
        return self.generator.generate(ast)

    def export_bf(self, source_code, output_file="out.bf"):
        bf_code = self.compile(source_code)
        with open(output_file, "w") as f:
            f.write(bf_code)
        print(f"[*] Código sagrado convertido e salvo em: {output_file}")
