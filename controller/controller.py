from model.core import Prairie, FunctionThread
from view.blocks_view import InputBlockView, FunctionBlockView, OutputBlockView, ChartBlockView
from view.prairie_view import PrairieView, ConnectionView, BlockView, NodeView
from model.blocks import *
from model.core import *
from PyQt5.QtCore import *
from pprint import pprint
import yaml


def describe_block(block: Block, mode='debug') -> dict:

    if mode == 'debug':

        block_dict = {'name': block.name,
                      'type': block.type,
                      'nodes': {'in': {node.name: node.id for node in list(block.nodes_in().values())},
                                'out': {node.name: node.id for node in list(block.nodes_out().values())}},
                      'id': str(block.id)}
    else:

        block_dict = {'name': block.name,
                      'type': block.type,
                      'nodes': {'in': {node.id: node.id for node in list(block.nodes_in().values())},
                                'out': {node.id: node.id for node in list(block.nodes_out().values())}},
                      'id': str(block.id)}

    if isinstance(block, InputBlock):
        block_dict['value'] = block.nodes_in()['x'].value
    elif isinstance(block, FunctionBlock):
        block_dict['script_function'] = block.thread.script_function
        block_dict['script_file'] = block.thread.script_file

    return block_dict


def describe_prairie_blocks(prairie: Prairie, mode='debug') -> dict:
    blocks = prairie.blocks_id()
    return {block_id: describe_block(blocks[block_id], mode=mode) for block_id in blocks}


def describe_prairie_nodes(prairie: Prairie) -> dict:
    nodes_dict = {}
    blocks_dict = describe_prairie_blocks(prairie, mode='debug')

    for block_id, block_dict in blocks_dict.items():
        block_nodes_dict = block_dict['nodes']
        for node_name, node_id in block_nodes_dict['in'].items():
            nodes_dict[node_id] = {'block_id': block_id, 'node_name': node_name, 'node_type': 'in'}
        for node_name, node_id in block_nodes_dict['out'].items():
            nodes_dict[node_id] = {'block_id': block_id, 'node_name': node_name, 'node_type': 'out'}

    return nodes_dict


def describe_prairie(prairie: Prairie) -> dict:
    connections = prairie.connections_id()
    nodes = describe_prairie_nodes(prairie)

    blocks_dict = describe_prairie_blocks(prairie, mode='dev')

    connections_dict = {connection.id: [connection.block_in().id, connection.node_in.id,
                        connection.block_out().id, connection.node_out.id]
                        for connection in list(connections.values())}

    return {'blocks': blocks_dict, 'connections': connections_dict, 'nodes': nodes}


def describe_prairie_view_blocks(prairie_view: PrairieView) -> dict:
    return {block_view_id: [block_view.scenePos().x(), block_view.scenePos().y()]
            for block_view_id, block_view in prairie_view.block_views().items()}


def nodes_reassignment(prairie: Prairie, prairie_view: PrairieView, nodes: dict):

    prairie_blocks = prairie.blocks_id()
    prairie_view_blocks = prairie_view.block_views()

    for node_id, node_dict in nodes.items():
        if node_dict['node_type'] == 'in':
            prairie_blocks[node_dict['block_id']].nodes_in()[node_dict['node_name']].id = node_id
            prairie_view_blocks[node_dict['block_id']].nodes_in()[node_dict['node_name']].id = node_id
        if node_dict['node_type'] == 'out':
            prairie_blocks[node_dict['block_id']].nodes_out()[node_dict['node_name']].id = node_id
            prairie_view_blocks[node_dict['block_id']].nodes_out()[node_dict['node_name']].id = node_id


