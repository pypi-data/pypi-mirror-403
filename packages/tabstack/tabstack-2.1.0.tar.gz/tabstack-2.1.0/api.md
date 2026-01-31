# Agent

Types:

```python
from tabstack.types import AutomateEvent, ResearchEvent
```

Methods:

- <code title="post /automate">client.agent.<a href="./src/tabstack/resources/agent.py">automate</a>(\*\*<a href="src/tabstack/types/agent_automate_params.py">params</a>) -> <a href="./src/tabstack/types/automate_event.py">AutomateEvent</a></code>
- <code title="post /research">client.agent.<a href="./src/tabstack/resources/agent.py">research</a>(\*\*<a href="src/tabstack/types/agent_research_params.py">params</a>) -> <a href="./src/tabstack/types/research_event.py">ResearchEvent</a></code>

# Extract

Types:

```python
from tabstack.types import ExtractJsonResponse, ExtractMarkdownResponse
```

Methods:

- <code title="post /extract/json">client.extract.<a href="./src/tabstack/resources/extract.py">json</a>(\*\*<a href="src/tabstack/types/extract_json_params.py">params</a>) -> <a href="./src/tabstack/types/extract_json_response.py">ExtractJsonResponse</a></code>
- <code title="post /extract/markdown">client.extract.<a href="./src/tabstack/resources/extract.py">markdown</a>(\*\*<a href="src/tabstack/types/extract_markdown_params.py">params</a>) -> <a href="./src/tabstack/types/extract_markdown_response.py">ExtractMarkdownResponse</a></code>

# Generate

Types:

```python
from tabstack.types import GenerateJsonResponse
```

Methods:

- <code title="post /generate/json">client.generate.<a href="./src/tabstack/resources/generate.py">json</a>(\*\*<a href="src/tabstack/types/generate_json_params.py">params</a>) -> <a href="./src/tabstack/types/generate_json_response.py">GenerateJsonResponse</a></code>
