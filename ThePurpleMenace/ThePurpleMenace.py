import sc2
import random
# print(sc2.__file__)
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import HATCHERY, EXTRACTOR, SPAWNINGPOOL, LARVA, OVERLORD, \
    DRONE, ZERGLING


# The Purple Menace -- a Zerg hive mind,
# about to cover the world in creep and gore.
class ThePurpleMenace(sc2.BotAI):
    async def on_step(self, iteration):
        # Limit the workers to as much a three per resource patch.
        await self.distribute_workers()
        await self.spawn_overlord()
        await self.morph_drone()
        await self.build_extractor()
        await self.build_spawningpool()
        await self.expand()
        await self.morph_zergling()
        await self.attack()

    # Spawn new overlord when necessary.
    async def spawn_overlord(self):
        if self.supply_left < 5 and not self.already_pending(OVERLORD):
            if self.can_afford(OVERLORD) and self.units(LARVA).ready.noqueue:
                larva = self.units(LARVA).random
                await self.do(larva.train(OVERLORD))

            # for larva in self.units(LARVA).ready.noqueue:
            #     if self.can_afford(OVERLORD):
            #         await self.do(larva.train(OVERLORD))#, near=nexuses.first)

    # Morph more drones.
    async def morph_drone(self):
        hatcheries = self.units(HATCHERY).amount * 16
        # Use only two drones per geyser, because they get removed from the
        # game while "inside" the extractor. Thus, the count will be off
        # occasionally. However, eventually extra drones get spawned to fill
        # up the difference.
        extractors = self.units(EXTRACTOR).amount * 2
        # Account for drones in the process of being morphed.
        drones = self.units(DRONE).ready.amount + self.units(
            DRONE).not_ready.amount
        # print("* hatcheries: {}\n* extractors{}\n* drones{}".format(
        #     hatcheries, extractors, drones))
        drones_desired = hatcheries + extractors
        if drones < drones_desired and \
                self.units(LARVA).ready and self.can_afford(DRONE) \
                and not self.already_pending(DRONE):
            larva = self.units(LARVA).first
            await self.do(larva.train(DRONE))

    # Locate hatcheries and create vespene extractors in their vicinity.
    async def build_extractor(self):
        for hatchery in self.units(HATCHERY).ready:
            geysers = self.state.vespene_geyser.closer_than(15.0, hatchery)
            for geyser in geysers:
                if not self.can_afford(EXTRACTOR):
                    break
                worker = self.select_build_worker(geyser.position)
                if worker is None:
                    break
                if not self.units(EXTRACTOR).closer_than(1.0, geyser).exists \
                        and not self.already_pending(EXTRACTOR):
                    await self.do(worker.build(EXTRACTOR, geyser))

    # Build spawning pool at random location to get access to zerglings.
    async def build_spawningpool(self):
        if self.units(SPAWNINGPOOL).amount < 1 and \
            self.can_afford(SPAWNINGPOOL) \
                and not self.already_pending(SPAWNINGPOOL):
                hatcheries = self.units(HATCHERY).ready
                if hatcheries.exists:
                    await self.build(SPAWNINGPOOL, near=hatcheries.first)

    # Expand to a new location with resources.
    async def expand(self):
        if self.units(HATCHERY).amount < 3 and self.can_afford(HATCHERY):
            await self.expand_now()

    # Morph zerglings up to a specified amount. More hatcheries lead to
    # faster morph rates.
    async def morph_zergling(self):
        zerglings_desired = 50
        # Account for zerglings in the process of being morphed.
        zerglings = self.units(ZERGLING).ready.amount + self.units(
            DRONE).not_ready.amount

        # if zerglings < zerglings_desired and \
        #         self.units(LARVA).ready and self.can_afford(ZERGLING) \
        #         and not self.already_pending(ZERGLING):
        #     larva = self.units(LARVA).first
        #     await self.do(larva.train(ZERGLING))

        if zerglings < zerglings_desired:
            zl_morph_desired = self.units(HATCHERY).amount
            zl_morph = self.units(ZERGLING).not_ready.amount
            for hatchery in self.units(HATCHERY):
                if self.units(LARVA).ready \
                        and self.can_afford(ZERGLING) \
                        and zl_morph < zl_morph_desired:
                    larva = self.units(LARVA).random
                    await self.do(larva.train(ZERGLING))

    # Attack known enemy units.
    async def attack(self):
        if self.units(ZERGLING).amount > 5:
            if self.known_enemy_units:
                for s in self.units(ZERGLING).idle:
                    await self.do(s.attack(random.choice(
                        self.known_enemy_units)))


# Starts the game. Choose the map and the participants, race and difficulty.
run_game(maps.get("AbyssalReefLE"),
         [Bot(Race.Zerg, ThePurpleMenace()),
          Computer(Race.Terran, Difficulty.Easy)],
         realtime=True)