class Controller:

    def __init__(self, prairie: Prairie, prairie_view: PrairieView):

        self.prairie = prairie
        self.prairie_view = prairie_view

        self.prairie_view.controller = self

        # self.blocks = []
        self.threads = ThreadCollector()
        self.blocks = []
        self.connections = []

    def create_block_view_from_block(self, block, position=None, preview=False):

        block_view = -1

        if block.type == 'input':
            block_view = InputBlockView(block.name, describe_block(block)['nodes'],
                                        value=list(block.nodes_in().values())[0].value,
                                        block_id=block.id,
                                        preview=preview, view=self.prairie_view)

        elif block.type == 'function':
            block_view = FunctionBlockView(block.thread.script_function, describe_block(block)['nodes'],
                                           block_id=block.id,
                                           preview=preview)

        elif block.type == 'output':
            block_view = OutputBlockView(block.name, describe_block(block)['nodes'], block_id=block.id, preview=preview)

        elif block.type == 'chart':
            block_view = ChartBlockView(block.name, describe_block(block)['nodes'], block_id=block.id, preview=preview)

        if not preview:
            thread = Thread(FunctionThread(block))
            self.threads.add(thread)
            # print('thread will be added')
            thread.started.connect(block_view.thread_start)
            thread.notifyOutput.connect(block_view.thread_done)
            thread.notifyState.connect(block_view.thread_error)

        if position is None:
            block_view.setPos(*block_view.position)
        elif isinstance(position, list):
            block_view.setPos(*position)

        return block_view

    def add_block(self, block, position=None):
        self.prairie.add_block(block)
        block_view = self.create_block_view_from_block(block, position=position)
        self.prairie_view.scene.addItem(block_view)

    def create_block_from_dict(self, block_dict):

        block_type = block_dict['type']

        if block_type == 'input':
            block = InputBlock(block_dict['name'], str(block_dict['value']))
        elif block_type == 'function':
            block = FunctionBlock(block_dict['script_file'], block_dict['script_function'])
        elif block_type == 'output':
            block = OutputBlock(block_dict['name'])
        elif block_type == 'chart':
            block = ChartBlock(block_dict['name'])
        else:
            block = None

        try:
            block.id = block_dict['id']
        except KeyError:
            pass

        return block

    def delete_block(self):
        pass

    def connect_nodes(self, node_object_in, node_object_out):

        if isinstance(node_object_in, type(node_object_out)) and \
           isinstance(node_object_in, NodeView) or isinstance(node_object_in, Node):

            if isinstance(node_object_in, NodeView):
                node_in = self.model(node_object_in)
                node_out = self.model(node_object_out)
                node_in_view = node_object_in
                node_out_view = node_object_out

            else:
                node_in = node_object_in
                node_out = node_object_out
                node_in_view = self.view(node_object_in)
                node_out_view = self.view(node_object_out)

            connection = self.prairie.connect_nodes(node_in, node_out)

            if connection:
                connection_view = ConnectionView(node_in_view, node_out_view, self.prairie_view.scene)

                self.prairie_view.scene.addItem(connection_view)

                if isinstance(node_in_view.block, InputBlockView):
                    node_in_view.block.update_name_from_connection()

                return connection

        else:
            print('failed to connect', node_object_in, node_object_out)

        return -1

    def disconnect_nodes(self):
        pass

    def disconnect_connection(self, connection_object):
        if isinstance(connection_object, ConnectionView):
            connection_view = connection_object
            connection = self.model(connection_view)
            # self.prairie.
        pass

    def run(self):
        print('try to run')
        if not self.threads.isRunning():
            print('run')
            print(self.threads.threads_ready())
            self.threads.start()
        else:
            self.threads.quit()
            self.threads.terminate()

    def get_block_view_by_id(self):
        pass

    def load_file(self, filename):

        import_dict = {}

        with open(filename, 'r') as stream:
            try:
                import_dict = yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        for block_item, block_dict in import_dict['prairie']['blocks'].items():

            block = self.create_block_from_dict(block_dict)

            self.add_block(block, position=import_dict['prairie_view'][block.id])

        nodes_reassignment(self.prairie, self.prairie_view, import_dict['prairie']['nodes'])

        for connection_id, connection in import_dict['prairie']['connections'].items():
            block_in_id = connection[0]
            node_in_id = connection[1]
            block_out_id = connection[2]
            node_out_id = connection[3]

            connection = self.connect_nodes(self.model((block_in_id, node_in_id)),
                                            self.model((block_out_id, node_out_id)))

            if connection:
                connection.id = connection_id
            else:
                print('error')

    def save_file(self, filename):
        prairie_dict = describe_prairie(self.prairie)
        prairie_view_dict = describe_prairie_view_blocks(self.prairie_view)

        saving_dict = {'prairie': prairie_dict,
                       'prairie_view': prairie_view_dict}

        with open(filename, 'w') as outfile:
            yaml.dump(saving_dict, outfile, default_flow_style=False)

    def view(self, object_model):
        """
        Retrieve the view object
        :param object_model:
        :return:
        """
        if isinstance(object_model, Block):
            block = object_model
            return self.prairie_view.block_views()[block.id]
        elif isinstance(object_model, Node):
            node = object_model
            if node.type == 'in':
                return self.prairie_view.block_views()[node.block.id].nodes_in()[node.name]
            elif node.type == 'out':
                return self.prairie_view.block_views()[node.block.id].nodes_out()[node.name]

    def model(self, object_view):
        if isinstance(object_view, BlockView):
            block_view = object_view
            return self.prairie.blocks_id()[block_view.id]
        if isinstance(object_view, NodeView):
            node_view = object_view
            return self.prairie.blocks_id()[node_view.block.id].nodes_id()[node_view.id]
        if isinstance(object_view, ConnectionView):
            connection_view = object_view
            return self.prairie.connections_id()[connection_view.id]
        elif isinstance(object_view, str):
            block_id = object_view
            return self.prairie.blocks_id()[block_id]
        elif isinstance(object_view, tuple):
            block_id = object_view[0]
            node_id = object_view[1]
            return self.prairie.blocks_id()[block_id].nodes_id()[node_id]

    def reset_inputs(self):

        for block in list(self.prairie.blocks_id().values()):
            if isinstance(block, InputBlock) or isinstance(block, OutputBlock):
                block.set_ready()

    def update_node_value(self, block_id, node_id, value):
        self.prairie.blocks_id()[block_id].nodes_id()[node_id].value = value

    def get_connected_node_name(self, block_id, node_id):
        node = self.prairie.blocks_id()[block_id].nodes_id()[node_id]
        if node.is_connected():
            return node.connected_nodes()[0].name


