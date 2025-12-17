from django.http import JsonResponse
from django.conf import settings
import openai

openai.api_key = settings.OPENAI_API_KEY

def chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée."}, status=405)

    user_message = request.POST.get("message")
    if not user_message:
        return JsonResponse({"error": "Message manquant."}, status=400)

    try:
        # Nouvelle syntaxe OpenAI >=1.0.0
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un assistant spécialisé en sport, alimentation saine et style de vie healthy."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200
        )
        answer = response.choices[0].message.content
        return JsonResponse({"answer": answer})

    except Exception as e:
        return JsonResponse({"error": f"Erreur OpenAI: {str(e)}"}, status=500)
        
from django.shortcuts import render

def chatb(request):
    return render(request, 'chatb.html')