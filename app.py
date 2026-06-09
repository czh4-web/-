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

# ================= 优化后：每日运势接口 =================
@app.route('/api/daily', methods=['GET'])
def generate_daily_fortune():
    today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
    
    # 【新增功能】：建立心理学流派/理论的随机种子库
    PSYCH_DOMAINS = [
        "认知行为疗法（CBT）与情绪调节",
        "社会认知职业理论（SCCT）与生涯规划",
        "阿德勒目的论与个体心理学",
        "积极心理学与心流体验",
        "学习心理学与学业动机",
        "人本主义与自我实现",
        "精神分析与潜意识防御机制",
        "正念与接纳承诺疗法（ACT）"
    ]
    # 每次请求随机选择一个理论框架作为锚点
    current_domain = random.choice(PSYCH_DOMAINS)
    
    system_prompt = f"""
    你是一个深谙心理学的赛博电子容器。
    请生成一份今天的“赛博电子运势”。要求完全使用 JSON 格式输出，包含以下键：
    "fortune_level": 运势等级，从 [大吉, 中吉, 小吉, 平] 中选一个（不要写凶，保护用户心理）。
    "suitable": 宜做的事，用四个字的高级心理学术语。
    "suitable_desc": 用一句12字以内的大白话解释宜做的事（例如：分清你我，放下助人情结）。
    "unsuitable": 忌做的事，用四个字的高级心理学术语。
    "unsuitable_desc": 用一句12字以内的大白话解释忌做的事（例如：别在脑海里提前演灾难片）。
    "daily_quote": 一句有洞察力的心理学金句（40字左右）。

    【核心约束规则】：
    1. 理论限定：你必须严格基于【{current_domain}】的理论框架来提取术语和撰写金句。
    2. 禁止重复：去寻找该理论框架下更专业、更具学术美感的词汇。
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"今天是{today_str}，请基于指定的心理学框架，生成今天的运势。"}
            ],
            response_format={"type": "json_object"},
            temperature=0.9  # 【关键修改】：将温度调高到0.9，进一步激发大模型的创造力和词汇多样性
        )
        result = json.loads(response.choices[0].message.content)
        result['date'] = today_str
        
        # 可以在控制台打印出当前抽中的理论，方便你在后台监控
        print(f"今日运势生成框架: {current_domain}") 
        
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
    请严格以 JSON 格式输出，必须包含以下六个键："cbt_explanation", "socratic_question", "action_card", "book_title", "book_quote", "book_intro"。
    """
    user_prompt = f"""
    用户的烦恼：{user_anxiety}
    抽中的签文意象：{sign_title}
    
    【输出要求】
    1. "cbt_explanation": 用 CBT 理论给出现代解释。客观、有洞察力，约80字。
    2. "socratic_question": 提出一个直击本质的反思问题，引导区分“可控与不可控”。
    3. "action_card": 给出一个立刻可以执行的微小动作（Small Wins），20字以内。
    4. "book_title": 推荐一本能解决该用户具体焦虑的心理学/哲学经典书籍（如《被讨厌的勇气》《非暴力沟通》《活出意义来》等，不要带书名号）。
    5. "book_quote": 提取书中与用户当下困境最契合的一句经典原话。
    6. "book_intro": 简述这本书的核心理念，以及为什么它能解开用户当下的心结（约60字）。
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
