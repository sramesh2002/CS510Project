from django.shortcuts import render, redirect
from django.http import HttpResponse
import pandas as pd
import openai
import json


patients = pd.read_csv('PredictorApp/patients.csv')
admissions = pd.read_csv('PredictorApp/admissions.csv')
notes = pd.read_csv('PredictorApp/discharge.csv')

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm
from django.contrib import messages

# Create your views here.
def home(request):
    return render(request, 'home.html')

def results(request):
    if request.method == 'POST':
        age = request.POST.get('ageInput')
        conditions = request.POST.get('conditionsTextarea')
        race = request.POST.get('raceSelect')
        gender = request.POST.get('gender', 'Not specified')

        health_prediction = get_results_from_model(age, conditions, race, gender)
        health_prediction = str(health_prediction)
        health_prediction = health_prediction.replace("Name: count, dtype: float64", "")
        prediction_list = [item.replace('"', '').strip() for item in health_prediction.split('\n') if item.strip()]
        return render(request, 'results.html', {
            'age': age,
            'conditions': conditions,
            'race': race,
            'gender': gender,
            'prediction': prediction_list,
        })
    else:
        return HttpResponse("Invalid request", status=400)


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('home')  # Explicit redirect to 'home'
            else:
                return HttpResponse("Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')  # Redirect back to login page

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, "Signup successful! You can now log in.")
            return redirect('home')
        else:
            messages.error(request, "Signup failed. Please correct the errors below.")         
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})
        

def get_results_from_model(age, conditions, race, gender):
    # make these run initially at app start instead

    filtered_data = filter_data(age, gender[0], race)
    openai.api_type = "azure"
    openai.api_base = "https://mol-qa.openai.azure.com/"
    openai.api_version = "2023-07-01-preview"
    openai.api_key = None #YOUR OWN API KEY
    
    # call search data
    search_data(filtered_data, conditions)
    return top_five_diseases_weighted("clinical_notes_diseases_preconditions.csv")

def process_prompt(prompt):

    message_text = [{"role":"system","content":"You are an AI assistant that helps in medical information"},{"role":"user","content": prompt}]

    completion = openai.ChatCompletion.create(
      engine="gpt35turbo",
      messages = message_text,
      temperature=0.1,
      top_p=0.95,
      frequency_penalty=0,
      presence_penalty=0,
      stop=None
    )

    sample = completion.choices[0].message.content

    return sample


def filter_data(age,gender,race):

  filtered_patients = patients[(patients['anchor_age']== int(age)) & (patients['gender']=='F')]

  filtered_admissions = admissions[admissions['race']=='WHITE']

#   print(filtered_patients, filtered_admissions)

  merged_data = pd.merge(filtered_patients, filtered_admissions, on="subject_id")

  return merged_data


def search_data(filtered_data, preconditions):
  
  sample_filtered_data = filtered_data
  if not filtered_data.empty:
    sample_filtered_data = filtered_data.sample(n=3, random_state=42)
  
  
#   sample_filtered_data = filtered_data.sample(n=3, random_state=42)

  filtered_notes = pd.merge(notes,sample_filtered_data, on="subject_id")

  results = []

  for index, row in filtered_notes.iterrows():

    note = row['text']

    #print(len(note))
    #print("before")
    #removing discharge intructions (not related) to minimize the number of tokens
    """i = note.find("Discharge Instructions:")
    note = note[:i]

    # Find and remove the Allergies section
    start_allergies = note.find("Allergies:")
    end_allergies = note.find("\n", start_allergies)
    if start_allergies != -1 and end_allergies != -1:
        note = note[:start_allergies] + note[end_allergies:]

    # Find and remove the Allergies section
    start_allergies = note.find("Physical Exam:")
    end_allergies = note.find("\n", start_allergies)
    if start_allergies != -1 and end_allergies != -1:
        note = note[:start_allergies] + note[end_allergies:]"""

    #print(len(note))
    #print("after")
    # print(note)

    if len(note)<12500:

      prompt = f"""

      Given the clinical note: "{note}":

      1. Extract all the list of diseases and preconditions mentioned in the clinical note
      2. Based on the extracted list of preconditions, compare it to the given preconditions:"{preconditions}", and if any of precondition matched, then return the mtched preconditions mentioned in the clinical note
      3. Based on the matched preconditions, predict the most likely diseases that the patient might encounter in the future
      """
      # Process each segment with the prompt
      gpt_response = process_prompt(prompt)

      #print(gpt_response)
      #print("\n\n\n\n\n\n\n\n--------")


      # Store the results in a dictionary
      results.append({
          "Subject_Id": row['subject_id'],
          "note": note,
          "preconditions": preconditions,
          "gpt_response": gpt_response
      })

    #   print(results)
    #   print("\n\n\n\n\n")

  # Convert the list of dictionaries to a DataFrame
  results_df = pd.DataFrame(results)

  # Save the DataFrame to a CSV file
  results_df.to_csv('clinical_notes_diseases_preconditions.csv', index=False)


#scoring (new diseases other than preconditions (have higher weight))

def top_five_diseases_weighted(csv_file_path):
    # Load CSV
    data = pd.read_csv(csv_file_path)

    # Extract all predicted diseases into a single list
    all_diseases = []
    for diseases in data['gpt_response']:
        # Assuming the gpt_response is a string that includes disease predictions, e.g., "- Fibromyalgia - GERD - Hypertension"
        # We need to extract the diseases from each entry
        current_diseases = diseases.splitlines()
        for disease in current_diseases:
            if disease.strip().startswith('-'):
                # Remove the dash and extra spaces
                clean_disease = disease.strip()[1:].strip()
                all_diseases.append(clean_disease)

    # Frequency count of each disease
    disease_counts = pd.Series(all_diseases).value_counts()

    # Calculate MLE for each disease by dividing count by total diseases reported
    total_diseases = disease_counts.sum()
    mle = disease_counts / total_diseases

    preconditions = data['preconditions'][0].replace(" ","").split(",")

    for i, v in mle.items():
      if i in preconditions:
        #Punishment to repeating preconditions
        mle[i] = v*0.5


    # Sort by MLE in descending order and get top 5
    top_five = mle.sort_values(ascending=False).head(5)
    
    return top_five
