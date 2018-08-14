"""
core.py is the core of the Prairie software independent of:
- the GUI Framework used to create the view
- the Threading Framework used to generate the threads
- the Programming Languages of the script files running in the thread

The concept of Prairie is the following:
A Block contains input Nodes, output Nodes and a BlockThread: thread running a specific function from a script file.
BlockThread process the input nodes to fill the output nodes according to the function the thread is executing. A Block
wait for the input nodes to be ready before launching the thread. Blocks are connected through Connections. Blocks and
Connections lye in the Prairie.

Examples :

              - Hello World -
                ___________
               \          \
  'Hello' ----o\          \o---- 'World'
               \__________\

"""

from typing import List

import uuid
import os


class Node:

    def __init__(self, name: str, functional_type: str, block):
        """
        A Node is an object containing a value and connected to other nodes through connections. A node can transfer
        its value to another node through its Connection. Nodes are contained into Blocks.

        :param name: name of the node
        :param functional_type: 'in' if the node is an input for its block or 'out' if it is an output of its block
        :param block: block to which the node belong
        """

        self.name = name
        self.connections = []

        self.type = functional_type

        self._id = uuid.uuid4()
        self.value = -1
        self._ready = False

        self.block = block

    def __bool__(self):
        return True

    @property
    def id(self):
        return str(self._id)

    @id.setter
    def id(self, new_id: str):
        self._id = uuid.UUID(new_id)

    @property
    def ready(self) -> bool:
        """
        Return weather the node is ready

        :return: boolean
        """
        return self._ready

    @ready.setter
    def ready(self, ready):
        self._ready = ready

    # Public
    def is_connected(self):
        """
        Return weather the node is connected

        :return: boolean
        """
        return len(self.connections) > 0

    # Public
    def set_value(self, value):
        """
        Set the value of the node

        :param value:
        """
        self.value = value

    # Public
    def set_ready(self, ready: bool):
        self.ready = ready

    def connected_nodes(self):
        if self.type == 'in':
            return [connection.node_in for connection in self.connections]
        elif self.type == 'out':
            return [connection.node_out for connection in self.connections]


class Block:

    def __init__(self, name: str, functional_type: str=None, prairie=None):
        """
        A Block contains input Nodes, output Nodes and a BlockThread. The goal of a block is to pass the values of the
        input Nodes to the thread and update the output Nodes according to the thread output. A thread is simply the
        execution of a function.

        :param name:
        :param functional_type:
        """

        self._nodes = []

        self._id = uuid.uuid4()
        self.thread = FunctionThread(self)
        self._ready = False

        self.name = name
        self.type = functional_type

        if isinstance(prairie, Prairie):
            prairie.add_block(self)

    @property
    def ready(self) -> bool:
        """
        Return weather all the input nodes of the block are ready

        :return: boolean
        """
        return all(node.ready for node in list(self.nodes_in().values()))

    def update_ready(self):
        """
        Update the Ready attribute of the block if all the input nodes of the block are ready

        :return: boolean
        """
        self._ready = self.ready

    @property
    def id(self):
        return str(self._id)

    @id.setter
    def id(self, new_id: str):
        self._id = uuid.UUID(new_id)

    @property
    def nodes(self):
        return {node.name: node for node in self._nodes}

    @nodes.setter
    def nodes(self, new_nodes: List[Node]):
        self._nodes = new_nodes
        self.update_ready()

    def nodes_id(self):
        return {node.id: node for node in self._nodes}

    def connections(self):
        """
        Return all the connection from the block
        :return:
        """
        connections = []
        for node in self.nodes:
            connections += node.connections
        return connections

    def connections_out(self):
        """
        Return all the connection from the block
        :return:
        """
        connections = []
        for node in self._nodes:
            if node.type == 'out':
                connections += node.connections
        return connections

    def set_thread(self, script_file: str, script_function: str) -> bool:
        """
        Set script of the block thread
        :param script_file: path of the script file containing the script_function
        :param script_function: function in script_file to be executed by the thread
        :return: weather the thread has been well set
        """
        self.thread.script_file = script_file
        if self.thread.valid_script_file:
            self.thread.script_function = script_function
            return True
        else:
            return False

    def add_node(self, name: str, functional_type: str) -> Node:

        node = Node(name, functional_type, self)
        self._nodes.append(node)
        return node

    def nodes_values(self):

        return {node.name: node.value for node in self._nodes}

    def nodes_in(self):
        return {node.name: node for node in self._nodes if node.type == 'in'}

    def nodes_out(self):
        return {node.name: node for node in self._nodes if node.type == 'out'}

    def node(self, node_name: str):
        try:
            node = self.nodes[node_name]
        except KeyError:
            return False

        return node

    def node_by_id(self, node_id: str):
        try:
            node = self.nodes_id()[node_id]
        except KeyError:
            return False

        return node

    def initialize_in_nodes(self):
        for node in list(self.nodes_in().values()):
            node.ready = False


