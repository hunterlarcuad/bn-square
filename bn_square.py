import re
import os  # noqa
import sys  # noqa
import argparse
import random
import time
import pdb  # noqa
import shutil
import re  # noqa
from datetime import datetime  # noqa

from DrissionPage._elements.none_element import NoneElement

from fun_utils import ding_msg
from fun_utils import format_ts
from fun_glm import gene_by_llm

from fun_dp import DpUtils

from conf import DEF_USE_HEADLESS
from conf import DEF_DEBUG
from conf import DEF_PATH_USER_DATA
from conf import DEF_DING_TOKEN
from conf import DEF_PATH_DATA_STATUS

from conf import DEF_DIC_PROJECT

from conf import TZ_OFFSET
from conf import DEL_PROFILE_DIR

from conf import FILENAME_LOG
from conf import logger

"""
2026.01.23
"""


class BnSquare():
    def __init__(self) -> None:
        self.args = None

        self.file_status = None

        # 是否有更新
        self.is_update = False

        # 账号执行情况
        self.dic_status = {}
        self.dic_account = {}

        self.inst_dp = DpUtils()

        self.inst_dp.plugin_yescapcha = True
        self.inst_dp.plugin_capmonster = True
        self.inst_dp.plugin_okx = True

        self.lst_header_status = [
            'update',
            'op_type',
            'proj',
            'msg',
        ]
        self.DEF_HEADER_STATUS = ','.join(self.lst_header_status)

        self.proj = None

    def set_args(self, args):
        self.args = args
        self.is_update = False

        self.file_status = (
            f'{DEF_PATH_DATA_STATUS}/bn_square/square_operation.csv'
        )

    def __del__(self):
        pass

    def append2file(self, file_ot, s_content, header=''):
        """
        header: 表头
        s_content: 写入内容
        追加写入文件
        """
        b_ret = True
        s_msg = ''
        mode = 'a'

        dir_file_out = os.path.dirname(file_ot)
        if dir_file_out and (not os.path.exists(dir_file_out)):
            os.makedirs(dir_file_out)

        try:
            # 如果文件不存在，需要写入表头
            if not os.path.exists(file_ot):
                with open(file_ot, 'w') as fp:
                    fp.write(f'{header}\n')
                    fp.close()

            with open(file_ot, mode) as fp:
                # 写入内容
                fp.write(f'{s_content}\n')
                fp.close()
        except Exception as e:
            b_ret = False
            s_msg = f'[save2file] An error occurred: {str(e)}'

        return (b_ret, s_msg)

    def status_append(self, s_op_type, s_proj, s_msg):
        update_ts = time.time()
        update_time = format_ts(update_ts, 2, TZ_OFFSET)
        s_content = f'{update_time},{s_op_type},{s_proj},{s_msg}'  # noqa
        self.append2file(
            file_ot=self.file_status,
            s_content=s_content,
            header=self.DEF_HEADER_STATUS
        )
        self.is_update = True

    def close(self):
        # 在有头浏览器模式 Debug 时，不退出浏览器，用于调试
        if DEF_USE_HEADLESS is False and DEF_DEBUG:
            pass
        else:
            if self.browser:
                try:
                    self.browser.quit()
                except Exception as e:  # noqa
                    # logger.info(f'[Close] Error: {e}')
                    pass

    def logit(self, func_name=None, s_info=None):
        s_text = f'{self.args.s_profile}'
        if func_name:
            s_text += f' [{func_name}]'
        if s_info:
            s_text += f' {s_info}'
        logger.info(s_text)

    def select_item(self):
        tab = self.browser.latest_tab
        ele_blk = tab.ele(
            '@@tag()=div@@class=tippy-content@@data-state=visible', timeout=2)
        if not isinstance(ele_blk, NoneElement):
            tab.wait(1)
            # Token
            ele_btns = ele_blk.eles(
                '@@tag()=div@@class=css-1jwi1gb', timeout=1)
            if len(ele_btns) > 0:
                ele_btns[0].click(by_js=True)
                tab.wait(2)
                return True

            # Project Account
            ele_btns = ele_blk.eles(
                '@@tag()=div@@class=css-cqoyzh', timeout=1)
            if len(ele_btns) > 0:
                ele_btns[0].click(by_js=True)
                tab.wait(2)
                return True

            # Topic
            ele_btns = ele_blk.eles(
                '@@tag()=div@@class=css-chc6cu', timeout=1)
            if len(ele_btns) > 0:
                ele_btns[0].click(by_js=True)
                tab.wait(2)
                return True

        return False

    def input_post_text(self, ele_btn, lst_text):
        tab = self.browser.latest_tab
        tab.actions.move_to(ele_btn)
        self.logit(None, 'Try to input post text ...')

        try:
            tab.actions.move_to(ele_btn).click()
            b_first = True
            for s_text in lst_text:
                if not b_first:
                    s_text = ' ' + s_text
                tab.actions.type(s_text)
                tab.wait(1)
                self.select_item()
                b_first = False
        except Exception as e:  # noqa
            self.logit(None, f'Error: {e}')
            return False
        tab.wait(1)
        return True

    def bn_post(self, lst_text):
        max_try = 10
        for i in range(1, max_try+1):
            self.logit('bn_post', f'try_i={i}/{max_try}')
            tab = self.browser.latest_tab
            tab.wait.doc_loaded()

            ele_btn = tab.ele(
                '@@tag()=div@@class:json-article-editor', timeout=2)
            if not isinstance(ele_btn, NoneElement):
                self.input_post_text(ele_btn, lst_text)
            else:
                continue

            ele_btn = tab.ele(
                '@@tag()=button@@data-bn-type=button@@class:css-4dec1t',
                timeout=2)
            if not isinstance(ele_btn, NoneElement):
                self.logit(None, 'Try to click post button ...')
                tab.actions.move_to(ele_btn)
                if ele_btn.wait.clickable(timeout=5) is not False:
                    ele_btn.click(by_js=True)
                    self.status_append(
                        s_op_type='post_short',
                        s_proj='xpl',
                        s_msg='post short text successfully',
                    )
                    tab.wait(2)
                    return True

        return False

    def parse_post_text(self, s_text):
        """将文本处理成列表，用于分段输入和选择自动完成项

        按照标签分割文本，保留标签作为独立片段
        保留换行符，只清理每行内的多余空格
        例如："但 @plasma 架构" -> ['但', '@plasma', '架构']
        """
        lst_text = []

        # 定义所有标签的模式（按优先级排序）
        # 先匹配长的模式，避免短模式误匹配
        tag_pattern = r'\$[A-Z0-9]+|@\w+|#\w+'

        # 找到所有标签的位置
        matches = list(re.finditer(tag_pattern, s_text))

        if not matches:
            # 没有标签，直接返回文本（保留换行符）
            if s_text.strip():
                lst_text.append(s_text)
            return lst_text

        # 按照标签位置分割文本
        last_end = 0
        for match in matches:
            start, end = match.span()
            tag = match.group()

            # 添加标签前的文本（保留换行符，只清理每行内的多余空格）
            before_text = s_text[last_end:start]
            if before_text.strip():
                # 检查末尾是否有换行符
                has_trailing_newline = before_text.endswith('\n')
                # 清理每行内的多余空格，但保留换行符结构
                lines = before_text.split('\n')
                cleaned_lines = []
                for line in lines:
                    # 清理每行内的多个空格
                    cleaned_line = re.sub(r' +', ' ', line)
                    # 去掉每行的首尾空格
                    cleaned_line = cleaned_line.strip()
                    cleaned_lines.append(cleaned_line)

                # 将多个连续空行合并，最多保留2个连续换行符
                result_lines = []
                empty_count = 0
                for line in cleaned_lines:
                    if line:
                        result_lines.append(line)
                        empty_count = 0
                    else:
                        # 如果是空行，最多保留2个连续空行
                        if empty_count < 2:
                            result_lines.append('')
                            empty_count += 1

                # 去掉末尾的空行（如果有）
                while result_lines and not result_lines[-1]:
                    result_lines.pop()

                before_text_cleaned = '\n'.join(result_lines)
                # 去掉首尾的空白
                before_text_cleaned = before_text_cleaned.strip('\n\r\t ')
                if before_text_cleaned:
                    # 如果原始文本末尾有换行符，添加回去
                    if has_trailing_newline:
                        before_text_cleaned += '\n'
                    lst_text.append(before_text_cleaned)

            # 添加标签
            lst_text.append(tag)

            last_end = end

        # 添加最后一个标签后的文本（保留换行符）
        after_text = s_text[last_end:]
        if after_text.strip():
            # 检查开头是否有换行符
            has_leading_newline = after_text.startswith('\n')
            # 清理每行内的多余空格，但保留换行符结构
            lines = after_text.split('\n')
            cleaned_lines = []
            for line in lines:
                # 清理每行内的多个空格
                cleaned_line = re.sub(r' +', ' ', line)
                # 去掉每行的首尾空格
                cleaned_line = cleaned_line.strip()
                cleaned_lines.append(cleaned_line)

            # 将多个连续空行合并，最多保留2个连续换行符
            result_lines = []
            empty_count = 0
            for line in cleaned_lines:
                if line:
                    result_lines.append(line)
                    empty_count = 0
                else:
                    # 如果是空行，最多保留2个连续空行
                    if empty_count < 2:
                        result_lines.append('')
                        empty_count += 1

            # 去掉开头的空行（如果有）
            while result_lines and not result_lines[0]:
                result_lines.pop(0)

            after_text_cleaned = '\n'.join(result_lines)
            # 去掉首尾的空白
            after_text_cleaned = after_text_cleaned.strip('\n\r\t ')
            if after_text_cleaned:
                # 如果原始文本开头有换行符，添加回去
                if has_leading_newline:
                    after_text_cleaned = '\n' + after_text_cleaned
                lst_text.append(after_text_cleaned)

        return lst_text

    def is_reply_ok(self, s_reply, n_min_len=100, n_max_len=500):
        """
        检查回复内容是否合格

        检查规则：
        1. 如果回复长度小于 n_min_len 字符，则认为回复不合格
        2. 如果回复长度超过 n_max_len 字符，则认为回复不合格
        3. 如果 @ # $ 出现次数超过 1 次，则认为回复不合格
        4. 如果非中文字符串(英文、数字、符号，符号只考虑 @ # $ 三个)与中文之间没有空格，则认为回复不合格

        Args:
            s_reply: 回复内容
            n_min_len: 最小长度限制，默认100字符
            n_max_len: 最大长度限制，默认500字符

        Returns:
            tuple: (bool, str) - (是否合格, 不合格原因)
                   True表示合格，False表示不合格
        """
        errors = []

        # 检查长度
        if len(s_reply) < n_min_len:
            errors.append(f'长度不足({len(s_reply)}<{n_min_len}) [回答太短了，需要增加内容]')
        if len(s_reply) > n_max_len:
            # errors.append(f'长度超限({len(s_reply)}>{n_max_len})')
            errors.append(f'长度超限({len(s_reply)}>{n_max_len}) [回答太长了，字数减少一点]')

        # 检查特殊字符出现次数
        special_chars = ['@', '#', '$']
        for char in special_chars:
            count = s_reply.count(char)
            if count > 1:
                errors.append(f'"{char}"出现{count}次')

        # 检查换行符使用是否合理（允许换行，但不允许过多的连续换行）
        if re.search(r'\n{3,}', s_reply):
            errors.append('出现过多连续换行符（超过2个）')

        # 开头是否有空格
        if s_reply.startswith(' '):
            errors.append('开头有空格')
        # 末尾是否有空格
        if s_reply.endswith(' '):
            errors.append('末尾有空格')

        # 检查是否出现 <|begin_of_box|> 和 <|end_of_box|> 标签
        if '<|begin_of_box|>' in s_reply or '<|end_of_box|>' in s_reply:
            errors.append('出现 <|begin_of_box|> 和 <|end_of_box|> 标签')

        # 如果有错误，返回 False 和拼接的错误信息
        if errors:
            error_msg = '; '.join(errors)
            self.logit(None, f'Reply not qualified: {error_msg}')
            return False, error_msg

        return True, ""

    def clean_reply(self, s_reply):
        # 去掉 <|begin_of_box|> 和 <|end_of_box|> 标签
        s_reply = re.sub(r'<\|begin_of_box\|>|<\|end_of_box\|>', '', s_reply)  # noqa

        # 规范化换行：将多个连续换行符统一为单个换行符
        s_reply = re.sub(r'\n{3,}', '\n\n', s_reply)

        # 清理每行前后的空格，但保留换行符
        lines = s_reply.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        s_reply = '\n'.join(cleaned_lines)

        # 清理多余的空格（但保留换行）
        # 将每行内的多个空格合并为单个空格
        lines = s_reply.split('\n')
        cleaned_lines = [re.sub(r' +', ' ', line) for line in lines]
        s_reply = '\n'.join(cleaned_lines)

        # 去掉前后的空格和换行
        s_reply = s_reply.strip()

        return s_reply

    def gene_title_by_llm(self, s_text, min_len=10, max_len=30):
        """
        通过大模型生成标题

        参数:
            s_text: 输入的文本内容
            min_len: 标题最小长度（字符数），默认 10
            max_len: 标题最大长度（字符数），默认 30

        返回:
            str: 生成的标题，如果生成失败返回 None
        """
        if not s_text or not s_text.strip():
            self.logit(None, 's_text is empty, cannot generate title')
            return None

        s_rules = (
            "请用中文输出\n"
            f"标题长度不少于 {min_len} 且不超过 {max_len}（英文、数字、符号按字符数计算，中文汉字按汉字数计算）\n"
            "标题要简洁明了，能够概括文本的主要内容\n"
            "标题要有吸引力，能够引起读者的兴趣\n"
            "标题不要包含标签符号（如 @、#、$）\n"
            "标题不要出现换行符，必须是一行文本\n"
            "标题不要出现 <|begin_of_box|> 和 <|end_of_box|> 标签\n"
            "标题要符合中文表达习惯，语言自然流畅\n"
        )

        s_prompt = (
            "# 【功能】\n"
            "根据给定的文本内容，生成一个简洁、吸引人的标题\n"
            "\n"
            "# 【要求】\n"
            f"{s_rules}\n"
            "\n"
            "# 【文本内容】\n"
            f"{s_text}\n"
            "\n"
            "# 【重要提示】\n"
            "- 标题要准确概括文本的核心内容\n"
            "- 标题要简洁有力，避免冗长\n"
            "- 标题要有吸引力，能够引起读者的点击欲望\n"
            "- 直接输出标题内容，不要添加任何前缀或说明\n"
        )

        self.logit(None, f'Generating title for text (length: {len(s_text)})')

        try:
            s_title = gene_by_llm(s_prompt)
            if not s_title:
                self.logit(None, 's_title from llm is empty')
                return None

            # 清理标题
            s_title = s_title.strip()
            # 去掉可能的标签符号
            s_title = re.sub(r'[@#$]', '', s_title)
            # 去掉换行符
            s_title = re.sub(r'\n+', '', s_title)
            # 去掉多余的空格
            s_title = re.sub(r' +', ' ', s_title).strip()
            # 去掉可能的标签符号（如 <|begin_of_box|> 和 <|end_of_box|>）
            s_title = s_title.replace('<|begin_of_box|>', '')
            s_title = s_title.replace('<|end_of_box|>', '')
            s_title = s_title.strip()

            # 验证标题长度
            if len(s_title) < min_len or len(s_title) > max_len:
                self.logit(
                    None,
                    f'Title length ({len(s_title)}) not in range [{min_len}, {max_len}], '  # noqa
                    f'retrying...'
                )
                # 如果长度不符合要求，尝试重新生成
                s_prompt_retry = (
                    "# 【要求】\n"
                    f"{s_rules}\n"
                    "\n"
                    "# 【文本内容】\n"
                    f"{s_text}\n"
                    "\n"
                    "# 【之前生成的标题有问题】\n"
                    f"之前生成的标题：{s_title}\n"
                    f"标题长度：{len(s_title)} 字符\n"
                    f"要求长度：{min_len}-{max_len} 字符\n"
                    "\n"
                    "# 【重要】\n"
                    "请重新生成一个符合长度要求的标题。\n"
                    "标题要简洁明了，能够概括文本的主要内容。\n"
                    "直接输出标题内容，不要添加任何前缀或说明。\n"
                )
                try:
                    s_title = gene_by_llm(s_prompt_retry)
                    if s_title:
                        s_title = s_title.strip()
                        s_title = re.sub(r'[@#$]', '', s_title)
                        s_title = re.sub(r'\n+', '', s_title)
                        s_title = re.sub(r' +', ' ', s_title).strip()
                        s_title = s_title.replace('<|begin_of_box|>', '')
                        s_title = s_title.replace('<|end_of_box|>', '')
                        s_title = s_title.strip()
                except Exception as e:  # noqa
                    self.logit(None, f'Error retrying title generation: {e}')

            # 最终验证
            if not s_title or len(s_title) < min_len:
                self.logit(
                    None, f'Title generation failed, length: {len(s_title) if s_title else 0}')  # noqa
                return None

            # 如果标题太长，截断
            if len(s_title) > max_len:
                s_title = s_title[:max_len].rstrip()
                # 如果截断后以不完整的词结尾，尝试找到最后一个完整的词
                if s_title and s_title[-1] not in '，。！？、；：':
                    # 尝试找到最后一个空格或标点符号
                    last_space = s_title.rfind(' ')
                    if last_space > min_len:
                        s_title = s_title[:last_space].rstrip()

            self.logit(
                None, f'Generated title: {s_title} (length: {len(s_title)})')
            return s_title

        except Exception as e:
            self.logit(None, f'Error calling gene_by_llm for title: {e}')
            return None

    def gene_new_post_text_by_llm(self, min_len=100, max_len=500):
        """
        Generate new post text by LLM

        参数:
            min_len: 最小长度（字符数），默认 100
            max_len: 最大长度（字符数），默认 500
        """
        d_proj = DEF_DIC_PROJECT.get(self.proj, {})
        s_at = d_proj.get('at', '@plasma')
        s_tag = d_proj.get('tag', '#plasma')
        s_token = d_proj.get('token', '$XPL')
        lst_at = s_at if isinstance(s_at, list) else [s_at]
        lst_tag = s_tag if isinstance(s_tag, list) else [s_tag]
        lst_token = s_token if isinstance(s_token, list) else [s_token]
        s_at_opt = ' '.join(lst_at)
        s_tag_opt = ' '.join(lst_tag)
        s_token_opt = ' '.join(lst_token)
        s_proj_name = d_proj.get('name', self.proj or '')

        # 定义5种风格
        styles = {
            '小红书风格': (
                "风格要求：采用小红书风格，轻松、生活化、分享感强。"
                "语言要亲切自然，可以适当使用口语化表达，"
                "内容要有个人体验感和情感色彩，让读者感觉像是在和朋友聊天。"
            ),
            '专业分析风格': (
                "风格要求：采用专业分析风格，深度、专业、数据驱动。"
                "语言要严谨客观，可以引用数据和技术细节，"
                "内容要有逻辑性和说服力，适合对技术感兴趣的读者。"
            ),
            '幽默段子风格': (
                "风格要求：采用幽默段子风格，搞笑、轻松、有趣。"
                "语言要幽默风趣，可以适当使用网络流行语和段子，"
                "内容要有趣味性和娱乐性，让读者在轻松的氛围中了解信息。"
            ),
            '深度思考风格': (
                "风格要求：采用深度思考风格，哲学、思考、启发。"
                "语言要有深度和哲理性，可以引发读者思考，"
                "内容要有思想性和启发性，适合喜欢深度内容的读者。"
            ),
            '新闻资讯风格': (
                "风格要求：采用新闻资讯风格，客观、及时、信息量大。"
                "语言要客观中立，信息要准确及时，"
                "内容要有新闻价值和信息量，适合关注行业动态的读者。"
            )
        }

        # 随机选择一种风格
        selected_style = random.choice(list(styles.keys()))
        style_description = styles[selected_style]
        self.logit(None, f'Selected writing style: {selected_style}')

        s_rules = (
            "请用中文输出\n"
            "内容格式要求：生成的内容需要有清晰的换行，每段之间用换行符分隔，使内容结构清晰易读\n"
            f"内容长度不少于 {min_len} 且不超过 {max_len}（英文、数字、符号按字符数计算，中文汉字按汉字数计算）\n"
            f"内容必须提及 {s_at_opt}，包含代币标签 {s_token_opt}，并带有话题标签 {s_tag_opt}\n"
            f"内容必须与 {s_proj_name} 相关且完全原创，不能直接复制任何来源的内容\n"
            "内容需要有独到的见解和观点，不能是简单的信息堆砌\n"
            f"写作风格：{style_description}\n"
            "特别注意，中文(汉字)与非中文(英文、数字、符号)之间要加一个空格，不要连在一起，增加可读性\n"
            "特别注意，不要出现回复如下之类的字眼，直接输出回复内容\n"
            "特别注意，回复不要出现 <|begin_of_box|> 和 <|end_of_box|> 标签\n"
        )

        s_prompt = (
            "# 【功能】\n"
            f"生成一条关于 {s_proj_name} 的原创推文\n"
            "\n"
            "# 【背景信息】\n"
            f"请先 搜索 与 {s_proj_name} 相关的内容，分析这些内容中的观点和趋势，\n"
            "然后基于这些分析，生成一条见解独到的原创推文。\n"
            "\n"
            "# 【要求】\n"
            f"{s_rules}\n"
            "\n"
            "# 【生成步骤】\n"
            f"1. 搜索 关键词 '{s_proj_name}'，获取最新的内容（建议搜索 10-20 条）\n"
            "2. 分析内容：分析这些推文中的主要观点、讨论焦点、趋势和独特见解\n"
            "3. 生成原创推文：基于分析结果，结合自己的独到见解，按照指定的写作风格生成一条原创推文\n"
            "\n"
            "# 【重要提示】\n"
            "- 推文需要有独到的观点和见解，不能只是信息的简单汇总\n"
            f"- 推文内容要与 {s_proj_name} 项目相关，可以涉及技术、生态、应用场景等方面\n"
            f"- 推文必须严格按照「{selected_style}」的风格要求来写作\n"
            "- 推文要富有哲理或启发性，能够引起读者的思考和共鸣\n"
        )

        self.logit(None, f's_prompt: {s_prompt}')

        try:
            s_text = gene_by_llm(s_prompt)
            if not s_text:
                self.logit(None, 's_text from llm is empty, skip ...')
                s_text = ''
                # return False
        except Exception as e:
            self.logit(None, f'Error calling gene_by_llm: {e}')
            s_text = ''
            # return False

        # 尝试生成合格的回复，最多尝试次数
        max_attempts = 6
        for attempt in range(1, max_attempts + 1):
            self.logit(
                None, f'quality check attempt: {attempt}/{max_attempts}')
            s_text = self.clean_reply(s_text)

            self.logit(None, f'[To Verify]post_by_llm: {s_text}')
            # 验证推文内容是否合格
            is_ok, reason = self.is_reply_ok(
                s_text, n_min_len=min_len, n_max_len=max_len)
            if is_ok:
                self.logit(
                    None,
                    f'Post qualified on attempt {attempt}/{max_attempts}'
                )
                break
            else:
                self.logit(
                    None,
                    f'Attempt {attempt}/{max_attempts}: '
                    f'Post not qualified: {reason}'
                )
                if attempt < max_attempts:
                    # 修改 prompt，要求大模型根据错误原因进行改进
                    s_prompt = (
                        "# 【要求】\n"
                        f"{s_rules}\n"
                        "\n"
                        "# 【推文内容有问题，请根据错误原因进行修改】\n"
                        f"{reason}\n"
                        "\n"
                        "# 【推文内容】\n"
                        f"{s_text}\n"
                        "\n"
                        "# 【重要】\n"
                        "请根据错误原因修改推文，确保符合所有要求。\n"
                        f"如果内容长度不符合要求，请调整到 {min_len}-{max_len} 字符之间。\n"
                        f"如果缺少必要的标签提及，请确保内容与 {s_at_opt}、{s_token_opt}、{s_tag_opt} 相关。\n"  # noqa
                        f"请保持「{selected_style}」的写作风格不变。\n"
                    )
                    try:
                        s_text = gene_by_llm(s_prompt)
                        if not s_text:
                            self.logit(
                                None, 's_text from llm is empty, skip ...')
                            return False
                    except Exception as e:
                        self.logit(None, f'Error calling gene_by_llm: {e}')
                        return False
                else:
                    if not s_text:
                        self.logit(
                            None, 'All attempts failed, post is empty, skip ...')  # noqa
                        return False
                    self.logit(
                        None, 'All attempts failed, ignore the check, use the post ...')  # noqa

        return s_text

    def normalize_post_tags(self, s_text):
        """
        规范化推文中的标签：
        1. 如果包含 XPL 但前面没有 $，则替换为 $XPL
        2. 如果 $XPL 前后没有空格，则增加空格
        3. 如果不包含 XPL，则在最后增加 ' $XPL'
        4. 对 @plasma 和 #plasma 做类似处理

        参数:
            s_text: 原始文本

        返回:
            str: 规范化后的文本
        """
        if not s_text:
            return s_text

        # 处理 $XPL
        # 1. 如果包含 XPL 但前面没有 $，则替换为 $XPL（不区分大小写）
        # 替换所有独立的 XPL（不在 $ 后面）
        s_text = re.sub(r'(?i)(?<!\$)\bXPL\b', r'$XPL', s_text)

        # 2. 如果 $XPL 前后没有空格，则增加空格
        # 前面没有空格且不是开头，且前面不是 $，则添加空格
        s_text = re.sub(r'(?<!\s)(?<!\$)(?<!^)\$XPL', r' $XPL', s_text)
        # 后面没有空格且不是结尾，则添加空格
        s_text = re.sub(r'\$XPL(?!\s)(?!$)', r'$XPL ', s_text)

        # 3. 如果不包含 $XPL，则在最后增加 ' $XPL'
        if not re.search(r'\$XPL', s_text, re.IGNORECASE):
            s_text = s_text.rstrip() + ' $XPL'

        # 处理 @plasma（不区分大小写）
        # 先统一将 @Plasma、@PLASMA 等统一为 @plasma（小写）
        s_text = re.sub(r'(?i)@plasma', r'@plasma', s_text)

        # 如果文本中还没有 @plasma，查找独立的 plasma 词并替换
        # 替换所有独立的 plasma（不在 @、#、$ 后面），不区分大小写
        # 但只替换第一个，避免替换太多
        if not re.search(r'@plasma', s_text, re.IGNORECASE):
            s_text = re.sub(
                r'(?i)(?<!@)(?<!#)(?<!\$)\bplasma\b',
                r'@plasma',
                s_text,
                count=1
            )

        # 2. 如果 @plasma 前后没有空格，则增加空格
        s_text = re.sub(r'(?i)(?<!\s)(?<!@)@plasma', r' @plasma', s_text)
        s_text = re.sub(r'(?i)@plasma(?!\s)(?!$)', r'@plasma ', s_text)

        # 3. 如果不包含 @plasma，则在最后增加 ' @plasma'
        if not re.search(r'@plasma', s_text, re.IGNORECASE):
            s_text = s_text.rstrip() + ' @plasma'

        # 处理 #plasma（不区分大小写）
        # 先统一将 #Plasma、#PLASMA 等统一为 #plasma（小写）
        s_text = re.sub(r'(?i)#plasma', r'#plasma', s_text)

        # 2. 如果 #plasma 前后没有空格，则增加空格
        s_text = re.sub(r'(?i)(?<!\s)(?<!#)#plasma', r' #plasma', s_text)
        s_text = re.sub(r'(?i)#plasma(?!\s)(?!$)', r'#plasma ', s_text)

        # 3. 如果不包含 #plasma，则在最后增加 ' #plasma'
        if not re.search(r'#plasma', s_text, re.IGNORECASE):
            s_text = s_text.rstrip() + ' #plasma'

        # 清理多余的空格，但保留换行符和标签
        # 按行处理，清理每行内的多余空格
        lines = s_text.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip():
                # 清理每行内的多个空格（2个以上空格合并为1个）
                # 但保留标签周围的单个空格
                cleaned_line = re.sub(r' {2,}', ' ', line).strip()
                cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append('')

        # 删除所有空行（连续多个空行全部删除）
        final_lines = []
        for line in cleaned_lines:
            if line.strip():
                # 只保留非空行
                final_lines.append(line)

        s_text = '\n'.join(final_lines)

        # 限制带 $ 的标签不超过3个
        # 查找所有带 $ 的标签及其位置
        dollar_matches = list(re.finditer(r'\$[A-Z0-9]+', s_text))
        if len(dollar_matches) > 3:
            # 如果超过3个，只保留前3个，删除从第4个开始的所有标签
            # 从后往前删除，避免位置偏移问题
            tags_to_remove = dollar_matches[3:]
            # 从后往前删除
            for match in reversed(tags_to_remove):
                start, end = match.span()
                # 删除标签及其前后的空格
                # 检查前后是否有空格
                before_char = s_text[start-1] if start > 0 else ''
                after_char = s_text[end] if end < len(s_text) else ''

                # 构建删除范围
                del_start = start
                del_end = end

                # 如果前面是空格，也删除
                if before_char == ' ':
                    del_start = start - 1
                # 如果后面是空格，也删除
                if after_char == ' ':
                    del_end = end + 1

                # 删除
                s_text = s_text[:del_start] + s_text[del_end:]

            # 清理多余的空格
            s_text = re.sub(r' +', ' ', s_text).strip()

        # 去掉首尾的空格和换行
        s_text = s_text.strip()

        return s_text

    def long_input(self, lst_text, s_title=None):
        tab = self.browser.latest_tab
        ele_btn = tab.ele('@@tag()=div@@class=css-l3k73g', timeout=2)
        if not isinstance(ele_btn, NoneElement):
            tab.actions.move_to(ele_btn).click()
            tab.actions.type(s_title)
            tab.wait(1)
        else:
            return False

        ele_content = tab.ele('.article-editor css-timm1x', timeout=2)
        if not isinstance(ele_content, NoneElement):
            self.input_post_text(ele_content, lst_text)
        else:
            return False

        if self.args.upload_image:
            s_msg = 'Please upload the image manually ...'
            self.logit(None, s_msg)
            ding_msg(s_msg, DEF_DING_TOKEN, msgtype='text')
            input(s_msg)

        # publish
        ele_btn = tab.ele('@@tag()=button@@class:css-1uzbnpg', timeout=2)
        if not isinstance(ele_btn, NoneElement):
            if ele_btn.wait.clickable(timeout=5) is not False:
                ele_btn.click()
                self.status_append(
                    s_op_type='post_long',
                    s_proj='xpl',
                    s_msg='post long text successfully',
                )
                tab.wait(3)
                return True
        else:
            return False
        return False

    def post_article(self):
        tab = self.browser.latest_tab
        s_url = 'https://www.binance.com/zh-CN/square/'
        tab.get(s_url)
        tab.wait(3)
        tab.wait.doc_loaded()

        ele_btn = tab.ele(
            '@@tag()=div@@class:center icon-box cursor-pointer', timeout=2)
        if not isinstance(ele_btn, NoneElement):
            ele_btn.click()
            tab.wait(3)
            return True
        return False

    def post_long_text(self):
        tab = self.browser.latest_tab
        s_url = 'https://www.binance.com/zh-CN/square/creatorpad/xpl'
        tab.get(s_url)
        tab.wait(3)
        tab.wait.doc_loaded()

        ele_blk = tab.ele(
            '@@tag()=div@@class:flex items-start justify-between@@text():在币安广场使用文章编辑器', timeout=2)  # noqa
        if not isinstance(ele_blk, NoneElement):
            ele_btn = ele_blk.ele(
                '@@tag()=button@@class:bn-button', timeout=2)
            if not isinstance(ele_btn, NoneElement):
                s_text = ele_btn.text
                if s_text in ['已完成']:
                    if self.post_article():
                        return True
                ele_btn.click()
                tab.wait(3)
                return True
        return False

    def publish_post(self, min_len=100, max_len=500):
        s_text = self.gene_new_post_text_by_llm(
            min_len=min_len, max_len=max_len)

        s_text = self.normalize_post_tags(s_text)

        if s_text is False:
            return False

        lst_text = self.parse_post_text(s_text)

        if min_len > 500:
            self.post_long_text()
            s_title = self.gene_title_by_llm(s_text, min_len=10, max_len=30)
            if self.long_input(lst_text, s_title) is False:
                return False
        else:
            if self.bn_post(lst_text) is False:
                return False
        return True

    def get_new_post(self):
        tab = self.browser.latest_tab
        ele_btn = tab.ele('.css-1e53l72', timeout=2)
        if not isinstance(ele_btn, NoneElement):
            ele_btn.click()
            tab.wait(5)
            return True
        return False

    def get_last_post_ts(self, file_path, s_proj, s_post_type):
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, 'r') as fp:
                lines = fp.readlines()
        except Exception:  # noqa
            return None

        for line in reversed(lines):
            line = line.strip()
            if not line or line.startswith('update'):
                continue
            parts = line.split(',', 3)
            if len(parts) < 4:
                continue
            s_ts, s_op_type, s_proj_line, _ = parts
            if s_op_type == s_post_type and s_proj_line == s_proj:
                try:
                    return datetime.strptime(s_ts, '%Y-%m-%dT%H:%M:%S%z')
                except Exception:  # noqa
                    return None
        return None

    def is_time_ready(self, s_post_type, s_proj, n_sleep):
        last_ts = self.get_last_post_ts(self.file_status, s_proj, s_post_type)
        if last_ts is not None:
            now_ts = datetime.now().astimezone()
            if (now_ts - last_ts).total_seconds() < n_sleep:
                self.logit(
                    'square_process',
                    f'skip {s_post_type} for {s_proj}, last update within {n_sleep} seconds',  # noqa
                )
                return False
        return True

    def square_process(self):

        # open BnSquare url
        tab = self.browser.latest_tab
        tab.get(self.args.url)
        tab.wait(3)
        # tab.set.window.max()

        for s_proj, d_proj in DEF_DIC_PROJECT.items():
            self.logit('square_process', f'proj: {s_proj}')
            self.proj = s_proj

            n_sleep = random.randint(1800, 3600)
            b_is_ready = self.is_time_ready('post_short', s_proj, n_sleep)
            if b_is_ready:
                self.publish_post(min_len=150, max_len=400)

            n_sleep = random.randint(3600, 7200)
            b_is_ready = self.is_time_ready('post_long', s_proj, n_sleep)
            if b_is_ready:
                self.publish_post(min_len=600, max_len=800)

        return True

    def square_run(self):
        self.browser = self.inst_dp.get_browser(self.args.profile)

        self.square_process()

        if self.args.manual_exit:
            s_msg = 'Manual Exit. Press any key to exit! ⚠️'  # noqa
            input(s_msg)

        self.logit('square_run', 'Finished!')

        return True


