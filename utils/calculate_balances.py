from restapi.models import UserExpense


def get_user_balances(expenses, user):
    final_balance = {}
    for expense in expenses:
        expense_balances = normalize([expense])
        for eb in expense_balances:
            from_user = eb['from_user']
            to_user = eb['to_user']
            if from_user == user.id:
                final_balance[to_user] = final_balance.get(to_user, 0) - eb['amount']
            if to_user == user.id:
                final_balance[from_user] = final_balance.get(from_user, 0) + eb['amount']
    final_balance = {k: v for k, v in final_balance.items() if v != 0}
    return final_balance


def normalize(expenses):
    dues = {}
    for expense in expenses:
        user_balances = UserExpense.objects.filter(expense=expense)
        for user_balance in user_balances:
            dues[user_balance.user] = dues.get(user_balance.user, 0) + user_balance.amount_lent \
                                      - user_balance.amount_owed
    dues = [(k, v) for k, v in sorted(dues.items(), key=lambda item: item[1])]
    start = 0
    end = len(dues) - 1
    balances = []
    while start < end:
        amount = min(abs(dues[start][1]), abs(dues[end][1]))
        user_balance = {"from_user": dues[start][0].id, "to_user": dues[end][0].id, "amount": amount}
        balances.append(user_balance)
        dues[start] = (dues[start][0], dues[start][1] + amount)
        dues[end] = (dues[end][0], dues[end][1] - amount)
        if dues[start][1] == 0:
            start += 1
        if dues[end][1] == 0:
            end -= 1
    return balances
