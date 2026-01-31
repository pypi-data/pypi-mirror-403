"""
@Author: 馒头 (chocolate)
@Email: neihanshenshou@163.com
@File: ExpectFormat.py
@Time: 2023/12/9 18:00
"""


def should_contains(member, container, desc=None):
    """
    Examples
    Args1:
        first: int = 1
        second: int = [1, 2] or (1, 2) or {1} or {1: 2}
        desc: will return True
    Args2:
        first: list = [1, 2]
        second: int = [1, 2, 3] or (3, 1, 2) or {3, 2, 1} or {1: 2, 3: 5, 2: 4}
        desc: will return True
    """
    if isinstance(member, (str, int, float)):
        if member not in container:
            raise AttributeError(f"""
                member: {member}
                container: {container}
                desc: {desc or "期望member是container的子集, 实际与期望结果不一致"}
                """)

    if isinstance(member, (list, dict, set, tuple)):
        for m in member:
            should_contains(member=m, container=container)


def should_equal(first, second, desc: str = ""):
    """
    Examples
    Args1:
        first: int = 1
        second: int = 1
        desc: will return True

    Args2:
        first: str = 'abc'
        second: str = 'abc'
        desc: will return True

    Args3:
        first: list = ['abc']
        second: str = ['abc', 1.3]
        desc: will return False

    Args4:
        first: dict = {"key1": "value1", "key2": "value2"}
        second: dict = {"key2": "value2", "ke1y": "value1"}
        desc: will return False

    Returns:

    """
    if first != second:
        raise AssertionError(
            f"""
                first: {first}
                second: {second}
                desc: 实际{desc}与预期不相同
                """
        )


def should_not_equal(first, second, desc: str = ""):
    """
    Examples
    Args1:
        first: int = 1
        second: int = 1
        desc: will return False

    Args2:
        first: str = 'abc'
        second: str = 'abc'
        desc: will return False

    Args3:
        first: list = ['abc']
        second: str = ['abc', 1.3]
        desc: will return True

    Args4:
        first: dict = {"key1": "value1", "key2": "value2"}
        second: dict = {"key2": "value2", "ke1y": "value1"}
        desc: will return True

    Returns:

    """
    if first == second:
        raise AssertionError(
            f"""
                first: {first}
                second: {second}
                desc: 实际{desc}与预期不相同
                """
        )


def should_true(first, desc: str = ""):
    if not first:
        raise AssertionError(
            f"""
                first: {first}
                desc: 实际{desc}与预期不相同
                """
        )
