import ast
import inspect
import re
import string
import importlib.util
import os


def function_returns(program_string):
    result = {}
    func_name = None
    for line in re.findall('def .+\w|(?<=return ).+', program_string):
        if line.startswith('def '):
            func_name = line[4:]
        result[func_name] = line

    return [return_value.strip('(') for return_value in list(result.values())[0].split(', ')]


def exec_import(script_file, script_function):

    script_file = script_file.strip('.py').replace('/', '.')

    exec('import ' + script_file)
    function_attr = getattr(eval(script_file), script_function)

    return function_attr


def format_filename(s):
    """Take a string and return a valid filename constructed from the string.
Uses a whitelist approach: any characters not present in valid_chars are
removed. Also spaces are replaced with underscores.

Note: this method may produce invalid filenames such as ``, `.` or `..`
When I use this method I prepend a date string like '2009_01_15_19_46_32_'
and append a file extension like '.txt', so I avoid the potential of using
an invalid filename.

"""
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    filename = filename.replace(' ', '_')
    filename = filename.replace('-', '/-')# I don't like spaces in filenames.
    return filename


def functions(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        f = file.read()
        ast_parsed_object = ast.parse(f)

        spec = importlib.util.spec_from_file_location("module.name", os.path.abspath(file_path))
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)

        # exec('import ' + file_module)

        functions_dict = {}

        for x in ast_parsed_object.body:
            function_dict = {}
            if isinstance(x, ast.FunctionDef):
                function_name = x.name

                function_attr = exec_import(file_path, function_name)

                function_attr = getattr(foo, function_name)
                signature = inspect.signature(function_attr)
                function_dict['args'] = [arg for arg in signature.parameters if
                                         signature.parameters[arg].default == inspect._empty]
                function_dict['kwargs'] = {arg: signature.parameters[arg].default for arg in signature.parameters if
                                          signature.parameters[arg].default != inspect._empty}
                # function_dict['returns'] = ['return_' + str(i) for i, ret in enumerate(x.body)
                #                             if isinstance(ret, ast.Return)]
                function_dict['returns'] = function_returns(inspect.getsource(function_attr))

                functions_dict[x.name] = function_dict

    return functions_dict