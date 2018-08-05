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
    CYBERNETICSCORE, STALKER, STARGATE, VOIDRAY



class SentdeBot(sc2.BotAI):

    def __init__(self):
        # Make the iterations accessible throughout the class.
        # From sentdex: about 165 iterations per minute.
        self.iterations_per_minute = 10000
        self.max_workers = 65

    # Defines asynchronous methods for the classes.
    async def on_step(self, iteration):
        # Keep track of the iterations.
        self.iteration = iteration
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
        # Check how many probes exist and scale the amount by the Nexuses.
        # Max amount is capped.
        if len(self.units(NEXUS)) * 16 > len(self.units(PROBE)):
            if len(self.units(PROBE)) < self.max_workers:
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

            # If no Gateway is found, try to build one about every two minutes.
            elif len(self.units(GATEWAY)) < \
                    ((self.iteration / self.iterations_per_minute) / 2):
                if self.can_afford(GATEWAY) and not self.already_pending(
                        GATEWAY):
                    print(self.iteration, self.iterations_per_minute,
                          ((self.iteration / self.iterations_per_minute) / 2))
                    await self.build(GATEWAY, near=pylon)

            # If no Stargate is found, try to build one about every two minutes.
            if self.units(CYBERNETICSCORE).ready.exists:
                if len(self.units(STARGATE)) < \
                        ((self.iteration / self.iterations_per_minute) / 2):
                    if self.can_afford(STARGATE) and not self.already_pending(
                            STARGATE):
                        print(self.iteration, self.iterations_per_minute,
                              ((self.iteration / self.iterations_per_minute)
                               / 2))
                        await self.build(STARGATE, near=pylon)

    # Build stalkers as offencive force.
    async def build_offensive_force(self):
        for gw in self.units(GATEWAY).ready.noqueue:
            if not self.units(STALKER).amount > self.units(VOIDRAY).amount:
                if self.can_afford(STALKER) and self.supply_left > 0:
                    await self.do(gw.train(STALKER))

        for sg in self.units(STARGATE).ready.noqueue:
            if self.can_afford(VOIDRAY) and self.supply_left > 0:
                await self.do(sg.train(VOIDRAY))

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
        # {unit: [n to fight, n to defend]}
        aggressive_units = {STALKER: [15, 5],
                            VOIDRAY: [8, 3]}

        for unit in aggressive_units:
            if self.units(STALKER).amount > aggressive_units[unit][0] \
                    and self.units(unit).amount > aggressive_units[unit][1]:
                for s in self.units(unit).idle:
                    await self.do(s.attack(self.find_target(self.state)))

            elif self.units(unit).amount > aggressive_units[unit][1]:
                if len(self.known_enemy_units) > 0:
                    for s in self.units(unit).idle:
                        await self.do(s.attack(random.choice(
                            self.known_enemy_units)))


# Starts the game. Choose the map and the participants, race and difficulty.
run_game(maps.get("AbyssalReefLE"),
         [Bot(Race.Protoss, SentdeBot()),
          Computer(Race.Terran, Difficulty.Medium)],
         realtime=True)