class Thread(QThread):
    notifyState = pyqtSignal(bool)
    notifyOutput = pyqtSignal(list)

    def __init__(self, function_thread: FunctionThread, parent=None):

        super(Thread, self).__init__(parent)
        self.args = []
        self.kwargs = []
        self.output = []

        self.block = function_thread.block
        self.function_attr = -1

        self.exec_import()

    def exec_import(self):
        # dev : Check if already imported

        script_file = self.block.thread.script_file.strip('.py').replace('/', '.')

        exec('import ' + script_file)
        self.function_attr = getattr(eval(script_file), self.block.thread.script_function)
        a = 0

    def run(self):

        try:
            #    Function call
            if len(self.args) == 0 and len(self.kwargs) == 0:
                self.output = self.function_attr()
            elif len(self.args) >= 1 and len(self.kwargs) == 0:
                self.output = self.function_attr(*self.args)
            elif len(self.args) == 0 and len(self.kwargs) >= 1:
                self.output = self.function_attr(**self.kwargs)
            elif len(self.args) > 1 and len(self.kwargs) >= 1:
                self.output = self.function_attr(*self.args, **self.kwargs)
            if isinstance(self.output, tuple):
                self.output = [return_value for return_value in self.output]
            else:
                self.output = [self.output]
            self.set_out_nodes_variables()
            self.notifyOutput.emit(self.output)
            self.notifyState.emit(True)

        except:
            self.block.initialize_in_nodes()
            self.notifyState.emit(False)

        self.quit()

    def set_arguments(self, args, kwargs=None):
        self.args = args
        if kwargs is not None:
            self.kwargs = kwargs
        else:
            self.kwargs = []

    def set_out_nodes_variables(self):
        # Set the out nodes variables from the thread output
        for connection in self.block.connections_out():
            nodes_out = self.block.nodes_out()
            organized_nodes_out = [nodes_out[output_name] for output_name in self.block.function_signature['returns']]
            for i, node in enumerate(organized_nodes_out):
                if self.output is not None:
                    node.set_value(self.output[i])
            connection.transfer_value()
        self.block.initialize_in_nodes()


class ThreadCollector(QThread):

    def __init__(self, parent=None):
        super(ThreadCollector, self).__init__(parent)
        self.threads = []

    def run(self):
        while self.threads_ready():
            for thread in self.threads:
                if thread.block.ready and not thread.isRunning():
                    nodes_in = thread.block.nodes_in()
                    args = [nodes_in[arg_name].value for arg_name in thread.block.function_signature['args']]
                    # We only do the args, not kwargs, for now
                    thread.set_arguments(args)
                    thread.start()

    def add(self, thread: Thread):
        self.threads.append(thread)

    def threads_ready(self):
        return any([thread.block.ready for thread in self.threads])

    def describe_blocks(self):
        return {thread.block.id: [thread.block.name, thread.block.ready] for thread in self.threads}
