"""
pick 业务逻辑层

负责抽奖核心逻辑：文件列表、随机选择、兑换码生成、抽奖动画等。

类:
- PickService: 抽奖服务核心类
  - reset_state(): 重置所有抽奖状态
  - list_files(files_mode_root) -> List[Dict]: 列出文件模式下可供抽取的文件
  - pick_file(candidates) -> Dict: 从候选文件列表中随机选择一个
  - pick_random_item(items) -> str: 从列表中随机选择一个元素
  - generate_redeem_codes(count, length) -> Iterable[str]: 生成若干个随机兑换码
  - pick_item(items): 执行抽奖动画（命令行模式）

状态管理:
- ip_draw_records: IP 抽奖记录（旧逻辑，按 IP 限制）
- redeem_codes: 兑换码使用状态（新逻辑，按兑换码限制）
- ip_file_history: IP 文件历史（避免同一 IP 重复抽到同一个文件）
- code_results: 兑换码抽奖结果（用于页面刷新后恢复）
"""

import click
import random
import os
from typing import Iterable, Dict, Set, List, Optional

from fcbyk.utils import storage, files, common
from fcbyk.cli_support import output


class PickService:
    """抽奖服务业务逻辑"""

    def __init__(self, config_file: str, default_config: dict):
        self.config_file = config_file
        self.default_config = default_config

        # 兑换码持久化文件：~/.fcbyk/data/pick_redeem_codes.json
        self.redeem_codes_file = storage.get_path('pick_redeem_codes.json', subdir='data')

        # 抽奖限制模式：
        # - 旧逻辑：按 IP 限制（ip_draw_records），每个 IP 只能抽一次
        # - 新逻辑：按兑换码限制（redeem_codes），当 redeem_codes 不为空时优先生效，每个兑换码只能使用一次
        # - ip_file_history：记录每个 IP 已经抽中过哪些文件，避免同一 IP 重复抽到同一个文件
        self.ip_draw_records: Dict[str, str] = {}                    # {ip: filename}
        self.redeem_codes: Dict[str, bool] = {}                      # {code: used_flag}
        self.ip_file_history: Dict[str, Set[str]] = {}               # {ip: {filename, ...}}
        self.code_results: Dict[str, Dict] = {}                      # {code: {file: {...}, download_url: str, timestamp: str}} 保存兑换码的抽奖结果

    def reset_state(self):
        """重置抽奖状态"""
        self.ip_draw_records = {}
        self.redeem_codes = {}
        self.ip_file_history = {}
        self.code_results = {}

    def list_files(self, files_mode_root: str) -> List[Dict]:
        """列出文件模式下可供抽取的文件（支持单文件或目录）"""
        return files.get_files_metadata(files_mode_root)

    def pick_file(self, candidates: List[Dict]) -> Dict:
        """从候选文件列表中随机选择一个"""
        return random.choice(candidates)

    def pick_random_item(self, items: List[str]) -> str:
        """从列表中随机选择一个元素"""
        return random.choice(items)

    def generate_redeem_codes(self, count: int, length: int = 4) -> Iterable[str]:
        """生成若干个随机兑换码（字母数字混合，大写）"""
        codes = set()
        while len(codes) < count:
            codes.add(common.generate_random_string(length))
        return sorted(codes)

    def _load_redeem_codes_data(self) -> Dict:
        data = storage.load_json(
            self.redeem_codes_file,
            default={'codes': {}},
            create_if_missing=True,
            strict=False,
        )
        if not isinstance(data, dict):
            return {'codes': {}}
        if not isinstance(data.get('codes'), dict):
            data['codes'] = {}
        return data

    def _save_redeem_codes_data(self, data: Dict) -> None:
        storage.save_json(self.redeem_codes_file, data)

    def load_redeem_codes_from_storage(self) -> Dict[str, bool]:
        """从持久化文件加载兑换码状态到内存。"""
        data = self._load_redeem_codes_data()
        codes = data.get('codes', {})
        out = {}
        for k, v in codes.items():
            code = str(k).strip().upper()
            if not code:
                continue
            used = False
            if isinstance(v, dict):
                used = bool(v.get('used'))
            elif isinstance(v, bool):
                used = bool(v)
            out[code] = used
        return out

    def export_redeem_codes_from_storage(self, only_unused: bool = False) -> List[Dict]:
        """导出兑换码（从持久化读取，返回 [{code, used}, ...]）。

        Args:
            only_unused: 为 True 时，只导出未使用的兑换码。
        """
        data = self._load_redeem_codes_data()
        codes = data.get('codes', {})
        out = []
        if isinstance(codes, dict):
            for k, v in sorted(codes.items()):
                code = str(k).strip().upper()
                if not code:
                    continue
                used = False
                if isinstance(v, dict):
                    used = bool(v.get('used'))
                elif isinstance(v, bool):
                    used = bool(v)

                if only_unused and used:
                    continue

                out.append({'code': code, 'used': used})
        return out

    def add_redeem_code_to_storage(self, code: str) -> bool:
        """新增兑换码到持久化文件，返回是否新增成功。"""
        code = str(code or '').strip().upper()
        if not code:
            return False

        data = self._load_redeem_codes_data()
        codes = data.get('codes', {})
        if code in codes:
            return False
        codes[code] = {'used': False}
        data['codes'] = codes
        self._save_redeem_codes_data(data)
        return True

    def delete_redeem_code_from_storage(self, code: str) -> Optional[bool]:
        """从持久化文件删除兑换码。

        Returns:
            - True : 删除成功
            - False: code 不存在
            - None : 参数非法
        """
        code = str(code or '').strip().upper()
        if not code:
            return None

        data = self._load_redeem_codes_data()
        codes = data.get('codes', {})
        if code not in codes:
            return False

        try:
            del codes[code]
        except Exception:
            return False

        data['codes'] = codes
        self._save_redeem_codes_data(data)
        return True

    def clear_redeem_codes_in_storage(self) -> int:
        """清空所有兑换码（持久化），返回清空前数量。"""
        data = self._load_redeem_codes_data()
        codes = data.get('codes', {})
        n = len(codes) if isinstance(codes, dict) else 0
        data['codes'] = {}
        self._save_redeem_codes_data(data)
        return n

    def reset_redeem_code_unused_in_storage(self, code: str) -> Optional[bool]:
        """将兑换码重置为未使用（持久化）。

        Returns:
            - True : 重置成功
            - False: code 不存在 或 已经是未使用
            - None : 参数非法
        """
        code = str(code or '').strip().upper()
        if not code:
            return None

        data = self._load_redeem_codes_data()
        codes = data.get('codes', {})
        if code not in codes:
            return False

        v = codes.get(code)
        used = False
        if isinstance(v, dict):
            used = bool(v.get('used'))
        elif isinstance(v, bool):
            used = bool(v)

        if not used:
            return False

        # 统一存 dict 结构
        codes[code] = {'used': False}
        data['codes'] = codes
        self._save_redeem_codes_data(data)
        return True

    def mark_redeem_code_used_in_storage(self, code: str) -> bool:
        """标记兑换码已使用（持久化），返回是否标记成功。"""
        code = str(code or '').strip().upper()
        if not code:
            return False

        data = self._load_redeem_codes_data()
        codes = data.get('codes', {})
        if code not in codes:
            return False

        v = codes.get(code)
        if isinstance(v, dict):
            if v.get('used'):
                return False
            v['used'] = True
            codes[code] = v
        elif isinstance(v, bool):
            if v:
                return False
            codes[code] = True
        else:
            codes[code] = {'used': True}

        data['codes'] = codes
        self._save_redeem_codes_data(data)
        return True

    def generate_and_add_redeem_codes_to_storage(self, count: int, length: int = 4) -> List[str]:
        """批量生成并写入持久化（同时更新内存 redeem_codes）。

        说明：
        - 由 Web Admin 调用，用于批量生成兑换码。
        - count 建议由上层限制在 1..100。

        Returns:
            list[str]: 实际生成的新兑换码列表。
        """
        try:
            n = int(count)
        except Exception:
            return []
        if n <= 0:
            return []

        # 读取持久化，确保去重
        data = self._load_redeem_codes_data()
        codes = data.get('codes', {})
        if not isinstance(codes, dict):
            codes = {}

        existed = set([str(k).strip().upper() for k in codes.keys() if str(k).strip()])

        new_codes = []
        tries = 0
        max_tries = max(100, n * 50)
        extra = 0
        cur_len = int(length) if int(length) > 0 else 4

        # 生成策略：先用默认长度生成；如果冲突太多，逐步加长
        while len(new_codes) < n and tries < max_tries:
            tries += 1
            code = common.generate_random_string(cur_len)
            if not code or code in existed:
                # 冲突较多时，适当提高长度
                extra += 1
                if extra >= 20:
                    extra = 0
                    cur_len = min(cur_len + 1, 16)
                continue
            existed.add(code)
            new_codes.append(code)
            codes[code] = {'used': False}

        data['codes'] = codes
        self._save_redeem_codes_data(data)

        # 同步内存态（本次 server 会话立刻可用）
        for c in new_codes:
            self.redeem_codes[c] = False

        return new_codes

    def pick_item(self, items: List[str]):
        """执行抽奖动画"""
        if not items:
            click.echo("Error: No items available. Please use --add to add items first")
            return

        click.echo("=== Random Pick ===")
        click.echo("Spinning...")

        max_length = max(len(f"Current pointer: {item}") for item in items) if items else 0

        # 三个阶段：快速 -> 中速 -> 慢速
        output.show_spinning_animation(items, random.randint(100, 200), 0.05, max_length=max_length)
        output.show_spinning_animation(items, random.randint(20, 40), 0.3, max_length=max_length)
        output.show_spinning_animation(items, random.randint(3, 10), 0.7, max_length=max_length)

        click.echo("\nPick finished!")
