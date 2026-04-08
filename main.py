import json
import vk_api
import time
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from config import TOKEN, ADMIN

# Аутентификация
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, 237338455)
admin_id = ADMIN
user_state = {}
PIZZERIAS = None
VEGETABLES = None
BRIEF = None

# Клавиатура
keyboard = VkKeyboard(inline=True)
keyboard.add_button('Новый заказ', color=VkKeyboardColor.POSITIVE)


# Список пиццерий (JSON)
def load_pizzerias():
    global PIZZERIAS
    with open('adress.json', 'r', encoding='utf8') as f:
        PIZZERIAS = json.load(f)


# Кэширование пиццерии
def pizzerias():
    return PIZZERIAS, [i[0]['action']['label'] for i in PIZZERIAS['buttons']]


# Кнопки страница назад, назад, страница вперед
def button(page):
    with open('buttons.json', 'r', encoding='utf8') as fb:
        buttons = json.load(fb)
    if page == 1:
        buttons[0] = buttons[0][1:3]
    elif page == len(pizzerias()[1]) // 4:
        buttons[0] = buttons[0][:2]
    elif page == 0:
        buttons[0] = buttons[0][1:2]
    elif page == -1:
        buttons[0] = buttons[0][3:4]
    else:
        buttons[0] = buttons[0][:3]
    return buttons


# Список овощей (JSON)
def load_vege():
    global VEGETABLES
    with open('vegetables.json', 'r', encoding='utf8') as fv:
        VEGETABLES = json.load(fv)


# Кэширование пиццерии
def vege():
    return VEGETABLES, [i[j]['action']['label'] for j in range(2) for i in VEGETABLES['buttons']]


# Сводка
def load_brief():
    global BRIEF
    with open('brief.json', 'r', encoding='utf8') as ff:
        BRIEF = json.load(ff)


# Кэширование сводки
def briefs():
    return BRIEF


# Команда "начать"
def start(id):
    vk.messages.send(user_id=id,
                     message='Нажмите на кнопку ниже, чтоб сделать новый заказ',
                     random_id=0,
                     keyboard=keyboard.get_keyboard())


# Очистить сводку
def clear_of_brief():
    output = {}
    with open('brief.json', 'w', encoding='utf8') as fw:
        for i in pizzerias()[1]:
            output[i] = output.get(i, {i: 0 for i in vege()[1]})
        json.dump(output, fw, ensure_ascii=False)
    load_brief()


# Выбор пиццерии
def choice_of_pizzeria(id, page=1):
    limit = 5 * page
    kkey = pizzerias()[0].copy()
    kkey['buttons'] = (pizzerias()[0]['buttons'][limit - 5:limit] + button(page))
    kkey = json.dumps(kkey, ensure_ascii=False)
    vk.messages.send(user_id=id,
                     message='Выберите пиццерию',
                     random_id=0,
                     keyboard=kkey)


# Создание нового адреса доставки
def add_pizzeria(id, text):
    with open('adress.json', 'r', encoding='utf8') as fr:
        adress = json.load(fr)
    with open('adress.json', 'w', encoding='utf8') as fw:
        adress['buttons'].append([{"color":"positive","action":{"type":"text","payload":None,"label":text}}])
        adress['buttons'].sort(key=lambda x: x[0]['action']['label'])
        json.dump(adress, fw, ensure_ascii=False)
    vk.messages.send(user_id=id,
                     message=f'Пиццерия по адресу {text} добавлена',
                     random_id=0)
    load_pizzerias()


# Удаление адреса доставки
def delete_pizzeria(id, text):
    adress = pizzerias()[0]
    with open('adress.json', 'w', encoding='utf8') as fw:
        adress['buttons'] = list(filter(lambda x: x[0]['action']['label'] != text, adress['buttons']))
        json.dump(adress, fw, ensure_ascii=False)
    load_pizzerias()
    vk.messages.send(user_id=id,
                     message=f'Пиццерия по адресу {text} удалена',
                     random_id=0)


# Выбор овощей
def new_order(id, text):
    kkey = vege()[0].copy()
    kkey['buttons'] = (kkey['buttons'] + button(0))
    kkey = json.dumps(kkey, ensure_ascii=False)
    vk.messages.send(user_id=id,
                     message=f'Заказ для {text}\nНажмите на необходимый товар',
                     random_id=0,
                     keyboard=kkey)


# Сбор количества овощей
def quantity_of_vegetables(id, text):
    vk.messages.send(user_id=id,
                     message=f'{text}\nУкажите количество в килограммах (например, 0.1, 0.5, 1.0)',
                     random_id=0)


# Обработка перелистывания страницы и выхода
def turn_page(id, cmid, pay):
    try:
        vk.messages.delete(peer_id=id, cmids=cmid, delete_for_all=1)
        if pay == 0:
            start(id)
            user_state.pop(id, None)
        else:
            user_state[id]['page'] += pay
            choice_of_pizzeria(id, user_state[id]['page'])
    except Exception as e:
        print(f'Ошибка при удалении сообщения: {e}')


