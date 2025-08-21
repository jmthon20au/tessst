# api/hello.py
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/hello', methods=['GET', 'POST'])
def hello():
    # مثــال: استقبال اسم بالـ JSON في POST
    if request.method == 'POST':
        payload = request.get_json(silent=True) or {}
        name = payload.get('name', 'مستخدم')
    else:
        name = request.args.get('name', 'مستخدم')

    return jsonify({
        'ok': True,
        'message': f'أهلاً {name}! هذه استجابة من بايثون (Flask) على Vercel.'
    })

# هام: لا تشغل app.run هنا — Vercel يدير الخادم تلقائياً.
