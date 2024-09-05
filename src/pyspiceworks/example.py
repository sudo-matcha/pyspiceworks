from Spiceworks import Spiceworks
import dotenv
dotenv.load_dotenv()

sw = Spiceworks()
tickets = sw.tickets()
sw.kill_driver()