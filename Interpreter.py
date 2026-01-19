from sly import Lexer, Parser

# --- 1. LEXER (Đã sửa lỗi thiếu toán tử so sánh) ---
class JoulLexer(Lexer):
    tokens = {
        NAME, NUMBER, STRING,
        PLUS, MINUS, TIMES, DIVIDE, ASSIGN,
        LPAREN, RPAREN, LBRACE, RBRACE, SEMI, COMMA,
        IF, ELSE, WHILE, FUNC, PRINT, RETURN,
        GT, LT, EQ, NE, GE, LE  # <--- THÊM: NE (!=), GE (>=), LE (<=)
    }

    # Bỏ qua Space, Tab và Carriage Return (cho Windows)
    ignore = ' \t\r'

    # Token toán tử (SLY tự sắp xếp theo độ dài, nên <= sẽ được ưu tiên hơn <)
    PLUS    = r'\+'
    MINUS   = r'-'
    TIMES   = r'\*'
    DIVIDE  = r'/'
    EQ      = r'=='
    NE      = r'!='  # <--- Mới
    LE      = r'<='  # <--- Mới (Khắc phục lỗi của bạn)
    GE      = r'>='  # <--- Mới
    ASSIGN  = r'='
    LPAREN  = r'\('
    RPAREN  = r'\)'
    LBRACE  = r'\{'
    RBRACE  = r'\}'
    SEMI    = r';'
    COMMA   = r','
    GT      = r'>'
    LT      = r'<'

    # String
    @_(r'\"[^\"]*\"')
    def STRING(self, t):
        t.value = t.value[1:-1]
        return t

    # Identifier & Keywords
    NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
    
    identifiers = {
        'if': IF,
        'else': ELSE,
        'while': WHILE,
        'func': FUNC,
        'print': PRINT,
        'return': RETURN
    }

    def NAME(self, t):
        t.type = self.identifiers.get(t.value, 'NAME')
        return t

    @_(r'\d+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    @_(r'\#.*')
    def ignore_comment(self, t):
        pass

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    def error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {self.lineno}")
        self.index += 1

# --- 2. PARSER (Đã cập nhật grammar cho <=, >=, !=) ---
class JoulParser(Parser):
    tokens = JoulLexer.tokens

    precedence = (
        ('left', EQ, NE, GT, LT, GE, LE), # <--- Cập nhật độ ưu tiên
        ('left', PLUS, MINUS),
        ('left', TIMES, DIVIDE),
        ('right', UMINUS),
    )

    def __init__(self):
        self.env = {}

    # --- Program Structure ---
    @_('statements')
    def program(self, p):
        return p.statements

    @_('statement statements')
    def statements(self, p):
        return [p.statement] + p.statements

    @_('')
    def statements(self, p):
        return []

    # --- Statements ---
    @_('NAME ASSIGN expr SEMI')
    def statement(self, p):
        return ('assign', p.NAME, p.expr)

    @_('PRINT expr SEMI')
    def statement(self, p):
        return ('print_stmt', p.expr)

    @_('RETURN expr SEMI')
    def statement(self, p):
        return ('return_stmt', p.expr)

    @_('IF LPAREN expr RPAREN LBRACE statements RBRACE')
    def statement(self, p):
        return ('if_stmt', p.expr, p.statements, [])

    @_('IF LPAREN expr RPAREN LBRACE statements RBRACE ELSE LBRACE statements RBRACE')
    def statement(self, p):
        return ('if_stmt', p.expr, p.statements0, p.statements1)

    @_('WHILE LPAREN expr RPAREN LBRACE statements RBRACE')
    def statement(self, p):
        return ('while_stmt', p.expr, p.statements)

    @_('FUNC NAME LPAREN parameters RPAREN LBRACE statements RBRACE')
    def statement(self, p):
        return ('func_def', p.NAME, p.parameters, p.statements)
    
    @_('FUNC NAME LPAREN RPAREN LBRACE statements RBRACE')
    def statement(self, p):
        return ('func_def', p.NAME, [], p.statements)

    @_('expr SEMI')
    def statement(self, p):
        return ('expr_stmt', p.expr)

    # --- Params & Args ---
    @_('NAME')
    def parameters(self, p):
        return [p.NAME]

    @_('NAME COMMA parameters')
    def parameters(self, p):
        return [p.NAME] + p.parameters

    @_('expr')
    def arguments(self, p):
        return [p.expr]

    @_('expr COMMA arguments')
    def arguments(self, p):
        return [p.expr] + p.arguments

    # --- Expressions ---
    # Gộp tất cả phép toán 2 ngôi lại cho gọn
    @_('expr PLUS expr',
       'expr MINUS expr',
       'expr TIMES expr',
       'expr DIVIDE expr',
       'expr EQ expr',
       'expr NE expr',  # !=
       'expr GT expr',
       'expr LT expr',
       'expr GE expr',  # >=
       'expr LE expr')  # <=
    def expr(self, p):
        return (p[1], p.expr0, p.expr1) 

    @_('MINUS expr %prec UMINUS')
    def expr(self, p):
        return ('uminus', p.expr)

    @_('LPAREN expr RPAREN')
    def expr(self, p):
        return p.expr

    @_('NUMBER')
    def expr(self, p):
        return ('number', p.NUMBER)

    @_('STRING')
    def expr(self, p):
        return ('string', p.STRING)

    @_('NAME')
    def expr(self, p):
        return ('variable', p.NAME)

    @_('NAME LPAREN arguments RPAREN')
    def expr(self, p):
        return ('func_call', p.NAME, p.arguments)

    @_('NAME LPAREN RPAREN')
    def expr(self, p):
        return ('func_call', p.NAME, [])

    def error(self, p):
        if p:
            print(f"Syntax error at line {p.lineno}, token={p.type}, value='{p.value}'")
        else:
            print("Syntax error at EOF")

# --- 3. INTERPRETER (Cập nhật xử lý logic <=, >=, !=) ---
class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class JoulInterpreter:
    def __init__(self):
        self.env = {}
        self.functions = {}

    def walk(self, node):
        if node is None: return None
        
        if isinstance(node, list):
            res = None
            for stmt in node:
                res = self.walk(stmt)
            return res

        tag = node[0]

        if tag == 'number': return node[1]
        if tag == 'string': return node[1]
        if tag == 'variable':
            return self.env.get(node[1], 0)

        if tag == 'expr_stmt':
            return self.walk(node[1]) 

        if tag == 'assign':
            self.env[node[1]] = self.walk(node[2])
            return None

        if tag == 'print_stmt':
            print(self.walk(node[1]))
            return None

        if tag == 'if_stmt':
            if self.walk(node[1]):
                return self.walk(node[2])
            elif node[3]:
                return self.walk(node[3])
            return None

        if tag == 'while_stmt':
            while self.walk(node[1]):
                self.walk(node[2])
            return None

        # --- Operators ---
        if tag == '+': 
            left = self.walk(node[1])
            right = self.walk(node[2])
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
            
        if tag == '-': return self.walk(node[1]) - self.walk(node[2])
        if tag == '*': return self.walk(node[1]) * self.walk(node[2])
        if tag == '/': return self.walk(node[1]) / self.walk(node[2])
        
        # So sánh
        if tag == '==': return self.walk(node[1]) == self.walk(node[2])
        if tag == '!=': return self.walk(node[1]) != self.walk(node[2])
        if tag == '>':  return self.walk(node[1]) > self.walk(node[2])
        if tag == '<':  return self.walk(node[1]) < self.walk(node[2])
        if tag == '>=': return self.walk(node[1]) >= self.walk(node[2])
        if tag == '<=': return self.walk(node[1]) <= self.walk(node[2]) # <--- Logic cho <=

        if tag == 'uminus': return -self.walk(node[1])

        # --- Functions ---
        if tag == 'func_def':
            self.functions[node[1]] = (node[2], node[3])
            return None

        if tag == 'func_call':
            name = node[1]
            args = [self.walk(a) for a in node[2]]
            
            if name not in self.functions:
                print(f"Error: Function '{name}' not defined.")
                return None
            
            params, body = self.functions[name]
            
            if len(args) != len(params):
                print(f"Error: Function '{name}' expects {len(params)} args, got {len(args)}.")
                return None

            # Scope mới
            old_env = self.env.copy()
            for p, a in zip(params, args):
                self.env[p] = a
            
            result = None
            try:
                result = self.walk(body) # Gán kết quả của lệnh cuối cùng
            except ReturnException as e:
                result = e.value
            
            self.env = old_env
            return result
        
        if tag == 'return_stmt':
            val = self.walk(node[1])
            raise ReturnException(val)

        return None

