from model.core import Block
from model.compiler import functions
import uuid


class FunctionBlock(Block):
    
    def __init__(self, script_file: str, script_function: str, prairie=None, block_id=None):
        super(FunctionBlock, self).__init__(name=script_function, functional_type='function', prairie=prairie)

        self.function_signature = {}
        self.creation_success = False

        if self.set_thread(script_file, script_function):
            self.create_nodes()
            self.creation_success = True
        else:
            print('failed to create FunctionBLock', self.name)

        if block_id is not None:
            self.id = uuid.UUID(block_id)

    def __bool__(self):
        return self.creation_success

    # Override
    def set_thread(self, script_file: str, script_function: str) -> bool:
        if super(FunctionBlock, self).set_thread(script_file, script_function):
            try:
                self.function_signature = functions(self.thread.script_file)[self.thread.script_function]
                return True

            except KeyError:
                return False

    def create_nodes(self):

        for arg in self.function_signature['args']:
            self.add_node(arg, 'in')

        for return_value in self.function_signature['returns']:
            self.add_node(return_value, 'out')


class InputBlock(FunctionBlock):

    def __init__(self, name: str, value, prairie=None):

        super(InputBlock, self).__init__('files/scripts/basic_functions.py', 'input', prairie=prairie)

        self.name = name
        self.type = 'input'
        list(self.nodes_in().values())[0].value = value
        list(self.nodes_in().values())[0].ready = True

    def set_ready(self):
        list(self.nodes_in().values())[0].ready = True
        list(self.nodes_out().values())[0].ready = True


class OutputBlock(FunctionBlock):

    def __init__(self, name: str, prairie=None):

        super(OutputBlock, self).__init__('files/scripts/basic_functions.py', 'output', prairie=prairie)

        self.name = name
        self.type = 'output'
        self.nodes_in()['x'].value = 0

    def set_ready(self):
        pass
        # list(self.nodes_in().values())[0].ready = True
        # list(self.nodes_out().values())[0].ready = True


class ChartBlock(FunctionBlock):

    def __init__(self, name: str, prairie=None):

        super(ChartBlock, self).__init__('files/scripts/basic_functions.py', 'chart', prairie=prairie)

        self.name = name
        self.type = 'chart'
        self.nodes_in()['x'].value = 0
        self.nodes_in()['y'].value = 0

    def set_ready(self):
        pass
        # list(self.nodes_in().values())[0].ready = True
        # list(self.nodes_out().values())[0].ready = True