"""
Collection of LangChain tools for various tasks.
Optimized for practical use cases with local LLMs.
"""

import math
import datetime
import json
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from langchain_core.tools import tool


# Mathematical Tools
@tool
def multiply(x: int, y: int) -> int:
    """Multiply two numbers together."""
    return x * y


@tool
def add(x: int, y: int) -> int:
    """Add two numbers together."""
    return x + y


@tool
def divide(x: float, y: float) -> float:
    """Divide two numbers. Returns the result of x divided by y."""
    if y == 0:
        return "Error: Cannot divide by zero"
    return x / y


@tool
def power(x: float, y: float) -> float:
    """Calculate x raised to the power of y."""
    try:
        return x ** y
    except BaseException:
        return "Error: Invalid calculation"


@tool
def square_root(x: float) -> float:
    """Calculate the square root of a number."""
    if x < 0:
        return "Error: Cannot calculate square root of negative number"
    return math.sqrt(x)


# Text Processing Tools
@tool
def word_count(text: str) -> int:
    """Count the number of words in a text string."""
    words = text.split()
    return len(words)


@tool
def character_count(text: str) -> int:
    """Count the number of characters in a text string."""
    return len(text)


@tool
def extract_emails(text: str) -> List[str]:
    """Extract all email addresses from a text string."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails


@tool
def extract_urls(text: str) -> List[str]:
    """Extract all URLs from a text string."""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return urls


@tool
def to_uppercase(text: str) -> str:
    """Convert text to uppercase."""
    return text.upper()


@tool
def to_lowercase(text: str) -> str:
    """Convert text to lowercase."""
    return text.lower()


# Date and Time Tools
@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def get_current_date() -> str:
    """Get the current date."""
    return datetime.date.today().strftime("%Y-%m-%d")


@tool
def calculate_age(birth_date: str) -> int:
    """
    Calculate age from birth date.
    Args:
        birth_date: Date in YYYY-MM-DD format
    """
    try:
        birth = datetime.datetime.strptime(birth_date, "%Y-%m-%d").date()
        today = datetime.date.today()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return age
    except BaseException:
        return "Error: Invalid date format. Use YYYY-MM-DD"


@tool
def days_until_date(target_date: str) -> int:
    """
    Calculate days until a target date.
    Args:
        target_date: Date in YYYY-MM-DD format
    """
    try:
        target = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()
        today = datetime.date.today()
        delta = target - today
        return delta.days
    except BaseException:
        return "Error: Invalid date format. Use YYYY-MM-DD"


# Web Search Tools
@tool
def web_search(query: str) -> str:
    """
    Search the web using DuckDuckGo for information.
    Args:
        query: Search query string
    """
    try:
        # DuckDuckGo instant answer API
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': 1,
            'skip_disambig': 1
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()

            # Extract relevant information
            results = []

            # Abstract (instant answer)
            if data.get('Abstract'):
                results.append(f"Answer: {data['Abstract']}")

            # Related topics
            if data.get('RelatedTopics'):
                for topic in data['RelatedTopics'][:3]:  # Limit to top 3
                    if topic.get('Text'):
                        results.append(f"• {topic['Text']}")

            if not results:
                return f"No results found for: {query}"

            return "\n".join(results)
        else:
            return f"Search failed with status: {response.status_code}"

    except Exception as e:
        return f"Search error: {str(e)}"


@tool
def get_weather(location: str) -> str:
    """
    Get current weather information for a location.
    Args:
        location: City name or location
    """
    try:
        # Using DuckDuckGo to get weather info
        query = f"weather {location}"
        return web_search(query)
    except Exception as e:
        return f"Weather search error: {str(e)}"


# Data Conversion Tools
@tool
def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9 / 5) + 32


@tool
def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return (fahrenheit - 32) * 5 / 9


@tool
def meters_to_feet(meters: float) -> float:
    """Convert meters to feet."""
    return meters * 3.28084


@tool
def feet_to_meters(feet: float) -> float:
    """Convert feet to meters."""
    return feet / 3.28084


@tool
def kilograms_to_pounds(kg: float) -> float:
    """Convert kilograms to pounds."""
    return kg * 2.20462


@tool
def pounds_to_kilograms(pounds: float) -> float:
    """Convert pounds to kilograms."""
    return pounds / 2.20462


# Utility Tools
@tool
def calculate_tip(bill_amount: float, tip_percentage: float) -> Dict[str, float]:
    """
    Calculate tip amount and total bill.
    Args:
        bill_amount: The original bill amount
        tip_percentage: Tip percentage (e.g., 15 for 15%)
    """
    tip_amount = bill_amount * (tip_percentage / 100)
    total = bill_amount + tip_amount
    return {
        "bill_amount": bill_amount,
        "tip_percentage": tip_percentage,
        "tip_amount": round(tip_amount, 2),
        "total": round(total, 2)
    }


@tool
def bmi_calculator(weight_kg: float, height_m: float) -> Dict[str, Any]:
    """
    Calculate Body Mass Index (BMI).
    Args:
        weight_kg: Weight in kilograms
        height_m: Height in meters
    """
    if height_m == 0:
        return {"error": "Height cannot be zero"}

    bmi = weight_kg / (height_m ** 2)

    # BMI categories
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal weight"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    return {
        "weight_kg": weight_kg,
        "height_m": height_m,
        "bmi": round(bmi, 2),
        "category": category
    }


@tool
def json_formatter(text: str) -> str:
    """
    Format text as JSON if possible, otherwise return error.
    Args:
        text: Text to format as JSON
    """
    try:
        # Try to parse as JSON first
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2)
    except BaseException:
        # Try to create JSON from plain text
        try:
            return json.dumps({"text": text}, indent=2)
        except BaseException:
            return "Error: Cannot format text as JSON"


# Tool Collections
MATH_TOOLS = [multiply, add, divide, power, square_root]
TEXT_TOOLS = [word_count, character_count, extract_emails, extract_urls, to_uppercase, to_lowercase]
DATE_TOOLS = [get_current_time, get_current_date, calculate_age, days_until_date]
WEB_TOOLS = [web_search, get_weather]
CONVERSION_TOOLS = [celsius_to_fahrenheit, fahrenheit_to_celsius, meters_to_feet, feet_to_meters,
                    kilograms_to_pounds, pounds_to_kilograms]
UTILITY_TOOLS = [calculate_tip, bmi_calculator, json_formatter]

# All available tools
ALL_TOOLS = MATH_TOOLS + TEXT_TOOLS + DATE_TOOLS + WEB_TOOLS + CONVERSION_TOOLS + UTILITY_TOOLS

# Tool categories for UI organization
TOOL_CATEGORIES = {
    "Mathematics": MATH_TOOLS,
    "Text Processing": TEXT_TOOLS,
    "Date & Time": DATE_TOOLS,
    "Web Search": WEB_TOOLS,
    "Conversions": CONVERSION_TOOLS,
    "Utilities": UTILITY_TOOLS
}


def get_tools_by_category(category: str) -> List:
    """Get tools by category name."""
    return TOOL_CATEGORIES.get(category, [])


def get_tool_names() -> List[str]:
    """Get list of all tool names."""
    return [tool.name for tool in ALL_TOOLS]


def get_tool_by_name(name: str) -> Any:
    """Get a specific tool by name."""
    for tool in ALL_TOOLS:
        if tool.name == name:
            return tool
    return None
