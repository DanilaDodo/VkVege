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
        return json.dumps(vege, ensure_ascii=False)


# Команда "начать"
def start(id):
    vk.messages.send(user_id=id, message='Нажмите на кнопку ниже, чтоб сделать новый заказ', random_id=0, keyboard=keyboard.get_keyboard())


# Выбор пиццерии
def choice_of_pizzeria(id):
    strt, end = 0, 5
    kkey = pizzerias()[0]
    kkey['buttons'] = (pizzerias()[0]['buttons'][strt:end] + button())
    keyboard = json.dumps(kkey, ensure_ascii=False)
    vk.messages.send(user_id=id, message='Выберите пиццерию', random_id=0, keyboard=keyboard)


# Создание нового адреса доставки
def add_pizzeria(id, text):
    with open('adress.json', 'r', encoding='utf8') as fr:
        adress = json.load(fr)
    with open('adress.json', 'w', encoding='utf8') as fw:
        adress['buttons'].append([{"color":"positive","action":{"type":"text","payload":None,"label":text}}])
        adress['buttons'].sort(key=lambda x: x[0]['action']['label'])
        json.dump(adress, fw, ensure_ascii=False)
    vk.messages.send(user_id=id, message=f'Пиццерия по адресу {text} добавлена', random_id=0)


# Удаление адреса доставки
def delete_pizzeria(id, text):
    adress = pizzerias()[0]
    with open('adress.json', 'w', encoding='utf8') as fw:
        adress['buttons'] = list(filter(lambda x: x[0]['action']['label'] != text, adress['buttons']))
        json.dump(adress, fw, ensure_ascii=False)
    return vk.messages.send(user_id=id, message=f'Пиццерия по адресу {text} удалена', random_id=0)


# Сообщение заказа
def new_order(id, text):
    vk.messages.send(user_id=id, message=f'Заказ для {text}\nНажмите на необходимый товар', random_id=0, keyboard=vege())


def main():
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.object.message['text']
            id = event.object.message['from_id']
            if msg.lower() == 'начать':
                start(id)
                user_state[id] = 'starting'
            elif msg.lower() == 'новый заказ':
                choice_of_pizzeria(id)
                user_state[id] = 'choice_of_pizzeria'
            elif msg.lower() == 'добавить пиццерию':
                vk.messages.send(user_id=id, message=f'Введите пиццерию, которую необходимо добавить', random_id=0)
                user_state[id] = 'adding pizzeria'
            elif msg.lower() == 'удалить пиццерию':
                choice_of_pizzeria(id)
                user_state[id] = 'deleting pizzeria'
            else:
                if user_state[id] == 'adding pizzeria' and id in admin_id:
                    add_pizzeria(id, msg)
                    user_state[id] = None
                elif user_state[id] == 'choice_of_pizzeria' and msg in pizzerias()[1]:
                    new_order(id, msg)
                    user_state[id] = 'ordering'
                elif user_state[id] == 'deleting pizzeria' and msg in pizzerias()[1]:
                    delete_pizzeria(id, msg)
                    user_state[id] = None
                else:
                    vk.messages.send(user_id=id, message=f'Сообщение нераспознанно', random_id=0)


main()
