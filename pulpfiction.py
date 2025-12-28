import azure.cosmos
from azure.cosmos.partition_key import PartitionKey
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import openai

# Replace with your Cosmos DB account details
ENDPOINT = "https://your-unique-cosmos-account-name.documents.azure.com:443/"
KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = "grocerydb"
CONTAINER_NAMES = ["pos_history", "sku_master", "store_profile", "vendor_catalog", "constraints"]

# Initialize the Cosmos client
client = azure.cosmos.CosmosClient(ENDPOINT, KEY)

# Get a reference to the database
database = client.get_database_client(DATABASE_NAME)

# Get references to all containers
containers = {}
for name in CONTAINER_NAMES:
    containers[name] = database.get_container_client(name)

print("Connected to all containers.")

# Connect to Microsoft Foundry model
endpoint = "https://supplychainproblem.cognitiveservices.azure.com/"
model = "gpt-4o"
token = os.getenv("AZURE_AI_API_KEY")

client = openai.AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=token,
    api_version="2025-01-01-preview"
)

print("Connected to Foundry model.")

# Example chat
response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)

# Example usage: Access a specific container
# container = containers["sku_master"]
# Then perform operations like create_item, query_items, etc.

