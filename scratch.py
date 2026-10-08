from google import genai

client = genai.Client()  # reads GEMINI_API_KEY from the environment

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Say hello in one sentence",
)

print("TEXT:", repr(response.text))
print("FULL:", response)