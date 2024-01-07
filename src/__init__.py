import os
from shutil import move, rmtree
import typing
import logging
import schedule
from time import sleep
from datetime import datetime
from aiogram import Dispatcher, Bot 
from src.utils.client import Client 
from src.data import bot_tokens,  message_categories, msg_categories, TESTING, NEW_MESSAGES_PATH, SENDED_DIR

bots: typing.Dict[int, Bot] = {}
bot_working = True

def run_bots():
    for dog in bot_tokens:
        if bot_tokens[dog]:
            bots[dog] = Bot(bot_tokens[dog])


async def start_bot():
    if not TESTING:
        logging.basicConfig(
            filename = 'logs/bot.log' if not TESTING else 'logs/bot-test.log',
            filemode = 'a',
            level = logging.WARNING,
            format='[%(asctime)s]:(%(levelname)s):%(message)s', datefmt='%b/%d %H:%M:%S'
        )
        logging.write = logging.exception
    else:
        logging.basicConfig(level = logging.INFO)
    await new_message_checker()


async def new_message_checker():
    schedule.every().hour.do(delete_sended_messages_older_than_day)
    try:
        delete_sended_messages_older_than_day()
    except Exception as e:
        logging.exception('Error ocured while deleting old messages:', str(e), exc_info = True)
    while bot_working:
        try:
            schedule.run_pending()
        except Exception as e:
            logging.exception('Error ocured while deleting old messages:', str(e), exc_info = True)
        try:
            await send_message_to_clients()
        except Exception as e:
            logging.error(
                f'error while sending message to clients {e}', 
                exc_info = True
            )
        finally:
            sleep(0.1)


def delete_sended_messages_older_than_day():
    for m in message_categories:
        path_to_sended_messages = (NEW_MESSAGES_PATH+SENDED_DIR+msg_categories[m])
        now = datetime.now()
        for d in try_to_list_msg_dir(NEW_MESSAGES_PATH, SENDED_DIR, msg_categories[m]):
            file = path_to_sended_messages+'/'+d
            inside_file = os.listdir(file)[0]
            sending_date = datetime.utcfromtimestamp(os.path.getctime(file+'/'+inside_file))
            if (now - sending_date).days >= 1:
                rmtree(file)

def try_to_list_msg_dir(*directory_path: str) -> typing.List[str]:
    '''each directiory except for the last must to be ended with "/"'''
    try:
        dirs = os.listdir(''.join(directory_path))
    except FileNotFoundError:
        directory_path = list(directory_path)
        path = ''.join(directory_path)
        current_path = ''
        while True:
            current_path += directory_path.pop(0)
            if not os.path.exists(current_path):
                mkdir(current_path)
            if current_path == path: break
        dirs = []
    return dirs


async def send_message_to_clients():
    for m in bots:
        message_dir, text = eject_new_message(m)    
        if not text:
            if message_dir:
                rmtree(message_dir)
            continue
        try:
            inside_bot_msg_id = int(message_dir.split('/')[-1])
        except:
            inside_bot_msg_id = -1
        if isinstance(text, int): # the function returned id of inside-bot message to delete it
            await message_deleting.delete_message_from_inside_bot(text, m, bots[m])
            rmtree(message_dir)
            return
        msg_index = None
        now = datetime.now()
        if await check_standart_filter(text.lower(), m):
            Statistics.increase_new_messages_number(for_category = m)
            msg_index = message_deleting.get_index_for_new_message()
            for i in USERS_THAT_ALLOWED_TO_DELETE_MESSAGES if not TESTING else (DEVELOPER_ID,):
                if Client.get_clients_by_filter(id = i, payment_period_end = now, greater = True, category = m):
                    continue 
                if get_admin_of_account(i, m):
                    continue
                try:
                    await bots[m].send_message(
                        i, text,
                        reply_markup = message_deleting.delete_message_kb(msg_index),
                        parse_mode = 'HTML'
                    )
                except (ChatNotFound, BotBlocked, UserDeactivated, CantParseEntities):
                    pass
                except Exception as e:
                    logging.error(f'Failed to send {msg_categories[m]} for admin ({i}): {e}', exc_info = True)
            clients = Client.get_clients_by_filter(
                is_paused = False, payment_period_end = now, greater = True, category = m, is_paid = True)
            clients += Client.get_clients_by_filter(
                is_paused = False, payment_period_end = now, greater = True, category = m, is_paid = False)
            lower_text = text.lower()
            for client in clients:

                admin = Accounts.get_admin_of_account(client.id, m)
                if admin and Votes.check_if_client_is_allowed_to_get_vote_buttons(admin, m): 
                # it will be sent later or was sent before, beacuse the client is account of admin
                    continue
                if await stop_words_in_text(lower_text, client) and client.id not in USERS_THAT_ALLOWED_TO_DELETE_MESSAGES:
                    continue
                try:
                    if await client_is_using_trial_and_not_subscribed(client):
                        await bots[client.sending_mode].send_message(client.id, 'Для того, чтобы продолжить пользоваться пробным периодом, '
                            f'подпишитесь на {get_channel_for_trial_period()[0]}')
                        continue 
                except:
                    logging.error('Failed to check user`s subscribe for channel: ', exc_info=True)

                send_vote_kb = client.payment_period >= days_per_period[MIN_PERIOD_TO_GET_VOTE_BUTTONS] and \
                    client.has_paid_period
                accounts = [client.id]
                if send_vote_kb:
                    accounts += Accounts.get_all_accounts_of(client.id, m)
                for acc in accounts:
                    kb = InlineKeyboardMarkup()
                    if send_vote_kb:
                        kb = Votes.generate_vote_keyboard(msg_index)
                    else:
                        kb.add(Votes.get_spam_button(msg_index))
                    if acc in USERS_THAT_ALLOWED_TO_DELETE_MESSAGES:
                        kb.add(message_deleting.delete_message_kb(msg_index).inline_keyboard[0][0])
                    await send_message_to_client(acc, client.sending_mode, text, msg_index, inside_bot_msg_id, kb)
            if m in CHANNELS_OF_CATEGORIES:
                try:
                    await paying_bot.send_message(CHANNELS_OF_CATEGORIES[m], text, 'HTML')
                except:
                    logging.error('Failed to send to channel:', exc_info=True)
        if msg_index == None:
            rmtree(message_dir)
        else:
            move(message_dir, NEW_MESSAGES_PATH+SENDED_DIR+msg_categories[m]+f'/{msg_index}')

def eject_new_message(category: int) -> Union[Union[str, int],str]:
    m_dir = text = ''
    path = (NEW_MESSAGES_PATH+msg_categories[category])
    dirs = try_to_list_msg_dir(NEW_MESSAGES_PATH, msg_categories[category])
    if not dirs:
        return m_dir, text
    m_dir = path+'/'+dirs[0]
    if TEXT_INFO in listdir(m_dir):
        try:
            with open(m_dir+'/'+TEXT_INFO) as file:
                text = file.read()
        except:
            with open(m_dir+'/'+listdir(m_dir)[0]) as file:
                text = file.read()
    else: # if dir does not  contain any files it means that inside-bot want the bot to delete message
        try:
            text = int(dirs[0])
        except ValueError:
            pass
    return m_dir, text



def run_app():
    ...