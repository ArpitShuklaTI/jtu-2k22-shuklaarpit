# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import time
from typing import Any

from django.http import HttpResponse
from django.contrib.auth.models import User

# Create your views here.
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, authentication_classes, permission_classes, action
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status

from restapi.models import *
from restapi.serializers import *
from restapi.custom_exception import UnauthorizedUserException
from utils.process_logs import *
from utils.base_logger import logger
from utils.calculate_balances import get_user_balances, normalize


def index(_request):
    return HttpResponse("Hello, world. You're at Rest.")


@api_view(['POST'])
def logout(request):
    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def get_balances(request):
    user = request.user
    expenses = Expense.objects.filter(users__in=user.expenses.all())
    final_balance: dict[int, float] = get_user_balances(expenses, user)
    response: list[dict[str, Any]] = [{"user": k, "amount": int(v)} for k, v in final_balance.items()]
    return Response(response, status=status.HTTP_200_OK)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    http_method_names = ['get', 'post']


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def get_queryset(self):
        user = self.request.user
        groups = user.members.all()
        if self.request.query_params.get('q', None) is not None:
            groups = groups.filter(name__icontains=self.request.query_params.get('q', None))
        return groups

    def create(self, request, *args, **kwargs):
        user: User = self.request.user
        data = self.request.data
        group: Group = Group(**data)
        group.members.add(user)
        group.save()
        logger.info(f"New group created by {user}, group={group}")
        serializer: GroupSerializer = self.get_serializer(group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['put'], detail=True)
    def update_members(self, request, pk=None):
        group: Group = Group.objects.get(id=pk)
        if group not in self.get_queryset():
            logger.error(f"Unauthorized access to group with pk={pk} by {request.user}")
            raise UnauthorizedUserException()
        body = request.data
        if body.get('add', None) is not None and body['add'].get('user_ids', None) is not None:
            added_ids = body['add']['user_ids']
            for user_id in added_ids:
                logger.info(f"Adding {user_id} to group with pk={pk}")
                group.members.add(user_id)
        if body.get('remove', None) is not None and body['remove'].get('user_ids', None) is not None:
            removed_ids = body['remove']['user_ids']
            for user_id in removed_ids:
                logger.info(f"Removing {user_id} from group with pk={pk}")
                group.members.remove(user_id)
        group.save()
        logger.info("Group members updated successfully")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'], detail=True)
    def get_expenses(self, request, pk=None):
        group: Group = Group.objects.get(id=pk)
        if group not in self.get_queryset():
            logger.error(f"Unauthorized access to group with pk={pk} by {request.user}")
            raise UnauthorizedUserException()
        expenses: list[Expense] = group.expenses_set
        serializer: ExpenseSerializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def get_balances(self, request, pk=None):
        group: Group = Group.objects.get(id=pk)
        if group not in self.get_queryset():
            logger.error(f"Unauthorized access to group with pk={pk} by {request.user}")
            raise UnauthorizedUserException()
        expenses = Expense.objects.filter(group=group)
        balances: list[dict[str, Any]] = normalize(expenses)
        return Response(balances, status=status.HTTP_200_OK)


class ExpensesViewSet(ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        user: User = self.request.user
        if self.request.query_params.get('q', None) is not None:
            expenses = Expense.objects.filter(users__in=user.expenses.all())\
                .filter(description__icontains=self.request.query_params.get('q', None))
        else:
            expenses = Expense.objects.filter(users__in=user.expenses.all())
        return expenses

@api_view(['post'])
@authentication_classes([])
@permission_classes([])
def process_logs(request):
    data = request.data
    num_threads: int = data['parallelFileProcessingCount']
    log_files: list[str] = data['logFiles']
    if num_threads <= 0 or num_threads > 30:
        return Response({"status": "failure", "reason": "Parallel Processing Count out of expected bounds"},
                        status=status.HTTP_400_BAD_REQUEST)
    if len(log_files) == 0:
        return Response({"status": "failure", "reason": "No log files provided in request"},
                        status=status.HTTP_400_BAD_REQUEST)
    start = time.time()
    logs: list[str] = read_logs_from_urls(urls=data['logFiles'], num_threads=data['parallelFileProcessingCount'])
    time_taken = int((time.time() - start) * 1000)
    logger.info(f"Took {time_taken}ms to read {len(log_files)} logs using {num_threads} threads")
    sorted_logs: list[list[str]] = sort_by_timestamp(logs)
    cleaned: list[list[str]] = transform(sorted_logs)
    data: dict[str, dict[str, int]] = aggregate(cleaned)
    response: list[dict[str, Any]] = format_response(data)
    time_taken = int((time.time() - start) * 1000)
    logger.info(f"Took {time_taken}ms to process all logs")
    return Response({"response": response}, status=status.HTTP_200_OK)
