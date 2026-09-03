"""Demo 规则注册与规则判定辅助。"""

from __future__ import annotations

from typing import Any

from core.rule_engine import RuleEngine


RULE_BOW_TO_TREE = "rule_bow_to_tree"
RULE_POOL_REFLECTION = "rule_pool_reflection"
RULE_NO_EYE_CONTACT = "rule_no_eye_contact"
RULE_TREE_BLEEDING = "rule_tree_bleeding"
PSEUDO_RULE_YUTU_WATCH = "pseudo_rule_yutu_watch"
PSEUDO_RULE_HELP_WUGANG = "pseudo_rule_help_wugang"


RULE_TEXTS = {
    RULE_BOW_TO_TREE: "月桂未见血时，来使不得近。异像现时，方可查验。",
    RULE_POOL_REFLECTION: "凝视月池至久，陟罚自有分晓。",
    RULE_NO_EYE_CONTACT: "玉兔捣药时，不可与之对视。行走于前，恐被其噬。",
    RULE_TREE_BLEEDING: "吴刚第五千斧落下时，月桂流血自修，十息之内来使只可记录，不可代职。",
}


def register_demo_rules(rule_engine: RuleEngine) -> None:
    """注册 Demo 规则，具体上下文由 Game 在检测时传入。"""
    rule_engine.register_rule(
        RULE_BOW_TO_TREE,
        RULE_TEXTS[RULE_BOW_TO_TREE],
        lambda context: not bool(context.get("too_close", False)),
    )
    rule_engine.register_rule(
        RULE_POOL_REFLECTION,
        RULE_TEXTS[RULE_POOL_REFLECTION],
        lambda context: not bool(context.get("staring_reflection", False)),
    )
    rule_engine.register_rule(
        RULE_NO_EYE_CONTACT,
        RULE_TEXTS[RULE_NO_EYE_CONTACT],
        lambda context: not (
            bool(context.get("yutu_pounding", False))
            and bool(context.get("facing_yutu", False))
        ),
    )
    rule_engine.register_rule(
        RULE_TREE_BLEEDING,
        RULE_TEXTS[RULE_TREE_BLEEDING],
        lambda context: bool(context.get("near_bleeding_tree", True)),
    )
    rule_engine.register_pseudo_rule(
        PSEUDO_RULE_YUTU_WATCH,
        "广寒宫前，疾走以示敬意。",
        lambda context: bool(context.get("running_near_palace", False)),
    )
    rule_engine.register_pseudo_rule(
        PSEUDO_RULE_HELP_WUGANG,
        "帮吴刚砍树，可以更快离开月宫。",
        lambda context: bool(context.get("helping_wugang", False)),
    )


def is_facing_rect(source_rect, facing: str, target_rect) -> bool:
    """判断 source 是否大致面向 target，用于玉兔对视规则。"""
    source_center = source_rect.center
    target_center = target_rect.center
    dx = target_center[0] - source_center[0]
    dy = target_center[1] - source_center[1]

    if abs(dx) > abs(dy):
        return facing == ("right" if dx > 0 else "left")
    return facing == ("down" if dy > 0 else "up")


def context_copy(context: dict[str, Any]) -> dict[str, Any]:
    """测试辅助：返回浅拷贝，避免调用方误改原始上下文。"""
    return dict(context)
