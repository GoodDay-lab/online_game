from app.server import Server
from app.storage import Storage
from app.simulation import Simulation


game_server = Server("gameserver", ('127.0.0.1', 8081))
game_store = Storage()
game_store.add_table("sessions", {"sid": str,
                                  "session": Simulation})


@game_server.add_udp_handler("name")
async def react(addr, request):
    game_server.logger.debug("react")
