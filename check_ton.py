import asyncio

from pytoniq import LiteClient
import typer

CONFIG_DATA = [
    {
        "ip": "0.0.0.0",
        "port": 00000,
        "id": {
            "@type": "pub.ed25519",
            "key": "xxxxxxxxxx===="
        }
    }
]

TON_API_URL = "https://tonapi.io"
TON_APT_PATH = "/v2/liteserver/get_masterchain_info"

L = list[dict]

app = typer.Typer()


async def get_ton_chain_info(url: str, path: str, semaphore: int = 10) -> dict:
    from aiohttp import ClientSession
    async with asyncio.Semaphore(semaphore):
        async with ClientSession() as session:
            async with session.get(url + path) as response:
                res = await response.json(content_type=None)
                return {"url": url, "data": res}


async def get_ton_full_node_by_self(host: str, port: int, server_pub_key: str) -> dict:
    client = LiteClient(
        host=host,
        port=port,
        server_pub_key=server_pub_key
    )

    await client.connect()
    data = await client.get_masterchain_info()
    await client.close()
    return {"url": host, "data": data}


async def get_last_block_info(data: list, num: int = 3, alter: bool = False) -> dict:
    task_list = list()

    # default 官方节点接口
    task = asyncio.create_task(get_ton_chain_info(TON_API_URL, TON_APT_PATH))
    task_list.append(task)

    # 自建节点
    for conf in data:
        task = asyncio.create_task(get_ton_full_node_by_self(conf["ip"], conf["port"], conf["id"]["key"]))
        task_list.append(task)

    done, pending = await asyncio.wait(task_list, timeout=None)
    l = list()
    for done_task in done:
        x = done_task.result()
        l.append(x)

    if alter:
        if check_results(l):
            return {"code": 0, "message": "check success"}
        else:
            return {"code": -2, "message": "ton fullnode sync gt " + str(num)}
    else:
        message = marge_message(l)
        return send_tg("\n".join(message))


def marge_message(l: L) -> list:
    message = list()
    for i in l:
        if "@type" in i["data"]:
            t = i["data"]["@type"]
        else:
            t = "官方"
        message.append("{url}@{type}: {seqno}".format(url=i["url"], type=t, seqno=i["data"]["last"]["seqno"]))
    return message


def check_results(l: L, num: int = 3) -> bool:
    ton_main_seqno = 0

    for x in l:
        if "@type" in x["data"]:
            ton_main_seqno = x["data"]["last"]["seqno"]

    for y in l:
        if "@type" not in y["data"]:
            if ton_main_seqno - y["data"]["last"]["seqno"] >= num:
                return False
    return True


@app.command()
def send_tg(message: str, token: str, chat_id: str) -> dict:
    import requests

    tg_url = "https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}&parse_mode=html".format(token=token, chat_id=chat_id, message=message)
    data = requests.get(tg_url)
    return data.json()


@app.command()
def alter_check_ton():
    import time
    start_time = time.time()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(get_last_block_info(CONFIG_DATA, num=3, alter=True))
    print("result: ", result)
    print("总耗时: ", time.time() - start_time)
    if result.get("code") != 0:
        send_tg(result.get("message"))
    return result


@app.command()
def send_check_ton_info():
    import time
    start_time = time.time()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(get_last_block_info(CONFIG_DATA, num=3, alter=False))
    print("result: ", result)
    print("总耗时: ", time.time() - start_time)
    return result


if __name__ == '__main__':
    app()
