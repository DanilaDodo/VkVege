import json
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from config import TOKEN, ADMIN

# Аутентификация
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
admin_id = ADMIN

# Клавиатура
keyboard = VkKeyboard(inline=True)
keyboard.add_button('Новый заказ', color=VkKeyboardColor.POSITIVE)

# JSON и список пиццерий
def pizzerias():
    with open('adress.json', 'r', encoding='utf8') as f:
        adress = json.load(f)
        return adress, [i[0]['action']['label'] for i in adress['buttons']]

def button():
    with open('buttons.json', 'r', encoding='utf8') as fr:
        buttons = json.load(fr)
        return buttons

# Принять одно сообщение и обработать его
def message():
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                return event.text

# Команда "начать"
def start(id, text):
    vk.messages.send(user_id=id, message=text, random_id=0, keyboard=keyboard.get_keyboard())

# Выбор пиццерии
def choice_of_pizzeria(id, text):
    strt, end = 0, 5
    kkey = pizzerias()[0]
    kkey['buttons'] = (pizzerias()[0]['buttons'][strt:end] + button())
    keyboard = json.dumps(kkey, ensure_ascii=False)
    vk.messages.send(user_id=id, message=text, random_id=0, keyboard=keyboard)



# Создание нового адреса доставки
def add_pizzeria(id, text):
    vk.messages.send(user_id=id, message=text, random_id=0)
    for ev in longpoll.listen():
        if ev.type == VkEventType.MESSAGE_NEW:
            if ev.to_me:
                msg = ev.text
                with open('adress.json', 'r', encoding='utf8') as fr:
                    adress = json.load(fr)
                with open('adress.json', 'w', encoding='utf8') as fw:
                    adress['buttons'].append([{"color":"positive","action":{"type":"text","payload":None,"label":msg}}])
                    adress['buttons'].sort(key=lambda x: x[0]['action']['label'])
                    json.dump(adress, fw, ensure_ascii=False)
                vk.messages.send(user_id=id, message=f'Пиццерия по адресу {msg} добавлена', random_id=0)
                break

# Удаление адреса доставки
def delete_pizzeria(id, text):
    choice_of_pizzeria(id, text)
    msg = message()
    with open('adress.json', 'r', encoding='utf8') as fr:
        adress = json.load(fr)
    if msg not in pizzerias()[1]:
        return delete_pizzeria(id, text)
    with open('adress.json', 'w', encoding='utf8') as fw:
        adress['buttons'] = list(filter(lambda x: x[0]['action']['label'] != msg, adress['buttons']))
        json.dump(adress, fw, ensure_ascii=False)

    return vk.messages.send(user_id=id, message=f'Пиццерия по адресу {msg} удалена', random_id=0)

# Чтение нового сообщения
def new_message(event):
    msg = event.text.lower()
    id = event.user_id
    if msg == 'начать':
        start(id, 'Нажмите кнопку ниже, чтоб сделать заказ')
    elif msg == 'новый заказ':
        choice_of_pizzeria(id, 'Выбор пиццерии')
    elif msg == 'добавить пиццерию' and id in admin_id:
        add_pizzeria(id, 'Введите адрес пиццерии, которую необходимо добавить')
    elif msg == 'удалить пиццерию' and id in admin_id:
        delete_pizzeria(id, 'Нажмите на пиццерию, которую необходимо удалить')
    else:
        vk.messages.send(user_id=id, message='Сообщение нераспознанно', random_id=0)


def main():
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                new_message(event)

main()