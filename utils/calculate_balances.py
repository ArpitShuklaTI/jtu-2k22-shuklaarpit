from typing import Any
from restapi.models import UserExpense, Expense
from django.contrib.auth.models import User


def get_user_balances(expenses: list[Expense], user: User) -> dict[int, float]:
    final_balance: dict[int, float] = {}
    for expense in expenses:
        expense_balances: list[dict[str, Any]] = normalize([expense])
        for eb in expense_balances:
            from_user: int = eb['from_user']
            to_user: int = eb['to_user']
            if from_user == user.id:
                final_balance[to_user] = final_balance.get(to_user, 0) - eb['amount']
            if to_user == user.id:
                final_balance[from_user] = final_balance.get(from_user, 0) + eb['amount']
    final_balance = {k: v for k, v in final_balance.items() if v != 0}
    return final_balance


def normalize(expenses: list[Expense]) -> list[dict[str, Any]]:
    dues: dict[User, float] = {}
    for expense in expenses:
        user_balances: list[UserExpense] = UserExpense.objects.filter(expense=expense)
        for user_balance in user_balances:
            dues[user_balance.user] = dues.get(user_balance.user, 0) + user_balance.amount_lent \
                                      - user_balance.amount_owed
    dues: list[tuple[User, float]] = [(k, v) for k, v in sorted(dues.items(), key=lambda item: item[1])]
    start = 0
    end = len(dues) - 1
    balances: list[dict[str, Any]] = []
    while start < end:
        amount: float = min(abs(dues[start][1]), abs(dues[end][1]))
        user_balance: dict[str, Any] = {"from_user": dues[start][0].id, "to_user": dues[end][0].id, "amount": amount}
        balances.append(user_balance)
        dues[start] = (dues[start][0], dues[start][1] + amount)
        dues[end] = (dues[end][0], dues[end][1] - amount)
        if dues[start][1] == 0:
            start += 1
        if dues[end][1] == 0:
            end -= 1
    return balances
