Chat
====

Chat Completion
~~~~~~~~~~~~~~~

The GEAI SDK provides functionality to interact with the Globant Enterprise AI chat system, allowing users to generate chat completions using specified models and parameters. This can be achieved through the command line interface, the low-level service layer (ChatClient), or the high-level service layer (ChatManager). The `stream` parameter, which enables streaming responses, is supported in the command line and low-level service layer but not in the high-level service layer.

Command Line
^^^^^^^^^^^^

The `geai chat completion` command generates a chat completion based on the provided model and messages. Various flags allow customization of the response, such as streaming, temperature, and maximum tokens.

.. code-block:: shell

    geai chat completion \
      --model "saia:assistant:Welcome data Assistant 3" \
      --messages '[{"role": "user", "content": "Hi, welcome to Globant Enterprise AI!!"}]' \
      --temperature 0.7 \
      --max-tokens 1000 \
      --stream 1

To use a different API key alias for authentication:

.. code-block:: shell

    geai --alias admin chat completion \
      --model "saia:assistant:Welcome data Assistant 3" \
      --messages '[{"role": "user", "content": "What is Globant Enterprise AI?"}]' \
      --temperature 0.5 \
      --max-tokens 500

For a non-streaming response with additional parameters like frequency and presence penalties:

.. code-block:: shell

    geai chat completion \
      --model "saia:assistant:Welcome data Assistant 3" \
      --messages '[{"role": "user", "content": "Can you explain AI solutions offered by Globant?"}]' \
      --temperature 0.6 \
      --max-tokens 800 \
      --frequency-penalty 0.1 \
      --presence-penalty 0.2 \
      --stream 0

Using tools and tool choice to fetch weather data:

.. code-block:: shell

    geai chat completion \
      --model "saia:assistant:Welcome data Assistant 3" \
      --messages '[{"role": "user", "content": "Please get the current weather for San Francisco."}]' \
      --temperature 0.6 \
      --max-tokens 800 \
      --tools '[{"name": "get_weather", "description": "Fetches the current weather for a given location", "parameters": {"type": "object", "properties": {"location": {"type": "string", "description": "City name"}}, "required": ["location"]}, "strict": true}]' \
      --tool-choice '{"type": "function", "function": {"name": "get_weather"}}' \
      --stream 1

Low Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

The `ChatClient` class provides a low-level interface to generate chat completions. It supports both streaming and non-streaming responses and allows fine-grained control over parameters.

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    response = client.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=[{"role": "user", "content": "What is Globant Enterprise AI?"}],
        temperature=0.5,
        max_tokens=500,
        stream=False
    )
    print(response)

Streaming response with tools:

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    llm_settings = {
        "temperature": 0.6,
        "max_tokens": 800,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.2
    }

    messages = [{"role": "user", "content": "Please get the current weather for San Francisco."}]

    tools = [
        {
            "name": "get_weather",
            "description": "Fetches the current weather for a given location",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string", "description": "City name"}},
                "required": ["location"]
            },
            "strict": True
        }
    ]

    tool_choice = {"type": "function", "function": {"name": "get_weather"}}

    response = client.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=messages,
        stream=True,
        tools=tools,
        tool_choice=tool_choice,
        **llm_settings
    )

    for chunk in response:
        print(chunk, end="")

Using variables and thread ID:

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    response = client.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for Globant Enterprise AI."},
            {"role": "user", "content": "What AI solutions does Globant offer?"}
        ],
        temperature=0.8,
        max_tokens=2000,
        presence_penalty=0.1,
        thread_id="thread_123e4567-e89b-12d3-a456-426614174000",
        variables=[{"key": "user_region", "value": "North America"}, {"key": "industry", "value": "Technology"}],
        stream=False
    )
    print(response)

High Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^^

The `ChatManager` class provides a high-level interface for generating chat completions. It does not support streaming responses but simplifies the process by using structured models like `ChatMessageList` and `LlmSettings`.

.. code-block:: python

    from pygeai.chat.managers import ChatManager
    from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage

    manager = ChatManager()

    llm_settings = LlmSettings(
        temperature=0.5,
        max_tokens=500,
        frequency_penalty=0.2
    )

    messages = ChatMessageList(
        messages=[ChatMessage(role="user", content="Can you explain what Globant Enterprise AI does?")]
    )

    response = manager.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=messages,
        llm_settings=llm_settings
    )
    print(response)

