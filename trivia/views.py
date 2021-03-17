from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.exceptions import SuspiciousOperation
from django.conf import settings

from twilio.twiml.voice_response import VoiceResponse, Pause

from pyopentdb import OpenTDBClient, QuestionType, Difficulty

from twilio.request_validator import RequestValidator

request_validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)


def validate_django_request(request: HttpRequest):
    try:
        signature = request.META["HTTP_X_TWILIO_SIGNATURE"]
    except KeyError:
        is_valid_twilio_request = False
    else:
        is_valid_twilio_request = request_validator.validate(
            signature=signature,
            uri=request.get_raw_uri(),
            params=request.POST,
        )
    if not is_valid_twilio_request:
        # Invalid request from Twilio
        raise SuspiciousOperation()


@csrf_exempt
def question(request: HttpRequest) -> HttpResponse:
    validate_django_request(request)
    vr = VoiceResponse()
    vr.say("Welcome to Trivia IVR!")

    client = OpenTDBClient()
    questions = client.get_questions(
        amount=1, question_type=QuestionType.MULTIPLE, difficulty=Difficulty.EASY
    ).to_serializable(as_json=False)

    with vr.gather(
        action=reverse("outcome"),
        numDigits=1,
        timeout=60,
    ) as gather:
        gather.say(f"Alright heres your question. {questions[0]['question']}.")
        index = 1
        for i in questions[0]["choices"]:
            gather.pause(length=1)
            gather.say(f"for {i}, press {index}.")
            index += 1

    request.session["answer"] = questions[0]["answer"]
    request.session["answer_index"] = questions[0]["answer_index"]

    vr.say("We did not receive your selection")
    vr.redirect("")

    return HttpResponse(str(vr), content_type="text/xml")


@csrf_exempt
def outcome(request: HttpRequest) -> HttpResponse:
    validate_django_request(request)
    vr = VoiceResponse()

    digits = request.POST.get("Digits")
    answer = request.session["answer"]
    answer_index = request.session["answer_index"] + 1

    if int(digits) == answer_index:
        vr.say("Congratulations! you got this question correct!")
    else:
        vr.say(f"Sorry. The answer we were looking for was {answer}.")

    vr.say("Please call again soon!")

    return HttpResponse(str(vr), content_type="text/xml")
