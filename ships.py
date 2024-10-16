import json
import pandas
import requests

API_URL = "https://api.korabli.su"
API_KEY = "PLACE-LESTA-APPLICATION-ID-HERE"
SHIPS_LIST_METHOD = "/wows/encyclopedia/ships/"
SHIP_PROFILE_METHOD = "/wows/encyclopedia/shipprofile/"
RETRY_LIMIT = 5
    
def transform_ships_list(shipsList):
  shortShipsList = {}
  for shipIndex, ship_id in enumerate(shipsList):
      if len(shipsList[ship_id]["modules"]["torpedoes"]) == 1:
        shortShipsList[ship_id] = {
                                    'tier': shipsList[ship_id]["tier"],
                                    'type': shipsList[ship_id]["type"],
                                    'nation': shipsList[ship_id]["nation"],
                                    'name': shipsList[ship_id]["name"],
                                    'torpedo_name': shipsList[ship_id]["default_profile"]["torpedoes"]["torpedo_name"],
                                    "visibility_dist": shipsList[ship_id]["default_profile"]["torpedoes"]["visibility_dist"],
                                    "torpedo_speed": shipsList[ship_id]["default_profile"]["torpedoes"]["torpedo_speed"]
                                  }
      elif len(shipsList[ship_id]["modules"]["torpedoes"]) > 1:
        for torpedoes_id in shipsList[ship_id]["modules"]["torpedoes"]:
          res = get_ship_profile(ship_id = ship_id, torpedoes_id = torpedoes_id, retry_count = 0)
          shortShipsList[str(ship_id) + '_' + str(torpedoes_id)] = {
                                                                      'tier': shipsList[ship_id]["tier"],
                                                                      'type': shipsList[ship_id]["type"],
                                                                      'nation': shipsList[ship_id]["nation"],
                                                                      'name': shipsList[ship_id]["name"],
                                                                      'torpedo_name': res["torpedo_name"],
                                                                      "visibility_dist": res["visibility_dist"],
                                                                      "torpedo_speed": res["torpedo_speed"]
                                                                    }
      else:
        pass

  return shortShipsList
  
def get_api_ships_data(page: int, retry_count: int):
  url = API_URL + SHIPS_LIST_METHOD + '?' + 'application_id=' + API_KEY + '&page_no=' + str(page)
  try:
    resp = requests.get(url)
    if resp.ok:
      api_resp = json.loads(resp.text)
      if api_resp["status"] == "ok":
        shortShipsList = transform_ships_list(api_resp["data"])
        if api_resp["meta"]["page_total"] > page:
          shortShipsList.update(get_api_ships_data(page = page + 1, retry_count = 0))
        return shortShipsList
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
  
def main():
  shortShips = get_api_ships_data(page = 1, retry_count = 0)
  pandas.DataFrame.from_dict(shortShips, orient='index').to_excel("ships.xlsx")

if __name__ == '__main__':
    main()