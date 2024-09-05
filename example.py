from Spiceworks import Spiceworks
import dotenv
dotenv.load_dotenv()

sw = Spiceworks()
sw.init_driver()
sw.login()
sw.get_tron_session()
tickets = sw.tickets()
sw.kill_driver()