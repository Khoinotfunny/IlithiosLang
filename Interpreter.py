from sly import Lexer, Parser

# --- 1. LEXER (Đã tối ưu) ---
class JoulLexer(Lexer):
    tokens = {
        NAME, NUMBER, STRING,
        PLUS, MINUS, TIMES, DIVIDE, ASSIGN,
        LPAREN, RPAREN, LBRACE, RBRACE, SEMI, COMMA,
        IF, ELSE, WHILE, FUNC, PRINT,
        GT, LT, EQ, RETURN
    }

    # Các ký tự bị bỏ qua (Space, Tab)
    ignore = ' \t'

    # Token đơn giản
    PLUS    = r'\+'
    MINUS   = r'-'
    TIMES   = r'\*'
    DIVIDE  = r'/'
    EQ      = r'=='
    ASSIGN  = r'='
    LPAREN  = r'\('
    RPAREN  = r'\)'
    LBRACE  = r'\{'
    RBRACE  = r'\}'
    SEMI    = r';'
    COMMA   = r','
    GT      = r'>'
    LT      = r'<'

    # Xử lý String (Cắt bỏ dấu ngoặc kép)
    @_(r'\"[^\"]*\"')
    def STRING(self, t):
        t.value = t.value[1:-1]
        return t

    # Xử lý Identifier và Keyword (Cách chuẩn nhất)
    # Định nghĩa NAME khớp với ID, sau đó kiểm tra xem nó có phải từ khóa không
    NAME = r'[a-zA-Z_][a-zA-Z0-9]*'
    
    # Mapping từ khóa
    identifiers = {
        'if': IF,
        'else': ELSE,
        'while': WHILE,
        'func': FUNC,
        'print': PRINT,
        'return': RETURN
    }

    # Xử lý tên biến (NAME) để map sang từ khóa nếu trùng
    def NAME(self, t):
        t.type = self.identifiers.get(t.value, 'NAME')
        return t

    # Xử lý số
    @_(r'\d+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    # Bỏ qua Comment (bắt đầu bằng #)
    @_(r'\#.*')
    def ignore_comment(self, t):
        pass

    # Đếm dòng (để báo lỗi chính xác)
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

    def error(self, t):
        print(f"Illegal character '{t.value[0]}' at line {self.lineno}")
        self.index += 1

# --- 2. PARSER (Đã thêm xử lý lỗi) ---
class JoulParser(Parser):
    tokens = JoulLexer.tokens

    # Thứ tự ưu tiên toán tử
    precedence = (
        ('left', EQ, GT, LT),
        ('left', PLUS, MINUS),
        ('left', TIMES, DIVIDE),
        ('right', UMINUS),
    )

    def __init__(self):
        self.env = {}

    # --- Cấu trúc chương trình ---
    @_('statements')
    def program(self, p):
        return p.statements

    @_('statement statements')
    def statements(self, p):
        return [p.statement] + p.statements

    @_('')
    def statements(self, p):
        return []

    # --- Các loại câu lệnh (Statements) ---
    
    # 1. Gán biến
    @_('NAME ASSIGN expr SEMI')
    def statement(self, p):
        return ('assign', p.NAME, p.expr)

    # 2. In ấn
    @_('PRINT expr SEMI')
    def statement(self, p):
        return ('print_stmt', p.expr)

    @_('RETURN expr SEMI')
    def statement(self, p):
        return ('return_stmt', p.expr)

    # 3. IF - ELSE (Sửa lại optional cho rõ ràng)
    @_('IF LPAREN expr RPAREN LBRACE statements RBRACE')
    def statement(self, p):
        return ('if_stmt', p.expr, p.statements, [])

    @_('IF LPAREN expr RPAREN LBRACE statements RBRACE ELSE LBRACE statements RBRACE')
    def statement(self, p):
        return ('if_stmt', p.expr, p.statements0, p.statements1)

    # 4. WHILE
    @_('WHILE LPAREN expr RPAREN LBRACE statements RBRACE')
    def statement(self, p):
        return ('while_stmt', p.expr, p.statements)

    # 5. Khai báo hàm
    @_('FUNC NAME LPAREN parameters RPAREN LBRACE statements RBRACE')
    def statement(self, p):
        return ('func_def', p.NAME, p.parameters, p.statements)
    
    # Hỗ trợ hàm không tham số: func name() {}
    @_('FUNC NAME LPAREN RPAREN LBRACE statements RBRACE')
    def statement(self, p):
        return ('func_def', p.NAME, [], p.statements)

    # 6. Biểu thức độc lập (VD: gọi hàm; )
    @_('expr SEMI')
    def statement(self, p):
        return ('expr_stmt', p.expr)

    # --- Tham số (Parameters) ---
    @_('NAME')
    def parameters(self, p):
        return [p.NAME]

    @_('NAME COMMA parameters')
    def parameters(self, p):
        return [p.NAME] + p.parameters

    # --- Đối số (Arguments) ---
    @_('expr')
    def arguments(self, p):
        return [p.expr]

    @_('expr COMMA arguments')
    def arguments(self, p):
        return [p.expr] + p.arguments

    # --- Biểu thức (Expressions) ---
    
    @_('expr PLUS expr',
       'expr MINUS expr',
       'expr TIMES expr',
       'expr DIVIDE expr',
       'expr EQ expr',
       'expr GT expr',
       'expr LT expr')
    def expr(self, p):
        return (p[1], p.expr0, p.expr1) # p[1] lấy tag operator (PLUS, EQ...)

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

    # Gọi hàm có tham số
    @_('NAME LPAREN arguments RPAREN')
    def expr(self, p):
        return ('func_call', p.NAME, p.arguments)

    # Gọi hàm không tham số
    @_('NAME LPAREN RPAREN')
    def expr(self, p):
        return ('func_call', p.NAME, [])

    # Bắt lỗi cú pháp
    def error(self, p):
        if p:
            print(f"Syntax error at line {p.lineno}, token={p.type}, value='{p.value}'")
        else:
            print("Syntax error at EOF")

# --- 3. INTERPRETER ---
# --- 3. INTERPRETER (Đã sửa lỗi tag toán tử) ---
class JoulInterpreter:
    def __init__(self):
        self.env = {}
        self.functions = {}

    def walk(self, node):
        if node is None: return None
        
        # Xử lý block code (danh sách lệnh)
        if isinstance(node, list):
            res = None
            for stmt in node:
                res = self.walk(stmt)
            return res

        tag = node[0]

        # --- XỬ LÝ GIÁ TRỊ ---
        if tag == 'number': return node[1]
        if tag == 'string': return node[1]
        if tag == 'variable':
            return self.env.get(node[1], 0)

        # --- XỬ LÝ CÂU LỆNH ---
        if tag == 'expr_stmt':
            return self.walk(node[1]) 

        if tag == 'assign':
            self.env[node[1]] = self.walk(node[2])
            return None

        if tag == 'print_stmt':
            val = self.walk(node[1])
            # Xử lý in True/False cho đẹp nếu cần, hoặc in thẳng giá trị
            print(str(val).lower() if isinstance(val, bool) else val)
            return None

        if tag == 'if_stmt':
            condition = self.walk(node[1])
            if condition:
                return self.walk(node[2])
            elif node[3]: # Else block
                return self.walk(node[3])
            return None

        if tag == 'while_stmt':
            while self.walk(node[1]):
                self.walk(node[2])
            return None

        # --- XỬ LÝ TOÁN TỬ (Đã sửa để khớp với Parser) ---
        # Parser trả về ký tự: +, -, *, /, ==, >, <
        
        if tag == '+': 
            left = self.walk(node[1])
            right = self.walk(node[2])
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
            
        if tag == '-': return self.walk(node[1]) - self.walk(node[2])
        if tag == '*': return self.walk(node[1]) * self.walk(node[2])
        if tag == '/': return self.walk(node[1]) / self.walk(node[2])
        if tag == '==': return self.walk(node[1]) == self.walk(node[2])
        if tag == '>': return self.walk(node[1]) > self.walk(node[2])
        if tag == '<': return self.walk(node[1]) < self.walk(node[2])
        
        # 'uminus' được define riêng trong Parser nên giữ nguyên
        if tag == 'uminus': return -self.walk(node[1])

        # --- XỬ LÝ HÀM ---
        if tag == 'func_def':
            self.functions[node[1]] = (node[2], node[3])
            return None

        if tag == 'func_call':
            name = node[1]
            args = [self.walk(a) for a in node[2]]
            
            if name not in self.functions:
                print(f"Lỗi Runtime: Hàm '{name}' chưa được định nghĩa.")
                return None
            
            params, body = self.functions[name]
            
            if len(args) != len(params):
                print(f"Lỗi: Hàm '{name}' cần {len(params)} tham số, nhận được {len(args)}.")
                return None


            old_env = self.env.copy()
            for p, a in zip(params, args):
                self.env[p] = a
            
            # Hàm walk trả về kết quả của lệnh cuối cùng trong body
            try:
                result = self.walk(body)
            except ReturnException as e:
                result = e.value # Nhận giá trị từ lệnh return
            else:
                if result is None: 
                    result = 0
            
            self.env = old_env
            return result
        
        if tag == 'return_stmt':
            val = self.walk(node[1])
            raise ReturnException(val)
        
    

        return None

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value