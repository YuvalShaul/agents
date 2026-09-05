# `langchain-core` Reference

> **Superseded.** A newer edition of this file, updated to langchain-core 1.6.2 with re-verified examples,
> lives on yuval.guide: <a href="https://www.yuval.guide/ai/langchain-core-reference/" target="_blank" rel="noopener">langchain_core-reference</a>.
> The <a href="https://www.yuval.guide/ai/langchain-stack/" target="_blank" rel="noopener">stack overview</a> explains how the three packages relate.
> This copy is kept as it was for the course material that references these versions.

**Pinned version: `langchain-core==1.5.3`** — everything below was derived by inspecting this
exact installed package, and every example was executed against it. Each heading links to
[reference.langchain.com](https://reference.langchain.com/python/langchain-core), which is
unversioned and always serves the latest 1.x.

## What `langchain-core` is

`langchain-core` is the interface layer of the LangChain ecosystem: it defines the abstract
types and the shared vocabulary that every other package speaks. It contains almost no working
implementations — no OpenAI client, no agent loop, no vector database — only the contracts.
Provider packages (`langchain-openai`, `langchain-ollama`) implement those contracts, and the
higher layers (`langchain`, `langgraph`) consume them. That is why a LangGraph agent can accept
a chat model from any provider: they all subclass the same `BaseChatModel` defined here.

**Layer order — the dependency arrow points one way:**

```
langchain  ──depends on──▶  langgraph  ──depends on──▶  langchain-core
```

Nothing below depends on anything above it. Verified from package metadata: `langchain` 1.3.14
requires `langgraph<1.3.0,>=1.2.5` and `langchain-core<2.0.0,>=1.4.9`; `langgraph` 1.2.10 requires
`langchain-core<2,>=1.4.7` and **does not require `langchain` at all**; `langchain-core` 1.5.3
requires neither. So `langchain-core` is the bottom of the stack — import it first, and expect
every layer above to speak its types.

## Index

| Name | What it is | Most-used methods & fields |
| --- | --- | --- |
| [`BaseChatModel`](#basechatmodel) | The interface every chat model implements | `invoke`, `stream`, `bind_tools`, `with_structured_output` |
| [`HumanMessage`](#humanmessage) | A turn written by the user | `text`, `pretty_print` |
| [`AIMessage`](#aimessage) | A turn produced by the model | `text`, `tool_calls`, `usage_metadata` |
| [`ToolMessage`](#toolmessage) | The result of a tool execution, fed back to the model | `content`, `tool_call_id`, `status` |
| [`SystemMessage`](#systemmessage) | Standing instructions for the model | `text`, `pretty_print` |
| [`@tool`](#tool) | Decorator turning a Python function into a tool | `invoke`, `name`, `args` |
| [`BaseTool`](#basetool) | The interface every tool implements | `invoke`, `run`, `args`, `tool_call_schema` |
| [`Runnable`](#runnable) | The universal "unit of work" contract behind everything | `invoke`, `batch`, `stream`, `pipe` (`\|`) |
| [`ChatPromptTemplate`](#chatprompttemplate) | Builds a message list from variables | `from_messages`, `format_messages`, `invoke` |
| [`StrOutputParser`](#stroutputparser) | Unwraps a model reply down to plain text | `invoke`, `parse` |

---

### [`BaseChatModel`](https://reference.langchain.com/python/langchain-core/language_models/chat_models/BaseChatModel)

The abstract base class every chat model subclasses. It takes a list of messages in and returns
a single `AIMessage` out. Because it is a `Runnable`, it gets `invoke`/`batch`/`stream` for
free; on top of that it adds `bind_tools` (attach tools the model may call) and
`with_structured_output` (force replies into a schema). You never instantiate this class
directly — a provider package gives you a concrete subclass.

```python
from langchain_core.language_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

# GenericFakeChatModel is core's own test double, so this runs with no provider installed.
model = GenericFakeChatModel(messages=iter([AIMessage("Paris.")]))

reply = model.invoke([SystemMessage("Be terse."), HumanMessage("Capital of France?")])
print(type(reply).__name__, reply.text)   # AIMessage Paris.
```

[↩ back to index](#index)

---

### [`HumanMessage`](https://reference.langchain.com/python/langchain-core/messages/human/HumanMessage)

The user's turn in a conversation. Its `type` is `"human"`, and its `content` is normally a
plain string (it can also be a list of content blocks for multimodal input). The `.text`
property always gives you the text, whatever shape `content` has.

```python
from langchain_core.messages import HumanMessage

msg = HumanMessage("What is 2 + 2?")
print(msg.type, "|", msg.text)   # human | What is 2 + 2?
```

[↩ back to index](#index)

---

### [`AIMessage`](https://reference.langchain.com/python/langchain-core/messages/ai/AIMessage)

The model's turn. Beyond `content`, it carries the two fields that make agent loops possible:
`tool_calls`, a list of `{"name", "args", "id"}` dicts the model wants executed, and
`usage_metadata` with token counts. When a model decides to call a tool, `content` is often
empty and `tool_calls` holds the real payload.

```python
from langchain_core.messages import AIMessage

msg = AIMessage(
    content="",
    tool_calls=[{"name": "add", "args": {"a": 2, "b": 2}, "id": "call_1"}],
)
print(msg.type, "|", msg.tool_calls[0]["name"], msg.tool_calls[0]["args"])
# ai | add {'a': 2, 'b': 2}
```

[↩ back to index](#index)

---

### [`ToolMessage`](https://reference.langchain.com/python/langchain-core/messages/tool/ToolMessage)

The result of running a tool, handed back to the model so it can continue. `tool_call_id` is
required and must match the `id` of the `AIMessage.tool_calls` entry it answers — that is how
the model pairs a request with its result. `status` is `"success"` by default, or `"error"` if
the tool raised.

```python
from langchain_core.messages import ToolMessage

msg = ToolMessage(content="4", tool_call_id="call_1")
print(msg.type, "|", msg.tool_call_id, "|", msg.status)   # tool | call_1 | success
```

[↩ back to index](#index)

---

### [`SystemMessage`](https://reference.langchain.com/python/langchain-core/messages/system/SystemMessage)

Standing instructions that frame the whole conversation — persona, rules, output format. It
conventionally sits first in the message list and is not part of the back-and-forth.

```python
from langchain_core.messages import HumanMessage, SystemMessage

conversation = [SystemMessage("You are a terse calculator."), HumanMessage("2 + 2?")]
print([m.type for m in conversation])   # ['system', 'human']
```

[↩ back to index](#index)

---

### [`@tool`](https://reference.langchain.com/python/langchain-core/tools/convert/tool)

A decorator that converts a plain Python function into a `BaseTool`. It reads the function name
as the tool name, the docstring as the description, and the type hints as the argument schema —
all three are what the model sees when deciding whether to call it, so the docstring is part of
the prompt, not just documentation.

```python
from langchain_core.tools import tool


@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


print(add.name, "|", add.description)   # add | Add two integers.
print(add.args)   # {'a': {'title': 'A', 'type': 'integer'}, 'b': {'title': 'B', 'type': 'integer'}}
print(add.invoke({"a": 2, "b": 3}))     # 5
```

[↩ back to index](#index)

---

### [`BaseTool`](https://reference.langchain.com/python/langchain-core/tools/base/BaseTool)

The interface behind every tool, including the ones `@tool` builds. It is a `Runnable`, so tools
are invoked like anything else — and `invoke` accepts either a plain argument dict or a whole
tool-call dict from an `AIMessage`, in which case it returns a ready-made `ToolMessage`.
Subclass it directly when a tool needs state or setup that a bare function cannot hold.

```python
from langchain_core.tools import BaseTool


class Echo(BaseTool):
    name: str = "echo"
    description: str = "Echo the input text."

    def _run(self, text: str) -> str:
        return text


print(Echo().invoke({"text": "hello"}))   # hello
```

[↩ back to index](#index)

---

### [`Runnable`](https://reference.langchain.com/python/langchain-core/runnables/base/Runnable)

The single most important abstraction in core: a unit of work that can be invoked, batched,
streamed and composed. Chat models, tools, prompts and parsers are all `Runnable`s, which is why
they share one calling convention and why the `|` operator can chain any of them into a pipeline.
Every method has an `a`-prefixed async twin (`ainvoke`, `abatch`, `astream`).

```python
from langchain_core.runnables import RunnableLambda

shout = RunnableLambda(lambda s: s.upper())
exclaim = RunnableLambda(lambda s: s + "!")
chain = shout | exclaim

print(chain.invoke("hello"))        # HELLO!
print(chain.batch(["a", "b"]))      # ['A!', 'B!']
```

[↩ back to index](#index)

---

### [`ChatPromptTemplate`](https://reference.langchain.com/python/langchain-core/prompts/chat/ChatPromptTemplate)

Turns variables into a message list. You declare turns as `(role, template)` tuples with
`{placeholders}`, then fill them in. It is a `Runnable`, so it chains straight into a model —
this is the standard first stage of a LangChain pipeline.

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [("system", "You translate to {language}."), ("human", "{text}")]
)

for m in prompt.format_messages(language="French", text="hello"):
    print(m.type, "|", m.text)
# system | You translate to French.
# human | hello
```

[↩ back to index](#index)

---

### [`StrOutputParser`](https://reference.langchain.com/python/langchain-core/output_parsers/string/StrOutputParser)

The simplest output parser: it takes whatever a model returned and gives you back a plain
string. Its job is to end a pipeline so the caller gets `str` instead of `AIMessage`. Core also
ships `JsonOutputParser` and `PydanticOutputParser` for structured results.

```python
from langchain_core.language_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([("human", "{text}")])
model = GenericFakeChatModel(messages=iter([AIMessage("bonjour")]))
pipeline = prompt | model | StrOutputParser()

print(repr(pipeline.invoke({"text": "hello"})))   # 'bonjour'
```

[↩ back to index](#index)
