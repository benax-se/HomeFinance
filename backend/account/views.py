import distutils.util
from datetime import datetime

from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from . import serializers
from . import models
from rest_flex_fields.views import FlexFieldsMixin
from rest_flex_fields import is_expanded
from rest_framework.views import APIView
import requests
import xml.etree.ElementTree as ET


class CurrencyUpdate(APIView):

    def get(self, request):
        doc = requests.get('http://www.cbr.ru/scripts/XML_daily.asp')
        doc.encoding = 'utf-8'
        doc = ET.fromstring(doc.content)
        # root = doc.getroot()
        for currency in doc:
            num_code = currency.find('NumCode').text
            let_code = currency.find('CharCode').text
            units = currency.find('Nominal').text
            name = currency.find('Name').text
            rate = currency.find('Value').text
            rate = rate.replace(',', '.')
            rate = float(rate)
            # print(numCode, let_code, units, name, rate)
            cur = models.Currency.objects.get(num_code=num_code)
            cur.rate = rate
            cur.save()
            print('Currencies updated')
            return Response(status=200)


class CurrencyView(ReadOnlyModelViewSet):
    serializer_class = serializers.CurrencySerializer
    queryset = models.Currency.objects.all()


class AccountView(FlexFieldsMixin, ModelViewSet):
    serializer_class = serializers.AccountSerializer
    permit_list_expands = ['user', 'currencies', 'category', 'payout', 'payout.category']

    def get_queryset(self):
        user = self.request.user
        queryset = models.Account.objects.filter(user=user)

        if is_expanded(self.request, 'user'):
            queryset = queryset.select_related('user')

        if is_expanded(self.request, 'currencies'):
            queryset = queryset.prefetch_related('currencies')

        if is_expanded(self.request, 'category'):
            queryset = queryset.prefetch_related('category')

        if is_expanded(self.request, 'currencies'):
            queryset = queryset.prefetch_related('payout')

        if is_expanded(self.request, 'category'):
            queryset = queryset.prefetch_related('payout__category')

        return queryset

    def list(self, request, *args, **kwargs):
        user = self.request.user
        account = models.Account.objects.get(user=user)
        serializer = self.get_serializer(account)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        user = self.request.user
        account = models.Account.objects.get(user=user)
        serializer = self.get_serializer(account)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        if models.Account.objects.get(user=request.user):
            return Response({"detail": "Account already exist"})
        request.data['user'] = request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def partial_update(self, request, *args, **kwargs):
        account = models.Account.objects.get(user=request.user)
        if 'currencies' in request.data:
            currencies_ids = request.data['currencies']
            currencies_ids = currencies_ids.split(',')
            for cur_id in currencies_ids:
                account.currencies.add(models.Currency.objects.get(pk=cur_id))
        if 'total' in request.data:
            total = request.data['total']
            account.total = total
        serializer = self.get_serializer(account)
        account.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        account = models.Account.objects.get(user=request.user)
        if 'currencies' in request.data:
            currencies_ids = request.data['currencies']
            currencies_ids = currencies_ids.split(',')
            for cur_id in currencies_ids:
                account.currencies.remove(models.Currency.objects.get(pk=cur_id))
        serializer = self.get_serializer(account)
        account.save()
        return Response(serializer.data)


