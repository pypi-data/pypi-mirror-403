from PGram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import UpdateType
from aiogram.types import InlineKeyboardButton, WebAppInfo
from xync_schema.enums import OrderErr

from xync_bot.shared import BoolCd, cur_symbols
from xync_schema.models import Order, User, Transaction, Transfer

from xync_bot.store import Store
from xync_bot.routers import last
from xync_bot.routers.main.handler import mr
from xync_bot.routers.pay.handler import pr
from xync_bot.routers.cond import cr
from xync_bot.routers.send import sd
from xync_bot.routers.hot import hot

au = [
    UpdateType.MESSAGE,
    UpdateType.CALLBACK_QUERY,
    UpdateType.CHAT_MEMBER,
    UpdateType.MY_CHAT_MEMBER,
]  # , UpdateType.CHAT_JOIN_REQUEST


class XyncBot(Bot):
    app_url: str

    def __init__(self, token, cn, app_url: str = None):
        self.app_url = app_url
        super().__init__(token, cn, [hot, sd, cr, pr, mr, last], Store(), DefaultBotProperties(parse_mode="HTML"))

    async def start(self, wh_host: str = None):
        self.dp.workflow_data["xbt"] = self  # todo: refact?
        # self.dp.workflow_data["store"].glob = await Store.Global()  # todo: refact store loading
        await super().start(au, wh_host)
        return self

    # итерация: предоставляем юзеру кнопки для перехода на hot объявления
    async def go_hot(self, user: User, ex_ids: list[int]):
        curr_hot = await user.get_last_hot()
        if curr_hot.msg_ids:
            await self.bot.delete_messages(user.username_id, curr_hot.msg_ids)
            curr_hot.msg_ids = []
        bads, sads, balances = await user.get_hot_ads(ex_ids)
        btns = [
            [
                InlineKeyboardButton(text=t + "🌐", url=bad.get_url()[0]),
                InlineKeyboardButton(text=t + "📱", url=bad.get_url()[1]),
            ]
            for bad in bads
            if (t := f"{bad.ad.price * 10**-2:.2f}{cur_symbols[bad.ad.pair_side.pair.cur_id]} {bad.ad.maker.name}")
        ]
        msg = await self.send(user.username_id, "🟥Sell USDT", btns)
        # и если есть достаточные балансы валют для покупки:
        curr_hot.msg_ids.append(msg.message_id)
        if not sads:
            return
        btns = []
        for sad in sads:
            t = f"{sad.ad.price * 10**-2:.2f} [≤ {balances[sad.ad.pair_side.pair.cur_id]:.2f}]{cur_symbols[sad.ad.pair_side.pair.cur_id]} {sad.ad.maker.name}"
            btns += [
                [
                    InlineKeyboardButton(text=t + "🌐", url=sad.get_url()[0]),
                    InlineKeyboardButton(text=t + "📱", url=sad.get_url()[1]),
                ],
            ]
        msg = await self.send(user.username_id, "🟩Buy USDT", btns)
        curr_hot.msg_ids += [msg.message_id]
        await curr_hot.save()

    async def def_actor(self, uid: int, order: Order):
        """
        Если актор прилетевшего ордера по прогреву еще не связан ни с одним юзером, спрашиваем hot-юзера он ли это
        """
        txt = f"{order.taker.name}:{order.taker.exid} is you?"
        btns = [
            [
                InlineKeyboardButton(text="Yes", callback_data=BoolCd(req="is_you", res=True, xtr=order.id).pack()),
                InlineKeyboardButton(text="No", callback_data=BoolCd(req="is_you", res=False, xtr=order.id).pack()),
            ]
        ]
        await self.send(uid, txt, btns)

    async def hot_result(self, taker_user: User, order: Order):
        res: Order.Result = await order.hot_process(taker_user)
        btns = None
        if not res.err:
            if not isinstance(res.data, Transfer):
                raise NotImplementedError(order)
            txt = (
                f"You have buy {order.quantity * 0.0001:.4f} USDT for {res.data.amount * 0.01:.2f}!\n"
                f"XyncPay balance: {await taker_user.balance(order.ad.pair_side.pair.cur_id) * 0.01:.2f} RUB now"
            )
        elif res.err == OrderErr.party_balance_shortage:
            txt = f"Bro, you can't buy more than {res.data * 0.01:.2f} now! Deposit to XyncPay or Sell more at first"
        elif res.err == OrderErr.i_wait_for_release:
            txt = "Accept the order now, bro!"
            btns = [
                [InlineKeyboardButton(text=str(order.exid), url=f"https://www.bybit.com/p2p/orderList/{order.exid}")]
            ]
        elif res.err == OrderErr.seller_had_confirmed:
            raise ValueError("WTF 7!")
        elif res.err == OrderErr.uncompleted_orders:
            txt = "At first accept previous orders, bro!"
            btns = [
                [InlineKeyboardButton(text=str(order.exid), url=f"https://www.bybit.com/p2p/orderList/{order.exid}")]
                for order in res.data
            ]
        elif res.err == OrderErr.my_balance_shortage:
            await self.send(order.ad.maker.person.user.username_id, "Пополни баланс срочно, HOT ордер висит!")
            _tx = await (await User[0]).send(1, order.ad.maker.person.user.id, order.amount)
            return await order.hot_process(taker_user)
        elif res.err == OrderErr.unimplemented_status:
            await self.send(order.ad.maker.username_id, f"Order {order.exid} unimplemented status {order.status}")
            raise ValueError({"err": "unimplemented status", "res": res, "order": order})
        else:
            raise ValueError({"err": "WTF?", "res": res, "order": order})
        return await self.send(taker_user.username_id, txt, btns)

    async def tx_send_tg(self, tx: Transaction):
        await tx.fetch_related("cur", "sender__username", "receiver__username")
        amt = f"{tx.amount * 10**-tx.cur.scale:.2f} {tx.cur.ticker}"
        btns = [[InlineKeyboardButton(text="Transactions", web_app=WebAppInfo(url=self.app_url + "/history"))]]
        bot_nick = (await self.bot.me()).username
        qr = tx.qr_gen(bot_nick)
        sender = "@" + tx.sender.username.username if tx.sender.username.username else tx.sender.username_id
        await self.send(tx.receiver.username_id, f"{sender} sent you {amt}. <code>#{tx.id.hex}</code>", btns, qr)
        receiver = "@" + tx.receiver.username.username if tx.receiver.username.username else tx.receiver.username_id
        await self.send(tx.sender.username_id, f"You sent {amt} to {receiver}. <code>#{tx.id.hex}</code>", btns)
