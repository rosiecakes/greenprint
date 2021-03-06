#views.py
# Created On: 9/5/2016
# Created By: Matt Agresta
#-----------------------------------------------------------#
#Set up Environment
from django.shortcuts import render,redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from .forms import ExpensesForm, IncomeForm, EditForm, UserCreateForm
from .models import Items, BudgetData
from .budget import Budget

#VIew to load and validate registration form
def signup(request):
    if request.method == 'POST':
        #Figure out which button was pressed
        #Options: add_income, add_expense, edit_item, delete_item
        if request.POST.get("submit"):
            form = UserCreateForm(request.POST)
            if form.is_valid():
                user = form.save()
                #Log user in
                username = request.POST['username']
                password = request.POST['password1']
                user = authenticate(username=username, password=password)
                if user.is_active:
                    login(request, user)
                    # Redirect to a success page.
                    return redirect('home')
                #else - Disabled Account would go here
            else:
                temp = 'register.html'
                footer = 'New User'
                c = {'footer': footer,'form': form}
                return render(request, temp, c)
    else:
        form = UserCreateForm()
        temp = 'register.html'
        footer = 'New User'
        c = {'footer': footer,
             'form': form}
        return render(request, temp, c)

# Create your views here.
#View to hold account management
@login_required
def account_mgmt(request):
    if request.method == 'POST':
        #BUtton Options 
        #profile - Load Profile Form
        #categories - Load Categories Form
        #deldata - Delete all Items for user
        #delacct - Delete account
        #save - Get Form Name and save
        #Cancel - redirect back to this view
        if request.POST.get("cancel"):
            temp = 'manage.html'
            footer = ''
            is_get = True
            c = {'is_get': is_get,
                 'footer':footer}
            return render(request, temp, c)
            
        #Cancel back to home page
        elif request.POST.get("home"):
            return redirect('home')
        else:
            temp = 'manage.html'
            footer = 'This Feature is in Development!'
            c = {'footer':footer}
            return render(request, temp, c)
    #Accessed from link (GET)
    else:
        temp = 'manage.html'
        footer = ''
        #Variable to display menu buttons
        is_get = True
        c = {'is_get': is_get,
             'footer':footer}
        return render(request, temp, c)
    
    
#View to Add income and expenses
@login_required
def config(request):
    #uses config.html
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        #Figure out which button was pressed
        #Options: add_income, add_expense, edit_item, delete_item
        if request.POST.get("add_income"):
            #Render Income ModelForm
            footer = 'Adding Income'
            form = IncomeForm(initial={'itemType': 'income',
                                       'user': request.user})
            itemtype = 'Income'
            c = {'itemtype':itemtype,
                 'form':form,
                 'footer':form.fields['user'],}
            return render(request, 'config.html', c)
        elif request.POST.get("add_expense"):
            #Render Expense ModelForm
            footer = 'Adding Expense'
            itemtype = 'Expense'
            form = ExpensesForm(initial={'itemType': 'expense',
                                         'user': request.user})
            c = {'itemtype':itemtype,
                 'form':form,
                 'footer':footer,}
            return render(request, 'config.html', c)
        #Save button on config.html IncomeForm/Expenses Form
        elif request.POST.get("config_save"):
            #ExpensesForm submitted
            if 'expenseName' in request.POST:
                form = ExpensesForm(request.POST)
                #form.fields['user'] = request.user
                if form.is_valid():
                    form.save()
                    return redirect('home')
                else:
                    temp = 'config.html'     
                    footer = 'Expense Form Invalid'
                    c = {'form':form,
                         'footer':footer,}
                    return render(request, temp, c)
            #IncomeForm submitted
            else:
                form = IncomeForm(request.POST)
                #form.fields['user'] = request.user
                if form.is_valid():
                    form.save()
                    return redirect('home')
                else:
                    form = IncomeForm(request.POST)
                    temp = 'config.html'     
                    footer = 'Form Invalid'
                    c = {'form':form,
                         'footer':footer,}
                    return render(request, temp, c)
        #Cancel Button    
        else:
            return redirect('home')

    # if a GET (or any other method) we'll create a blank form
    else:
        footer = 'GET request'
        c = {'footer':footer,}
        return render(request, 'config.html', c)
#Home view - displays budget    
@login_required
def home(request):
    footer = '* Line item modified'
    Budget.update_data({'user': request.user,
                        'months':12})
    lineitems = Budget.build(request.user)
    c = {'lineitems': lineitems,
         'footer':footer,}
    return render(request, 'home.html', c)

#View to edit budget line items
@login_required
def edit(request, item_id):
    if request.method == 'POST':
    #Update button on on edititem.html EditForm
        if request.POST.get("edititem_update"):
            item = BudgetData.objects.get(pk=item_id)
            init = {'itemAmmount':item.itemAmmount,
                    'itemNote':item.itemNote}
            form = EditForm(request.POST, initial=init)
            if form.is_valid():
                #If Nothing has changed redirect to /payplanner
                changed = form.changed_data
                if len(changed) < 2:
                    return redirect('home')
                #If something has changed call update_line(), redirect home
                else:
                    #Get Radio button value if present, if not assign single
                    try:
                        editopt = request.POST['edit_opt']
                    except:
                        editopt = 'single'
                    #If future radio button selected    
                    if editopt == 'future':
                        #Update current and future dates()
                        junk,bunk = Budget.update_future(item,request.POST)
                        footer = ('NEW:%s   -   OLD:%s' % (junk,bunk))
                    #If All button selected    
                    elif editopt == 'all':
                        Budget.update_all(item,request.POST)
                    #If single or not present (implied single) update line
                    else:
                        Budget.update_line(item,request.POST)
                  
                    #Redirect to home
                    return redirect('home')
            #Form Not Valid
            else:
                temp = 'edititem.html'
                name = item.parentItem.itemName.rstrip('*')
                notsingle = True
                if item.parentItem.payCycle.cycleName == 'Single':
                    notsingle = False
                footer = ('Edit %s' % name)
                c = {'itemid': item_id,
                     'name':name,
                     'notsingle':notsingle,
                     'form':form,
                     'footer':footer,}
                #Indent this when done with updating line items
                return render(request, temp, c)
            
        #Delete button on on edititem.html EditForm
        elif request.POST.get("edititem_delete"):
            item = BudgetData.objects.get(pk=item_id)
            #Get Radio button value if present, if not assign single
            try:
                editopt = request.POST['edit_opt']
            except:
                editopt = 'single'
            Budget.delete_item(item,editopt)
            return redirect('home')
        #Any other POST request
        else:
            return redirect('home')
    #Get Request (First call from home page)    
    else:
        temp = 'edititem.html'
        item = BudgetData.objects.get(pk=item_id)
        notsingle = True
        if item.parentItem.payCycle.cycleName == 'Single':
            notsingle = False
        form = EditForm(instance=item)
        name = item.parentItem.itemName.rstrip('*')
        footer = ('Edit %s' % name)
        c = {'itemid': item_id,
             'name':name,
             'notsingle':notsingle,
             'form':form,
             'footer':footer,}
        return render(request, temp, c)

                
    
