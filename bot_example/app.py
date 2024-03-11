from logging import NOTSET, DEBUG, getLogger
from neonize.client import DeviceProps, NewClient
from neonize.events import MessageEv, ConnectedEv
import yaml
from neonize.utils.jid import Jid2String, JIDToNonAD
from thundra.chain import execute_agent
from thundra.profiler import Profile, Profiler
from thundra.storage import storage, File
from thundra.types import MediaMessageType, MessageWithContextInfoType
from thundra.core.memory import memory
from thundra.utils import ChainMessage, get_tag, get_user_id, workdir, get_message_type
from thundra.middleware import middleware
import signal
from neonize.events import event

# evaluate all module
from thundra.evaluater import evaluate_module
from thundra.config import config_toml

evaluate_module(workdir / "commands")
evaluate_module(workdir / "middleware")
evaluate_module(workdir / "agents")
# from .ipc import lexz
from thundra.command import command

app = NewClient(
    (workdir / config_toml["thundra"]["db"]).__str__(),
    DeviceProps(
        os=config_toml["thundra"]["name"], platformType=DeviceProps.PlatformType.SAFARI
    ),
    uuid=config_toml["thundra"]["name"],
)

signal.signal(signal.SIGINT, lambda *x: event.set())


@app.event(ConnectedEv)
def connected(client: NewClient, connect: ConnectedEv):
    me = app.get_me()
    me_jid = me.JID
    Profiler.add_profile(
        Profile(
            workspace=workdir.__str__(), phonenumber=me_jid.User, pushname=me.PushName
        )
    )
    # def set_debug(x: bytes):
    #     getLogger().setLevel([NOTSET, DEBUG][int(x.decode())])

    # lexz.set_handler("debug", set_debug)
    setattr(client, "my_tag", Jid2String(JIDToNonAD(me_jid)))
    setattr(client, "my_number", me_jid.User)


def save_to_storage(message: MessageEv):
    try:
        msg = get_message_type(message.Message)
        if isinstance(msg, MessageWithContextInfoType):
            get_msg_type = get_message_type(msg.contextInfo.quotedMessage)
            if isinstance(get_msg_type, MediaMessageType):
                storage.save(
                    get_user_id(message),
                    message.Info.ID,
                    File.from_message(get_msg_type),
                )
    except IndexError:
        return


@app.event(MessageEv)
def on_message(client: NewClient, message: MessageEv):
    r = middleware.execute(client, message)
    if r in [False, None]:
        cmd = command.execute(client, message)
        # if not cmd:
        #     save_to_storage(message)
        #     chat = message.Info.MessageSource.Chat
        #     sender = message.Info.MessageSource.Sender
        #     context = memory.get_memory(get_user_id(message))
        #     if sender.User == chat.User:
        #         yamlx = yaml.dump(ChainMessage(message.Message, message).to_json())
        #         client.send_message(
        #             chat,
        #             execute_agent(context, client, message).invoke(yamlx)["output"],
        #         )
        #     elif client.my_tag in get_tag(message.Message):
        #         save_to_storage(message)
        #         yamlx = yaml.dump(
        #             ChainMessage(message.Message, message).to_json()
        #         ).replace(f"@{client.my_number}".strip(), "")
        #         client.reply_message(
        #             execute_agent(context, client, message).invoke(yamlx)["output"],
        #             quoted=message,
        #         )


if __name__ == "__main__":
    # app.connect()
    pass
