import asyncio
from pathlib import Path
from neonize.aioze.client import NewAClient
from neonize.proto.Neonize_pb2 import Message
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import InteractiveMessage
from pydantic import BaseModel, Field
from thundra_io.button import create_button_message, ListButtonV2, RowV2, create_carousel_message
from thundra_io.command import Command, command
from thundra_io.utils import ChainMessage
from thundra_io.button.v2 import ListButtonV2, QuickReplyV2, RowV2, SectionV2
from concurrent.futures import ThreadPoolExecutor
from pytubefix import Search, YouTube
import sys
sys.path.insert(0, Path(__file__).parent.parent.__str__())
from agents.yt import convert_size, parse_duration


class AudioYT(BaseModel):
    mime_type: str = Field()
    abr: int = Field()
    url: str = Field()


class VideoYT(BaseModel):
    fps: int = Field()
    vcodec: str = Field()
    res: str = Field()
    mime_type: str = Field()
    url: str = Field()


class AudioSection(SectionV2[AudioYT]):
    event_id = "audio_section"

    async def on_click(self, client: NewAClient, message: Message, param: AudioYT):
        await client.send_audio(message.Info.MessageSource.Chat, param.url)


class VideoSection(SectionV2[VideoYT]):
    event_id = "video_section"

    async def on_click(self, client: NewAClient, message: Message, param: VideoYT):
        await client.send_video(message.Info.MessageSource.Chat, param.url)

async def send_video_download_list(client: NewAClient, message: Message, url: str):
    yt = YouTube(url)
    stream = yt.streams
    audio_button = [
        RowV2[AudioYT](
            title=i.subtype,
            header=i.bitrate.__str__(),
            description=convert_size(i.filesize_approx),
            params=AudioYT(mime_type=i.mime_type, abr=i.bitrate, url=i.url),
        )
        for i in stream.filter(type="audio")
    ]
    video_button = [
        RowV2[VideoYT](
            header=i.resolution.__str__(),
            title=i.fps.__str__(),
            description=convert_size(i.filesize_approx),
            params=VideoYT(
                fps=i.fps,
                vcodec=i.video_codec,
                mime_type=i.mime_type,
                res=i.resolution,
                url=i.url,
            ),
        )
        for i in stream.filter(type="video")
    ]
    msg = await client.build_image_message(yt.thumbnail_url)
    await client.send_message(
        message.Info.MessageSource.Chat,
        create_button_message(
            InteractiveMessage(
                body=InteractiveMessage.Body(
                    text=f"Duration: {parse_duration(yt.length)}\nViews: {yt.views}\n\n{yt.description or ''}"
                ),
                header=InteractiveMessage.Header(
                    title=yt.title,
                    imageMessage=msg.imageMessage,
                    hasMediaAttachment=True,
                ),
                footer=InteractiveMessage.Footer(text="@thundra-ai"),
            ),
            buttons=[
                ListButtonV2(
                    title="Download",
                    sections=[
                        VideoSection(
                            title="Video", highlight_label="Video", rows=video_button
                        ),
                        AudioSection(
                            title="Audio", highlight_label="Audio", rows=audio_button
                        ),
                    ],
                )
            ],
        ),
    )
@command.register(Command("yt"))
async def yt(client: NewAClient, message: Message):
    url = ChainMessage.extract_text(message.Message)[3:].strip()
    await send_video_download_list(client, message, url)


class VideoMetadata(BaseModel):
    url: str = Field()

class GetItem(QuickReplyV2[VideoMetadata]):
    event_id= "get_video"
    async def on_click(self, client: NewAClient, message: Message, params: VideoMetadata) -> None:
        await send_video_download_list(
            client, message, params.url
        )



@command.register(Command("ytsearch"))
async def yt_search(client: NewAClient, message: Message):
    if message.Info.MessageSource.Chat.User != message.Info.MessageSource.Sender.User:
        await client.send_message(message.Info.MessageSource.Chat, "Tidak bisa digunakan dalam grup")
        return
    query = ChainMessage.extract_text(message.Message)[9:].strip()
    search = Search(query)
    async def create_card(yt: YouTube):
        print('yt', yt)
        try:
            length = yt.length
        except TypeError:
            length = 0
        return create_button_message(
            InteractiveMessage(
                header=InteractiveMessage.Header(
                    imageMessage=(await client.build_image_message(yt.thumbnail_url)).imageMessage,
                    title=yt.title,
                    subtitle='',
                    hasMediaAttachment=True
                ),
                body=InteractiveMessage.Body(text=f"{yt.title}\nduration: {parse_duration(length)}\ndescription: {yt.description}"),
                footer=InteractiveMessage.Footer(text=yt.author)
            ),
            [
                GetItem(
                    display_text="Download",
                    params=VideoMetadata(
                        url=yt.watch_url
                    )
                )
            ],
            direct_send=False
        )
    results = search.videos
    cards = await asyncio.gather(*[create_card(i) for i in (results or [])[:5]])
    if cards:
        await client.send_message(
            message.Info.MessageSource.Chat,
            create_carousel_message(
                InteractiveMessage(
                    body=InteractiveMessage.Body(text="hasil pencarian youtube dengan query %r" % query)
                ),
                cards=cards
            )
        )
    else:
        await client.reply_message(
            "Video tidak ditemukan",
            message
        )