class Connection:

    def __init__(self, node_in: Node, node_out: Node):
        """
        A Connection connects two Nodes together and transfer the value of an output node to the input nodes.

        :param node_in: Node of type 'out' with respect to its Block
        :param node_out: Node of type 'in' with respect to its Block
        """

        self.node_in = node_in
        self.node_out = node_out

        self._ready = False

        self._connection_success = False

        self._id = uuid.uuid4()

        if isinstance(node_in, Node) and isinstance(node_out, Node):
            if node_in.type == 'out' and node_out.type == 'in' and node_in.block != node_out.block:
                # and not node_out.is_connected():
                self.node_in.connections.append(self)
                self.node_out.connections.append(self)
                self._connection_success = True

    def __bool__(self):
        return self._connection_success

    @property
    def id(self):
        return str(self._id)

    @id.setter
    def id(self, new_id: str):
        self._id = uuid.UUID(new_id)

    def block_in(self) -> Block:
        """
        Return the Block connected to the input of the connection
        :return: Block
        """
        return self.node_in.block

    def block_out(self) -> Block:
        """
        Return the Block connected to the output of the connection
        :return: Block
        """

        return self.node_out.block

    @property
    def ready(self) -> bool:
        """
        Return weather node_in is ready

        :return:
        """
        return self.node_in.ready

    def disconnect(self) -> bool:
        """
        Disconnect two nodes by removing the connection to their connections list
        :return: Weather the disconnection is successful
        """
        if self in [self.node_in.connections, self.node_out.connections]:
            self.node_in.connections.remove(self)
            self.node_out.connections.remove(self)
            return True
        else:
            return False

    def transfer_value(self):
        self.node_out.value = self.node_in.value
        self.node_out.ready = True
        self.block_out().update_ready()


class FunctionThread:

    def __init__(self, block: Block):
        """
        A BlockThread is a thread where a specific function is executed
        :param block: Block containing the thread
        """

        self.block = block
        self._script_file = ''
        self._script_function = ''

        self._ready = False
        self.running = False

        self.valid_script_file = False
        self.inputs = {}
        self.outputs = {}

    @property
    def ready(self):
        return self._ready

    @ready.setter
    def ready(self, ready: bool):
        self._ready = ready
        self.block.update_ready()

    @property
    def script_file(self):
        return self._script_file

    @script_file.setter
    def script_file(self, script_file):
        if os.path.exists(script_file):
            self._script_file = script_file
            self.valid_script_file = True

    @property
    def script_function(self):
        return self._script_function

    @script_function.setter
    def script_function(self, script_function):
        self._script_function = script_function


class Prairie:

    def __init__(self):
        """
        A Prairie is an environment where Blocks operate through their connections
        """

        self._blocks = []
        self._connections = []

    def connect_nodes(self, node_in: Node, node_out: Node) -> bool:
        """
        Connect two nodes together and place the connection in the prairie

        :param node_in: Input node
        :param node_out: Output node
        :return: Weather the connection is successful
        """

        connection = Connection(node_in, node_out)

        if connection:
            self._connections.append(connection)
        else:
            print('nodes connection failed')

        return connection

    def connect_blocks(self, block_in: Block, node_in_name: str, block_out: Block, node_out_name: str):
        node_in = block_out.node(node_out_name)
        node_out = block_in.node(node_in_name)

        return self.connect_nodes(node_out, node_in)

    def delete_block(self, block: Block):
        if block in self._blocks:
            for connection in block.connections():
                if connection.disconnect():
                    self._connections.remove(connection)
                else:
                    return False

            self._blocks.remove(block)
        else:
            return False

    def add_block(self, block: Block):
        if isinstance(block, Block):
            self._blocks.append(block)

    def describe_connection(self):
        return {connection.node_in.block.name + '__' +
                connection.node_in.name: connection.node_out.block.name + '__'
                + connection.node_out.name for connection in self._connections}

    @property
    def blocks(self):
        return {block.name: block for block in self._blocks}

    def connections_id(self):
        return {connection.id: connection for connection in self._connections}

    def blocks_id(self):
        return {block.id: block for block in self._blocks}

    def remove_connection(self, connection):
        pass
