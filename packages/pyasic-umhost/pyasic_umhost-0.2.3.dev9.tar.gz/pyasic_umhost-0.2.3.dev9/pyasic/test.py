import asyncio
import datetime
import json

import requests
from requests.auth import HTTPBasicAuth

from pyasic import get_miner, settings, MinerConfig, MinerNetwork
from pyasic.miners.antminer import BMMinerS19jPro
from pyasic.config.pools import Pool


def print_inheritance(cls, indent=0):
    """Рекурсивно печатает дерево наследования"""
    print('  ' * indent + cls.__name__)
    for base in cls.__bases__:
        print_inheritance(base, indent + 1)


async def main():

    # ip = "10.86.120.86"
    # ip = "10.76.107.252" # L7

    # ip = "10.91.115.27" # M30
    # ip = "10.91.115.58" # M30
    # ip = "10.91.115.71" # M30


    # ip = "10.7.16.226"
    # ip = "10.86.120.136" # -- не работает pool
    # ip = "10.81.120.100" # 'M61VL30'
    # ip = "10.86.120.86"
    # ip = "10.7.11.174" # VNISH
    # ip = "10.7.21.109" # T21
    # ip = "10.86.120.86" # M61VK70  --- version "20251014.18.REL2"
    # ip = "10.86.113.97" # нет доступа к http
    # ip = "10.81.113.161"
    # ip = "10.85.116.160" # .expected_hashrate = -0.003  --- version='20251121.18.Rel2'
    # ip = "10.81.113.109"

    # ip = "10.77.112.12" # Avalon
    # ip = "10.77.112.11"

    # ip = '10.73.112.220'

    # ip = "10.96.106.175" # S19j Pro -- не рабочий -- что-то с сетью
    # ip = "10.96.106.173" # вернул пуллы и вроде работает
    # ip = "10.91.106.49" # S19j Pro -- рабочий

    # ip = "10.91.115.34"
    # ip = "10.91.115.112"

    ip = "10.91.115.104" # Не выходит из сна
    # ip = "10.91.115.105"
    # ip = "10.91.115.48"

    # ip = "10.71.111.113" # AntMiner S19j Pro
    # ip = "10.81.143.178" # Antminer S19 XP+ Hyd

    try:
        # networks = [f"10.7.34.{i}" for i in range(0, 256)]
        # network = MinerNetwork(networks)
        # # Сканируем сеть
        # miners = await network.scan()
        # print(f"Найдено майнеров: {len(miners)}")


        miner = await get_miner(ip=ip)
        print(f"{type(miner)=}")
        print(f"Miner: {miner}")

        # print(await miner.stop_mining())

        # await miner.stop_mining()

        # await miner.resume_mining()
        #
        # await asyncio.sleep(5)

        # cfg: MinerConfig = await miner.get_config()
        # print(f"{cfg.mining_mode=}")

        # await miner.reboot()
        # await asyncio.sleep(5)
        miningMode = await miner.is_mining()
        sleepMode = await miner.is_sleep()
        errors = await miner.get_errors()
        minerData = await miner.get_data()
        # #
        # # print("\n\n")
        # # print(minerData.pools)
        print(f"Is mining: {miningMode}")
        print(f"Sleep mode: {sleepMode}")
        print(f"Errors: {errors}")
        # print(f"{minerData.wattage_limit=}, {minerData.wattage=}")
        print(f"MinerData: {minerData}")

        ### STOP

        # stop = await miner.stop_mining()
        # print(f"Stop mining: {stop}")

        ### RESUME

        # resume = await miner.resume_mining()
        # print(f"Resume mining: {resume}")

        ### REBOOT

        # reboot = await miner.reboot()
        # print(f"Reboot mining: {reboot}")

        ### LED ON
        # fault_light_on = await miner.fault_light_on()
        # print(f"Fault light on: {fault_light_on}")

    except Exception as e:
        print(f"Error:: {e}")


if __name__ == "__main__":
    asyncio.run(main())