# Обработчик состояний
# Добавление пиццерии
def handle_adding_pizzeria(id, text):
    add_pizzeria(id, text)
    user_state[id].pop('state', None)


# Удаление пиццерии
def handle_deleting_pizzeria(id, text):
    if text in pizzerias()[1]:
        delete_pizzeria(id, text)
        user_state[id].pop('state', None)
    else:
        choice_of_pizzeria(id)


# Выбор пиццерии
def handle_choice_of_pizzeria(id, text):
    if text in pizzerias()[1]:
        user_state[id] = {
            'state': 'choice of vege',
            'pizzeria': text,
            'cart': {
                i: 0 for i in vege()[1]
            },
            'page': 1
        }
        new_order(id, text)
    else:
        choice_of_pizzeria(id)


# Выбор овощей
def handle_choice_of_vegetables(id, text):
    if text in vege()[1]:
        user_state[id]['cart'][text], user_state[id]['state'] = user_state[id]['cart'].get(text, 0), 'quantity'
        user_state[id]['current_item'] = text
        handle_quantity(id, text)
    else:
        new_order(id, user_state[id]['pizzeria'])


# Установка количества
def handle_quantity(id, text):
    veg = user_state[id]['current_item']
    try:
        user_state[id]['cart'][veg] = round(float(text), 1)
    except ValueError:
        quantity_of_vegetables(id, veg)
    else:
        vk.messages.send(user_id=id,
                         message='Ваш заказ\n' +
                                 '\n'.join([f"{i} - {j} кг" for i, j in user_state[id]["cart"].items()]),
                         random_id=0,
                         keyboard=json.dumps({"one_time": False, "inline": True, "buttons": button(-1)},
                                             ensure_ascii=False))
        user_state[id]['state'] = 'choice of vege'
        new_order(id, user_state[id]['pizzeria'])


# Обработчик команд
# /start
def command_start(id):
    start(id)
    user_state[id]['state'] = 'starting'


# Новый заказ
def command_new_order(id):
    choice_of_pizzeria(id)
    user_state[id]['state'] = 'choice of pizzeria'


# Добавить пиццерию
def command_add_pizzeria(id):
    vk.messages.send(user_id=id,
                     message=f'Введите пиццерию, которую необходимо добавить',
                     random_id=0)
    user_state[id]['state'] = 'adding pizzeria'


# Удалить пиццерию
def command_delete_pizzeria(id):
    choice_of_pizzeria(id)
    user_state[id]['state'] = 'deleting pizzeria'


# Отправить заказ
def command_send(id):
    print(user_state)
    for i in admin_id:
        vk.messages.send(user_id=i,
                         message=f'{user_state[id]["pizzeria"]}\n' + '\n'.join(f'{key}: {value}' for key, value in user_state[id]["cart"].items()),
                         random_id=0)
    brief = briefs()
    with open('brief.json', 'w', encoding='utf8') as fw:
        for i in brief:
            if brief[i] != user_state[id]["cart"] and i == user_state[id]['pizzeria']:
                brief[i] = user_state[id]["cart"]
        json.dump(brief, fw, ensure_ascii=False)
    load_brief()
    vk.messages.send(user_id=id,
                     message=f'Заказ для {user_state[id]["pizzeria"]} успешно отправлен',
                     random_id=0)
    command_start(id)


# Очистить сводку
def command_clear_of_brief(id):
    clear_of_brief()
    vk.messages.send(user_id=id,
                     message='Сводка успешно очищена',
                     random_id=0)


def main():
    time.sleep(1)
    handlers = {
        'adding pizzeria': handle_adding_pizzeria,
        'deleting pizzeria': handle_deleting_pizzeria,
        'choice of pizzeria': handle_choice_of_pizzeria,
        'choice of vege': handle_choice_of_vegetables,
        'quantity': handle_quantity,
    }
    commands = {
        'начать': command_start,
        'новый заказ': command_new_order,
        'добавить пиццерию': command_add_pizzeria,
        'удалить пиццерию': command_delete_pizzeria,
        'отправить заказ': command_send,
        'очистить сводку': command_clear_of_brief

    }
    load_vege()
    load_pizzerias()
    load_brief()
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.object.message['text']
            id = event.object.message['from_id']
            if id not in user_state:
                user_state[id] = {
                    'state': None,
                    'pizzeria': None,
                    'cart': {
                        i: 0 for i in vege()[1]
                    },
                    'page': 1
                }
            state = user_state[id].get('state')
            command = commands.get(msg.lower())
            if command:
                command(id)
            else:
                handler = handlers.get(state)
                if handler:
                    handler(id, msg)
                else:
                    vk.messages.send(user_id=id,
                                     message=f'Сообщение нераспознанно',
                                     random_id=0)
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            user_id = event.object['user_id']
            cmid = event.object['conversation_message_id']
            payload = event.object.payload['actions']
            turn_page(user_id, cmid, payload)


while True:
    try:
        main()
    except Exception as e:
        print(f'Произошла ошибка: {e}')
        time.sleep(5)
