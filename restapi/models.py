# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
from django.contrib.auth.models import User

from utils.contants import CATEGORY_NAME_MAX_LENGTH, GROUP_NAME_MAX_LENGTH, EXPENSE_DESCRIPTION_MAX_LENGTH, \
    EXPENSE_AMOUNT_MAX_DIGITS, EXPENSE_AMOUNT_DECIMAL_PLACES


class Category(models.Model):
    name = models.CharField(max_length=CATEGORY_NAME_MAX_LENGTH, null=False)


class Group(models.Model):
    name = models.CharField(max_length=GROUP_NAME_MAX_LENGTH, null=False)
    members = models.ManyToManyField(User, related_name='members', blank=True)


class Expense(models.Model):
    description = models.CharField(max_length=EXPENSE_DESCRIPTION_MAX_LENGTH)
    total_amount = models.DecimalField(max_digits=EXPENSE_AMOUNT_MAX_DIGITS, decimal_places=EXPENSE_AMOUNT_DECIMAL_PLACES)
    group = models.ForeignKey(Group, null=True, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, default=1, on_delete=models.CASCADE)


class UserExpense(models.Model):
    expense = models.ForeignKey(Expense, default=1, on_delete=models.CASCADE, related_name="users")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    amount_owed = models.DecimalField(max_digits=EXPENSE_AMOUNT_MAX_DIGITS, decimal_places=EXPENSE_AMOUNT_DECIMAL_PLACES)
    amount_lent = models.DecimalField(max_digits=EXPENSE_AMOUNT_MAX_DIGITS, decimal_places=EXPENSE_AMOUNT_DECIMAL_PLACES)

    def __str__(self):
        return f"user: {self.user}, amount_owed: {self.amount_owed} amount_lent: {self.amount_lent}"