class CategoryView(FlexFieldsMixin, ModelViewSet):
    serializer_class = serializers.CategorySerializer
    permit_list_expands = ['account', 'payout']
    filterset_fields = ('account', 'payout')

    def get_queryset(self):
        user = self.request.user
        account = models.Account.objects.get(user=user)
        queryset = models.Category.objects.filter(account=account)
        # queryset = models.Category.objects.all()

        if is_expanded(self.request, 'account'):
            queryset = queryset.select_related('account')

        if is_expanded(self.request, 'payout'):
            queryset = queryset.prefetch_related('payout')

        return queryset

    def create(self, request, *args, **kwargs):
        user = self.request.user
        account = models.Account.objects.get(user=user)
        request.data._mutable = True
        request.data.update({"account": account.id})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        categoryID = serializer.data['id']
        category = models.Category.objects.get(id=categoryID)
        value = request.data['prognosis']
        categoryId = category
        categoryPrognosis = models.CategoryPrognosis(categoryId=categoryId, value=value)
        categoryPrognosis.save()

        return Response(serializer.data, status=201, headers=headers)

    def partial_update(self, request, *args, **kwargs):
        if 'prognosis' in request.data:
            account = models.Account.objects.get(user=request.user)
            category = models.Category.objects.get(id=self.kwargs['pk'])
            value = request.data['prognosis']
            categoryId = category
            categoryPrognosis = models.CategoryPrognosis(categoryId=categoryId, value=value)
            categoryPrognosis.save()

        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class PayOutView(FlexFieldsMixin, ModelViewSet):
    serializer_class = serializers.PayOutSerializer
    permit_list_expands = ['account', 'category']
    filterset_fields = ('account', 'category')

    def get_queryset(self):
        user = self.request.user
        account = models.Account.objects.get(user=user)
        queryset = models.PayOut.objects.filter(account=account, isFastRecord=False)

        if is_expanded(self.request, 'account'):
            queryset = queryset.select_related('account')

        if is_expanded(self.request, 'category'):
            queryset = queryset.select_related('category')

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if 'date_from' in request.data and 'date_to' in request.data:
            print(request.data['date_from'])
            date_from = datetime.strptime(request.data['date_from'], '%d/%m/%y')
            date_to = datetime.strptime(request.data['date_to'], '%d/%m/%y')
            queryset = queryset.filter(creation_date__range=[date_from, date_to])
        if 'isExpenditure' in request.data:  # Получить сумму
            payout_type = request.data['isExpenditure']
            queryset = queryset.filter(isExpenditure=payout_type)
        if 'category' in request.data:
            category = request.data['category']
            queryset = queryset.filter(category=category)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = request.user
        account = models.Account.objects.get(user=user)
        request.data._mutable = True
        request.data.update({"account": account.id})
        isExpenditure = bool(distutils.util.strtobool(request.data.get('isExpenditure')))
        value = int(request.data.get('value'))
        if isExpenditure:
            account.total += value
        else:
            account.total -= value
        account.save()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # if 'category' in request.data:
        #     instance.category = None
        user = self.request.user
        account = models.Account.objects.get(user=user)
        request.data._mutable = True
        request.data.update({"account": account.id})
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


@api_view(['GET'])
def category_stat(request):
    category = models.Category.objects.get(id=request.data['category'])
    value = 0
    date_from = datetime.strptime(request.data['date_from'], '%d/%m/%y')
    date_to = datetime.strptime(request.data['date_to'], '%d/%m/%y')
    isExpenditure = request.data['isExpenditure']
    payouts = models.PayOut.objects.filter(category=category, isExpenditure=isExpenditure,
                                           creation_date__range=[date_from, date_to])

    queryset = models.CategoryPrognosis.objects.filter(categoryId=category, creation_date__range=["2011-01-01", date_to])
    max_date = queryset.latest('creation_date').creation_date
    catProgs = models.CategoryPrognosis.objects.get(creation_date=max_date)

    for payout in payouts:
        value += payout.value
    return Response({"category": category.title, "value": value, "prognosis": catProgs.value})


@api_view(['GET'])
def graph_points(request):
    date_from = datetime.strptime(request.data['date_from'], '%d/%m/%y')
    date_to = datetime.strptime(request.data['date_to'], '%d/%m/%y')
    account = models.Account.objects.get(user=request.user)

    payouts = models.PayOut.objects.filter(account=account, creation_date__range=[date_from, date_to])

    points = []
    for payout in payouts:
        point = {"date": payout.creation_date, "value": payout.value, "isExpenditure": payout.isExpenditure}
        points.append(point)
    return JsonResponse(points, safe=False)




class FastPayOut(FlexFieldsMixin, ModelViewSet):
    serializer_class = serializers.PayOutSerializer
    permit_list_expands = ['account', 'category']
    filterset_fields = ('account', 'category')

    def get_queryset(self):
        user = self.request.user
        account = models.Account.objects.get(user=user)
        queryset = models.PayOut.objects.filter(account=account, isFastRecord=True)

        if is_expanded(self.request, 'account'):
            queryset = queryset.select_related('account')

        if is_expanded(self.request, 'category'):
            queryset = queryset.select_related('category')

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        user = self.request.user
        account = models.Account.objects.get(user=user)
        request.data._mutable = True
        request.data.update({"account": account.id})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        # if 'category' in request.data:
        #     instance.category = None
        user = self.request.user
        account = models.Account.objects.get(user=user)
        request.data._mutable = True
        request.data.update({"account": account.id})
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)



