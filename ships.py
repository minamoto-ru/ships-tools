import json
import math
import pandas
import requests
from bs4 import BeautifulSoup
from decimal import *

API_URL = "https://api.korabli.su"
API_KEY = "PLACE-LESTA-APPLICATION-ID-HERE"
PROSHIPS_URL = "https://proships.ru/stat/ru/s/99999-h/"
SHIPS_LIST_METHOD = "/wows/encyclopedia/ships/"
SHIP_PROFILE_METHOD = "/wows/encyclopedia/shipprofile/"
RETRY_LIMIT = 5
    
def transform_ships_list(ships_list):
  short_ships_list = {}
  for ship_index, ship_id in enumerate(ships_list):
      if len(ships_list[ship_id]["modules"]["torpedoes"]) == 1:
        short_ships_list[ship_id] = {
                                    'tier': ships_list[ship_id]["tier"],
                                    'type': ships_list[ship_id]["type"],
                                    'nation': ships_list[ship_id]["nation"],
                                    'name': ships_list[ship_id]["name"],
                                    'torpedo_name': ships_list[ship_id]["default_profile"]["torpedoes"]["torpedo_name"],
                                    "visibility_dist": ships_list[ship_id]["default_profile"]["torpedoes"]["visibility_dist"],
                                    "torpedo_speed": ships_list[ship_id]["default_profile"]["torpedoes"]["torpedo_speed"]
                                  }
      elif len(ships_list[ship_id]["modules"]["torpedoes"]) > 1:
        for torpedoes_id in ships_list[ship_id]["modules"]["torpedoes"]:
          res = get_api_ship_profile(ship_id = ship_id, torpedoes_id = torpedoes_id, retry_count = 0)
          short_ships_list[str(ship_id) + '_' + str(torpedoes_id)] = {
                                                                      'tier': ships_list[ship_id]["tier"],
                                                                      'type': ships_list[ship_id]["type"],
                                                                      'nation': ships_list[ship_id]["nation"],
                                                                      'name': ships_list[ship_id]["name"],
                                                                      'torpedo_name': res["torpedo_name"],
                                                                      "visibility_dist": res["visibility_dist"],
                                                                      "torpedo_speed": res["torpedo_speed"]
                                                                    }
      else:
        pass

  return short_ships_list
  
def get_api_ships_data(page: int, retry_count: int):
  url = API_URL + SHIPS_LIST_METHOD + '?' + 'application_id=' + API_KEY + '&page_no=' + str(page)
  try:
    resp = requests.get(url)
    if resp.ok:
      api_resp = json.loads(resp.text)
      if api_resp["status"] == "ok":
        ships_list = api_resp["data"]
        if api_resp["meta"]["page_total"] > page:
          ships_list.update(get_api_ships_data(page = page + 1, retry_count = 0))
        return ships_list
      else:
        print("API ERROR:")
        print(api_resp)
        return None
    else:
      retry_count += 1
      print(retry_count)
      if retry_count < RETRY_LIMIT:
        return get_api_ships_data(page = page, retry_count = retry_count)
      else:
        raise("Retry limit exceeded")
  except:
    retry_count += 1
    print(retry_count)
    if retry_count < RETRY_LIMIT:
      return get_api_ships_data(page = page, retry_count = retry_count)
    else:
      raise("Retry limit exceeded")

def get_api_ship_profile(ship_id: int, torpedoes_id: int, retry_count: int):
  url = API_URL + SHIP_PROFILE_METHOD + '?' + 'application_id=' + API_KEY + '&ship_id=' + str(ship_id) + '&torpedoes_id=' + str(torpedoes_id)
  try:
    resp = requests.get(url)
    if resp.ok:
      api_resp = json.loads(resp.text)
      if api_resp["status"] == "ok":
        return {
                  'torpedo_name': api_resp["data"][ship_id]["torpedoes"]["torpedo_name"],
                  "visibility_dist": api_resp["data"][ship_id]["torpedoes"]["visibility_dist"],
                  "torpedo_speed": api_resp["data"][ship_id]["torpedoes"]["torpedo_speed"]
                }
      else:
        print("API ERROR:")
        print(api_resp)
        return None
    else:
      retry_count += 1
      print(retry_count)
      if retry_count < RETRY_LIMIT:
        return get_api_ship_profile(ship_id = ship_id, torpedoes_id = torpedoes_id, retry_count = retry_count)
      else:
        raise("Retry limit exceeded")
  except:
    retry_count += 1
    print(retry_count)
    if retry_count < RETRY_LIMIT:
      return get_api_ship_profile(ship_id = ship_id, torpedoes_id = torpedoes_id, retry_count = retry_count)
    else:
      raise("Retry limit exceeded")
  
def get_api_ships_data_from_cache():
  with open('ships.json') as f:
    d = json.load(f)
    return(d)

