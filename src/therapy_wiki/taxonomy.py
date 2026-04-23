"""Lightweight theme and pattern taxonomy for deterministic wiki compilation."""

from typing import Dict, List

THEMES: Dict[str, Dict[str, List[str]]] = {
    "family": {
        "title": "家庭与原生关系",
        "keywords": ["妈妈", "爸爸", "家里", "家庭", "父母", "小时候", "弟弟", "姐姐", "关系"],
    },
    "work-career": {
        "title": "工作与职业",
        "keywords": ["工作", "老板", "同事", "项目", "职业", "学校", "研究", "毕业", "申请"],
    },
    "intimacy": {
        "title": "亲密关系",
        "keywords": ["喜欢", "关系", "分手", "亲密", "伴侣", "恋爱", "暧昧", "沟通", "约会"],
    },
    "self-worth": {
        "title": "自我价值",
        "keywords": ["价值", "不配", "自信", "证明", "失败", "优秀", "羞耻", "评价"],
    },
    "anxiety": {
        "title": "焦虑与不确定",
        "keywords": ["焦虑", "担心", "害怕", "紧张", "控制", "不确定", "慌", "压力"],
    },
    "boundaries": {
        "title": "边界与冲突",
        "keywords": ["边界", "拒绝", "冲突", "生气", "讨好", "委屈", "表达", "压抑"],
    },
}

PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "rumination": {
        "title": "反刍与过度分析",
        "keywords": ["一直想", "反复", "脑补", "停不下来", "分析", "想很多"],
    },
    "self-criticism": {
        "title": "自我批评",
        "keywords": ["是不是我", "怪自己", "不够好", "做错", "失败", "羞耻"],
    },
    "people-pleasing": {
        "title": "讨好与迎合",
        "keywords": ["讨好", "不敢拒绝", "怕别人", "照顾别人", "迎合", "委屈自己"],
    },
    "avoidance-cycle": {
        "title": "回避循环",
        "keywords": ["逃避", "拖延", "不想面对", "躲开", "回避", "不去想"],
    },
    "ambivalence": {
        "title": "矛盾拉扯",
        "keywords": ["一方面", "另一方面", "又想", "又怕", "矛盾", "拉扯"],
    },
    "control-safety": {
        "title": "控制与安全感",
        "keywords": ["控制", "安全感", "失控", "安排", "把握", "确定"],
    },
}