def show_msg(args):
    current_directory = os.getcwd()
    FILE_LOG = f'{current_directory}/{FILENAME_LOG}'
    FILE_STATUS = f'{current_directory}/{DEF_PATH_DATA_STATUS}/status.csv'

    print('########################################')
    print('The program is running')
    print(f'headless={args.headless}')
    print('Location of the running result file:')
    print(f'{FILE_STATUS}')
    print('The running process is in the log file:')
    print(f'{FILE_LOG}')
    print('########################################')


def main(args):
    if args.sleep_sec_at_start > 0:
        logger.info(f'Sleep {args.sleep_sec_at_start} seconds at start !!!')  # noqa
        time.sleep(args.sleep_sec_at_start)

    if DEL_PROFILE_DIR and os.path.exists(DEF_PATH_USER_DATA):
        logger.info(f'Delete {DEF_PATH_USER_DATA} ...')
        shutil.rmtree(DEF_PATH_USER_DATA)
        logger.info(f'Directory {DEF_PATH_USER_DATA} is deleted')  # noqa

    s_profile = args.profile
    inst_square = BnSquare()
    inst_square.set_args(args)

    # 如果出现异常(与页面的连接已断开)，增加重试
    max_try_except = 3
    for j in range(1, max_try_except+1):
        try:
            if j > 1:
                logger.info(f'⚠️ 正在重试，当前是第{j}次执行，最多尝试{max_try_except}次 [{s_profile}]')  # noqa

            inst_square.set_args(args)
            inst_square.inst_dp.plugin_yescapcha = False
            inst_square.inst_dp.plugin_capmonster = False
            inst_square.inst_dp.plugin_okx = False
            inst_square.inst_dp.set_args(args)
            inst_square.square_run()
            break

        except Exception as e:
            logger.info(f'[{args.profile}] An error occurred: {str(e)}')
            inst_square.close()
            if j < max_try_except:
                time.sleep(5)

        sleep_time = random.randint(args.sleep_sec_min, args.sleep_sec_max)
        if sleep_time > 60:
            logger.info('sleep {} minutes ...'.format(int(sleep_time/60)))
        else:
            logger.info('sleep {} seconds ...'.format(int(sleep_time)))
        time.sleep(sleep_time)