def get_proships_data(retry_count: int):
  url = PROSHIPS_URL
  try:
    resp = requests.get(url)
    if resp.ok:
        return resp.text
    else:
      retry_count += 1
      print(retry_count)
      if retry_count < RETRY_LIMIT:
        return get_proships_data(retry_count = retry_count)
      else:
        raise("Retry limit exceeded")
  except:
    retry_count += 1
    print(retry_count)
    if retry_count < RETRY_LIMIT:
      return get_proships_data(retry_count = retry_count)
    else:
      raise("Retry limit exceeded")

def get_prev_module_xp_price(modules_list, module_id):
  for module_index, prev_module_id in enumerate(modules_list):
    if (modules_list[prev_module_id]["next_modules"] is not None and int(module_id) in modules_list[prev_module_id]["next_modules"]):
      return(modules_list[prev_module_id]["price_xp"] + get_prev_module_xp_price(modules_list, prev_module_id))
  return(0)

def get_modules_xp_price(modules_list, ship_id, next_ship_id):
  modules_xp_price = {'price_xp': 0,
                      'price_xp_full': 0}
                      
  for module_index, module_id in enumerate(modules_list):
    modules_xp_price["price_xp_full"] += modules_list[module_id]["price_xp"]
    
    if (next_ship_id is not None and modules_list[module_id]["next_ships"] is not None and int(next_ship_id) in modules_list[module_id]["next_ships"]):
      modules_xp_price["price_xp"] += modules_list[module_id]["price_xp"] + get_prev_module_xp_price(modules_list, module_id)
      
  return(modules_xp_price)
  
def get_ship_xp_price(ships_list, pro_ships_list, pro_ships_avg_xp, ship_id, next_ship_id):
  ship_xp_price = get_modules_xp_price(ships_list[ship_id]["modules_tree"], ship_id, next_ship_id) 

  if next_ship_id in ships_list[ship_id]["next_ships"]:
    ship_xp_price["price_xp"] += ships_list[ship_id]["next_ships"][next_ship_id]
    ship_xp_price["price_xp_full"] += ships_list[ship_id]["next_ships"][next_ship_id]
  
  if ships_list[ship_id]["name"] in pro_ships_list:
    avg_xp = pro_ships_list[ships_list[ship_id]["name"]]["avg_xp"]
  else:
    avg_xp = pro_ships_avg_xp
    
  ship_xp_price["battles"] = math.ceil(ship_xp_price["price_xp"] / avg_xp)
  ship_xp_price["battles_full"] = math.ceil(ship_xp_price["price_xp_full"] / avg_xp)
  ship_xp_price["battles_1"] = math.ceil(ship_xp_price["price_xp"] / avg_xp / 2)
  ship_xp_price["battles_full_1"] = math.ceil(ship_xp_price["price_xp_full"] / avg_xp / 2)
  ship_xp_price["battles_2"] = math.ceil(ship_xp_price["price_xp"] / avg_xp / 3)
  ship_xp_price["battles_full_2"] = math.ceil(ship_xp_price["price_xp_full"] / avg_xp / 3)
  ship_xp_price["battles_3"] = math.ceil(ship_xp_price["price_xp"] / avg_xp / 9)
  ship_xp_price["battles_full_3"] = math.ceil(ship_xp_price["price_xp_full"] / avg_xp / 9)
  ship_xp_price["battles_4"] = math.ceil(ship_xp_price["price_xp"] / avg_xp / 17)
  ship_xp_price["battles_full_4"] = math.ceil(ship_xp_price["price_xp_full"] / avg_xp / 17)
  
  for ship_index, prev_ship_id in enumerate(ships_list):
    if (ship_id in ships_list[prev_ship_id]["next_ships"]):
      prev_ship_xp_price = get_ship_xp_price(ships_list = ships_list, pro_ships_list = pro_ships_list, pro_ships_avg_xp = pro_ships_avg_xp, ship_id = prev_ship_id, next_ship_id = ship_id)
      ship_xp_price["price_xp"] += prev_ship_xp_price["price_xp"]
      ship_xp_price["price_xp_full"] += prev_ship_xp_price["price_xp_full"]
      ship_xp_price["battles"] += prev_ship_xp_price["battles"]
      ship_xp_price["battles_full"] += prev_ship_xp_price["battles_full"]
      ship_xp_price["battles_1"] += prev_ship_xp_price["battles_1"]
      ship_xp_price["battles_full_1"] += prev_ship_xp_price["battles_full_1"]
      ship_xp_price["battles_2"] += prev_ship_xp_price["battles_2"]
      ship_xp_price["battles_full_2"] += prev_ship_xp_price["battles_full_2"]
      ship_xp_price["battles_3"] += prev_ship_xp_price["battles_3"]
      ship_xp_price["battles_full_3"] += prev_ship_xp_price["battles_full_3"]
      ship_xp_price["battles_4"] += prev_ship_xp_price["battles_4"]
      ship_xp_price["battles_full_4"] += prev_ship_xp_price["battles_full_4"]
      
  return(ship_xp_price)

