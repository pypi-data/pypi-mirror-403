from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Self
from openai import AsyncOpenAI
from pydantic import BaseModel, field_validator, Field
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall
from mcp import ClientSession, Tool as _Tool
import json


class DialogueMessager(BaseModel):
    role: Literal['assistant', 'user']
    content: str|list[dict] = ''
    
    @field_validator('content', mode='before')
    def _strip(cls, value, data):
        if isinstance(value, str):
            value = value.strip()
        elif hasattr(value, 'text'):
            setattr(value, 'text', getattr(value, 'text').strip())
        return value

class Messager(DialogueMessager):
    role: Literal['developer', 'system', 'assistant', 'user', 'tool']
    chunk: str|None = None
    name: str|None = None
    args: dict|list|None = None
    tool_call_id: str|None = None
    tool_calls: list[ChoiceDeltaToolCall]|None = None
    is_finish:bool = True
    time:str = Field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    file_map:dict[Literal['image', 'video', 'audio', 'file'], list[dict|str]]|None = None
    
    @property
    def is_tool(self)->bool:
        return self.role == 'tool'
    
    @property
    def is_assistant(self):
        return self.role == 'assistant'
    
    @property
    def is_user(self):
        return self.role == 'user'
    
    @property
    def is_dialogue(self):
        return bool(self.content and self.role in ('assistant','user'))
    
    @property
    def debug_log(self)->str:
        if self.role == 'assistant' and not self.content:
            log = '; '.join(f'{tool.function.name} {tool.function.arguments}'for tool in self.tool_calls)
        else:
            log = self.content.split('\n')
            if len(log)>1 or len(log[0])>100:
                log = log[0][:100]+'...'
            else:
                log = log[0]
        return f"{self.role}: {log}"
    
    @property
    def tool_call_arguments(self)->list[dict]:
        return [json.loads(tool_call.function.arguments) for tool_call in (self.tool_calls or ())]
    
    def to_messager(self)->dict:
        dt = self.model_dump(exclude_none=True, exclude={'content', 'chunk', 'is_finish', 'time', 'file_map'})
        if self.file_map:
            dt['content'] = [*self.file_map.get('image', ()), *self.file_map.get('video', ()), *self.file_map.get('audio', ())]
            content = self.content
            if self.file_map.get('file'):
                filetemplate = '\n- '.join(['## 上传其他文件列表', *[f'[{f['name']}]({f['url']})' for f in self.file_map['file']]])
                content = f'{filetemplate}\n\n{content}'
            dt['content'].append({'type': 'text', 'text': content })
        else:
            dt['content'] = self.content
        return dt
    
    def addFile(self, *, imgs:list[str|dict]=(), videos:list[str|dict]=(), audios:list[dict]=(), other_files:list[dict]=())->Self:
        self.file_map = self.file_map or {}
        if imgs:
            self.file_map['image'] = self.file_map.get('image', [])
            self.file_map['image'].extend([{'type': 'image_url', 'image_url': { 'url': img } if isinstance(img, str) else img} for img in imgs])
        if videos:
            self.file_map['video'] = self.file_map.get('video', [])
            self.file_map['video'].extend([{'type': 'video_url', 'video_url': { 'url': video } if isinstance(video, str) else video} for video in videos])
        if audios:
            self.file_map['audio'] = self.file_map.get('audio', [])
            self.file_map['audio'].extend([{'type': 'input_audio', 'input_audio': audio} for audio in audios])
        if other_files:
            self.file_map['file'] = self.file_map.get('file', [])
            self.file_map['file'].extend([{'name': file['name'], 'url': file['url']} for file in other_files])
        return self
    
