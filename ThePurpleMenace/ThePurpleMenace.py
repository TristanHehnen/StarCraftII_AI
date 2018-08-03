import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer


# The Purple Menace -- a Zerg hive mind,
# about to cover the wold in creep and gore.
class ThePurpleMenace(sc2.BotAI):
    async def on_step(self, iteration):
        # Limit the workers to as much a three per resource patch.
        await self.distribute_workers()


# Starts the game. Choose the map and the participants, race and difficulty.
run_game(maps.get("AbyssalReefLE"),
         [Bot(Race.Zerg, ThePurpleMenace()),
          Computer(Race.Terran, Difficulty.Easy)],
         realtime=True)
