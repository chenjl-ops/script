#! /bin/env python

'''
highest_known_checkpoint 3618906
highest_synced_checkpoint 3618901
highest_verified_checkpoint 3618901
'''
import time
import asyncio
import typer

L = list[int]
app = typer.Typer()
check_data = {"name": "sui test chain", "nodes": [{"name":"f1", "ip": "f1"}, {"name": "f2", "ip": "f2"}, {"name": "f3", "ip": "f3"}, {"name":"f4", "ip": "f4"}]}

'''
highest_synced_checkpoint
'''
async def get_check_data_num(name: str, url: str, semaphore: int=10) -> dict:
    from aiohttp import ClientSession
    async with asyncio.Semaphore(semaphore):
        async with ClientSession() as session:
            async with session.get(url + "/metrics") as response:
                res = await response.text()
                for i in res.split("\n"):
                    if i.startswith("highest_synced_checkpoint"):
                        return {"name": name, "num": int(i.split()[1])}


# l is list like [3618901, 3618902, 3618903, 3618904] return true or false
def check_checkpoint_num(l: L, num: int=3) -> bool:
    if len(l) < 1:
        return False # check node num must lg 2
    else:
        l.sort(reverse=True)
        if l[0] - l[-1] >= num:
            return False
        else:
            return True


'''
check sui chain cluster 
'''
async def get_cluster_main(data:dict, num: int=10) -> dict:
    # ips = ["f1", "f2", "f3", "f4"]
    # data like {"name": "prod sui chain", "nodes": [{"name": "prod-sui-master-1", "ip": "10.10.10.10"}]}
    task_list = list()
    if isinstance(data, dict):
        for i in data["nodes"]:
            url = "http://" + i.get("ip") + ":37212"
            task = asyncio.create_task(get_check_data_num(i.get("name"), url))
            task_list.append(task)
        done, pending = await asyncio.wait(task_list, timeout=None)
        l = list()
        for done_task in done:
            x = done_task.result()
            l.append(x.get("num"))
        if check_checkpoint_num(l, num):
            return {"code": 0, "message": data["name"] + " check success"}
        else:
            return {"code": -2, "message": data["name"] + " sync num gt " + str(num)}
    else:
        return {"code": -1, "message": "check data type error, ep: {'name': 'prod sui chain', 'nodes': [{'name': 'prod-sui-master-1', 'ip': '10.10.10.10'}, {'name': 'prod-sui-master-2', 'ip': '10.10.10.11'}]}"}


'''
check sui node 
'''
async def get_node_main(data: dict, sleep_time: int=5) -> dict:
    # data ep: {"name": "prod sui chain", "nodes": [{"name": "prod-sui-master-1", "ip": "10.10.10.10"}]}
    import time
    message_list = list()
    if isinstance(data, dict):
        task_list = list()
        for i in data["nodes"]:
            url = "http://" + i.get("ip") + ":37212"
            task = asyncio.create_task(get_check_data_num(i.get("name"), url))
            task_list.append(task)
        done, pending = await asyncio.wait(task_list, timeout=None)
        l1 = list()
        for done_task in done:
            x = done_task.result()
            l1.append(x)

        time.sleep(sleep_time)
        task_list = list()
        for i in data["nodes"]:
            url = "http://" + i.get("ip") + ":37212"
            task = asyncio.create_task(get_check_data_num(i.get("name"), url))
            task_list.append(task)
        done, pending = await asyncio.wait(task_list, timeout=None)
        l2 = list()
        for done_task in done:
            x = done_task.result()
            l2.append(x)

        for x in l1:
            for y in l2:
                if x.get("name") == y.get("name"):
                    if y.get("num") - x.get("num") == 0:                        
                        message_list.append("node_name: {name}, has {t}s no sync ".format(name=x.get("name"), t=sleep_time))

        if message_list:
            return {"code": -2, "message": "\n".join(message_list)}
        else:
            return {"code": 0, "message": data["name"] + " all nodes sync success"}
            pass
    else:
        return {"code": -1, "message": "check data type error, ep: {'name': 'prod sui chain', 'nodes': [{'name': 'prod-sui-master-1', 'ip': '10.10.10.10'}, {'name': 'prod-sui-master-2', 'ip': '10.10.10.11'}]}"}


@app.command()
def main(t: str):
    start_time = time.time()
    loop = asyncio.get_event_loop()
    if t == "cluster":
        result = loop.run_until_complete(get_cluster_main(check_data))
    elif t == "nodes":
        result = loop.run_until_complete(get_node_main(check_data))
    else:
        result = {"code": -3, "message": "{t} not supported yet".format(t=t)}
    print("result: ", result)
    print("总耗时: ", time.time()-start_time)
    return result

@app.command()
def check_cluster():
    start_time = time.time()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(get_cluster_main(check_data))
    print("result: ", result)
    print("总耗时: ", time.time()-start_time)
    return result

@app.command()
def check_nodes():
    start_time = time.time()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(get_node_main(check_data))
    print("result: ", result)
    print("总耗时: ", time.time()-start_time)
    return result


if __name__ == "__main__":
    app()
