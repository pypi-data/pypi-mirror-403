"""
File & Image Output - Agent-Generated Content

Set your API key:
  export LYZR_API_KEY="your-api-key"

Get your API key: https://studio.lyzr.ai
"""

from lyzr import Studio
from lyzr.image_models import Gemini, DallE


studio = Studio(
    env="dev"  # Set LYZR_API_KEY environment variable, log="debug"
)  # Uses LYZR_API_KEY env var

# Example 1: File Output
print("=" * 70)
print("Example 1: File Generation")
print("=" * 70)

doc_agent = studio.create_agent(
    name="Report Generator",
    provider="openai/gpt-4o",
    role="Professional report generator",
    goal="Create comprehensive reports",
    instructions="Generate detailed reports in PDF or DOCX",
    file_output=True,
)

response = doc_agent.run("Create a Q4 2024 sales report in PDF")
print(response.response)

if response.has_files():
    for file in response.files:
        print(f"  File: {file.name} ({file.format_type}) - {file.url}")

doc_agent.delete()

# Example 2: Image Generation
print("\n" + "=" * 70)
print("Example 2: Image Generation")
print("=" * 70)

image_agent = studio.create_agent(
    name="Image Creator",
    provider="gpt-4o",
    role="Creative designer",
    goal="Generate visual content",
    instructions="Create images based on descriptions",
    image_model=Gemini.PRO,  # Enable image generation
)

response = image_agent.run("Create an image of a futuristic city at sunset")
print(response.response)

if response.has_files():
    for artifact in response.files:
        if artifact.format_type == "image":
            print(f"  Image: {artifact.name} - {artifact.url}")
            # Download: artifact.download("./city.png")

# Change to DALL-E
image_agent = image_agent.set_image_model(DallE.DALL_E_3)
response = image_agent.run("Generate abstract art with vibrant colors")

if response.has_files():
    for artifact in response.files:
        print(f"  {artifact.name}: {artifact.url}")

image_agent.delete()

# Example 3: Both File and Image Output
print("\n" + "=" * 70)
print("Example 3: File + Image Output")
print("=" * 70)

multi_agent = studio.create_agent(
    name="Content Creator",
    provider="gpt-4o",
    role="Content creator",
    goal="Create documents and images",
    instructions="Generate both documents and images as needed",
    file_output=True,
    image_model=Gemini.FLASH,
)

response = multi_agent.run("Create a product brochure with an image of the product")

if response.has_files():
    for artifact in response.files:
        print(f"  {artifact.format_type.upper()}: {artifact.name} - {artifact.url}")

multi_agent.delete()
