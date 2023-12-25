from telegram.ext import CommandHandler, CallbackContext, Application
from telegram import Update
from sclib import SoundcloudAPI, Track, Playlist
import os, logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log", encoding="utf-8")]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
telegram_token = os.getenv('TELEGRAM_TOKEN')
api = SoundcloudAPI()

async def start(update: Update, context: CallbackContext) -> None:
    logger.info(f"{update.message.from_user.name} used /start")
    await update.message.reply_text("Hello!\nSend me a link to a SoundCloud track using /soundcloud command and I will send you a file.")

async def soundcloud(update: Update, context: CallbackContext) -> None:
    logger.info(f"{update.message.from_user.name} used /soundcloud, args: {context.args}")
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    if len(context.args) == 0:
        await update.message.reply_text('where link')
        return
    soundcloud_url = context.args[0]
    if not soundcloud_url.startswith('https://soundcloud.com/') and not soundcloud_url.startswith('https://on.soundcloud.com/'):
        await update.message.reply_text('This isn\'t a SoundCloud link, use https://soundcloud.com/ or https://on.soundcloud.com/')
        return
    resource = api.resolve(soundcloud_url)
    if isinstance(resource, Track):
        try:
            title = resource.title.replace("/", "").replace("\\", "")
            artist = resource.artist.replace("/", "").replace("\\", "")
            if '/' or '\\' in resource.title and resource.artist:
                filename = f'{artist} - {title}.mp3'
            else:
                filename = f'{resource.artist} - {resource.title}.mp3'
            with open(filename, 'wb+') as fp:
                resource.write_mp3_to(fp)
            await context.bot.send_audio(chat_id=chat_id, audio=open(filename, 'rb'), reply_to_message_id=message_id)
            os.remove(filename)
        except Exception as e:
            await update.message.reply_text(f'Error: {e}')
            logger.error(f"Error: {e}")
            os.remove(filename)
    elif isinstance(resource, Playlist):
        try:
            for track in resource.tracks:
                title = track.title.replace("/", "").replace("\\", "")
                artist = track.artist.replace("/", "").replace("\\", "")
                if '/' or '\\' in track.title and track.artist:
                    filename = f'{artist} - {title}.mp3'
                else:
                    filename = f'{track.artist} - {track.title}.mp3'
                with open(filename, 'wb+') as fp:
                    track.write_mp3_to(fp)
                await context.bot.send_audio(chat_id=chat_id, audio=open(filename, 'rb'), reply_to_message_id=message_id)
                os.remove(filename)
        except Exception as e:
            await update.message.reply_text(f'Error: {e}')
    else:
        await update.message.reply_text('This isn\'t a track or playlist')

def main() -> None:
    application = Application.builder().token(telegram_token).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('soundcloud', soundcloud))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
if __name__ == '__main__':
    main()
