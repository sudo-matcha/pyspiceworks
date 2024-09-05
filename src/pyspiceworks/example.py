from Spiceworks import Spiceworks
import dotenv
from pprint import pprint
dotenv.load_dotenv()

sw = Spiceworks()
tickets = sw.tickets()
pprint(tickets)
sw.kill_driver()