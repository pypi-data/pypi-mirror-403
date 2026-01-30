"""Natural language agent using OpenAI API."""

import json
from typing import Any

from openai import OpenAI

from .api import CircleMsClient
from .image import fetch_image_as_braille

# Callback for direct output (set by main.py)
_direct_output_callback = None


def set_direct_output_callback(callback):
    """Set callback for direct CLI output (bypassing LLM)."""
    global _direct_output_callback
    _direct_output_callback = callback


SYSTEM_PROMPT = """あなたはコミケWebカタログの検索アシスタントです。
ユーザーの自然言語での質問に対して、適切なAPI呼び出しを行い、結果をわかりやすく説明します。

利用可能な機能:
- サークル検索（名前、ジャンル、館で検索）
- 頒布物検索（作品名で検索）
- サークル詳細情報の取得
- サークルカット画像の表示
- ホールマップ表示（サークルの位置を★で表示）
- ジャンル一覧の取得
- お気に入りサークルの一覧・追加・削除
- イベント一覧の取得
- ユーザー情報の取得

回答は日本語で、簡潔にお願いします。

出力は全て左寄せで表示してください。

重要: show_circle_cut/show_circle_mapの結果が{"status": "displayed"}の場合、
画像/マップは既にCLIに直接表示されています。
再度テキストで表現しようとしないでください。「表示しました」と簡潔に伝えるだけで十分です。
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_circles",
            "description": "サークルを検索します（配置情報付き）",
            "parameters": {
                "type": "object",
                "properties": {
                    "circle_name": {
                        "type": "string",
                        "description": "サークル名（部分一致）",
                    },
                    "block": {
                        "type": "string",
                        "description": "ブロック名（あ/ア/A等）",
                    },
                    "day": {
                        "type": "integer",
                        "description": "参加日（1=1日目, 2=2日目）",
                    },
                    "genre": {
                        "type": "string",
                        "description": "ジャンル名（部分一致、例: ガンダム, 東方）",
                    },
                    "space_from": {
                        "type": "integer",
                        "description": "スペース番号の開始（例: 40で40番以降）",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "結果のオフセット（ページング用）",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_placement",
            "description": "サークルの配置場所（日程、ブロック、スペース番号）を取得します",
            "parameters": {
                "type": "object",
                "properties": {
                    "wcid": {
                        "type": "integer",
                        "description": "サークルID（wcid）",
                    },
                },
                "required": ["wcid"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "init_database",
            "description": "最新イベントのデータベースをダウンロードして初期化します",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_books",
            "description": "頒布物（同人誌など）を検索します",
            "parameters": {
                "type": "object",
                "properties": {
                    "work_name": {
                        "type": "string",
                        "description": "頒布物名（部分一致）",
                    },
                    "circle_name": {
                        "type": "string",
                        "description": "サークル名（部分一致）",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_circle",
            "description": "サークルの詳細情報を取得します",
            "parameters": {
                "type": "object",
                "properties": {
                    "wcid": {
                        "type": "integer",
                        "description": "サークルID（wcid）",
                    },
                },
                "required": ["wcid"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_favorites",
            "description": "お気に入りサークル一覧を取得します",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_favorite",
            "description": "サークルをお気に入りに追加します",
            "parameters": {
                "type": "object",
                "properties": {
                    "wcid": {
                        "type": "integer",
                        "description": "サークルID（wcid）",
                    },
                    "color": {
                        "type": "integer",
                        "description": "カラー番号（1-9）",
                        "default": 1,
                    },
                    "memo": {
                        "type": "string",
                        "description": "メモ",
                        "default": "",
                    },
                },
                "required": ["wcid"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_favorite",
            "description": "お気に入りサークルの情報（カラー、メモ）を更新します",
            "parameters": {
                "type": "object",
                "properties": {
                    "wcid": {
                        "type": "integer",
                        "description": "サークルID（wcid）",
                    },
                    "color": {
                        "type": "integer",
                        "description": "カラー番号（1-9）",
                    },
                    "memo": {
                        "type": "string",
                        "description": "メモ",
                    },
                },
                "required": ["wcid", "color", "memo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_favorite",
            "description": "サークルをお気に入りから削除します",
            "parameters": {
                "type": "object",
                "properties": {
                    "wcid": {
                        "type": "integer",
                        "description": "サークルID（wcid）",
                    },
                },
                "required": ["wcid"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_favorite_works",
            "description": "お気に入りサークルの頒布物一覧を取得します",
            "parameters": {
                "type": "object",
                "properties": {
                    "work_name": {
                        "type": "string",
                        "description": "頒布物名（部分一致）",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_circles",
            "description": "ユーザーが所属するサークル一覧を取得します",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_events",
            "description": "イベント一覧を取得します",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "ログイン中のユーザー情報を取得します",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "show_circle_cut",
            "description": "サークルカット画像をBraille Unicode（点字）アートで表示します",
            "parameters": {
                "type": "object",
                "properties": {
                    "wcid": {
                        "type": "integer",
                        "description": "サークルID（wcid）",
                    },
                },
                "required": ["wcid"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "show_circle_map",
            "description": "サークルの位置をホールマップ上に★で表示します",
            "parameters": {
                "type": "object",
                "properties": {
                    "wcid": {
                        "type": "integer",
                        "description": "サークルID（wcid）",
                    },
                },
                "required": ["wcid"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_genres",
            "description": "ジャンル一覧を取得します",
            "parameters": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "integer",
                        "description": "参加日で絞り込み（1=1日目, 2=2日目）",
                    },
                },
            },
        },
    },
]


class Agent:
    """Natural language agent for Comiket WebCatalog."""

    def __init__(self, openai_api_key: str, api_client: CircleMsClient):
        self.client = OpenAI(api_key=openai_api_key)
        self.api = api_client
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _execute_function(self, name: str, args: dict) -> Any:
        """Execute a function call."""
        if name == "search_circles":
            return self.api.search_circles_local(
                name=args.get("circle_name"),
                block=args.get("block"),
                day=args.get("day"),
                genre=args.get("genre"),
                space_from=args.get("space_from"),
                offset=args.get("offset", 0),
            )
        elif name == "get_placement":
            return self.api.get_placement(args["wcid"])
        elif name == "init_database":
            event_id = self.api.ensure_database()
            return {"status": "success", "event_id": event_id}
        elif name == "search_books":
            return self.api.search_books(**args)
        elif name == "get_circle":
            return self.api.get_circle(**args)
        elif name == "get_favorites":
            return self.api.get_favorite_circles()
        elif name == "add_favorite":
            return self.api.add_favorite(**args)
        elif name == "update_favorite":
            return self.api.update_favorite(**args)
        elif name == "remove_favorite":
            return self.api.remove_favorite(**args)
        elif name == "get_favorite_works":
            return self.api.get_favorite_works(**args)
        elif name == "get_user_circles":
            return self.api.get_user_circles()
        elif name == "get_events":
            return self.api.get_event_list()
        elif name == "get_user_info":
            return self.api.get_user_info()
        elif name == "show_circle_cut":
            wcid = args.get("wcid")
            if not wcid:
                return {"error": "wcidが指定されていません"}
            # Get circle info to find image URL
            circle_info = self.api.get_circle(wcid)
            if circle_info.get("status") != "success":
                return {"error": f"APIエラー: {circle_info.get('status')}", "detail": circle_info}
            circle = circle_info.get("response", {}).get("circle", {})
            if not circle:
                return {"error": "サークル情報が見つかりません", "wcid": wcid}
            # Try all possible image URLs
            cut_url = (
                circle.get("cut_url") or circle.get("cut_web_url") or circle.get("cut_base_url")
            )
            if not cut_url:
                return {
                    "error": "サークルカット画像URLが見つかりません",
                    "circle_name": circle.get("name", ""),
                }
            try:
                braille_art = fetch_image_as_braille(cut_url)
                circle_name = circle.get("name", "")
                # Direct output to CLI, bypassing LLM
                if _direct_output_callback:
                    _direct_output_callback(f"\n【{circle_name}】\n{braille_art}\n")
                return {"status": "displayed", "circle_name": circle_name}
            except Exception as e:
                return {"error": f"画像取得エラー: {str(e)}", "url": cut_url}
        elif name == "show_circle_map":
            wcid = args.get("wcid")
            if not wcid:
                return {"error": "wcidが指定されていません"}
            result = self.api.get_circle_map(wcid)
            if "error" in result:
                return result
            # Direct output to CLI, bypassing LLM
            if _direct_output_callback:
                header = f"\n【{result['circle_name']}】{result['placement']} ({result['hall']})"
                _direct_output_callback(f"{header}\n{result['map_art']}\n")
            return {"status": "displayed", "circle_name": result["circle_name"]}
        elif name == "get_genres":
            return self.api.get_genres(day=args.get("day"))
        else:
            raise ValueError(f"Unknown function: {name}")

    def chat(self, user_input: str) -> str:
        """Process user input and return response."""
        self.messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        # Handle tool calls
        while message.tool_calls:
            self.messages.append(message.model_dump())

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                try:
                    result = self._execute_function(func_name, func_args)
                    tool_result = json.dumps(result, ensure_ascii=False, indent=2)
                except Exception as e:
                    tool_result = json.dumps({"error": str(e)}, ensure_ascii=False)

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            message = response.choices[0].message

        assistant_content = message.content or ""
        self.messages.append({"role": "assistant", "content": assistant_content})

        return assistant_content

    def reset(self) -> None:
        """Reset conversation history."""
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
