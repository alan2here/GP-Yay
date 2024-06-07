from openai import OpenAI
import safety
import random
import ast

client : str = "give me a proper value in GPT.py"
section = ["\n\n", "\n\n\n"]

def cont(token_count : int, text : str) -> str: # short for "continuation"
    if token_count <= 0: raise ValueError("token_count must be positive")
    if token_count != int(token_count): raise ValueError("token_count must be integer")
    safety.check(text.__len__(), token_count)
    return client.completions.create(
        model = "gpt-3.5-turbo-instruct",
        prompt = text,
        temperature = 1,
        max_tokens = token_count,
        top_p = 1,
        frequency_penalty = 0,
        presence_penalty = 0
    ).choices[0].text

# Trailing "\n" after for example a colon generates "\n ..." (2 total),
# but trailing "\n\n" generates "\n ..." (3 total).
# beta.openai.com/playground also has this problem
# as a result some the features include extra .strip() or [1:]

def ask(max_tokens : int, question : str, question_prompt : str = "Question",
    answer_prompt : str = "Answer", answer_start : str = None,
    question_prompt_symbol = ":", answer_prompt_symbol : str = ":") -> str:
    return cont(max_tokens, question_prompt + question_prompt_symbol + section[0] +
        question + section[1] + answer_prompt + answer_prompt_symbol +
        ((section[0] + answer_start) if answer_start else "\n")).strip()

# Specific question, answer here "(output) --> answer"
def query_quote(token_count : int, query_text : str) -> str:
    result = cont(token_count, query_text + " \"")
    response = ""
    for char in result:
        response += char
        if char == "\"": break
    return response.strip()

# Question: Two pieces of text follow.
#
# 1. text block
#
# 2. text block
#
#
# From only the answers "Yes" and "No", do the two pieces of text mean the same thing?
#
# (output) --> answer
def same_meaning(text : str, text2 : str) -> bool:
    result = ask(1, "Two pieces of text follow" + section[0] + "1. " + text +
        section[0] + "2. " + text2, answer_prompt =
        "From only the answers \"Yes\" and \"No\", do the two pieces of text mean the same thing",
        answer_prompt_symbol = "?")
    if result == "Yes":
        return True
    else:
        if result == "No": return False
        else: return None # the boolean form of None is False

def simplify(token_count : int, text : str) -> str:
    return ask(token_count, text, question_prompt = "Text", answer_prompt =
        "Repeated but mildly summarized, the resulting text should be shorter")

def simplify_iter(simplification_steps : int,
    max_tokens_per_simplification : int, text : str) -> str:
    for _ in range(simplification_steps):
        text = simplify(max_tokens_per_simplification, text)
    return text

# for debugging
def simplify_iter_verbose(simplification_steps : int,
    max_tokens_per_simplification : int, text : str) -> str:
    for _ in range(simplification_steps):
        text += "\n\n" + simplify(max_tokens_per_simplification, text)
    return text

# "stool, pint glass, door, pint glass, person, window, person" --> "pub"
def location_from_entities(max_tokens : int, entities : str) -> str:
    return query_quote(max_tokens, 0, "The following items are nearby \"" + \
        entities + "\". Therefore my location is a\\the")

# "tall, quiet, older gentleman who loves to play golf"
def random_personality() -> str:
    traits = ("friendly", "curious", "analytical", "creative", "angry", "confrontational",
        "opinionated", "tactile", "merry", "boisterous", "self-absorbed", "speedy", "introspective",
        "empathetic", "understanding", "resilient ", "humble", "impulsive", "happy",
        "adventurous", "risk-adverse", "reliable", "ambitious", "stoic", "shy", "nervous",
        "cautious", "dangerous", "charming", "pleasant", "attractive", "egotistic",
        "determined", "energetic", "enthusiastic", "generous", "meticulous", "aggravating",
        "optimistic", "pessimistic", "rebellious", "authoritarian", "skeptical", "outspoken",
        "doubtful", "questioning", "spontaneous", "stubborn", "thoughtful", "reflective")
    chosen_traits = []
    while True:
        chosen_traits += random.choice(traits)
        if random.randint(0, 2) == 0: break
    result = "A "
    for trait in chosen_traits:
        result.append(trait)
        if result != chosen_traits[-1]:
            result.append(" ")
    result.append(" " + random.choice("man", "women", "individual"))
    return result

# ("learn'ed scholar", "history book") --> "a wealth of insight into the ways of ..."
# ("history book", "learn'ed scholar") --> "is always attentive towards me"
def opinion(subject: str, of: str) -> str:
    return ask(200, "Imagine a fiction, in this fiction \"" +
        subject + "\" has an opinion of \"" + of + "\", state the opinion").strip()