Using tools to check weather and send an email:

.. code-block:: python

    from pygeai.chat.managers import ChatManager
    from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage, ChatTool, ChatToolList

    manager = ChatManager()

    llm_settings = LlmSettings(
        temperature=0.7,
        max_tokens=1000,
        frequency_penalty=0.3,
        presence_penalty=0.2
    )

    messages = ChatMessageList(
        messages=[ChatMessage(role="user", content="Can you check the weather for New York and send an email summary?")]
    )

    tools = ChatToolList(
        variables=[
            ChatTool(
                name="get_weather",
                description="Fetches the current weather for a given location",
                parameters={
                    "type": "object",
                    "properties": {"location": {"type": "string", "description": "City name"}},
                    "required": ["location"]
                },
                strict=True
            ),
            ChatTool(
                name="send_email",
                description="Sends an email to a recipient with a subject and body",
                parameters={
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string", "description": "Email address"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email content"}
                    },
                    "required": ["recipient", "subject", "body"]
                },
                strict=False
            )
        ]
    )

    response = manager.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=messages,
        llm_settings=llm_settings,
        tools=tools
    )
    print(response)

With variables and thread ID:

.. code-block:: python

    from pygeai.chat.managers import ChatManager
    from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage, ChatVariable, ChatVariableList

    manager = ChatManager()

    llm_settings = LlmSettings(
        temperature=0.8,
        max_tokens=2000,
        presence_penalty=0.1
    )

    messages = ChatMessageList(
        messages=[
            ChatMessage(role="system", content="You are a helpful assistant for Globant Enterprise AI."),
            ChatMessage(role="user", content="What AI solutions does Globant offer?")
        ]
    )

    variables = ChatVariableList(
        variables=[
            ChatVariable(key="user_region", value="North America"),
            ChatVariable(key="industry", value="Technology")
        ]
    )

    response = manager.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=messages,
        llm_settings=llm_settings,
        thread_id="thread_123e4567-e89b-12d3-a456-426614174000",
        variables=variables
    )
    print(response)

With tool choice:

.. code-block:: python

    from pygeai.chat.managers import ChatManager
    from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage, ChatTool, ChatToolList, ToolChoice, ToolChoiceObject, ToolChoiceFunction

    manager = ChatManager()

    llm_settings = LlmSettings(
        temperature=0.6,
        max_tokens=800,
        frequency_penalty=0.1,
        presence_penalty=0.2
    )

    messages = ChatMessageList(
        messages=[ChatMessage(role="user", content="Please get the current weather for San Francisco.")]
    )

    tools = ChatToolList(
        variables=[
            ChatTool(
                name="get_weather",
                description="Fetches the current weather for a given location",
                parameters={
                    "type": "object",
                    "properties": {"location": {"type": "string", "description": "City name"}},
                    "required": ["location"]
                },
                strict=True
            ),
            ChatTool(
                name="send_notification",
                description="Sends a notification with a message",
                parameters={
                    "type": "object",
                    "properties": {"message": {"type": "string", "description": "Notification content"}},
                    "required": ["message"]
                },
                strict=False
            )
        ]
    )

    tool_choice = ToolChoice(
        value=ToolChoiceObject(
            function=ToolChoiceFunction(name="get_weather")
        )
    )

    response = manager.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=messages,
        llm_settings=llm_settings,
        tool_choice=tool_choice,
        tools=tools
    )
    print(response)

Image Generation
~~~~~~~~~~~~~~~~

The GEAI SDK provides functionality to generate images using AI models. This can be achieved through the command line interface or the low-level service layer (ChatClient).

Command Line
^^^^^^^^^^^^

The `geai chat generate-image` command generates images based on the provided model and parameters.

.. code-block:: shell

    geai chat generate-image \
      --model "openai/dall-e-3" \
      --prompt "A futuristic city with flying cars at sunset" \
      --n 1 \
      --quality "hd" \
      --size "1024x1024" \
      --aspect-ratio "1:1"

Generate multiple images with different aspect ratio:

.. code-block:: shell

    geai chat generate-image \
      --model "openai/dall-e-3" \
      --prompt "A serene mountain landscape with a lake" \
      --n 2 \
      --quality "standard" \
      --size "1792x1024" \
      --aspect-ratio "16:9"

