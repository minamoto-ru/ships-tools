import json
import pandas
import requests

API_URL = "https://api.korabli.su"
API_KEY = "PLACE-LESTA-APPLICATION-ID-HERE"
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
          res = get_ship_profile(ship_id = ship_id, torpedoes_id = torpedoes_id, retry_count = 0)
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

def get_ship_profile(ship_id: int, torpedoes_id: int, retry_count: int):
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
        return get_ship_profile(ship_id = ship_id, torpedoes_id = torpedoes_id, retry_count = retry_count)
      else:
        raise("Retry limit exceeded")
  except:
    retry_count += 1
    print(retry_count)
    if retry_count < RETRY_LIMIT:
      return get_ship_profile(ship_id = ship_id, torpedoes_id = torpedoes_id, retry_count = retry_count)
    else:
      raise("Retry limit exceeded")
  
def get_api_ships_data_from_cache():
  with open('ships.json') as f:
    d = json.load(f)
    return(d)

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
  
def get_ship_xp_price(ships_list, ship_id, next_ship_id):
  ship_xp_price = get_modules_xp_price(ships_list[ship_id]["modules_tree"], ship_id, next_ship_id) 

  for ship_index, prev_ship_id in enumerate(ships_list):
    if (ship_id in ships_list[prev_ship_id]["next_ships"]):
      prev_ship_xp_price = get_ship_xp_price(ships_list = ships_list, ship_id = prev_ship_id, next_ship_id = ship_id)
      ship_xp_price["price_xp"] += ships_list[prev_ship_id]["next_ships"][ship_id] + prev_ship_xp_price["price_xp"]
      ship_xp_price["price_xp_full"] += ships_list[prev_ship_id]["next_ships"][ship_id] + prev_ship_xp_price["price_xp_full"]
      
  return(ship_xp_price)

def get_transformed_list():
  ships_list = get_api_ships_data(page = 1, retry_count = 0)
  return transform_ships_list(ships_list)

def calculate_experience():
  ships_list = get_api_ships_data(page = 1, retry_count = 0)
  short_ships_list = {}
  for ship_index, ship_id in enumerate(ships_list):
    if(not(ships_list[ship_id]["is_premium"]) and not(ships_list[ship_id]["is_special"]) and int(ships_list[ship_id]["tier"]) == 10 and int(ships_list[ship_id]["price_credit"]) > 0):
      ship_xp_price = get_ship_xp_price(ships_list = ships_list, ship_id = ship_id, next_ship_id = None)
      short_ships_list[ship_id] = {
                                    'tier': ships_list[ship_id]["tier"],
                                    'type': ships_list[ship_id]["type"],
                                    'nation': ships_list[ship_id]["nation"],
                                    'name': ships_list[ship_id]["name"],
                                    'price_xp': ship_xp_price["price_xp"],
                                    'price_xp_full': ship_xp_price["price_xp_full"]
                                  }
  return (short_ships_list)
      
def main():
  mode = input('''Выберите режим работы скрипта.
  1) Выгрузка списка кораблей с торпедами в Excel-файл с именем ships.xlsx
  2) Выгрузка списка прокачиваемых кораблей 10-го уровня с информацией о количестве опыта, необходимого для прокачки в файл upgrades.xlsx
  ''')
  match mode:
    case "1":
      short_ships_list = get_transformed_list()
      pandas.DataFrame.from_dict(short_ships_list, orient='index').to_excel("ships.xlsx", index=False)
    case "2":
      short_ships_list = calculate_experience()
      pandas.DataFrame.from_dict(short_ships_list, orient='index').to_excel("upgrades.xlsx", index=False)
    case _:
      print ("Not supported")


if __name__ == '__main__':
    main()