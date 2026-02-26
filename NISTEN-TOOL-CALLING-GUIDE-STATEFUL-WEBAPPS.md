# 🔧 LLM Tool Calling with TanStack Store & W&B Inference

> A complete guide to building apps where an LLM calls functions,
> using **TanStack Store** for state management, **SSE streaming**
> for real-time responses, and **W&B Inference API** as the LLM backend.
>
> Framework-agnostic. Works with Preact, React, Vue, Svelte, or vanilla JS.

---

## Table of Contents

1.  [Architecture Overview](#1-architecture-overview)
2.  [TanStack Store Crash Course](#2-tanstack-store-crash-course)
3.  [Chat State Design](#3-chat-state-design)
4.  [Settings Store (Persisted)](#4-settings-store-persisted)
5.  [Defining Tools](#5-defining-tools)
6.  [The System Prompt](#6-the-system-prompt)
7.  [Sending the Request](#7-sending-the-request)
8.  [Parsing the SSE Stream](#8-parsing-the-sse-stream)
9.  [Executing Tools](#9-executing-tools)
10. [The Follow-Up Loop](#10-the-follow-up-loop)
11. [Message Serialization](#11-message-serialization)
12. [Server Proxy (Bun)](#12-server-proxy-bun)
13. [W&B Inference API Reference](#13-wb-inference-api-reference)
14. [UI Integration](#14-ui-integration)
15. [Adapting for Different Apps](#15-adapting-for-different-apps)
16. [Gotchas & Debugging](#16-gotchas--debugging)
17. [Quick Reference Card](#17-quick-reference-card)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TOOL CALLING LIFECYCLE                            │
│                                                                           │
│                                                                           │
│   User types:  "check the weather and set AC to 72"                       │
│       │                                                                   │
│       ▼                                                                   │
│   ┌───────────────┐                                                       │
│   │ TanStack Store │  chatStore.setState(s => ({...s,                     │
│   │ (add user msg) │    messages: [...s.messages, userMsg]                 │
│   │               │  }))                                                  │
│   └───────┬───────┘                                                       │
│           │                                                               │
│           ▼                                                               │
│   ┌───────────────┐  POST /api/chat   ┌──────────────┐                    │
│   │   Frontend     │ ────────────────► │  Bun Server   │                   │
│   │   (browser)    │  {messages,       │  (proxy)      │                   │
│   │                │   tools,          │               │                   │
│   │                │   stream:true}    │  hides API    │                   │
│   │                │                   │  key from     │                   │
│   │                │                   │  browser      │                   │
│   └───────┬───────┘                   └───────┬───────┘                   │
│           │                                   │                           │
│           │                                   │  POST /v1/chat/completions│
│           │                                   ▼                           │
│           │                           ┌──────────────┐                    │
│           │                           │  W&B Inference│                   │
│           │                           │  API          │                   │
│           │                           │              │                   │
│           │                           │  Kimi-K2.5   │                   │
│           │                           │  Qwen        │                   │
│           │                           │  Llama       │                   │
│           │                           │  etc.        │                   │
│           │                           └───────┬──────┘                    │
│           │                                   │                           │
│           │  ◄──────── SSE stream ────────────┘                           │
│           │                                                               │
│   ┌───────▼───────┐                                                       │
│   │ streamResponse │  Parses 3 delta types:                               │
│   │ ()             │    • reasoning_content  (thinking)                   │
│   │                │    • tool_calls         (function calls)             │
│   │                │    • content            (text response)              │
│   └───────┬───────┘                                                       │
│           │                                                               │
│           │  tool_calls found?                                            │
│           │                                                               │
│     NO    │    YES                                                        │
│     │     │     │                                                         │
│     │     │     ▼                                                         │
│     │     │  ┌──────────────────┐                                         │
│     │     │  │ executeTool()     │  Run each tool locally                 │
│     │     │  │                  │  (API calls, DOM updates,              │
│     │     │  │                  │   postMessage, etc.)                    │
│     │     │  └────────┬─────────┘                                         │
│     │     │           │                                                   │
│     │     │           ▼                                                   │
│     │     │  ┌──────────────────┐                                         │
│     │     │  │ Add role:"tool"   │  Store results in chatStore            │
│     │     │  │ messages          │                                         │
│     │     │  └────────┬─────────┘                                         │
│     │     │           │                                                   │
│     │     │           ▼                                                   │
│     │     │  ┌──────────────────┐                                         │
│     │     │  │ sendFollowUp()    │  POST /api/chat again ──────┐          │
│     │     │  │ (recursive)       │                              │          │
│     │     │  └──────────────────┘              loops back to   │          │
│     │     │                                   streamResponse() │          │
│     ▼     │                                                    │          │
│   DONE    └────────────────────────────────────────────────────┘          │
│   (show                                                                   │
│    text)   The loop repeats until LLM returns text with NO tool_calls.   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**The protocol in one sentence**: Send tools + messages → LLM replies with
`tool_calls` → you execute them → send results back → LLM replies with text
(or more tool_calls).

This is the **OpenAI tool calling standard**. Kimi-K2.5, GPT-4, Claude,
Mistral, Qwen, Llama, and all models on W&B Inference support it.

---

## 2. TanStack Store Crash Course

TanStack Store is a **tiny** (~1KB) reactive state manager. No reducers,
no actions, no boilerplate. Just stores you read and write.

```
┌──────────────────────────────────────────────────────────────┐
│                  TANSTACK STORE API                           │
│                                                              │
│  import { Store, batch } from '@tanstack/store'              │
│  import { useStore } from '@tanstack/preact-store'           │
│  // or: '@tanstack/react-store', '@tanstack/vue-store', etc  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  CREATE                                             │     │
│  │  const store = new Store<Type>({ initial: "value" })│     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  UPDATE                                             │     │
│  │  store.setState(s => ({ ...s, field: newVal }))     │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  READ (in components — auto-subscribes)             │     │
│  │  const val = useStore(store, s => s.field)          │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  READ (outside components)                          │     │
│  │  const val = store.state.field                      │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  BATCH (multiple updates → single re-render)        │     │
│  │  batch(() => {                                      │     │
│  │    storeA.setState(...)                              │     │
│  │    storeB.setState(...)                              │     │
│  │  })                                                 │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  SUBSCRIBE (side effects outside components)        │     │
│  │  const { unsubscribe } = store.subscribe(() => {    │     │
│  │    console.log("changed:", store.state)              │     │
│  │  })                                                 │     │
│  │                                                     │     │
│  │  ⚠️  Returns { unsubscribe }, NOT a bare function!  │     │
│  │  ✅ const { unsubscribe } = store.subscribe(cb)     │     │
│  │  ❌ const unsub = store.subscribe(cb); unsub()      │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ⚠️  NEVER use useState, useReducer, or useEffect.          │
│      TanStack Store replaces all of them.                    │
└──────────────────────────────────────────────────────────────┘
```

### Install

```bash
bun add @tanstack/store @tanstack/preact-store
# or: @tanstack/react-store, @tanstack/vue-store, @tanstack/svelte-store
```

---

## 3. Chat State Design

Two stores handle all chat state: one for the conversation, one for user settings.

### ChatMsg Type

```typescript
interface ChatMsg {
  role: "user" | "assistant" | "tool";
  content: string;
  id: string;                // unique per message (for keying UI lists)
  toolName?: string;         // which tool was called (on role:"tool")
  toolArgs?: any;            // parsed arguments (for UI display)
  toolCallId?: string;       // links to the assistant's tool_calls[].id
  toolCalls?: any[];         // the raw tool_calls array (on assistant msgs)
  imageUrl?: string;         // base64 data URL for vision models
}
```

### Chat Store

```typescript
import { Store } from '@tanstack/store'

interface ChatState {
  messages: ChatMsg[];
  loading: boolean;          // true while waiting for LLM
  toolPhase: string | null;  // "get_weather..." shown during execution
  streamingText: string;     // partial text while streaming
  reasoningText: string;     // model's thinking (Kimi/DeepSeek)
  inputText: string;         // bound to the input field
  thinkingExpanded: boolean; // toggle for thinking bubble UI
}

const chatStore = new Store<ChatState>({
  messages: [],
  loading: false,
  toolPhase: null,
  streamingText: "",
  reasoningText: "",
  inputText: "",
  thinkingExpanded: false,
});
```

```
┌──────────────────────────────────────────────────────────────┐
│                 CHAT STATE FLOW                              │
│                                                              │
│  User sends message                                          │
│    │                                                         │
│    ├─► messages: [..., {role:"user", content:"..."}]         │
│    ├─► loading: true                                         │
│    ├─► streamingText: ""                                     │
│    │                                                         │
│  SSE reasoning chunks arrive                                 │
│    ├─► reasoningText: "Let me think..."  (shown in UI)       │
│    │                                                         │
│  SSE tool_call chunks arrive                                 │
│    ├─► toolPhase: "get_weather..."       (shown as badge)    │
│    ├─► reasoningText: ""                 (cleared)           │
│    │                                                         │
│  Stream ends, tools execute                                  │
│    ├─► messages: [..., {role:"assistant", toolCalls:[...]}]   │
│    ├─► messages: [..., {role:"tool", content:"{...}"}]       │
│    ├─► sendFollowUp()                                        │
│    │                                                         │
│  SSE content chunks arrive                                   │
│    ├─► streamingText: "The weather is..."                    │
│    ├─► messages[-1].content updated live                     │
│    │                                                         │
│  Stream ends, no tools                                       │
│    ├─► loading: false                                        │
│    └─► streamingText: ""                                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Settings Store (Persisted)

User preferences persisted to localStorage. Controls model, temperature,
which tools are enabled, etc.

```typescript
interface SettingsState {
  llmModel: string;           // "moonshotai/Kimi-K2.5"
  apiKey: string;             // user's own W&B key (optional)
  projectId: string;          // W&B project header
  temperature: number;        // 0.0 – 2.0
  topP: number;               // 0.0 – 1.0
  topK: number;               // 1 – 100
  repetitionPenalty: number;   // 1.0 – 2.0
  maxTokens: number;          // 1000 – 30000
  systemPrompt: string;       // custom override
  disabledTools: string[];    // ["search_web"] — tools user turned off
}

const STORAGE_KEY = "app_settings";

const DEFAULT_SETTINGS: SettingsState = {
  llmModel: "moonshotai/Kimi-K2.5",
  apiKey: "",
  projectId: "",
  temperature: 0.55,
  topP: 0.9,
  topK: 40,
  repetitionPenalty: 1.05,
  maxTokens: 16384,
  systemPrompt: "",
  disabledTools: [],
};

function loadSettings(): SettingsState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {}
  return { ...DEFAULT_SETTINGS };
}

function saveSettings(s: SettingsState) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); }
  catch {}
}

const settingsStore = new Store<SettingsState>(loadSettings());

// Auto-save on every change (subscribe returns {unsubscribe})
settingsStore.subscribe(() => saveSettings(settingsStore.state));
```

```
┌──────────────────────────────────────────────────────────────┐
│              SETTINGS PERSISTENCE PATTERN                    │
│                                                              │
│  App starts                                                  │
│    │                                                         │
│    ├─► loadSettings() reads localStorage                     │
│    ├─► Merges with DEFAULT_SETTINGS (handles new fields)     │
│    ├─► Creates Store with loaded state                       │
│    │                                                         │
│  User changes a setting                                      │
│    │                                                         │
│    ├─► settingsStore.setState(s => ({...s, temp: 0.7}))      │
│    ├─► subscribe() fires → saveSettings() writes localStorage│
│    │                                                         │
│  App restarts                                                │
│    └─► loadSettings() restores everything                    │
│                                                              │
│  ⚠️  Always merge with defaults: { ...DEFAULT, ...saved }   │
│      This prevents crashes when you add new settings later.  │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Defining Tools

Tools are JSON Schema objects describing functions the LLM can call.

### The Format

```
┌──────────────────────────────────────────────────────────────┐
│                  TOOL DEFINITION SHAPE                        │
│                                                              │
│  {                                                           │
│    type: "function",          ◄── always "function"          │
│    function: {                                               │
│      name: "snake_case_name", ◄── what the LLM calls        │
│      description: "...",      ◄── the LLM READS this!       │
│      parameters: {            ◄── JSON Schema for args      │
│        type: "object",                                       │
│        properties: {                                         │
│          arg1: { type: "string", description: "..." },       │
│          arg2: { type: "number" }                            │
│        },                                                    │
│        required: ["arg1"]                                    │
│      }                                                       │
│    }                                                         │
│  }                                                           │
└──────────────────────────────────────────────────────────────┘
```

### Example: Smart Home App

```typescript
const TOOL_DEFS = [
  {
    type: "function",
    function: {
      name: "get_weather",
      description:
        "Get current weather for a city. Returns temperature, " +
        "humidity, conditions. Call this before making thermostat " +
        "decisions.",
      parameters: {
        type: "object",
        properties: {
          city: {
            type: "string",
            description: "City name (e.g. 'Tokyo', 'New York')"
          }
        },
        required: ["city"]
      },
    },
  },
  {
    type: "function",
    function: {
      name: "set_thermostat",
      description:
        "Set home thermostat. temp in °F (60-85). " +
        "mode: 'heat', 'cool', or 'auto'.",
      parameters: {
        type: "object",
        properties: {
          temp: { type: "number", description: "Temperature in °F" },
          mode: {
            type: "string",
            enum: ["heat", "cool", "auto"],
            description: "HVAC mode"
          },
        },
        required: ["temp"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "control_lights",
      description:
        "Control smart lights. room: which room. " +
        "brightness: 0=off, 100=full. color: hex color code.",
      parameters: {
        type: "object",
        properties: {
          room:       { type: "string", description: "Room name" },
          brightness: { type: "number", description: "0-100" },
          color:      { type: "string", description: "Hex (#ff0000)" },
        },
        required: ["room", "brightness"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "search_web",
      description: "Search the web for current information.",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string" },
          count: { type: "number", description: "Results (1-10)" },
        },
        required: ["query"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "get_app_state",
      description:
        "Get current state of all devices — thermostat, lights, " +
        "locks. Call this to check before making changes.",
      parameters: { type: "object", properties: {} },  // no params
    },
  },
];
```

### Description Writing Rules

```
┌───────────────────────────────────────────────────────────────┐
│                 WRITING GOOD DESCRIPTIONS                     │
│                                                               │
│  The LLM only "sees" the name, description, and schema.      │
│  Your description IS your documentation. Make it count.       │
│                                                               │
│  ✅ DO                               ❌ DON'T                │
│  ──────────────────                  ──────────────────       │
│  List valid enum values              Vague one-liners         │
│  "mode: 'heat','cool','auto'"        "Controls the AC"       │
│                                                               │
│  Say WHEN to call it                 Assume LLM knows         │
│  "Call before making                 your app's logic         │
│   thermostat decisions"                                       │
│                                                               │
│  Give ranges & units                 Leave bounds open        │
│  "temp in °F (60-85)"               "Set temperature"        │
│                                                               │
│  Explain the return value            Only describe input      │
│  "Returns temperature,                                        │
│   humidity, conditions"                                       │
│                                                               │
│  Use snake_case for names            camelCase or spaces      │
│  set_thermostat ✅                   setThermostat ❌         │
│                                                               │
│  Mark truly required params          Make everything optional │
│  required: ["city"] ✅               required: [] ❌          │
│                                                               │
│  Put ordering hints                  Hope for the best        │
│  "Call FIRST" / "Call AFTER x"       (LLM guesses order)     │
└───────────────────────────────────────────────────────────────┘
```

---

## 6. The System Prompt

The system prompt tells the LLM **who it is** and **how to use tools**.

```
┌───────────────────────────────────────────────────────────────┐
│              SYSTEM PROMPT STRUCTURE                           │
│                                                               │
│  ┌────────────────────────┐                                   │
│  │  1. PERSONA            │  Who is the AI?                   │
│  │  "You are a smart home │  Sets tone, expertise,            │
│  │   assistant..."        │  personality.                     │
│  └──────────┬─────────────┘                                   │
│             ▼                                                 │
│  ┌────────────────────────┐                                   │
│  │  2. TOOL SUMMARY       │  List each tool with usage hints  │
│  │  "Use aggressively"    │  Tell it WHEN to call each one    │
│  │  "Call FIRST"          │  Ordering hints matter!           │
│  │  "Call MULTIPLE times" │                                   │
│  └──────────┬─────────────┘                                   │
│             ▼                                                 │
│  ┌────────────────────────┐                                   │
│  │  3. WORKFLOWS          │  Multi-step recipes               │
│  │  "First check state,   │  Show the LLM how to chain tools │
│  │   then adjust,         │  for complex tasks.               │
│  │   then confirm"        │                                   │
│  └──────────┬─────────────┘                                   │
│             ▼                                                 │
│  ┌────────────────────────┐                                   │
│  │  4. CONSTRAINTS        │  Hard rules & failure handling    │
│  │  "If tool fails,       │  Prevents hallucinating results  │
│  │   say so"              │  the tool didn't return.         │
│  │  "NEVER guess state"   │                                   │
│  └────────────────────────┘                                   │
└───────────────────────────────────────────────────────────────┘
```

### Example

```typescript
const SYSTEM_PROMPT = `You are a helpful smart home assistant.
You control lights, thermostat, and can search the web.

## YOUR TOOLS:
- **get_weather**: Check weather. Call FIRST before adjusting thermostat.
- **set_thermostat**: Set temperature and HVAC mode.
- **control_lights**: Set room brightness and color.
- **search_web**: Look up information online.
- **get_app_state**: Check current device states. Call this before
  describing what's currently set.

## WORKFLOWS:
1. "Make it warmer" → get_app_state → set_thermostat
2. "Movie mode" → control_lights(living_room, 20) + control_lights(kitchen, 0)
3. "Going to bed" → control_lights(all rooms, 0) + set_thermostat(68, heat)

## RULES:
- ALWAYS call get_app_state before saying what's currently set
- If a tool call FAILS, tell the user — don't pretend it worked
- For multi-device requests, call ALL tools (don't ask for confirmation)
- Keep responses concise — the app shows device states visually`;
```

---

## 7. Sending the Request

### Request Shape

```
POST /api/chat
Content-Type: application/json

┌──────────────────────────────────────────────────────────────┐
│ {                                                            │
│   "messages": [                                              │
│     { "role": "system", "content": "You are..." },          │
│     { "role": "user",   "content": "make it warmer" }       │
│   ],                                                         │
│                                                              │
│   "tools": [ ...TOOL_DEFS ],      ◄── array of tool schemas │
│   "tool_choice": "auto",          ◄── see options below     │
│   "stream": true,                  ◄── SSE streaming         │
│                                                              │
│   "max_tokens": 16384,                                       │
│   "temperature": 0.55,                                       │
│   "top_p": 0.9,                                              │
│   "top_k": 40,                                               │
│   "repetition_penalty": 1.05                                 │
│ }                                                            │
└──────────────────────────────────────────────────────────────┘
```

### `tool_choice` Values

```
┌──────────────────────────────────────────────────────────────┐
│  "auto"       LLM decides whether to call tools or not      │
│               → Use 99% of the time                         │
│                                                              │
│  "none"       LLM will NOT call tools (text only)           │
│               → Useful for forcing text after tool results   │
│                                                              │
│  "required"   LLM MUST call at least one tool               │
│               → Use for action-only flows                    │
│                                                              │
│  { "type":    Force a SPECIFIC tool                         │
│    "function",→ Use for guided step-by-step workflows        │
│    "function":                                               │
│    {"name":"get_weather"} }                                  │
└──────────────────────────────────────────────────────────────┘
```

### The `sendMessage()` Function

```typescript
async function sendMessage(userInput: string) {
  const input = userInput.trim();
  if (!input) return;

  // 1 ── Add user message to store
  const userMsg: ChatMsg = {
    role: "user",
    content: input,
    id: `u_${Date.now()}`
  };
  chatStore.setState(s => ({
    ...s,
    messages: [...s.messages, userMsg],
    loading: true,
    streamingText: "",
    toolPhase: null,
  }));

  try {
    // 2 ── Serialize conversation history
    const msgs = serializeMsgs(chatStore.state.messages);

    // 3 ── Filter out disabled tools
    const cfg = settingsStore.state;
    const activeTools = TOOL_DEFS.filter(
      t => !cfg.disabledTools.includes(t.function.name)
    );

    // 4 ── POST to server proxy
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: [
          { role: "system", content: cfg.systemPrompt || SYSTEM_PROMPT },
          ...msgs,
        ],
        tools: activeTools.length ? activeTools : undefined,
        tool_choice: activeTools.length ? "auto" : undefined,
        stream: true,
        max_tokens: cfg.maxTokens,
        temperature: cfg.temperature,
        top_p: cfg.topP,
        top_k: cfg.topK,
        repetition_penalty: cfg.repetitionPenalty,
        ...(cfg.llmModel ? { model: cfg.llmModel } : {}),
        ...(cfg.apiKey ? { apiKey: cfg.apiKey } : {}),
      }),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: "Unknown" }));
      chatStore.setState(s => ({
        ...s,
        messages: [...s.messages, {
          role: "assistant",
          content: `Error: ${err.error || resp.status}`,
          id: `e_${Date.now()}`
        }],
        loading: false,
      }));
      return;
    }

    // 5 ── Parse the SSE stream
    await streamResponse(resp);
  } catch (e: any) {
    chatStore.setState(s => ({
      ...s,
      messages: [...s.messages, {
        role: "assistant",
        content: `Network error: ${e.message}`,
        id: `ne_${Date.now()}`
      }],
      loading: false,
    }));
  }
}
```

---

## 8. Parsing the SSE Stream

The LLM sends **Server-Sent Events**. Tool call arguments arrive **in
fragments** that you must concatenate.

### Raw SSE From W&B / Kimi-K2.5

```
── Phase 1: Thinking (reasoning_content) ──────────────────────
data: {"choices":[{"delta":{"reasoning_content":"The user wants"}}]}
data: {"choices":[{"delta":{"reasoning_content":" it warmer. I should"}}]}
data: {"choices":[{"delta":{"reasoning_content":" check current state first."}}]}

── Phase 2: Tool calls (streamed in FRAGMENTS) ────────────────
data: {"choices":[{"delta":{"tool_calls":[{
  "index": 0,
  "id": "call_abc123",
  "function": {"name": "get_app_state", "arguments": ""}
}]}}]}

data: {"choices":[{"delta":{"tool_calls":[{
  "index": 0,
  "function": {"arguments": "{}"}
}]}}]}

── (after follow-up with results, more tool calls) ────────────
data: {"choices":[{"delta":{"tool_calls":[{
  "index": 0,
  "id": "call_def456",
  "function": {"name": "set_thermostat", "arguments": ""}
}]}}]}

data: {"choices":[{"delta":{"tool_calls":[{
  "index": 0,
  "function": {"arguments": "{\"te"}
}]}}]}

data: {"choices":[{"delta":{"tool_calls":[{
  "index": 0,
  "function": {"arguments": "mp\":74,\"mo"}
}]}}]}

data: {"choices":[{"delta":{"tool_calls":[{
  "index": 0,
  "function": {"arguments": "de\":\"heat\"}"}
}]}}]}

data: [DONE]
```

### Why Arguments Are Fragmented

```
┌──────────────────────────────────────────────────────────────┐
│         ARGUMENT STREAMING — THE KEY INSIGHT                 │
│                                                              │
│  The LLM generates tokens one at a time, including the       │
│  JSON arguments string. You get partial JSON:                │
│                                                              │
│  Chunk 1:  arguments: "{\"te"                                │
│  Chunk 2:  arguments: "mp\":74,\"mo"                         │
│  Chunk 3:  arguments: "de\":\"heat\"}"                       │
│                     ↓ concatenate                            │
│  Full:     arguments: "{\"temp\":74,\"mode\":\"heat\"}"      │
│                     ↓ JSON.parse()                           │
│  Result:   { temp: 74, mode: "heat" }                        │
│                                                              │
│  ⚠️  NEVER JSON.parse() until the stream is fully DONE!     │
│  ⚠️  Multiple tool calls use "index" to disambiguate.        │
└──────────────────────────────────────────────────────────────┘
```

### The `streamResponse()` Function

```typescript
async function streamResponse(resp: Response) {
  const reader = resp.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let accText = "";
  let accReasoning = "";
  const toolCalls: any[] = [];
  const assistantMsgId = `a_${Date.now()}`;

  // Add placeholder assistant message to UI
  chatStore.setState(s => ({
    ...s,
    messages: [...s.messages, {
      role: "assistant", content: "", id: assistantMsgId
    }],
    reasoningText: "",
  }));

  while (true) {
    const { done, value } = await reader!.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE lines are separated by \n
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";  // keep incomplete line in buffer

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6).trim();
      if (data === "[DONE]") break;

      let chunk: any;
      try { chunk = JSON.parse(data); }
      catch { continue; }

      const delta = chunk.choices?.[0]?.delta;
      if (!delta) continue;

      // ── Reasoning (Kimi-K2.5 / DeepSeek thinking) ──────
      if (delta.reasoning_content) {
        accReasoning += delta.reasoning_content;
        chatStore.setState(s => ({
          ...s,
          reasoningText: accReasoning,
        }));
      }

      // ── Text content ───────────────────────────────────
      if (delta.content) {
        accText += delta.content;
        chatStore.setState(s => ({
          ...s,
          streamingText: accText,
          reasoningText: "",  // clear thinking once text starts
          messages: s.messages.map(m =>
            m.id === assistantMsgId
              ? { ...m, content: accText }
              : m
          ),
        }));
      }

      // ── Tool calls (accumulate by index!) ──────────────
      if (delta.tool_calls) {
        for (const tc of delta.tool_calls) {
          const idx = tc.index ?? 0;

          // First chunk for this tool — create entry
          if (!toolCalls[idx]) {
            toolCalls[idx] = {
              id: tc.id || "",
              type: "function",
              function: { name: "", arguments: "" },
            };
          }

          // Set name (arrives in first chunk only)
          if (tc.function?.name) {
            toolCalls[idx].function.name = tc.function.name;
          }

          // CONCATENATE arguments (arrives across many chunks)
          if (tc.function?.arguments) {
            toolCalls[idx].function.arguments +=
              tc.function.arguments;
          }

          // Update UI with current tool phase
          chatStore.setState(s => ({
            ...s,
            toolPhase: `${toolCalls[idx].function.name}...`,
            reasoningText: "",
          }));
        }
      }
    }
  }

  // ── Stream finished ────────────────────────────────────
  chatStore.setState(s => ({
    ...s,
    streamingText: "",
    reasoningText: "",
    toolPhase: null,
  }));

  // ── Execute tools if any ───────────────────────────────
  if (toolCalls.length > 0) {
    // Attach tool_calls to the assistant message
    chatStore.setState(s => ({
      ...s,
      messages: s.messages.map(m =>
        m.id === assistantMsgId
          ? { ...m, toolCalls }
          : m
      ),
    }));

    // Execute each tool and collect results
    const toolResults: ChatMsg[] = [];
    for (const tc of toolCalls) {
      if (!tc.function.name) continue;
      chatStore.setState(s => ({
        ...s,
        toolPhase: tc.function.name,
      }));

      const args = safeJson(tc.function.arguments, {});
      const result = await executeTool(tc.function.name, args);

      toolResults.push({
        role: "tool",
        content: JSON.stringify(result),
        id: `t_${Date.now()}`,
        toolName: tc.function.name,
        toolArgs: args,
        toolCallId: tc.id,     // ◄── MUST match tc.id!
      });
    }

    // Add tool results to store
    chatStore.setState(s => ({
      ...s,
      messages: [...s.messages, ...toolResults],
      toolPhase: null,
    }));

    // Follow-up: send results back to LLM
    await sendFollowUp();
  } else {
    // No tools — just text. We're done.
    chatStore.setState(s => ({ ...s, loading: false }));
  }
}

// Safe JSON parse helper
function safeJson<T>(s: string, fallback: T): T {
  try { return JSON.parse(s); }
  catch { return fallback; }
}
```

### The Three Delta Types

```
┌──────────────────────────────────────────────────────────────┐
│              SSE DELTA TYPES                                 │
│                                                              │
│  delta.reasoning_content                                     │
│  ├── Only on thinking models (Kimi-K2.5, DeepSeek-R1)       │
│  ├── Arrives FIRST, before tool_calls or content             │
│  ├── Show as a collapsible "thinking" bubble in UI           │
│  └── Clear it when content or tool_calls start               │
│                                                              │
│  delta.tool_calls                                            │
│  ├── Array of {index, id?, function: {name?, arguments?}}    │
│  ├── index disambiguates parallel tool calls (0, 1, 2...)    │
│  ├── id only appears in the FIRST chunk for each call        │
│  ├── name only appears in the FIRST chunk                    │
│  ├── arguments is FRAGMENTED — concatenate as strings!       │
│  └── JSON.parse arguments ONLY after [DONE]                  │
│                                                              │
│  delta.content                                               │
│  ├── Normal text response — stream to UI character by char   │
│  ├── Mutually exclusive with tool_calls in same response     │
│  └── May appear after tool results in follow-up              │
│                                                              │
│  ⚠️  reasoning → tool_calls OR content (never both at once) │
└──────────────────────────────────────────────────────────────┘
```

---

## 9. Executing Tools

After streaming, you have `toolCalls[]` with `{name, arguments}`.
Parse and dispatch.

```typescript
async function executeTool(name: string, args: any): Promise<any> {
  switch (name) {

    case "get_weather": {
      try {
        const resp = await fetch(
          `/api/weather?city=${encodeURIComponent(args.city)}`
        );
        return await resp.json();
      } catch (e: any) {
        return { ok: false, reason: e.message };
      }
    }

    case "set_thermostat": {
      try {
        await fetch("/api/thermostat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            temp: args.temp,
            mode: args.mode || "auto"
          }),
        });
        // Update app state so UI reflects change
        appStore.setState(s => ({
          ...s,
          thermostat: { temp: args.temp, mode: args.mode || "auto" }
        }));
        return { ok: true, temp: args.temp, mode: args.mode || "auto" };
      } catch (e: any) {
        return { ok: false, reason: e.message };
      }
    }

    case "control_lights": {
      // postMessage to a lights controller, or call an API
      await fetch("/api/lights", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(args),
      });
      return { ok: true, room: args.room, brightness: args.brightness };
    }

    case "search_web": {
      const resp = await fetch(
        `/api/search?q=${encodeURIComponent(args.query)}&n=${args.count || 5}`
      );
      const data = await resp.json();
      return { ok: true, results: data.results.slice(0, 5) };
    }

    case "get_app_state": {
      // Read directly from store — no network call needed
      return {
        ok: true,
        thermostat: appStore.state.thermostat,
        lights: appStore.state.lights,
        locks: appStore.state.locks,
      };
    }

    default:
      return { ok: false, reason: `Unknown tool: ${name}` };
  }
}
```

### Tool Result Design

```
┌──────────────────────────────────────────────────────────────┐
│           WHAT executeTool() SHOULD RETURN                    │
│                                                              │
│  The return value is JSON.stringify'd and sent back to the   │
│  LLM as role:"tool" content. The LLM reads it to generate   │
│  its response.                                               │
│                                                              │
│  ✅ GOOD                                                     │
│  { ok: true, temp: 74, mode: "heat" }                        │
│  { ok: false, reason: "Device offline" }                     │
│  { ok: true, results: [{title:"...", url:"..."}] }           │
│                                                              │
│  ❌ BAD                                                      │
│  "success"               ← LLM can't reason about this      │
│  undefined               ← becomes "null", confusing         │
│  { data: <50KB blob> }   ← wastes context window             │
│  throw new Error(...)    ← breaks the tool loop entirely     │
│                                                              │
│  📏 RULES:                                                   │
│  • Always return { ok: true/false, ... }                     │
│  • On failure → { ok: false, reason: "what went wrong" }     │
│  • On success → include key data the LLM needs              │
│  • Keep it SMALL (<2KB) — this eats context window           │
│  • NEVER throw — always try/catch and return ok:false        │
│  • NEVER include raw HTML, base64, or giant arrays           │
└──────────────────────────────────────────────────────────────┘
```

---

## 10. The Follow-Up Loop

After tool execution, send results back. The LLM may call more tools
or finally produce text.

```
┌──────────────────────────────────────────────────────────────┐
│                    THE RECURSIVE LOOP                         │
│                                                              │
│  sendMessage()                                               │
│      │                                                       │
│      ▼                                                       │
│  ┌──────────────┐                                            │
│  │ streamResponse│                                            │
│  └──────┬───────┘                                            │
│         │                                                    │
│         │  toolCalls.length > 0?                              │
│         │                                                    │
│    NO ──┤── YES                                              │
│    │    │    │                                                │
│    │    │    ▼                                                │
│    │    │  execute tools                                      │
│    │    │  add role:"tool" msgs                               │
│    │    │    │                                                │
│    │    │    ▼                                                │
│    │    │  sendFollowUp() ──────────────────┐                 │
│    │    │    │                              │                 │
│    │    │    ▼                              │                 │
│    │    │  streamResponse() ◄──────────────┘                  │
│    │    │    │                                                │
│    │    │    └─► may loop again if LLM calls more tools       │
│    │    │                                                    │
│    ▼    │                                                    │
│  DONE   │  Typical: 1-2 loops. Complex: 3-4 loops.           │
│  (text) │                                                    │
└──────────────────────────────────────────────────────────────┘
```

```typescript
async function sendFollowUp() {
  try {
    const msgs = serializeMsgs(chatStore.state.messages);
    const cfg = settingsStore.state;
    const sysPrompt = cfg.systemPrompt || SYSTEM_PROMPT;
    const activeTools = TOOL_DEFS.filter(
      t => !cfg.disabledTools.includes(t.function.name)
    );

    // Use fewer tokens for follow-ups (LLM already has context)
    const followUpTokens = Math.max(
      1000,
      Math.round(cfg.maxTokens / 2)
    );

    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: [
          { role: "system", content: sysPrompt },
          ...msgs,   // ◄── now includes tool result messages!
        ],
        tools: activeTools.length ? activeTools : undefined,
        tool_choice: activeTools.length ? "auto" : undefined,
        stream: true,
        max_tokens: followUpTokens,
        temperature: cfg.temperature,
        top_p: cfg.topP,
        top_k: cfg.topK,
        repetition_penalty: cfg.repetitionPenalty,
        ...(cfg.llmModel ? { model: cfg.llmModel } : {}),
        ...(cfg.apiKey ? { apiKey: cfg.apiKey } : {}),
      }),
    });

    if (resp.ok) {
      await streamResponse(resp);  // ◄── RECURSIVE!
    } else {
      chatStore.setState(s => ({ ...s, loading: false }));
    }
  } catch {
    chatStore.setState(s => ({ ...s, loading: false }));
  }
}
```

---

## 11. Message Serialization

The OpenAI API is **strict** about message format. Three types need special
shapes.

```
┌──────────────────────────────────────────────────────────────┐
│              THE THREE MESSAGE SHAPES                         │
│                                                              │
│  ┌─ Plain User ──────────────────────────────────────────┐   │
│  │  { role: "user", content: "make it warmer" }          │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ User with Image (Vision) ────────────────────────────┐   │
│  │  { role: "user",                                      │   │
│  │    content: [                                         │   │
│  │      { type: "text", text: "what's this?" },          │   │
│  │      { type: "image_url",                             │   │
│  │        image_url: { url: "data:image/png;base64,..." }│   │
│  │      }                                                │   │
│  │    ]                                                  │   │
│  │  }                                                    │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ Assistant with Tool Calls ───────────────────────────┐   │
│  │  { role: "assistant",                                 │   │
│  │    content: "",        ◄── often empty                │   │
│  │    tool_calls: [                                      │   │
│  │      { id: "call_abc123",                             │   │
│  │        type: "function",                              │   │
│  │        function: {                                    │   │
│  │          name: "set_thermostat",                      │   │
│  │          arguments: "{\"temp\":74}"                   │   │
│  │        }                                              │   │
│  │      }                                                │   │
│  │    ]                                                  │   │
│  │  }                                                    │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ Tool Result ─────────────────────────────────────────┐   │
│  │  { role: "tool",                                      │   │
│  │    content: "{\"ok\":true,\"temp\":74}",              │   │
│  │    tool_call_id: "call_abc123",  ◄── MUST MATCH!      │   │
│  │    name: "set_thermostat"                             │   │
│  │  }                                                    │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ⚠️  tool_call_id MUST match the id from tool_calls[]       │
│  ⚠️  content in tool msgs MUST be a string (JSON.stringify)  │
│  ⚠️  assistant msg MUST include tool_calls array             │
└──────────────────────────────────────────────────────────────┘
```

### Full Conversation Example

```
┌─ What gets sent to the API ─────────────────────────────────┐
│                                                              │
│  [0] system:    "You are a smart home assistant..."          │
│  [1] user:      "make it warmer"                             │
│  [2] assistant: { content: "",                               │
│                   tool_calls: [{                             │
│                     id: "call_1",                            │
│                     function: {                              │
│                       name: "get_app_state",                 │
│                       arguments: "{}"                        │
│                     }                                        │
│                   }]                                         │
│                 }                                            │
│  [3] tool:      { content: "{\"thermostat\":{\"temp\":68}}", │
│                   tool_call_id: "call_1",                    │
│                   name: "get_app_state" }                    │
│  [4] assistant: { content: "",                               │
│                   tool_calls: [{                             │
│                     id: "call_2",                            │
│                     function: {                              │
│                       name: "set_thermostat",                │
│                       arguments: "{\"temp\":74}"             │
│                     }                                        │
│                   }]                                         │
│                 }                                            │
│  [5] tool:      { content: "{\"ok\":true,\"temp\":74}",      │
│                   tool_call_id: "call_2",                    │
│                   name: "set_thermostat" }                   │
│                                                              │
│  → LLM responds: "Done! I've bumped the thermostat from     │
│    68°F to 74°F. It should warm up in a few minutes."        │
└──────────────────────────────────────────────────────────────┘
```

### The `serializeMsgs()` Function

```typescript
function serializeMsgs(messages: ChatMsg[]) {
  return messages.map(m => {

    // Assistant with tool calls — include tool_calls array
    if (m.role === "assistant" && m.toolCalls?.length) {
      return {
        role: "assistant",
        content: m.content || "",
        tool_calls: m.toolCalls,
      };
    }

    // Tool result — include tool_call_id and name
    if (m.role === "tool") {
      return {
        role: "tool",
        content: m.content,            // already JSON string
        tool_call_id: m.toolCallId,    // MUST match call id
        name: m.toolName,
      };
    }

    // User with image — multipart content array
    if (m.role === "user" && m.imageUrl) {
      return {
        role: "user",
        content: [
          ...(m.content
            ? [{ type: "text", text: m.content }]
            : []),
          {
            type: "image_url",
            image_url: { url: m.imageUrl },
          },
        ],
      };
    }

    // Default — plain text
    return { role: m.role, content: m.content };
  });
}
```

---

## 12. Server Proxy (Bun)

Your server sits between browser and W&B API. It hides API keys, rate-limits,
and pipes the SSE stream.

```typescript
// serve.ts — Bun HTTP server

const WANDB_API_KEY = process.env.WANDB_API_KEY || "";
const PORT = Number(process.env.PORT) || 3001;

// ── Rate limiter (per IP, 20 requests/minute) ────────────
const rateLimits = new Map<string, number[]>();

function checkRateLimit(req: Request): boolean {
  const ip = req.headers.get("x-forwarded-for")
    || req.headers.get("cf-connecting-ip")
    || "unknown";
  const now = Date.now();
  const window = 60_000;  // 1 minute
  const max = 20;

  const times = (rateLimits.get(ip) || [])
    .filter(t => now - t < window);
  if (times.length >= max) return false;
  times.push(now);
  rateLimits.set(ip, times);
  return true;
}

// ── Bun.serve ────────────────────────────────────────────
Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);

    // ── Chat API proxy ───────────────────────────────────
    if (url.pathname === "/api/chat" && req.method === "POST") {
      if (!checkRateLimit(req)) {
        return new Response(
          JSON.stringify({ error: "Rate limited" }),
          { status: 429 }
        );
      }

      let body: any;
      try { body = await req.json(); }
      catch {
        return new Response(
          JSON.stringify({ error: "Invalid JSON" }),
          { status: 400 }
        );
      }

      // Cap max tokens server-side
      const MAX_ALLOWED = 30000;
      const maxTokens = Math.min(
        Math.max(1, body.max_tokens || 20000),
        MAX_ALLOWED
      );
      const doStream = body.stream !== false;

      // Resolve API key (body override > env var)
      const apiKey = body.apiKey || WANDB_API_KEY;
      if (!apiKey) {
        return new Response(
          JSON.stringify({ error: "No API key configured" }),
          { status: 500 }
        );
      }

      // W&B project header (routes to model group)
      const projectHeader =
        body.project || "your-org/your-project";

      // ── Forward to W&B Inference API ───────────────────
      let upstream: Response;
      try {
        upstream = await fetch(
          "https://api.inference.wandb.ai/v1/chat/completions",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${apiKey}`,
              "OpenAI-Project": projectHeader,
            },
            body: JSON.stringify({
              model: body.model || "moonshotai/Kimi-K2.5",
              messages: body.messages,

              // Pass tools through to the LLM
              ...(body.tools?.length
                ? {
                    tools: body.tools,
                    tool_choice: body.tool_choice || "auto",
                  }
                : {}),

              stream: doStream,
              max_tokens: maxTokens,
              temperature:
                typeof body.temperature === "number"
                  ? body.temperature : 0.55,
              top_p:
                typeof body.top_p === "number"
                  ? body.top_p : 0.9,
              top_k:
                typeof body.top_k === "number"
                  ? body.top_k : 40,
              repetition_penalty:
                typeof body.repetition_penalty === "number"
                  ? body.repetition_penalty : 1.05,
            }),
            signal: AbortSignal.timeout(300_000), // 5 min
          }
        );
      } catch (e) {
        return new Response(
          JSON.stringify({ error: "Failed to connect to LLM" }),
          { status: 502 }
        );
      }

      if (!upstream.ok) {
        const errText = await upstream.text();
        return new Response(
          JSON.stringify({
            error: `Upstream ${upstream.status}: ${errText.slice(0, 200)}`
          }),
          { status: upstream.status }
        );
      }

      // ── Streaming: pipe SSE as-is ──────────────────────
      if (doStream) {
        return new Response(upstream.body, {
          headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  // nginx: don't buffer
          },
        });
      }

      // ── Non-streaming: forward JSON ────────────────────
      const data = await upstream.json();
      return new Response(JSON.stringify(data), {
        headers: { "Content-Type": "application/json" },
      });
    }

    // ... your other routes ...

    return new Response("Not found", { status: 404 });
  },
});

console.log(`Server running on :${PORT}`);
```

```
┌──────────────────────────────────────────────────────────────┐
│              WHY A SERVER PROXY?                             │
│                                                              │
│  Browser ──► Your Server ──► W&B API                        │
│                                                              │
│  • API keys stay server-side (NEVER in browser JS)          │
│  • Rate limiting per IP                                      │
│  • max_tokens capped server-side (prevent abuse)             │
│  • Can swap models without changing frontend                 │
│  • SSE pass-through is zero-copy (pipe upstream.body)        │
│  • Add logging, monitoring, usage tracking                   │
└──────────────────────────────────────────────────────────────┘
```

---

## 13. W&B Inference API Reference

Weights & Biases (W&B) hosts open-source models behind an OpenAI-compatible
API. You get access to Kimi-K2.5, Qwen, Llama, and others.

### Getting a W&B API Key

```
1. Go to https://wandb.ai/settings
2. Scroll to "API Keys"
3. Click "New Key" or copy existing
4. Set as env var: export WANDB_API_KEY="wandb_v1_..."
```

### API Endpoint

```
┌──────────────────────────────────────────────────────────────┐
│  URL:     https://api.inference.wandb.ai/v1/chat/completions│
│  Method:  POST                                               │
│  Auth:    Bearer token (W&B API key)                        │
│  Format:  OpenAI-compatible (same as GPT-4 API)             │
└──────────────────────────────────────────────────────────────┘
```

### Headers

```
Content-Type:   application/json
Authorization:  Bearer wandb_v1_...
OpenAI-Project: your-org/your-project    ← routes to model group
```

### Available Models (as of 2025)

```
┌───────────────────────────────┬──────────────────────────────┐
│  Model ID                     │  Notes                       │
├───────────────────────────────┼──────────────────────────────┤
│  moonshotai/Kimi-K2.5         │  Thinking + tool calling     │
│  Qwen/Qwen3-235B-A22B        │  Large MoE                   │
│  Qwen/Qwen2.5-Coder-32B      │  Code-focused                │
│  meta-llama/Llama-3.3-70B     │  General purpose             │
│  deepseek-ai/DeepSeek-R1      │  Reasoning model             │
│  mistralai/Mistral-Large-2    │  General purpose             │
│  google/gemma-2-27b           │  Compact                     │
└───────────────────────────────┴──────────────────────────────┘

Check latest at: https://wandb.ai/site/inference
```

### Request Body

```typescript
{
  model: "moonshotai/Kimi-K2.5",
  messages: [
    { role: "system", content: "..." },
    { role: "user",   content: "..." },
  ],

  // Tool calling (optional)
  tools: TOOL_DEFS,           // array of tool definitions
  tool_choice: "auto",        // "auto" | "none" | "required"

  // Streaming
  stream: true,               // SSE mode

  // Generation parameters
  max_tokens: 16384,           // 1 – 30000+
  temperature: 0.55,           // 0.0 (deterministic) – 2.0 (creative)
  top_p: 0.9,                 // nucleus sampling
  top_k: 40,                  // top-k sampling
  repetition_penalty: 1.05,   // 1.0 = none, >1.0 = penalize repeats
}
```

### Kimi-K2.5 Special: `reasoning_content`

Kimi-K2.5 (and DeepSeek-R1) have a "thinking" phase. The model's internal
reasoning arrives as `delta.reasoning_content` before the actual response:

```
┌──────────────────────────────────────────────────────────────┐
│  KIMI-K2.5 RESPONSE PHASES                                  │
│                                                              │
│  Phase 1: reasoning_content                                  │
│  ├── "The user wants to increase the temperature..."         │
│  ├── "Current thermostat is at 68°F..."                      │
│  └── "I should call get_app_state first, then set_therm..." │
│                                                              │
│  Phase 2: tool_calls OR content                              │
│  ├── tool_calls: [{name: "get_app_state", args: "{}"}]      │
│  └── (after follow-up) content: "I've set it to 74°F!"      │
│                                                              │
│  Show reasoning as a collapsible "thinking" bubble.          │
│  Clear it once real content starts streaming.                │
└──────────────────────────────────────────────────────────────┘
```

### Recommended Parameters by Use Case

```
┌─────────────────────┬──────┬──────┬──────┬───────┬──────────┐
│  Use Case           │ Temp │ TopP │ TopK │ RepP  │ MaxTok   │
├─────────────────────┼──────┼──────┼──────┼───────┼──────────┤
│  Tool-heavy agent   │ 0.3  │ 0.9  │ 40   │ 1.05  │ 16384    │
│  Creative writing   │ 0.9  │ 0.95 │ 80   │ 1.1   │ 8192     │
│  Code generation    │ 0.2  │ 0.85 │ 30   │ 1.0   │ 16384    │
│  Chat assistant     │ 0.55 │ 0.9  │ 40   │ 1.05  │ 16384    │
│  Deterministic Q&A  │ 0.0  │ 1.0  │ 1    │ 1.0   │ 4096     │
└─────────────────────┴──────┴──────┴──────┴───────┴──────────┘
```

---

## 14. UI Integration

### Reading Store in Components (Preact/React)

```typescript
import { useStore } from '@tanstack/preact-store'
// React: import { useStore } from '@tanstack/react-store'

function ChatPanel() {
  // Auto-subscribes — component re-renders when these change
  const messages   = useStore(chatStore, s => s.messages);
  const loading    = useStore(chatStore, s => s.loading);
  const streaming  = useStore(chatStore, s => s.streamingText);
  const toolPhase  = useStore(chatStore, s => s.toolPhase);
  const reasoning  = useStore(chatStore, s => s.reasoningText);
  const inputText  = useStore(chatStore, s => s.inputText);

  return html`
    <div class="chat-panel">
      ${/* Message list */}
      ${messages.map(m => html`
        <div class="msg msg-${m.role}" key=${m.id}>
          ${m.role === "tool"
            ? html`<span class="tool-badge">🔧 ${m.toolName}</span>`
            : m.content
          }
        </div>
      `)}

      ${/* Thinking bubble */}
      ${reasoning && html`
        <div class="thinking">💭 ${reasoning}</div>
      `}

      ${/* Tool execution indicator */}
      ${toolPhase && html`
        <div class="tool-phase">⚙️ ${toolPhase}</div>
      `}

      ${/* Input */}
      <input
        value=${inputText}
        onInput=${(e) => chatStore.setState(s => ({
          ...s, inputText: e.target.value
        }))}
        onKeyDown=${(e) => {
          if (e.key === "Enter" && !loading) {
            sendMessage(inputText);
            chatStore.setState(s => ({ ...s, inputText: "" }));
          }
        }}
        disabled=${loading}
        placeholder=${loading ? "Thinking..." : "Type a message..."}
      />
    </div>
  `;
}
```

### Settings Panel

```typescript
function SettingsPanel() {
  const cfg = useStore(settingsStore, s => s);

  return html`
    <div class="settings">
      <label>Model</label>
      <select
        value=${cfg.llmModel}
        onChange=${(e) => settingsStore.setState(s => ({
          ...s, llmModel: e.target.value
        }))}
      >
        <option value="moonshotai/Kimi-K2.5">Kimi K2.5</option>
        <option value="Qwen/Qwen3-235B-A22B">Qwen3 235B</option>
        <option value="meta-llama/Llama-3.3-70B">Llama 3.3</option>
      </select>

      <label>Temperature: ${cfg.temperature}</label>
      <input type="range" min="0" max="2" step="0.05"
        value=${cfg.temperature}
        onInput=${(e) => settingsStore.setState(s => ({
          ...s, temperature: parseFloat(e.target.value)
        }))}
      />

      <label>Max Tokens</label>
      <input type="number" min="1000" max="30000"
        value=${cfg.maxTokens}
        onChange=${(e) => settingsStore.setState(s => ({
          ...s, maxTokens: parseInt(e.target.value)
        }))}
      />

      <label>Enabled Tools</label>
      ${TOOL_DEFS.map(t => html`
        <label key=${t.function.name}>
          <input type="checkbox"
            checked=${!cfg.disabledTools.includes(t.function.name)}
            onChange=${() => {
              const disabled = cfg.disabledTools.includes(t.function.name)
                ? cfg.disabledTools.filter(n => n !== t.function.name)
                : [...cfg.disabledTools, t.function.name];
              settingsStore.setState(s => ({
                ...s, disabledTools: disabled
              }));
            }}
          />
          ${t.function.name}
        </label>
      `)}
    </div>
  `;
}
```

---

## 15. Adapting for Different Apps

The pattern is identical. Only change `TOOL_DEFS`, `executeTool()`, and
the system prompt.

### IDE / Code Assistant

```typescript
const TOOLS = [
  tool("read_file",    "Read a project file",
       { path: "string" }),
  tool("edit_file",    "Replace text in a file",
       { path: "string", old_str: "string", new_str: "string" }),
  tool("run_command",  "Run a shell command",
       { cmd: "string" }),
  tool("search_code",  "Grep for a pattern",
       { pattern: "string", path: "string" }),
];
```

### E-Commerce Bot

```typescript
const TOOLS = [
  tool("search_products", "Search catalog",
       { query: "string", category: "string?", max_price: "number?" }),
  tool("add_to_cart",     "Add item to cart",
       { product_id: "string", quantity: "number" }),
  tool("get_cart",        "View current cart contents", {}),
  tool("apply_coupon",    "Apply discount code",
       { code: "string" }),
];
```

### Game NPC

```typescript
const TOOLS = [
  tool("move_to",      "Move NPC to world coordinates",
       { x: "number", y: "number", z: "number" }),
  tool("attack",       "Attack target with ability",
       { target_id: "string", ability: "string" }),
  tool("say_dialog",   "Speak with emotion",
       { text: "string", emotion: "string" }),
  tool("check_inventory", "Check player's items", {}),
];
```

### Dashboard / Analytics

```typescript
const TOOLS = [
  tool("run_query",     "Execute SQL against analytics DB",
       { sql: "string" }),
  tool("create_chart",  "Generate a chart",
       { type: "string", data_key: "string", title: "string" }),
  tool("send_alert",    "Send a Slack alert",
       { channel: "string", message: "string" }),
  tool("get_metrics",   "Get current system metrics", {}),
];
```

---

## 16. Gotchas & Debugging

### Common Mistakes

```
┌──────────────────────────────────────────────────────────────┐
│                    COMMON MISTAKES                            │
│                                                              │
│  ❌ Parsing arguments before stream ends                     │
│     → Arguments arrive in fragments! Wait for [DONE].        │
│                                                              │
│  ❌ Missing tool_call_id on tool result messages              │
│     → API returns 400. MUST match the id from tool_calls.    │
│                                                              │
│  ❌ Forgetting the assistant message with tool_calls          │
│     → Conversation must show: assistant(tools) → tool result │
│     → If you skip the assistant msg, the API rejects it.     │
│                                                              │
│  ❌ Sending tool results as role:"user"                       │
│     → Must be role:"tool" with tool_call_id and name.        │
│                                                              │
│  ❌ Not handling the recursive loop                           │
│     → LLM may call more tools after seeing results!          │
│     → Always check toolCalls.length after each stream.       │
│                                                              │
│  ❌ Huge tool results (>10KB)                                │
│     → Wastes context window. Summarize or truncate.          │
│                                                              │
│  ❌ No try/catch in executeTool                               │
│     → If a tool throws, the whole loop breaks.               │
│     → Always return { ok: false, reason: "..." }.            │
│                                                              │
│  ❌ Not clearing reasoning when content starts                │
│     → Kimi sends reasoning_content THEN content.             │
│     → Clear the thinking indicator when text arrives.        │
│                                                              │
│  ❌ TanStack Store subscribe() gotcha                         │
│     → .subscribe() returns { unsubscribe }, NOT a function!  │
│     → ✅ const { unsubscribe } = store.subscribe(cb)         │
│     → ❌ const unsub = store.subscribe(cb); unsub()          │
│                                                              │
│  ❌ Exposing API keys in browser JS                           │
│     → Always proxy through your server.                      │
│     → Never put WANDB_API_KEY in frontend code.              │
└──────────────────────────────────────────────────────────────┘
```

### Debugging SSE Streams

```typescript
// Log raw SSE data to console:
for (const line of lines) {
  if (!line.startsWith("data: ")) continue;
  console.log("[SSE]", line.slice(6, 200));
  // ...
}
```

### Testing Tool Calls Without an LLM

```typescript
// Create a mock SSE stream:
const mockSSE = [
  'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"test_1","function":{"name":"get_weather","arguments":""}}]}}]}',
  'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\\"city\\":\\"Tokyo\\"}"}}]}}]}',
  'data: [DONE]',
].join("\n") + "\n";

const blob = new Blob([mockSSE]);
const resp = new Response(blob, {
  headers: { "Content-Type": "text/event-stream" }
});
await streamResponse(resp);
// → executeTool("get_weather", {city:"Tokyo"}) gets called
```

### Verifying Message Order

```typescript
// Before sending, log the conversation:
const msgs = serializeMsgs(chatStore.state.messages);
console.table(msgs.map(m => ({
  role: m.role,
  has_tools: !!m.tool_calls?.length,
  tool_call_id: m.tool_call_id || "-",
  content: (m.content || "").slice(0, 50),
})));
```

---

## 17. Quick Reference Card

```
┌──────────────────────────────────────────────────────────────┐
│            TOOL CALLING CHEAT SHEET                          │
│                                                              │
│  ── TANSTACK STORE ──────────────────────────────────────    │
│  new Store<T>({ ... })           create store                │
│  store.setState(s => ({...}))    update                      │
│  useStore(store, s => s.field)   read in component           │
│  store.state.field               read outside component      │
│  batch(() => { ... })            batch updates               │
│                                                              │
│  ── REQUEST ─────────────────────────────────────────────    │
│  POST /api/chat                                              │
│  { messages, tools, tool_choice:"auto", stream:true }        │
│                                                              │
│  ── SSE PARSING ─────────────────────────────────────────    │
│  delta.reasoning_content  →  thinking (Kimi/DeepSeek)        │
│  delta.tool_calls[i]      →  accumulate by index             │
│  delta.content             →  text response                  │
│                                                              │
│  ── AFTER STREAM ────────────────────────────────────────    │
│  if toolCalls.length > 0:                                    │
│    1. Attach tool_calls to assistant message                 │
│    2. Execute each tool → get result                         │
│    3. Add role:"tool" msgs (with tool_call_id!)              │
│    4. sendFollowUp() → recursive streamResponse()            │
│  else:                                                       │
│    Done. Set loading = false.                                │
│                                                              │
│  ── MESSAGE ORDER ───────────────────────────────────────    │
│  system → user → assistant(tool_calls) → tool → tool →       │
│  assistant(text) → user → ...                                │
│                                                              │
│  ── W&B INFERENCE ───────────────────────────────────────    │
│  URL:    api.inference.wandb.ai/v1/chat/completions          │
│  Auth:   Bearer wandb_v1_...                                 │
│  Header: OpenAI-Project: org/project                         │
│  Model:  moonshotai/Kimi-K2.5 (default)                     │
│                                                              │
│  ── KEY RULES ───────────────────────────────────────────    │
│  • Never parse arguments mid-stream                          │
│  • tool_call_id MUST match tool_calls[].id                   │
│  • tool content MUST be JSON.stringify'd                      │
│  • Always try/catch in executeTool                           │
│  • API keys → server only, never browser                     │
│  • subscribe() returns { unsubscribe }, not a function       │
└──────────────────────────────────────────────────────────────┘
```

---

## File Listing

For a working implementation, you need:

```
your-app/
├── serve.ts          # Bun server with /api/chat proxy
├── app.ts            # Frontend with TanStack Store + stream parser
├── package.json      # @tanstack/store, @tanstack/preact-store
└── .env              # WANDB_API_KEY=wandb_v1_...
```

```bash
# Install
bun add @tanstack/store @tanstack/preact-store

# Run
WANDB_API_KEY=wandb_v1_... bun serve.ts
```

---

*Works with any OpenAI-compatible API: W&B Inference, OpenAI, Anthropic,
Together, Fireworks, Groq, Ollama, vLLM, etc. Just change the URL and auth.*