Low Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

The `ChatClient.generate_image` method provides a low-level interface to generate images.

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    response = client.generate_image(
        model="openai/dall-e-3",
        prompt="A futuristic city with flying cars at sunset",
        n=1,
        quality="hd",
        size="1024x1024",
        aspect_ratio="1:1"
    )
    print(response)

Generate images without aspect ratio specification:

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    response = client.generate_image(
        model="openai/dall-e-3",
        prompt="An abstract painting with vibrant colors",
        n=1,
        quality="standard",
        size="1024x1024"
    )
    print(response)

Image Editing
~~~~~~~~~~~~~

The GEAI SDK provides functionality to edit existing images using AI models. This can be achieved through the command line interface or the low-level service layer (ChatClient).

Command Line
^^^^^^^^^^^^

The `geai chat edit-image` command edits an existing image based on the provided instructions.

.. code-block:: shell

    geai chat edit-image \
      --model "openai/dall-e-2" \
      --prompt "Remove the ball from the image" \
      --image "https://example.com/image.jpg" \
      --size "1024x1024" \
      --n 1 \
      --quality "high"

Edit with multiple variations:

.. code-block:: shell

    geai chat edit-image \
      --model "openai/dall-e-2" \
      --prompt "Change the background to a beach scene" \
      --image "https://example.com/photo.jpg" \
      --size "512x512" \
      --n 3 \
      --quality "standard"

Low Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

The `ChatClient.edit_image` method provides a low-level interface to edit images.

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    response = client.edit_image(
        model="openai/dall-e-2",
        prompt="Remove the ball from the image",
        image="https://example.com/image.jpg",
        size="1024x1024",
        n=1,
        quality="high"
    )
    print(response)

Edit with default parameters:

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    response = client.edit_image(
        model="openai/dall-e-2",
        prompt="Add a rainbow to the sky",
        image="https://example.com/landscape.jpg",
        size="512x512"
    )
    print(response)

Responses API
~~~~~~~~~~~~~

The GEAI SDK provides a Responses API that supports processing images and PDF files alongside text input. This API is particularly useful for multi-modal applications that need to analyze documents or images.

Command Line
^^^^^^^^^^^^

The `geai chat response` command generates a response using the Responses API with support for file uploads.

.. code-block:: shell

    geai chat response \
      --model "openai/gpt-4o" \
      --input "What do you see in this image?" \
      --files '["image.jpg"]' \
      --temperature 0.7 \
      --max-output-tokens 1000

Process multiple files with tools:

.. code-block:: shell

    geai chat response \
      --model "openai/gpt-4o" \
      --input "Analyze these documents and extract key information" \
      --files '["doc1.pdf", "doc2.pdf", "chart.jpg"]' \
      --tools '[{"name": "extract_data", "description": "Extracts structured data", "parameters": {"type": "object"}}]' \
      --tool-choice "auto" \
      --temperature 0.5 \
      --max-output-tokens 2000 \
      --stream 1

With reasoning and metadata:

.. code-block:: shell

    geai chat response \
      --model "openai/o1-pro" \
      --input "Solve this mathematical problem shown in the image" \
      --files '["math_problem.jpg"]' \
      --instructions "Show your work step by step" \
      --reasoning '{"effort": "high"}' \
      --metadata '{"task": "math_solving", "user_id": "123"}' \
      --temperature 1.0

Low Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

The `ChatClient.get_response` method provides a low-level interface for the Responses API.

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    response = client.get_response(
        model="openai/gpt-4o",
        input="What do you see in this image?",
        files=["image.jpg"],
        temperature=0.7,
        max_output_tokens=1000
    )
    print(response)

Streaming response with files:

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    response = client.get_response(
        model="openai/gpt-4o",
        input="Describe the content of these images",
        files=["image1.jpg", "image2.jpg"],
        stream=True,
        temperature=0.7
    )

    for chunk in response:
        print(chunk, end="")

With tools and advanced options:

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    tools = [
        {
            "name": "analyze_document",
            "description": "Analyzes document content",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Main topic"}
                }
            }
        }
    ]

    response = client.get_response(
        model="openai/gpt-4o",
        input="Analyze this PDF and extract key topics",
        files=["document.pdf"],
        tools=tools,
        tool_choice="auto",
        temperature=0.5,
        max_output_tokens=2000,
        parallel_tool_calls=True,
        metadata={"task": "document_analysis"},
        user="user123"
    )
    print(response)

