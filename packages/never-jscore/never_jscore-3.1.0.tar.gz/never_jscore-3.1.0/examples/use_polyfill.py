import threading
import time
from fastapi import FastAPI, HTTPException
import never_jscore


with open('231_rand_fun copy.js',encoding='utf-8')as f:
    JS_CODE = f.read()
engine = never_jscore.JSEngine(JS_CODE, workers=1)

t = time.time()
import json
# 创建 Flask 应用
app = FastAPI()

# 每个线程一个 Context (使用 ThreadLocal)
thread_local = threading.local()


def get_context():
    """获取当前线程的 Context (懒加载)"""
    if not hasattr(thread_local, 'ctx'):
        thread_local.ctx = never_jscore.Context()
        thread_local.ctx.compile(JS_CODE)
    return thread_local.ctx

@app.post("/get_rand_value")
def get_rand_value():
    token = '300965934cef49ac98e627aeb66c5a6e'
    bn_id = 'scratch-captcha-btn'
    start = time.time()
    print(engine.call('get_style_value', [token, bn_id]))
    print(time.time()-start)


@app.post("/get_rand_value2")
def get_rand_value():
    token = '300965934cef49ac98e627aeb66c5a6e'
    bn_id = 'scratch-captcha-btn'
    ctx = get_context()
    start = time.time()
    print(ctx.call('get_style_value', [token, bn_id]))
    print(time.time()-start)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app='use_polyfill:app', host='0.0.0.0', port=8000, workers=4)