def get_transformed_list():
  ships_list = get_api_ships_data(page = 1, retry_count = 0)
  return transform_ships_list(ships_list)

def calculate_experience():
  ships_list = get_api_ships_data(page = 1, retry_count = 0)
  pro_ships_list = parse_proships()
  pro_ships_avg_xp = math.ceil(sum(v['avg_xp'] * v['battles'] for k, v in pro_ships_list.items()) / sum(v['battles'] for k, v in pro_ships_list.items()))
  short_ships_list = {}
  for ship_index, ship_id in enumerate(ships_list):
    if(not(ships_list[ship_id]["is_premium"]) and not(ships_list[ship_id]["is_special"]) and int(ships_list[ship_id]["tier"]) == 10 and int(ships_list[ship_id]["price_credit"]) > 0):
      ship_xp_price = get_ship_xp_price(ships_list = ships_list, pro_ships_list = pro_ships_list, pro_ships_avg_xp = pro_ships_avg_xp, ship_id = ship_id, next_ship_id = None)
      short_ships_list[ship_id] = {
                                    'tier': ships_list[ship_id]["tier"],
                                    'type': ships_list[ship_id]["type"],
                                    'nation': ships_list[ship_id]["nation"],
                                    'name': ships_list[ship_id]["name"],
                                    'price_xp': ship_xp_price["price_xp"],
                                    'price_xp_full': ship_xp_price["price_xp_full"],
                                    'battles': ship_xp_price["battles"],
                                    'battles_full': ship_xp_price["battles_full"],
                                    'battles_1': ship_xp_price["battles_1"],
                                    'battles_full_1': ship_xp_price["battles_full_1"],
                                    'battles_2': ship_xp_price["battles_2"],
                                    'battles_full_2': ship_xp_price["battles_full_2"],
                                    'battles_3': ship_xp_price["battles_3"],
                                    'battles_full_3': ship_xp_price["battles_full_3"],
                                    'battles_4': ship_xp_price["battles_4"],
                                    'battles_full_4': ship_xp_price["battles_full_4"],
                                  }
  return (short_ships_list)
      
def parse_proships():
  pro_ships_list = {}
  page = get_proships_data(retry_count = 0)
  soup = BeautifulSoup(page, "html.parser")
  my_ships_table = soup.find("table", {"id": "MyShips"})
  my_ships_rows = my_ships_table.findAll('tr')
  for row in my_ships_rows:
    cols = row.findAll('td')
    if len(cols) > 0 and cols[3].text is not None:
      pro_ships_list[cols[3].text] = {
                                      'type': cols[0].text,
                                      'nation': cols[1].text,
                                      'tier': int(cols[2].text),
                                      'players': int(cols[4].text),
                                      'battles': int(cols[5].text),
                                      'win_rate': Decimal(cols[6].text),
                                      'avg_xp': int(cols[7].text),
                                      'avg_damage': int(cols[8].text),
                                      'avg_ships_sunk': Decimal(cols[9].text),
                                      'avg_assist_damage': int(cols[10].text),
                                      'survive_rate': Decimal(cols[11].text),
                                      'avg_planes': Decimal(cols[12].text),
                                      'avg_attack': Decimal(cols[13].text),
                                      'avg_defence': Decimal(cols[14].text),
                                      'avg_potential_damage': int(cols[15].text),
                                      'avg_assist_ships': Decimal(cols[16].text),
                                      'kill_rate': Decimal(cols[17].text)                                      
                                      }
  return(pro_ships_list)

   
def main():
  mode = input('''Выберите режим работы скрипта.
  1) Выгрузка списка кораблей с торпедами в Excel-файл с именем ships.xlsx
  2) Выгрузка списка прокачиваемых кораблей 10-го уровня с информацией о количестве опыта, необходимого для прокачки в файл upgrades.xlsx
  3) Парсинг сайта proships.ru
  ''')
  match mode:
    case "1":
      short_ships_list = get_transformed_list()
      pandas.DataFrame.from_dict(short_ships_list, orient='index').to_excel("ships.xlsx", index=False)
    case "2":
      short_ships_list = calculate_experience()
      pandas.DataFrame.from_dict(short_ships_list, orient='index').to_excel("upgrades.xlsx", index=False)
    case "3":
      pro_ships_list = parse_proships()
      print(pandas.DataFrame.from_dict(pro_ships_list, orient='index'))
    case _:
      print ("Not supported")


if __name__ == '__main__':
    main()