With reasoning configuration:

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    response = client.get_response(
        model="openai/o1-pro",
        input="Solve this complex problem from the image",
        files=["problem.jpg"],
        instructions="Think step by step and show your reasoning",
        reasoning={"effort": "medium"},
        temperature=1.0,
        truncation="disabled",
        store=True
    )
    print(response)

Interactive Chat with Iris
~~~~~~~~~~~~~~~~~~~~~~~~~~

Iris is an AI assistant that helps guide users through the process of creating agents. The GEAI SDK provides an interactive chat interface for Iris.

Command Line
^^^^^^^^^^^^

The `geai chat iris` command starts an interactive chat session with Iris.

.. code-block:: shell

    geai chat iris

This opens an interactive prompt where you can ask Iris questions about creating and configuring agents. Type 'exit' or press Ctrl+C to close the chat.

Python API
^^^^^^^^^^

The `Iris` class provides a programmatic interface to chat with Iris.

.. code-block:: python

    from pygeai.chat.iris import Iris

    iris = Iris()
    messages = []

    user_message = {
        "role": "user",
        "content": "I want to create an agent for customer support"
    }
    messages.append(user_message)

    result = iris.stream_answer(messages)
    answer = ""
    for chunk in result:
        answer += chunk
        print(chunk, end="")

    assistant_message = {
        "role": "assistant",
        "content": answer
    }
    messages.append(assistant_message)

Interactive Chat with Agents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The GEAI SDK provides functionality to have interactive chat sessions with agents. This includes both command-line and GUI interfaces, as well as session management capabilities.

Command Line
^^^^^^^^^^^^

The `geai chat agent` command starts an interactive chat session with a specified agent.

Basic usage:

.. code-block:: shell

    geai chat agent --agent-name "my-support-agent"

This opens an interactive prompt where you can chat with the agent. Type 'exit' or press Ctrl+C to close the chat.

With GUI interface:

.. code-block:: shell

    geai chat agent --agent-name "my-support-agent" --gui

This launches a Streamlit-based graphical user interface for chatting with the agent. The GUI provides a more user-friendly experience with a web-based interface.

Note: The `--gui` option requires Streamlit to be installed. Install it with `pip install streamlit` if not already available.

Save conversation to a file:

.. code-block:: shell

    geai chat agent --agent-name "my-support-agent" --save-session conversation.json

This saves the conversation history to `conversation.json` after each message exchange. The session is automatically saved when you exit the chat.

Restore a previous conversation:

.. code-block:: shell

    geai chat agent --agent-name "my-support-agent" --restore-session conversation.json

This loads a previous conversation from `conversation.json` and continues the chat from where it left off. The conversation history is displayed before you can continue chatting.

Combine session save and restore:

.. code-block:: shell

    geai chat agent --agent-name "my-support-agent" --restore-session old_conv.json --save-session new_conv.json

This restores the conversation from `old_conv.json` and saves all subsequent messages to `new_conv.json`.

Python API
^^^^^^^^^^

The `AgentChatSession` class provides a programmatic interface to chat with agents.

.. code-block:: python

    from pygeai.chat.session import AgentChatSession

    session = AgentChatSession("my-support-agent")
    messages = []

    introduction = session.get_answer(
        ["You're about to speak to a user. Introduce yourself in a clear and concise manner."]
    )
    print(f"Agent: {introduction}")

    messages.append({"role": "assistant", "content": introduction})

    user_message = {
        "role": "user",
        "content": "How can I reset my password?"
    }
    messages.append(user_message)

    result = session.stream_answer(messages)
    answer = ""
    print("Agent: ", end="")
    for chunk in result:
        answer += chunk
        print(chunk, end="")

    messages.append({"role": "assistant", "content": answer})

Non-streaming chat:

.. code-block:: python

    from pygeai.chat.session import AgentChatSession

    session = AgentChatSession("my-support-agent")

    user_messages = [
        {"role": "user", "content": "What are your capabilities?"}
    ]

    answer = session.get_answer(user_messages)
    print(f"Agent: {answer}")