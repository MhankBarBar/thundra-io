from thundra_io.middleware import Middleware, middleware
from neonize.aioze.client import NewAClient
from neonize.proto.Neonize_pb2 import Message
from thundra_io.storage.file import File
from thundra_io.utils import get_message_type, get_user_id
from thundra_io.storage import storage, File
from thundra_io.types import MediaMessageType


class SaveMediaMessage(Middleware):
    async def run(self, client: NewAClient, message: Message):
        msg = get_message_type(message.Message)
        if isinstance(msg, MediaMessageType):
            storage.save(
                get_user_id(message),
                message.Info.ID,
                File.from_message(msg),
            )


middleware.add(SaveMediaMessage)
