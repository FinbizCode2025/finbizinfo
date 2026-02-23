from openai import OpenAI
 
client = OpenAI(
    api_key="sk-0BVkU05lve1kzpCD1Ri5nLkKh0gprDMfriSAUA8jVgT0vqdZ", # Replace MOONSHOT_API_KEY with the API Key you obtained from the Kimi Open Platform
    base_url="https://api.moonshot.ai/v1",
)
 
completion = client.chat.completions.create(
    model = "moonshot-v1-32k",
    messages = [
        {"role": "system", "content": "You are Kimi, an AI assistant provided by Moonshot AI. You are proficient in Chinese and English conversations. You provide users with safe, helpful, and accurate answers. You will reject any requests involving terrorism, racism, or explicit content. Moonshot AI is a proper noun and should not be translated."},
        {"role": "user", "content": "Hello, my name is Li Lei. What is 1+1?"}
    ],
    temperature = 0.6,
)
 
# We receive a response from the Kimi large language model via the API (role=assistant)
print(completion.choices[0].message.content)