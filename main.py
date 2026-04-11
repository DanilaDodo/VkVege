from config import TOKEN
from vkbottle.bot import Bot, Message, MessageEvent
from vkbottle import Keyboard, KeyboardButtonColor, Text, Callback
from vkbottle import BaseStateGroup, GroupEventType
from vkbottle import BuiltinStateDispenser
import json
import asyncio

bot = Bot(token=TOKEN)

# Состояния
class SuperStates(BaseStateGroup):
    START_STATE = 'start'
    CHOICE_OF_PIZZERIA_STATE = 'choice of pizzeria'
    ADD_PIZZERIA_STATE = 'add pizzeria'

# Data
with open('pizzerias.json', 'r', encoding='utf8') as f:
    pizzerias = json.load(f)

with open('buttons.json', 'r', encoding='utf8') as f:
    butt = json.load(f)


# Выбор пиццерии
async def choice_of_pizzeria(id, page=1):
    buttons = Keyboard(one_time=False, inline=True)
    limit = 5 * page
    for p in pizzerias[limit - 5:limit]:
        buttons.add(Text(p),
                    color=KeyboardButtonColor.POSITIVE)
        buttons.row()
    await button(buttons, page)
    return buttons


# Пагинация
async def button(buttons, page=1):
    if not page:
        new_order = Keyboard(one_time=False, inline=True)
        new_order.add(Text('Новый заказ'),
                      color=KeyboardButtonColor.POSITIVE)
        return new_order
    elif page == 1:
        for i in range(1, 3):
            label = list(butt[i].keys())[0]
            buttons.add(Callback(label,
                                 payload={'action': butt[i][label]['action']}),
                        color=KeyboardButtonColor(butt[i][label]['color']))
    elif page == len(pizzerias) // 4:
        for i in range(0, 2):
            label = list(butt[i].keys())[0]
            buttons.add(Callback(label,
                                 payload={'action': butt[i][label]['action']}),
                        color=KeyboardButtonColor(butt[i][label]['color']))
    else:
        for i in range(0, 3):
            label = list(butt[i].keys())[0]
            buttons.add(Callback(label,
                                 payload={'action': butt[i][label]['action']}),
                        color=KeyboardButtonColor(butt[i][label]['color']))
    return buttons


# Служебная пагинация
@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def turn_page(event: MessageEvent):
    try:
        await bot.api.messages.delete(peer_id=event.peer_id,
                                      cmids=event.conversation_message_id,
                                      delete_for_all=True)
        turning = event.payload['action']
        if turning:
            state = await bot.state_dispenser.get(event.peer_id)
            page = state.payload.get('page', 1)
            await bot.state_dispenser.set(event.peer_id,
                                          SuperStates.CHOICE_OF_PIZZERIA_STATE,
                                          page=page + turning)
            await event.send_message('Выберите пиццерию:',
                                     keyboard=await choice_of_pizzeria(event.peer_id, page + turning))
        else:
            await bot.state_dispenser.set(event.peer_id,
                                          SuperStates.START_STATE,
                                          page=0)
            await event.send_message('Нажмите на кнопку ниже, чтоб сделать новый заказ',
                                     keyboard=await button(butt, 0))
    except Exception as e:
        print(f'Произошла ошибка - {e}')

# Хендлер добавления пиццерии
@bot.on.message(state=SuperStates.ADD_PIZZERIA_STATE)
async def add_pizzeria_handler(message):
    with open('pizzerias.json', 'w', encoding='utf8') as fw:
        pizzerias.append(message.text)
        json.dump(sorted(pizzerias), fw, ensure_ascii=False)
    await message.answer(f"Пиццерия по адресу {message.text} добавлена")


# ADD_PIZZERIA_STATE
@bot.on.message(fuzzy='добавить пиццерию')
async def add_pizzeria(message):
    await bot.state_dispenser.set(message.peer_id,
                                  SuperStates.ADD_PIZZERIA_STATE,
                                  page=1)
    await message.answer('Введите адрес пиццерии, которую нужно добавить')


# START_STATE
@bot.on.message(fuzzy=['/start', 'начать'])
async def start_handler(message):
    await bot.state_dispenser.set(message.peer_id,
                                  SuperStates.START_STATE,
                                  page=0)
    await message.answer('Нажмите на кнопку ниже, чтоб сделать новый заказ',
                         keyboard=await button(butt, 0))


# CHOICE_OF_PIZZERIA_STATE
@bot.on.message(fuzzy='новый заказ')
async def new_order_handler(message):
    await bot.state_dispenser.set(message.peer_id,
                                  SuperStates.CHOICE_OF_PIZZERIA_STATE,
                                  page=1)
    await message.answer('Выберите пиццерию:',
                         keyboard=await choice_of_pizzeria(message.peer_id))



bot.run_forever()