class ToolCeil(BaseModel):
    name: str
    description: str
    parameters: dict
    strict: bool|None = None
    
    def to_tool(self)->dict:
        return {
                "type": "function",
                "function": {
                    "name":  self.name,
                    "description": self.description,
                    "parameters": self.parameters,
                    'strict': self.strict
                    }
                }
    
    @staticmethod
    def from_mcp_tool(tool:_Tool, strict:bool=None)->'ToolCeil':
        return ToolCeil(name=tool.name, description=tool.description, parameters=tool.inputSchema, strict=strict)
    
    @staticmethod
    def from_base(name:str, base:BaseModel, description:str=None, strict:bool=None)->'ToolCeil':
        bjson = base.model_json_schema()
        description0 = bjson.pop('description', None)
        description = description or description0
        if not description: raise ValueError('description is None')
        return ToolCeil(name=name, description=description.strip(), parameters=bjson, strict=strict)

@dataclass
class Tooler:
    name:str
    server: 'Server'
    tc:ToolCeil

@dataclass
class Server:
    name:str
    cs:ClientSession
    tools:list[Tooler]

def _get_chat_history_text(messagers:list[DialogueMessager])->str:
    return '\n'.join(f'{messager.role}: {messager.content}' for messager in messagers if messager.content)

async def _get_result(aclient:AsyncOpenAI, model:str, prompt:str)->dict:
    response = await aclient.chat.completions.create(model=model, 
                                                     messages=[{'role': 'user', 'content': prompt}],
                                                     stream=False)
    import json_repair
    return json_repair.loads(response.choices[0].message.content)

_trace_tp = '''### Task:
Suggest {trace_num} relevant follow-up questions or prompts that the user might naturally ask next in this conversation as a **user**, based on the chat history, to help continue or deepen the discussion.
### Guidelines:
- Write all follow-up questions from the user’s point of view, directed to the assistant.
- Make questions concise, clear, and directly related to the discussed topic(s).
- Only suggest follow-ups that make sense given the chat content and do not repeat what was already covered.
- If the conversation is very short or not specific, suggest more general (but relevant) follow-ups the user might ask.
- Use the conversation's primary language; default to English if multilingual.
- Response must be a JSON array of strings, no extra text or formatting.
### Output:
JSON format: {{ "follow_ups": ["Question 1?", "Question 2?", "Question 3?"] }}
### Chat History:
<chat_history>
{chat_history}
</chat_history>'''

async def aget_trace(aclient:AsyncOpenAI, model:str, messagers:list[DialogueMessager], trace_num:int=3)->list[str]:
    """获取根据历史对话生成追问"""
    result = await _get_result(aclient, model, _trace_tp.format(trace_num=trace_num, chat_history=_get_chat_history_text(messagers)))
    return result.get('follow_ups', [])

_title_tp ='''### Task:
Generate a concise, 3-5 word title with an emoji summarizing the chat history.
### Guidelines:
- The title should clearly represent the main theme or subject of the conversation.
- Use emojis that enhance understanding of the topic, but avoid quotation marks or special formatting.
- Write the title in the chat's primary language; default to English if multilingual.
- Prioritize accuracy over excessive creativity; keep it clear and simple.
- Your entire response must consist solely of the JSON object, without any introductory or concluding text.
- The output must be a single, raw JSON object, without any markdown code fences or other encapsulating text.
- Ensure no conversational text, affirmations, or explanations precede or follow the raw JSON output, as this will cause direct parsing failure.
### Output:
JSON format: {{ "title": "your concise title here" }}
### Examples:
- { "title": "📉 Stock Market Trends" },
- { "title": "🍪 Perfect Chocolate Chip Recipe" },
- { "title": "Evolution of Music Streaming" },
- { "title": "Remote Work Productivity Tips" },
- { "title": "Artificial Intelligence in Healthcare" },
- { "title": "🎮 Video Game Development Insights" }
### Chat History:
<chat_history>
{chat_history}
</chat_history>'''

async def aget_title(aclient:AsyncOpenAI, model:str, messagers:list[DialogueMessager])->str:
    """获取根据历史对话生成总结性的标题"""
    result = await _get_result(aclient, model, _title_tp.format(chat_history=_get_chat_history_text(messagers)))
    return result.get('title', '')
