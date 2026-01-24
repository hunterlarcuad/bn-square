"""
2026.01.24
https://docs.bigmodel.cn/cn/api/introduction

使用新的 zai SDK 和同步API调用方式
API端点: https://open.bigmodel.cn/api/paas/v4
Coding端点: https://open.bigmodel.cn/api/coding/paas/v4
"""
import sys
import time
import os

from conf import DEF_LLM_ZHIPUAI
from conf import DEF_MODEL_ZHIPUAI
from conf import DEF_GLM_BASE_URL

from zai import ZhipuAiClient


def get_glm_client():
    """
    获取智谱AI客户端

    参考文档: https://docs.bigmodel.cn/cn/api/introduction

    如果使用 GLM 编码套餐，需要在 conf.py 中设置 DEF_GLM_BASE_URL 为 Coding 端点
    Coding 端点: https://open.bigmodel.cn/api/coding/paas/v4
    通用端点: https://open.bigmodel.cn/api/paas/v4
    """
    # 设置环境变量，以便 SDK 使用指定的端点
    if DEF_GLM_BASE_URL:
        os.environ['ZHIPUAI_BASE_URL'] = DEF_GLM_BASE_URL

    # 初始化客户端
    # 尝试使用 base_url 参数（如果 SDK 支持）
    try:
        client = ZhipuAiClient(
            api_key=DEF_LLM_ZHIPUAI,
            base_url=DEF_GLM_BASE_URL
        )
    except TypeError:
        # 如果 SDK 不支持 base_url 参数，只使用 api_key
        # 端点将通过环境变量 ZHIPUAI_BASE_URL 设置
        client = ZhipuAiClient(api_key=DEF_LLM_ZHIPUAI)

    return client


def gene_by_llm_once_async(s_prompt, model=None):
    """
    异步API调用方式（作为备用方案）

    Return:
        None: Fail to generate msg by llm
        string: generated content by llm
    """
    if model is None:
        model = DEF_MODEL_ZHIPUAI
    client = get_glm_client()

    try:
        response = client.chat.asyncCompletions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": s_prompt
                }
            ],
        )
        task_id = response.id
        task_status = ''
        get_cnt = 0

        while task_status != 'SUCCESS' and task_status != 'FAILED' and get_cnt <= 40:  # noqa
            result_response = client.chat.asyncCompletions.retrieve_completion_result(  # noqa
                id=task_id)
            task_status = result_response.task_status

            if task_status == 'SUCCESS':
                s_cont = result_response.choices[0].message.content
                return s_cont

            time.sleep(2)
            get_cnt += 1

        return None
    except Exception as e:
        print(f"异步API调用失败: {e}")
        return None


def gene_by_llm_once(s_prompt):
    """
    使用新的同步API调用方式生成内容

    参考文档: https://docs.bigmodel.cn/cn/api/introduction

    Return:
        None: Fail to generate msg by llm
        string: generated content by llm
    """
    s_model = DEF_MODEL_ZHIPUAI
    client = get_glm_client()

    try:
        # 使用新的同步API，不再需要异步等待
        response = client.chat.completions.create(
            model=s_model,
            messages=[
                {
                    "role": "user",
                    "content": s_prompt
                }
            ],
            temperature=0.6,
        )

        # 直接获取回复内容
        if response and response.choices and len(response.choices) > 0:
            s_cont = response.choices[0].message.content
            return s_cont
        else:
            return None

    except Exception as e:
        error_str = str(e)
        # 检查是否是余额不足的错误
        if '429' in error_str or '余额不足' in error_str or '无可用资源包' in error_str:
            # 余额不足的错误不应该回退到异步API，直接返回None
            print(f"API调用失败（余额不足）: {e}")
            return None

        # 其他错误可以尝试回退到异步API
        print(f"同步API调用失败: {e}, 尝试使用异步API")
        return gene_by_llm_once_async(s_prompt)


def gene_by_llm(s_prompt, max_retry=3):
    """
    Return:
        None: Fail to generate msg by llm
        string: generated content by llm
    """
    n_try = 0
    while n_try < max_retry:
        n_try += 1
        s_cont = gene_by_llm_once(s_prompt)
        if not s_cont:
            continue
        return s_cont
    return None


if __name__ == "__main__":
    """
    """
    s_in = "I don't know why my account can't like or post"
    s_out = gene_by_llm(s_in)
    print(s_out)

    # main()

    sys.exit(0)


"""
# noqa
"""
