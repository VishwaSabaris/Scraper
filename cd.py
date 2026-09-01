import requests

url = "https://www.searchapi.io/api/v1/search"
params = {
  "engine": "google",
  "q": "chatgpt"
}

response = requests.get(url, params=params)
print(response.text)