if __name__ == '__main__':
    """
    每次随机取一个出来，并从原列表中删除，直到原列表为空
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--loop_interval', required=False, default=60, type=int,
        help='[默认为 60] 执行完一轮 sleep 的时长(单位是秒)，如果是0，则不循环，只执行一次'
    )
    parser.add_argument(
        '--sleep_sec_min', required=False, default=60, type=int,
        help='[默认为 60] 每个账号执行完 sleep 的最小时长(单位是秒)'
    )
    parser.add_argument(
        '--sleep_sec_max', required=False, default=120, type=int,
        help='[默认为 120] 每个账号执行完 sleep 的最大时长(单位是秒)'
    )
    parser.add_argument(
        '--sleep_sec_at_start', required=False, default=0, type=int,
        help='[默认为 0] 在启动后先 sleep 的时长(单位是秒)'
    )
    parser.add_argument(
        '--profile', required=False, default='bnsquare',
        help='按指定的 profile 执行，多个用英文逗号分隔'
    )
    parser.add_argument(
        '--manual_exit', required=False, action='store_true',
        help='Close chrome manual'
    )
    # 添加 --headless 参数
    parser.add_argument(
        '--headless',
        action='store_true',   # 默认为 False，传入时为 True
        default=False,         # 设置默认值
        help='Enable headless mode'
    )
    # 添加 --no-headless 参数
    parser.add_argument(
        '--no-headless',
        action='store_false',
        dest='headless',  # 指定与 --headless 参数共享同一个变量
        help='Disable headless mode'
    )
    parser.add_argument(
        '--url', required=False,
        default='https://www.binance.com/zh-CN/square',
        help='BnSquare url'
    )
    parser.add_argument(
        '--upload_image', required=False, action='store_true',
        help='Whether to upload an image when posting'
    )

    args = parser.parse_args()
    show_msg(args)
    if args.loop_interval <= 0:
        main(args)
    else:
        while True:
            main(args)
            logger.info('#####***** Loop sleep {} seconds ...'.format(args.loop_interval))  # noqa
            time.sleep(args.loop_interval)

"""
# noqa
python bn_square.py --upload_image
"""