def run_code(safety : set, max_tokens : int, description : str):
    print("\nPython Code:\n")
    code = ask(max_tokens,
        "Write Python code to perform the given task, no notes or comments, just code." +
        section[0] + description, question_prompt = "Instructions", answer_prompt = "Code")
    print("\"\n" + code + "\n\"")
    run_code_core(safety, code)

def run_code_core(safety: set, code: str):
    if not safety:
        raise ValueError("\"safety\" should contain items")
    for item in safety:
        if item != int(item):
            raise ValueError("\"safety\" should contain only integers")
        if item < 0 or item > 9:
            raise ValueError("items in \"safety\" should be in the range 0 to 9")
        if list(safety).count(item) > 1:
            raise ValueError("\"safety\" should not contain any duplicates")

    permitted_features = (
        # 0 - safe features
        (ast.Name, ast.Await, ast.Pass, ast.Nonlocal,

            # operations
            ast.UnaryOp, ast.BinOp, ast.UAdd, ast.USub, ast.Add,
            ast.Sub, ast.AugAssign, ast.keyword,

            # expressions and variables
            ast.Expr, ast.alias, ast.Assign, ast.Load, ast.Store, ast.Del,

            # comparisons
            ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,

            # bools
            ast.BoolOp, ast.And, ast.Or),

        # 1 - integers, strings and collections, unlimited memory
        (ast.Constant, # integers and strings

            # collection types
            ast.Set, ast.Dict, ast.Tuple, ast.List,

            # access collections
            ast.Slice, ast.Subscript,

            # integer operations\functions
            ast.Mod, ast.Pow),

        # 2 - functions and flow control, except calling functions - unlimited recursion
        (ast.GeneratorExp,

            # create functions and lambdas
            ast.FunctionDef, ast.Lambda, ast.AsyncFunctionDef,

            # return from functions, lambdas, and loops
            ast.Return, ast.Yield, ast.YieldFrom, ast.Break, ast.Continue,

            # loops
            ast.While, ast.For, ast.AsyncFor, ast.ListComp, ast.DictComp, ast.SetComp,

            # the arguments of a function
            ast.arguments, ast.arg),

        # 3 - modules, but also needed for classes - module use seems dangerous
        (ast.Module,),

        # 4 - classes
        (ast.Attribute, ast.ClassDef),

        # 5 - function calls - unlimited recursion and calling of built-in global functions
        (ast.Call,),

        # 6 - unlimited tampering with built-in globals
        (ast.Global,),

        # 7 - exceptions
        (ast.Raise, ast.Try, ast.ExceptHandler, ast.With, ast.AsyncWith),

        # 8 - importing - unlimited breaking of the computer
        (ast.Import, ast.ImportFrom),

        # 9 - conditions
        (ast.If,)
    )

    class SafetyVisitor(ast.NodeVisitor):
        def __init__(self, allowed_nodes):
            self.allowed_nodes = allowed_nodes
            self.safe = True
            self.invalid_node = None

        def generic_visit(self, node):
            if not isinstance(node, self.allowed_nodes):
                self.safe = False
                self.invalid_node = node
                return
            super().generic_visit(node)

    allowed_nodes = tuple(node for index in safety for node in permitted_features[index])
    visitor = SafetyVisitor(allowed_nodes)
    print("\nCode execution started")

    restricted_globals = {k: v for k, v in globals().items() if
        # built-in
        k not in ('exec', 'eval', 'open', 'subprocess', 'compile',
        'globals', 'locals', 'setattr', 'getattr', 'delattr', 'exit', 'quit',
        'help', 'memoryview', 'property', 'super', 'vars', 'dir', 'input',

        # libraries
        'OpenAI', 'safety', 'ast', 'client', 'random',

        # my objects
        'section', 'cont', 'ask', 'query_quote',
        'same_meaning', 'simplify', 'simplify_iter', 'simplify_iter_verbose',
        'location_from_entities', 'random_personality', 'opinion',
        'run_code', 'run_code_core',

        # dunder
        '__import__', '__name__', '__doc__', '__package__', '__loader__',
        '__spec__', '__file__', '__cached__', '__builtins__')}

    try:
        parsed_code = ast.parse(code)
    except SyntaxError as e:
        print("syntax error: " + e.__str__())
    visitor.visit(parsed_code)
    if visitor.safe:
        exec(code, restricted_globals) # TODO "input()" still works :/
    else:
        print("feature \"" + type(visitor.invalid_node).__name__ + "\" is not allowed")
    print("Code execution finished\n")
