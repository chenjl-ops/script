#! /bin/env python3.9
 
import time
import asyncio
import typer
 
L = list[int]
app = typer.Typer()
 
check_urls = ["http://10.56.32.138:8090/wallet/getblock", "http://10.56.36.114:8090/wallet/getblock"]
#{"blockID":"000000000357f367b7532f871f2478b4fe81adb926461c253b013e522f73f583","block_header":{"raw_data":{"number":56095591,"txTrieRoot":"5ff7c22db059836536e45cc52e5dea537631ac3b25bdbfbf9be52247f728637b","witness_address":"4162398d516b555ac64af24416e05c199c01823048","parentHash":"000000000357f36630a81d958ee20aac37b483ff937c975b8b6a724e3cee0f8a","version":28,"timestamp":1698918711000},"witness_signature":"35bd9eadc4e3084f8bfeefb59e9f343103b17525ba7995633da940264cff254a0d8d41a3bfd9c6de47ac2378c1e445e4fa5dd9ee363ac85fe3ca4b7f42fe82ba00"}}
tron_url = "https://apilist.tronscanapi.com/api/system/status"
#{"database":{"block":56095588,"confirmedBlock":56095570},"sync":{"progress":99.99999732599234},"network":{"type":"mainnet"},"full":{"block":56095588},"solidity":{"block":56095570}}
 
async def get_check_data_num(k: str, url: str, semaphore: int=10) -> dict:
    from aiohttp import ClientSession
    async with asyncio.Semaphore(semaphore):
        async with ClientSession() as session:
            try:
                async with session.get(url) as response:
                    res = await response.json()
                    return {"key": k, "data": res, "url": url, "code": 0}
            except Exception as e:
                print("error: ", e)
                return {"key": k, "data": dict(), "url": url, "code": -1}
 
def check_block_num(l: L, num: int=6) -> dict:
    x = 0
    for i in l:
        if i.get("key") == "1":
            if i.get("code") == 0:
                x = i.get("data").get("database").get("block")
            else:
                return {"code": 2, "message": "TRON URL request error response: {data}".format(data=i)}
 
    messages = list()
    for i in l:
        if i.get("key") == "2":
            if i.get("code") == 0:
                y = i.get("data").get("block_header").get("raw_data").get("number")
                if x - y >= num:
                    messages.append("URL: {url} block sync has error then {num}\n TRON Height: {x}, Node Height: {y}\n -------------------- ".format(url=i.get("url"), num=num, x=x, y=y))
            else:
                messages.append("URL: {url} request error".format(url=i.get("url")))
    if len(messages) == 1:
        return {"code": 2, "message": "\n".join(messages)}
    elif len(messages) >= 2:
        return {"code": 1, "message": "\n".join(messages)}
    else:
        return {"code": 0, "message": "sync success"}
 
# test
async def get_tron_data() -> list:
    task_list = list()
    task_list.append(asyncio.create_task(get_check_data_num("1", tron_url)))
    for url in check_urls:
        task = asyncio.create_task(get_check_data_num("2", url))
        task_list.append(task)
    done, pending = await asyncio.wait(task_list, timeout=None)
    l = list()
    for done_task in done:
        x = done_task.result()
        l.append(x)
        print("result: ", x)
        print("========"*10)
    return check_block_num(l)
 
def format_message(code: int, command: str, text: str) -> str:
    message = '''<strong>级别状态</strong>: >S{code} Triggered\n<strong>触发时间</strong>: {time}\n<strong>监控指标</strong>: {command}\n<strong>错误内容</strong>: {text}'''
 
    return message.format(code=code, time=time.strftime("%a, %d %b %Y %H:%M:%S -UTC", time.gmtime()), command=command, text=text)
 
def check_result(command: str, result:dict) -> dict:
    print("check_result result: ", result)
    if result.get("code") != 0:
        message = format_message(result.get("code"), command, result.get("message"))
        data = send_tg(message)
    else:
        data = dict()
    print("send_tg: ", data)
    return data
 
@app.command()
def send_tg(message: str, token: str="xxxx", chat_id: str="xxxx") -> dict:
    import requests
 
    tg_url = "https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}&parse_mode=html".format(token=token, chat_id=chat_id, message=message)
    data = requests.get(tg_url)
    return data.json()
 
@app.command()
def main(t: str):
    print("main test")
 
@app.command()
def check_tron():
    start_time = time.time()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(get_tron_data())
    print("result: ", result)
    print("总耗时: ", time.time()-start_time)
    check_result("check tron block", result)
    return result
     
 
if __name__ == "__main__":
    app()
