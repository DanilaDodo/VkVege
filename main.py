import json
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from config import TOKEN, ADMIN

# Аутентификация
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, 237338455)
admin_id = ADMIN
user_state = {}

# Клавиатура
keyboard = VkKeyboard(inline=True)
keyboard.add_button('Новый заказ', color=VkKeyboardColor.POSITIVE)


# JSON и список пиццерий
def pizzerias():
    with open('adress.json', 'r', encoding='utf8') as f:
        adress = json.load(f)
        return adress, [i[0]['action']['label'] for i in adress['buttons']]


# Кнопки страница назад, назад, страница вперед
def button():
    with open('buttons.json', 'r', encoding='utf8') as fb:
        buttons = json.load(fb)
        return buttons


# Список овощей (JSON)
def vege():
    with open('vegetables.json', 'r', encoding='utf8') as fv:
        vege = json.load(fv)
        return vege, [i[0]['action']['label'] for i in vege['buttons']]


# Команда "начать"
def start(id):
    vk.messages.send(user_id=id,
                     message='Нажмите на кнопку ниже, чтоб сделать новый заказ',
                     random_id=0,
                     keyboard=keyboard.get_keyboard())


# Выбор пиццерии
def choice_of_pizzeria(id):
    strt, end = 0, 5
    kkey = pizzerias()[0]
    kkey['buttons'] = (pizzerias()[0]['buttons'][strt:end] + button())
    keyboard = json.dumps(kkey, ensure_ascii=False)
    vk.messages.send(user_id=id,
                     message='Выберите пиццерию',
                     random_id=0,
                     keyboard=keyboard)


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


# Удаление адреса доставки
def delete_pizzeria(id, text):
    adress = pizzerias()[0]
    with open('adress.json', 'w', encoding='utf8') as fw:
        adress['buttons'] = list(filter(lambda x: x[0]['action']['label'] != text, adress['buttons']))
        json.dump(adress, fw, ensure_ascii=False)
    return vk.messages.send(user_id=id,
                            message=f'Пиццерия по адресу {text} удалена',
                            random_id=0)


# Сообщение заказа
def new_order(id, text):
    vk.messages.send(user_id=id,
                     message=f'Заказ для {text}\nНажмите на необходимый товар',
                     random_id=0,
                     keyboard=json.dumps(vege()[0], ensure_ascii=False))


# Сбор количества овощей
def quantity_of_vegetables(id, text):
    vk.messages.send(user_id=id,
                     message=f'{text}\nУкажите количество в килограммах (например, 0.1, 0.5, 1.0)',
                     random_id=0)


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
        new_order(id, text)
        user_state[id]['state'], user_state[id]['pizzeria'] = 'choice of vege', text
    else:
        choice_of_pizzeria(id)


# Выбор овощей
def handle_choice_of_vegetables(id, text):
    print(text)
    if text in vege()[1]:
        user_state[id]['cart'][text], user_state[id]['state'] = user_state[id]['cart'].get(text, 0), 'quantity'
        user_state[id]['current_item'] = text
        quantity_of_vegetables(id, text)
    else:
        new_order(id, user_state[id]['pizzeria'])


# Установка количества
def handle_quantity(id, text):
    veg = user_state[id]['current_item']
    if text.isdigit():
        user_state[id]['cart'][veg] = round(float(text), 1)
        vk.messages.send(user_id=id,
                         message='Ваш заказ\n' +
                                 '\n'.join([f"{i} - {j} кг" for i, j in user_state[id]["cart"].items()]),
                         random_id=0)
        user_state[id]['state'] = 'choice of vege'
        new_order(id, user_state[id]['pizzeria'])
    else:
        quantity_of_vegetables(id, veg)


def main():
    handlers = {
        'adding pizzeria': handle_adding_pizzeria,
        'deleting pizzeria': handle_deleting_pizzeria,
        'choice of pizzeria': handle_choice_of_pizzeria,
        'choice of vege': handle_choice_of_vegetables,
        'quantity': handle_quantity
    }
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.object.message['text']
            id = event.object.message['from_id']
            if id not in user_state:
                user_state[id] = user_state.get(id, {
                    'state': None,
                    'pizzeria': None,
                    'cart': {}})
            state = user_state[id].get('state')
            if msg.lower() == 'начать':
                start(id)
                user_state[id]['state'] = 'starting'
            elif msg.lower() == 'новый заказ' and state not in handlers:
                choice_of_pizzeria(id)
                user_state[id]['state'] = 'choice of pizzeria'
            elif msg.lower() == 'добавить пиццерию' and state not in handlers:
                vk.messages.send(user_id=id,
                                 message=f'Введите пиццерию, которую необходимо добавить',
                                 random_id=0)
                user_state[id]['state'] = 'adding pizzeria'
            elif msg.lower() == 'удалить пиццерию' and state not in handlers:
                choice_of_pizzeria(id)
                user_state[id]['state'] = 'deleting pizzeria'
            else:
                handler = handlers.get(state)
                if handler:
                    handler(id, msg)
                else:
                    vk.messages.send(user_id=id,
                                     message=f'Сообщение нераспознанно',
                                     random_id=0)


main()
