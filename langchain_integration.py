"""
LangChain integration module for handling LLM interactions with tool calling capabilities.
Optimized for Mac M2 with Metal GPU acceleration.
"""

import os
from pathlib import Path
import time
import re
from typing import List, Dict, Any, Optional
from functools import lru_cache

try:
    from langchain_ollama import ChatOllama
except ImportError:
    # Fallback for older langchain versions
    try:
        from langchain_community.chat_models import ChatOllama
    except ImportError:
        raise ImportError("Neither langchain_ollama nor langchain_community found. Please install: pip install langchain-ollama")

from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage


class LangChainManager:
    """Manages LangChain LLM interactions with tool calling capabilities."""
    
    def __init__(self, model_name: str = "llama3.2:1b", temperature: float = 0.7, 
                 conversation_limit: int = 10, enable_conversation: bool = True):
        """
        Initialize LangChain manager with optimized settings for Mac M2.
        
        Args:
            model_name: Name of the Ollama model to use
            temperature: Temperature for response generation
            conversation_limit: Maximum number of messages to keep in context
            enable_conversation: Whether to use conversational memory
        """
        self.model_name = model_name
        self.temperature = temperature
        self.conversation_limit = conversation_limit
        self.enable_conversation = enable_conversation
        self.llm = None
        self.tools = []
        self.conversation_history = []
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the ChatOllama LLM with Metal optimization."""
        try:
            self.llm = ChatOllama(
                model=self.model_name,
                temperature=self.temperature,
                # Metal GPU optimization settings
                num_ctx=2048,  # Reduced context for 8GB RAM
                num_gpu=1,     # Use Metal GPU
                num_thread=4,  # Optimize for M2 cores
                use_mmap=True,  # Memory mapping
                use_mlock=True,  # Lock memory for Metal
            )
        except Exception as e:
            raise Exception(f"Failed to initialize LLM: {e}")
    
    def set_tools(self, tools: List[BaseTool]):
        """
        Set the tools for the agent to use.
        
        Args:
            tools: List of LangChain tools
        """
        self.tools = tools
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        if self.enable_conversation:
            self.conversation_history.append({"role": role, "content": content})
            # Limit conversation history
            if len(self.conversation_history) > self.conversation_limit:
                self.conversation_history = self.conversation_history[-self.conversation_limit:]
    
    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_conversation_context(self) -> List:
        """Get conversation context as LangChain messages."""
        if not self.enable_conversation:
            return []
        
        messages = []
        for msg in self.conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        return messages
    
    @lru_cache(maxsize=128)
    def _cached_llm_call(self, message_hash: str, messages_tuple: tuple) -> str:
        """Cached LLM call for performance."""
        messages = list(messages_tuple)
        response = self.llm.invoke(messages)
        return response.content
    
    def _summarize_old_messages(self) -> str:
        """Summarize old messages to save context space."""
        if len(self.conversation_history) <= self.conversation_limit // 2:
            return ""
        
        # Keep recent messages, summarize older ones
        recent_messages = self.conversation_history[-(self.conversation_limit // 2):]
        old_messages = self.conversation_history[:-(self.conversation_limit // 2)]
        
        # Create a simple summary
        summary_parts = []
        for i, msg in enumerate(old_messages):
            if i % 2 == 0:  # User message
                summary_parts.append(f"User asked about: {msg['content'][:50]}...")
            else:  # Assistant message
                summary_parts.append(f"Assistant responded: {msg['content'][:50]}...")
        
        summary = "Earlier conversation: " + " | ".join(summary_parts)
        return summary
    
    def generate_response(self, message: str, use_tools: bool = True) -> tuple[str, float]:
        """
        Generate a response using either direct LLM or with tool calling.
        
        Args:
            message: The input message
            use_tools: Whether to use tools
            
        Returns:
            Tuple of (response_text, response_time)
        """
        start_time = time.time()
        
        try:
            if use_tools and self.tools:
                # Simple direct tool calling approach
                tool_response = self._handle_direct_tool_call(message)
                if tool_response:
                    end_time = time.time()
                    response_time = round(end_time - start_time, 2)
                    return tool_response, response_time
            
            # Use conversational LLM with date/time context
            conversation_context = self.get_conversation_context()
            
            # Add current date/time context for awareness
            import datetime
            current_context = f"Current date: {datetime.date.today().strftime('%Y-%m-%d')}, Current time: {datetime.datetime.now().strftime('%H:%M:%S')}"
            
            # Add system prompt about available tools
            system_prompt = "You have access to real-time tools including web search, calculations, conversions, and current date/time information. Use tools when appropriate for factual questions."
            
            # Add summary if conversation is getting long
            summary = self._summarize_old_messages()
            if summary:
                full_message = f"{system_prompt}\n{current_context}\n{summary}\n\nCurrent question: {message}"
            else:
                full_message = f"{system_prompt}\n{current_context}\n\n{message}"
            
            # Create messages with context
            messages = conversation_context + [HumanMessage(content=full_message)]
            
            # Use cached call for better performance
            import hashlib
            message_hash = hashlib.md5(full_message.encode()).hexdigest()
            messages_tuple = tuple((msg.content if hasattr(msg, 'content') else str(msg)) for msg in messages)
            
            try:
                response_text = self._cached_llm_call(message_hash, messages_tuple)
            except:
                # Fallback to regular call if cache fails
                response = self.llm.invoke(messages)
                response_text = response.content
            
            end_time = time.time()
            response_time = round(end_time - start_time, 2)
            
            return response_text, response_time
            
        except Exception as e:
            end_time = time.time()
            response_time = round(end_time - start_time, 2)
            error_msg = f"Error generating response: {e}"
            return error_msg, response_time
    
    def _handle_direct_tool_call(self, message: str) -> str:
        """Handle direct tool calls with simple pattern matching."""
        message_lower = message.lower()
        
        # Web search patterns
        if "search for" in message_lower or "look up" in message_lower or "find information about" in message_lower:
            # Extract search query
            if "search for" in message_lower:
                query = message_lower.split("search for")[-1].strip()
            elif "look up" in message_lower:
                query = message_lower.split("look up")[-1].strip()
            else:
                query = message_lower.split("find information about")[-1].strip()
            
            # Use web search tool
            for tool in self.tools:
                if tool.name == "web_search":
                    try:
                        result = tool.invoke(query)
                        return f"🔍 Web search results for '{query}':\n{result}"
                    except:
                        return f"🔍 Search failed for: {query}"
        
        # Weather patterns
        if "weather" in message_lower:
            # Extract location
            words = message.split()
            location_idx = -1
            for i, word in enumerate(words):
                if "weather" in word.lower():
                    location_idx = i + 1
                    break
            
            if location_idx > 0 and location_idx < len(words):
                location = words[location_idx]
                for tool in self.tools:
                    if tool.name == "get_weather":
                        try:
                            result = tool.invoke(location)
                            return f"🌤️ Weather in {location}:\n{result}"
                        except:
                            return f"🌤️ Weather search failed for: {location}"
        
        # Mathematics patterns
        if "times" in message_lower or "multiply" in message_lower:
            numbers = self._extract_numbers(message)
            if len(numbers) >= 2:
                result = numbers[0] * numbers[1]
                return f"{numbers[0]} times {numbers[1]} = {result}"
        
        if "plus" in message_lower or "add" in message_lower or "+" in message:
            numbers = self._extract_numbers(message)
            if len(numbers) >= 2:
                result = numbers[0] + numbers[1]
                return f"{numbers[0]} + {numbers[1]} = {result}"
        
        if "divide" in message_lower or "divided by" in message_lower:
            numbers = self._extract_numbers(message)
            if len(numbers) >= 2 and numbers[1] != 0:
                result = numbers[0] / numbers[1]
                return f"{numbers[0]} divided by {numbers[1]} = {result:.2f}"
        
        # Temperature conversion patterns
        if "celsius" in message_lower and "fahrenheit" in message_lower:
            numbers = self._extract_numbers(message)
            if numbers:
                celsius = numbers[0]
                fahrenheit = (celsius * 9/5) + 32
                return f"{celsius}°C = {fahrenheit:.1f}°F"
        
        if "fahrenheit" in message_lower and "celsius" in message_lower:
            numbers = self._extract_numbers(message)
            if numbers:
                fahrenheit = numbers[0]
                celsius = (fahrenheit - 32) * 5/9
                return f"{fahrenheit}°F = {celsius:.1f}°C"
        
        # Time/date patterns - enhanced to catch more variations
        if ("current time" in message_lower or "what time" in message_lower or 
            "time is it" in message_lower):
            import datetime
            now = datetime.datetime.now()
            return f"🕐 Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        
        if ("current date" in message_lower or "what date" in message_lower or 
            "today's date" in message_lower or "what is today" in message_lower or
            "todays date" in message_lower or "today date" in message_lower or
            "what year is it" in message_lower or "current year" in message_lower):
            import datetime
            today = datetime.date.today()
            return f"📅 Today's date is {today.strftime('%A, %B %d, %Y')}"
        
        if ("tomorrow" in message_lower or "date tomorrow" in message_lower or 
            "what is tomorrow" in message_lower or "tomorrows date" in message_lower or
            "date tomorrow" in message_lower):
            import datetime
            tomorrow = datetime.date.today() + datetime.timedelta(days=1)
            return f"📅 Tomorrow's date is {tomorrow.strftime('%A, %B %d, %Y')}"
        
        if ("yesterday" in message_lower or "date yesterday" in message_lower or 
            "what was yesterday" in message_lower or "yesterdays date" in message_lower):
            import datetime
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            return f"📅 Yesterday's date was {yesterday.strftime('%A, %B %d, %Y')}"
        
        # Catch any question about dates, years, or current time
        if any(word in message_lower for word in ["date", "year", "time", "today", "tomorrow", "yesterday"]) and \
           any(word in message_lower for word in ["what", "current", "the"]):
            import datetime
            today = datetime.date.today()
            return f"📅 Today's date is {today.strftime('%A, %B %d, %Y')}"
        
        # Word count
        if "word count" in message_lower or "how many words" in message_lower:
            # Extract text in quotes or use the whole message
            import re
            quoted_text = re.search(r'"([^"]*)"', message)
            if quoted_text:
                text = quoted_text.group(1)
            else:
                # Count words in the message itself (excluding the question part)
                text = message
            words = text.split()
            return f"Word count: {len(words)} words"
        
        return None  # No tool matched
    
    def _extract_numbers(self, text: str) -> list:
        """Extract numbers from text."""
        import re
        numbers = re.findall(r'\d+\.?\d*', text)
        return [float(n) if '.' in n else int(n) for n in numbers]
    
    def update_model_settings(self, model_name: str = None, temperature: float = None):
        """
        Update model settings and reinitialize.
        
        Args:
            model_name: New model name (optional)
            temperature: New temperature (optional)
        """
        if model_name:
            self.model_name = model_name
        if temperature is not None:
            self.temperature = temperature
        
        self._initialize_llm()
    
    def get_tool_info(self) -> List[Dict[str, Any]]:
        """
        Get information about available tools.
        
        Returns:
            List of tool information dictionaries
        """
        tool_info = []
        for tool in self.tools:
            tool_info.append({
                'name': tool.name,
                'description': tool.description,
                'args': tool.args if hasattr(tool, 'args') else {}
            })
        return tool_info
    
    def is_ready(self) -> bool:
        """Check if the manager is ready for use."""
        return self.llm is not None
