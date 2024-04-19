from django.shortcuts import render, redirect
from django.http import HttpResponse

# Create your views here.
def home(request):
    return render(request, "home.html", {})

def results(request):
    if request.method == 'POST':
        age = request.POST.get('ageInput')
        print(age)
        conditions =  request.POST.get('conditionsTextarea')
        race = request.POST.get('raceSelect')
        gender = request.POST.get('gender', 'Not specified')

        return render(request, 'results.html', {
            'age': age,
            'conditions': conditions,
            'race': race,
            'gender': gender
        })
    else:
        return HttpResponse("Invalid request", status=400)


        
        
