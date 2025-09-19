from typing import Callable, Optional
from models.clash_of_clans import ClanRole, ClanMember


def parse_custom_ping(custom_ping_started_string: str) -> Optional[Callable[[ClanMember], bool]]:
    # custom_ping_started_string format: @th16&chef|th11-&adj and then anything after that
    if len(custom_ping_started_string) == 0 or custom_ping_started_string[0] != '@':
        return None

    operations: list[str] = []
    operands: list[Callable[[ClanMember], bool]] = []
    keyword_acc = ''
    expect_keyword = True
    for char in custom_ping_started_string[1:]:
        if char not in '+-|&' and not char.isalnum():
            break
        if expect_keyword == (char in '+-|&') and keyword_acc == '':
            return None
        if char.isalnum():
            keyword_acc += char
        else:
            if len(keyword_acc) > 0:
                operands.append(get_custom_ping_filter(keyword_acc, char))
                keyword_acc = ''
            if char in '|&' and len(operands) > 0:
                operations.append(char)
                expect_keyword = True
            elif char in '+-':
                expect_keyword = False
    if len(keyword_acc) > 0:
        operands.append(get_custom_ping_filter(keyword_acc))
    while len(operands) > 1:
        operand_1 = operands.pop()
        operand_2 = operands.pop()
        operation = operations.pop()
        if operation == '&':
            operands.append(lambda m: operand_2(m) and operand_1(m))
        elif operation == '|':
            operands.append(lambda m: operand_2(m) or operand_1(m))
    if len(operands) == 0:
        return None
    return operands[0]


def get_custom_ping_filter(base_keyword: str, modifier: Optional[str] = None) -> Callable[[ClanMember], bool]:
    clan_role_base = None
    if len(base_keyword) == 0:
        return lambda _: False
    if base_keyword == 'clan':
        return lambda _: True
    if base_keyword == 'chef':
        clan_role_base = ClanRole.LEADER
    elif base_keyword in ('adj', 'adjoint', 'adjs', 'adjoints'):
        clan_role_base = ClanRole.COLEADER
    elif base_keyword in ('aine', 'ainé', 'aîné', 'aines', 'ainés', 'aînés'):
        clan_role_base = ClanRole.ADMIN
    elif base_keyword in ('membre', 'membres'):
        clan_role_base = ClanRole.MEMBER
    elif base_keyword in ('gdc', 'gdcattack', 'attack'):
        return lambda _: False  # TODO
    elif base_keyword.startswith('th') or base_keyword.startswith('hdv'):
        th_level_str = base_keyword[2 if base_keyword.startswith('th') else 3:]
        if not th_level_str.isdigit():
            return lambda _: False
        th_level = int(th_level_str)
        if modifier == '+':
            return lambda m: m.townhall_level >= th_level
        elif modifier == '-':
            return lambda m: m.townhall_level <= th_level
        return lambda m: m.townhall_level == th_level

    if clan_role_base is not None:
        if modifier == '+':
            return lambda m: m.role.value >= clan_role_base.value
        elif modifier == '-':
            return lambda m: m.role.value <= clan_role_base.value
        return lambda m: m.role == clan_role_base

    return lambda _: False
