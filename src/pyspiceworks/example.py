from pyspiceworks import Spiceworks
import dotenv
from pprint import pprint
dotenv.load_dotenv()

sw = Spiceworks()
tickets = sw.get_tickets()
pprint(tickets)
notifs = sw.get_notifications()
pprint(notifs)
sw.kill_driver()