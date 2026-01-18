from sly import Lexer,Parser

# Bo chia cac tu ngu thanh cac code
class JoulLexer(Lexer):
    # Dinh nghia mot so tu khoa cho ngon ngu
    tokens = {NAME,NUMBER,PLUS,MINUS,TIMES,DIVIDE,ASSIGN, PRINT, STRING
              ,LPAREN,RPAREN, SEMI}

    ignore = r' \t'

    # Bo qua comment
    ignore_comment = r'\#.'

    PRINT = r'print'
    NAME = r'[a-zA-Z_][a-zA-Z0-9]*'
    NUMBER = r'\d+'

    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIVIDE = r'/'
    ASSIGN = r'='

    LPAREN = r"\("
    RPAREN = r"\)"

    SEMI = r';'

    @_(r'\"[^\"]*\"')
    def STRING(self, t):
        t.value = t.value[1:-1]
        return t
    
    @_(r'\n+')
    def ignore_newline(self,t):
        self.lineno += len(t.value)

    def error(self,t):
        print("Illegal Character '%s'" % t.value[0])
        self.index += 1

class JoulParser(Parser):
    tokens = JoulLexer.tokens

    def __init__(self):
        self.env = {}
        self.error_occurred = False

    precedence = (
        ('left', PLUS, MINUS),
        ('left',TIMES, DIVIDE),
        ('right', UMINUS),
    )

    # Gom tất cả các lệnh thành một danh sách các AST Nodes
    @_('statement SEMI statements')
    def statements(self, p):
        return [p.statement] + p.statements

    @_('statement')
    def statements(self, p):
        return [p.statement]
    
    @_('statement SEMI')
    def statements(self, p):
        return [p.statement]

    @_('PRINT expr')
    def statement(self,p):
        return ('print_stmt', p.expr)

    @_('NAME ASSIGN expr')
    def statement(self, p):
        return ('assign',p.NAME,p.expr)

    @_('expr')
    def statement(self,p):
        return ('expr_stmt', p.expr)

    # Them kha nang cong 2 gia tri cung loai
    @_('expr PLUS expr')
    def expr(self,p):
        return ('plus',p.expr0,p.expr1)
    
    @_('expr MINUS expr')
    def expr(self,p):
        return ('minus',p.expr0,p.expr1)
    
    @_('expr TIMES expr')
    def expr(self,p):
        return ('times',p.expr0,p.expr1)
    
    @_('expr DIVIDE expr')
    def expr(self,p):
        return ('divide',p.expr0,p.expr1)
    
    @_('MINUS expr %prec UMINUS')
    def expr(self,p):
        return ('uminus',p.expr)
    
    @_('LPAREN expr RPAREN')
    def expr(self,p):
        return p.expr
    
    @_('NUMBER')
    def expr(self,p):
        return ('number',int(p.NUMBER))
    
    @_('NAME')
    def expr(self,p):
        return ('variable',p.NAME)
    
    @_('STRING')
    def expr(self,p):
        return ('string',p.STRING)

class JoulInterpreter:
    def __init__(self):
        self.env = {}
    
    def walk(self,node):
        if isinstance(node,list):
            result = None
            for stmt in node:
                result = self.walk(stmt)
            return result
        
        if node is None:
            return None
        
        tag = node[0]

        # -- CAC GIA TRI CO BAN --
        if tag == 'number':
            return node[1]
        if tag == 'string':
            return node[1]
        
        if tag == 'variable':
            var_name = node[1]
            if var_name in self.env:
                return self.env[var_name]
            else:
                print(f"Error: {var_name} isn't declare >:((")
                return 0
        
        if tag == 'expr_stmt':
            return self.walk(node[1])
        
        # --- XỬ LÝ PHÉP TOÁN ---
        if tag == 'plus':
            return self.walk(node[1]) + self.walk(node[2])
        
        if tag == 'minus':
            return self.walk(node[1]) - self.walk(node[2])
        
        if tag == 'times':
            return self.walk(node[1]) * self.walk(node[2])
        
        if tag == 'divide':
            try:
                return self.walk(node[1]) / self.walk(node[2])
            except ZeroDivisionError:
                print("Lỗi: Không thể chia cho 0!")
                return 0
        
        if tag == 'uminus':
            return -self.walk(node[1])

        # --- XỬ LÝ CÂU LỆNH (STATEMENTS) ---
        if tag == 'print_stmt':
            value = self.walk(node[1])
            print(value)
            return None

        if tag == 'assign':
            var_name = node[1]
            value = self.walk(node[2])
            self.env[var_name] = value
            return None
        
        return None