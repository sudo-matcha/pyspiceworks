from Spiceworks import Spiceworks
import dotenv
dotenv.load_dotenv()

sw = Spiceworks()
sw.init_driver(headless=False)
sw.login()
sw.get_ticket_CSRF_token()
print(sw.CSRF_token)
# sw.get_tron_session()
tickets = sw.tickets()
sw.kill_driver()