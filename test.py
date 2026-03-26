from google import genai

client = genai.Client(api_key="AIzaSyCxp60tMVYGqqvWz7NKDkvM6mHeo-bGnk4")

# List models
for m in client.models.list():
    print(m)

