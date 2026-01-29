import logging
from typing import Literal

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton

from xync_bot.shared import BoolCd
from xync_schema import models

hot = Router(name="hot")


class HotCd(CallbackData, prefix="hot"):
    typ: Literal["sell", "buy"]
    cex: int = 4


@hot.message(Command("hot"))
async def start(msg: Message, xbt: "XyncBot"):  # noqa: F821
    user = await models.User.get(username_id=msg.from_user.id)
    await xbt.go_hot(user, [4])


@hot.callback_query(BoolCd.filter(F.req.__eq__("is_you")))
async def is_you(query: CallbackQuery, callback_data: BoolCd, xbt: "XyncBot"):  # noqa: F821
    if not callback_data.res:
        try:
            await query.message.delete()
        except TelegramBadRequest as e:
            logging.error(e)
        return await query.answer("ok, sorry")
    user_person = await models.Person.get(user__username_id=query.from_user.id).prefetch_related("user__username")
    order = await models.Order.get(id=callback_data.xtr).prefetch_related(
        "ad__pair_side__pair", "ad__my_ad", "ad__maker", "taker"
    )
    actor_person: models.Person = await models.Person.get(actors=order.taker_id).prefetch_related("user")
    user: models.User = user_person.user
    user_txt = f"Юзер{user.id} @{user.username.username} {user.username_id}:{user.first_name}"
    actor_txt = f"Актор#{order.taker_id} {order.taker.exid}:{order.taker.name}"
    txt = f"{user_txt} прожал что {actor_txt} его!"
    logging.info(txt)
    btns = [[InlineKeyboardButton(text=f"👀{order.exid}", url=f"https://www.bybit.com/p2p/orderList/{order.exid}")]]
    await xbt.send(193017646, txt, btns)

    if actor_person.id == user_person.id:
        txt = f"{user_txt} и {actor_txt} уже оба в персоне:{actor_person.id}"
        logging.warning(txt)
        await xbt.send(193017646, txt, btns)
        try:
            await query.message.delete()
        except TelegramBadRequest as e:
            logging.error(e)
        return await query.answer("Уже ок")

    elif actor_person.user:
        txt = f"У {actor_txt} уже есть другой юзер#{actor_person.user.id}:{actor_person.user.username_id}"
        await xbt.send(193017646, "ПИЗДЕЦ!!! " + txt, btns)
        try:
            await query.message.delete()
        except TelegramBadRequest as e:
            logging.error(e)
        logging.exception(txt)
        return await query.answer("Ошибка, напишите в поддержку @XyncPay")

    # переназначаем тг-юзеру персону тейкера, вместо старой персоны юзера
    actor_person.tg_id = user_person.tg_id
    await models.User.filter(person_id=user_person.id).update(person_id=actor_person.id)
    # заново получаем персону юзера из бд
    user_person = await models.Person.get(id=user_person.id).prefetch_related("user")
    # и у нее уже не должно быть юзера (тк этого юзера уже тейкерская персона, а не эта)
    if user_person.user:
        txt = f"У персоны#{user_person.id}:{user_person.name} Уже не должно быть юзера, но есть #{user_person.user.id}:{user_person.user.username_id}"
        logging.error(txt)
        await xbt.send(193017646, txt, btns)
        try:
            await query.message.delete()
        except TelegramBadRequest as e:
            logging.error(e)
        return await query.answer("Ошибка, напишите в поддержку @XyncPay")

    await user_person.delete()
    await actor_person.save(update_fields=["tg_id"])
    await actor_person.fetch_related("user")
    # todo: пиздец какой то с юзером, рефакторь
    await xbt.hot_result(actor_person.user, order)

    try:
        await query.message.delete()
    except TelegramBadRequest as e:
        logging.error(e)
    return await query.answer("ok")
