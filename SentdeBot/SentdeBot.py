"""
Based on a tutorial series of sentdex, see YouTube:
https://www.youtube.com/watch?v=v3LJ6VvpfgI&t=1s
"""

import sc2
import random
# print(sc2.__file__)
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, GATEWAY, \
    CYBERNETICSCORE, STALKER


class SentdeBot(sc2.BotAI):
    # Defines asynchronous methods for the classes.
    async def on_step(self, iteration):
        # Automatically limit the workers to as much a two per resource patch.
        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()
        await self.expand()
        await self.offensive_force_buildings()
        await self.build_offensive_force()
        await self.attack()

    # Build new workers at a nexus that is ready.
    async def build_workers(self):
        for nexus in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE):
                await self.do(nexus.train(PROBE))

    # Build new pylons, somewhere close to the a nexus.
    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexuses.first)

    # Look for vespene geysers close to nexuses and build a refinery on top
    # them, if one can afford it.
    async def build_assimilators(self):
        for nexus in self.units(NEXUS).ready:
            vespenes = self.state.vespene_geyser.closer_than(15.0, nexus)
            for vespene in vespenes:
                if not self.can_afford(ASSIMILATOR):
                    break
                worker = self.select_build_worker(vespene.position)
                if worker is None:
                    break
                if not self.units(ASSIMILATOR).closer_than(1.0, vespene).exists:
                    await self.do(worker.build(ASSIMILATOR, vespene))

    # Expand to a new location with resources.
    async def expand(self):
        if self.units(NEXUS).amount < 3 and self.can_afford(NEXUS):
            await self.expand_now()

    #
    async def offensive_force_buildings(self):
        # Find random construction site near random pylon.
        if self.units(PYLON).ready:
            pylon = self.units(PYLON).ready.random

            # Figure out if a gateway exists, as well as a cybernetics core.
            if self.units(GATEWAY).ready and not self.units(CYBERNETICSCORE):
                # Build a cybernetics core.
                if self.can_afford(CYBERNETICSCORE) and not \
                        self.already_pending(CYBERNETICSCORE):
                    await self.build(CYBERNETICSCORE, near=pylon)
            # If no gateway is found, try to build one.
            elif len(self.units(GATEWAY)) < 3:
                if self.can_afford(GATEWAY) and not self.already_pending(
                        GATEWAY):
                    await self.build(GATEWAY, near=pylon)

    # Build stalkers as offencive force.
    async def build_offensive_force(self):
        for gw in self.units(GATEWAY).ready.noqueue:
            if self.can_afford(STALKER) and self.supply_left > 0:
                await self.do(gw.train(STALKER))

    #
    def find_target(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]

    # Attack known enemy units.
    async def attack(self):
        # Offensive part.
        if self.units(STALKER).amount > 15:
            for s in self.units(STALKER).idle:
                await self.do(s.attack(self.find_target(self.state)))

        # More for the defensive part.
        if self.units(STALKER).amount > 3:
            if len(self.known_enemy_units) > 0:
                for s in self.units(STALKER).idle:
                    await self.do(s.attack(random.choice(
                        self.known_enemy_units)))


# Starts the game. Choose the map and the participants, race and difficulty.
run_game(maps.get("AbyssalReefLE"),
         [Bot(Race.Protoss, SentdeBot()),
          Computer(Race.Terran, Difficulty.Medium)],
         realtime=True)
