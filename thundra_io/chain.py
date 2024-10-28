from langchain.agents import AgentExecutor, initialize_agent
from langchain.agents.agent_types import AgentType
from neonize.aioze.client import NewAClient
from neonize.proto.Neonize_pb2 import Message
from .utils import get_message_type
from .agents import agent
from .core.llm import chat_model


def execute_agent(memory, client: NewAClient, message: Message) -> AgentExecutor:
    """
    Execute an agent based on the incoming message.

    This function initializes and executes an agent based on the provided message and client.

    :param memory: Memory object for the agent execution.
    :type memory: Any
    :param client: Client object for communication.
    :type client: NewClient
    :param message: Incoming message to process.
    :type message: Message
    :return: AgentExecutor object for the executed agent.
    :rtype: AgentExecutor
    """
    tools = [
        tool.agent(client, message)
        for tool in agent.filter_tools(get_message_type(message.Message).__class__)
    ]
    return initialize_agent(
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        tools=tools,
        llm=chat_model.llm,
        verbose=True,
        max_iterations=3,
        early_stopping_method="generate",
        memory=memory,
    )
