import requests
import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta

if __name__ == "__main__":
	url_mtup = "https://api.meetup.com/"
	auth = {"sign":"true", "key":"347145183d421c22b3973556a475080"}
	my_params = {"page":"100", "order":"time", "text":"", "only":"events", "fields":"featured_photo", "order":"time"}
	my_params.update(auth)
	
	client = MongoClient()
	db = client.watchtower_db
	mtup_res = db.meetup_results
	
	search_topics = ["big data", "bitcoin", "machiene learning", "a"]
	
	for search_text in search_topics:
		my_params["text"] = search_text
		r = requests.get(url_mtup + "find/upcoming_events", params = my_params)
		search_result_json = r.json()
		
		search_result_list = []
		for eve in search_result_json["events"]:
			search_result = {"name":eve.get("name",""), "group_name":(eve.get("group",{})).get("name",""),
					"link":eve.get("link",""), "local_date":eve.get("local_date",""),
					"local_time":eve.get("local_time",""), "yes_rsvp_count":eve.get("yes_rsvp_count",""),
					"city":eve.get("venue",{}).get("city",""),
					"country":eve.get("venue",{}).get("country",""),
					"photo_link":eve.get("featured_photo",{}).get("photo_link","")}
			search_result_list.append(search_result)
		
		mtup_res.find_and_modify(
			query = {"search_text": search_text},
			update = { "$set": {"search_result_list": search_result_list, "last_update": datetime.now()}},
			upsert = True
		)
	
	