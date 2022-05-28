from app.server import Server, App
from app.simulation import Simulation
import logging

from auth import auth_server
from game import game_server

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


if __name__ == '__main__':
    app = App(logger)
    app.register(auth_server)
    app.register(game_server)
    app.run_polling()
