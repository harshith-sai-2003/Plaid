from django.shortcuts import render
from dotenv import load_dotenv
from os.path import join,dirname
import os
import plaid
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import PlaidCredential
import datetime
import calender

# Create your views here.
dotenv_path='.env'
load_dotenv(dotenv_path)

PLAID_CLIENT_ID=os.environ.get("PLAID_CLIENT_ID")
PLAID_CLIENT_SECRET=os.environ.get("PLAID_CLIENT_SECRET")

client=plaid.Client(
    client_id=PLAID_CLIENT_ID,
    secret=PLAID_CLIENT_SECRET,
    environment='sandbox',
    api_version='2019-05-29'
)

PLAID_COUNTRY_CODES=os.getenv('PLAID_COUNTRY_CODES','IN').split(',')
PLAID_PRODUCTS=os.getenv('PLAID_PRODUCTS','transactions').split(',')
PLAID_REDIRECT_URI=None

def index(request):
    return render(request,'plaid_api/index.html')

@csrf_exempt
def create_link_token(request):
    try:
        response=client.LinkToken.create(
            {
                'user':{
                    'client_user_id':request.user.id
                },
                'client_name': 'YABA',
                'products': PLAID_PRODUCTS,
                'country_codes':PLAID_COUNTRY_CODES,
                'language':'en',
                'redirect_uri':PLAID_REDIRECT_URI
            }
        )
        return JsonResponse(response)
    except plaid.errors.PlaidError as e:
        return JsonResponse(e)

@csrf_exempt
def get_access_token(request):
    public_token=request.POST['public_token']

    try:
        p=PlaidCredential.objects.get(user=request.user)
        request.session['access_token']=p.access_token
        return JsonResponse({'error':None,'access_token':p.access_token})
    except PlaidCredential.DoesNotExist:
        pass

    try:
        exchange_response=client.Item.public_token.exchange(public_token)
    except plaid.errros.PlaidError as e:
        return JsonResponse(e)
    
    request.seesion['access_token']=exchange_response['access_token']
    item_id=exchange_response['item_id']

    PlaidCredential.objects.create(user=request.user,
    access_token=exchange_response['access_token']).save()

    return JsonResponse(exchange_response)

@csrf_exempt
def info(request):
    if request.session['access_token']:
        access_token=request.session['access_token']
    else:
        access_token=None
    return JsonResponse({
        'item_id':item_id,
        'access_token':access_token,
        'products':PLAID_PRODUCTS,
    })

def _get_transactions(access_token, month=None,year=None):
    if not month and not year:
        given_date=datetime.datetime.today().date()
        start_date=str(given_date.replace(day=1))
        end_date='{:%Y-%m-%d}'.format(datetime.datetime.now())
    else:
        if month>=10:
            start_date=f'{str(year)}-{str(month)}-01'
            end_date=f'{str(year)}-{str(month)}-{calender.monthrange(year,month)[1]}'
        else:
            start_date=f'{str(year)}-0{str(month)}-01'
            end_date=f'{str(year)}-0{str(month)}-{calender.monthrange(year,month)[1]}'
    
    try:
        transaction_response=client.Transactions.get(access_token,start_date,end_date)
    except plaid.errors.PlaidError as e:
        return e
    
    return transaction_response

def get_transactions(request):
    month=request.GET.get('m')
    year=request.GET.get('y')

    return Jsonresponse(_get_transactions(access_token,month=m,year=y))