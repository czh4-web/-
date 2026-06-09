import os
import random
import json
import datetime
from flask import Flask, request, jsonify, render_template
from openai import OpenAI

# 强制忽略系统代理，防止连接失败
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""

app = Flask(__name__)

# 配置你的 DeepSeek API Key
api_key = os.environ.get("DEEPSEEK_API_KEY", "sk-8b91d75e146e4b6e84881583f87d33c0")

# 初始化客户端
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com" 
)

# 签文意象池
SIGN_TITLES = ['【见山】', '【破浪】', '【驻足】', '【拨云】', '【空谷】', '【听雨】', '【微光】']

@app.route('/')
def index():
    return render_template('index.html')

# ================= 新增：每日运势接口 =================
@app.route('/api/daily', methods=['GET'])
def generate_daily_fortune():
    # 获取当天的日期作为时间锚点
    today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
    
    system_prompt = """
    你是一个深谙现代认知行为疗法（CBT）的赛博心理容器。
    请生成一份今天的“赛博电子运势”。要求完全使用 JSON 格式输出，包含以下键：
    "fortune_level": 运势等级，从 [大吉, 中吉, 小吉, 平] 中选一个（不要写凶，保护用户心理）。
    "suitable": 宜做的事，用四个字的心理学术语，如"课题分离", "正念冥想", "接纳不完美", "允许停顿"。
    "unsuitable": 忌做的事，用四个字的心理学术语，如"灾难化预期", "精神内耗", "反刍思维", "过度控制"。
    "daily_quote": 一句结合今天运势的、有洞察力的心理学金句（40字左右）。
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"今天是{today_str}，请生成今天的运势。"}
            ],
            response_format={"type": "json_object"},
            temperature=0.8
        )
        result = json.loads(response.choices[0].message.content)
        result['date'] = today_str
        return jsonify(result)
    except Exception as e:
        print(f"Daily API Error: {e}")
        return jsonify({"error": "运势拉取失败"}), 500

# ================= 优化：电子求签接口 =================
@app.route('/api/generate', methods=['POST'])
def generate_counseling():
    data = request.json
    user_anxiety = data.get('anxiety', '')
    
    if not user_anxiety:
        return jsonify({"error": "未接收到用户的困惑"}), 400

    sign_title = random.choice(SIGN_TITLES)

    system_prompt = """
    你现在是一个深谙传统文化与现代认知行为疗法（CBT）的“赛博心理容器”。
    请严格以 JSON 格式输出，包含以下三个键："cbt_explanation", "socratic_question", "action_card"。
    """
    user_prompt = f"""
    用户的烦恼：{user_anxiety}
    抽中的签文意象：{sign_title}
    
    【输出要求】
    1. "cbt_explanation": 用 CBT 理论给出现代解释。客观、有洞察力，约80字。
    2. "socratic_question": 提出一个直击本质的反思问题，引导区分“可控与不可控”。
    3. "action_card": 给出一个立刻可以执行的微小动作（Small Wins），20字以内。
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        result_dict = json.loads(response.choices[0].message.content)
        result_dict['sign_title'] = sign_title
        return jsonify(result_dict)

    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"error": "AI 服务连接异常"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
