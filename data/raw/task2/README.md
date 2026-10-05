# Task 2 evidence (raw)

`evidence.jsonl`: one line per web page consulted while expanding a category's brand table.
Fields: category_id, url, retrieved (date), method (webfetch = brand names extracted from the fetched page;
websearch = names from a web-search result summary, weaker), brands_on_page (as named on the page).
Brand rows in `data/category_brands.csv` cite one of these URLs (or the Kantar seed source).
