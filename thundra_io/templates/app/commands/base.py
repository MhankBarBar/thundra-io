from thundra_io.command import command, Command, MessageType, Owner
from neonize.aioze.client import NewAClient
from neonize.proto.Neonize_pb2 import Message
import time
from thundra_io.agents import agent
from thundra_io.middleware import middleware
from thundra_io.utils import ChainMessage, get_user_id
from thundra_io.storage import storage
import tempfile
import graphviz, os
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    ExtendedTextMessage,
)


@command.register(name="owner test", filter=Command("owner") & Owner())
async def owner_test(client: NewAClient, message: Message):
    await client.reply_message("owner", message)


@command.register(
    name="ping", filter=Command("ping") & (MessageType(ExtendedTextMessage, str))
)
async def ping(client: NewAClient, message: Message):
    await client.reply_message("pong", quoted=message)


@command.register(name="file", filter=Command("file"))
async def my_file(client: NewAClient, message: Message):
    await client.reply_message(storage[get_user_id(message)].__str__(), message)


@command.register(name="debug", filter=Command("debug"))
async def debug(client: NewAClient, message: Message):
    await client.reply_message(
        message.Message.extendedTextMessage.contextInfo.quotedMessage.__str__(), message
    )


@command.register(name="shell", filter=Command(">", prefix="") & Owner())
async def evaluater(client: NewAClient, message: Message):
    try:
        msg = eval(ChainMessage.extract_text(message.Message)[1:].strip()).__str__()
    except Exception as e:
        msg = "Exception:" + e.__str__()
    await client.reply_message(msg, message)


@command.register(name="graph", filter=Command("graph"))
async def graph(client: NewAClient, message: Message):
    gv = command.combine_graph(middleware, command, agent)
    fname = tempfile.gettempdir() + "/" + time.time().__str__()
    outfile = tempfile.gettempdir() + "/" + time.time().__str__() + "_out.jpeg"
    with open(fname, "w") as file:
        file.write(gv)
    await client.send_image(
        message.Info.MessageSource.Chat,
        graphviz.render("circo", "jpeg", fname, outfile=outfile),
    )
    os.remove(fname)
    os.remove(outfile)
