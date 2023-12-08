#! /bin/env python

'''
'''
import time
import asyncio
import typer

L = list[int]
app = typer.Typer()
tron_url = ["https://api.github.com/repos/tronprotocol/java-tron/releases/latest"]

'''
get data
url https://api.github.com/repos/tronprotocol/java-tron/releases/latest
'''
async def get_url_data(url: str, semaphore: int=10) -> dict:
    from aiohttp import ClientSession
    async with asyncio.Semaphore(semaphore):
        async with ClientSession() as session:
            async with session.get(url) as response:
                res = await response.json()
                return {"url": url, "data": res}


def check_update(data) -> bool:
    f = open("tron.version", "r")
    current_version = f.readline().strip()
    f.close()

    print("current_version: ", current_version)
    print("tag_name: ", data.get("tag_name"))
    print("find data: ", data.get("body").find("Non-mandatory"))

    if data.get("tag_name") != current_version: 
        if data.get("body").find("Non-mandatory") == -1:
            return True

    return False


async def get_releases_main(num: int=10) -> dict:
    # ips = ["f1", "f2", "f3", "f4"]
    # data like {"name": "prod sui chain", "nodes": [{"name": "prod-sui-master-1", "ip": "10.10.10.10"}]}
    task_list = list()
    for i in tron_url:
        task = asyncio.create_task(get_url_data(i))
        task_list.append(task)
    done, pending = await asyncio.wait(task_list, timeout=None)
    for done_task in done:
        x = done_task.result()

        data = x.get("data", dict())
        if check_update(data):
            return {"code": -1, "message": "tron version check success \n has {v} version for update".format(v=data.get("tag_name"))}
        else:
            return {"code": 0, "message": "tron version check success no version for update"}


def update_version_file(version:str) -> bool:
    f = open("tron.version", "w+")
    f.write(version)
    f.close()
    return True

def format_message(command: str, text: str) -> str:
    message = '''<strong>级别状态</strong>: >S1 Triggered\n<strong>触发时间</strong>: {time}\n<strong>监控指标</strong>: {command}\n<strong>错误内容</strong>: {text}'''

    return message.format(time=time.strftime("%a, %d %b %Y %H:%M:%S -UTC", time.gmtime()), command=command, text=text)

def check_result(command: str, result:dict) -> dict:
    if result.get("code") != 0:
        message = format_message(command, result.get("message"))
        data = send_tg(message)
    else:
        data = dict()
    print("send_tg: ", data)
    return data
        

@app.command()
def send_tg(message: str, token: str="", chat_id: str="") -> dict:
    import requests

    tg_url = "https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}&parse_mode=html".format(token=token, chat_id=chat_id, message=message)
    data = requests.get(tg_url)
    return data.json()


@app.command()
def check_version():
    start_time = time.time()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(get_releases_main())
    print("result: ", result)
    print("总耗时: ", time.time()-start_time)
    check_result("Check Tron Release Version", result)
    return result

@app.command()
def update_version(version:str):
    start_time = time.time()
    print("总耗时: ", time.time()-start_time)
    return update_version_file(version)


if __name__ == "__main__":
    app()
