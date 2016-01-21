from datetime import datetime

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render

from apps.projects.models import Project

from .models import Interview, Question, Answer
from .forms import InterviewCreateForm, QuestionForm


def interview(request, pk):
    interview = Interview.objects.get(pk=pk)
    return render(request, 'interviews/interview.html', {'interview': interview})


def interview_create(request):

    if request.method == 'POST':
        form = InterviewCreateForm(request.POST)
        form.fields["project"].queryset = Project.objects.filter(owner=request.user)

        if form.is_valid():
            interview = Interview()
            interview.project = form.cleaned_data['project']
            interview.title = form.cleaned_data['title']
            interview.save()

            return HttpResponseRedirect(reverse('interview_question', kwargs={
                'interview_id': interview.pk,
                'question_id': Question.objects.get_first_question().pk
            }))

    else:
        form = InterviewCreateForm()
        form.fields["project"].queryset = Project.objects.filter(owner=request.user)

    return render(request, 'interviews/interview_create.html', {'form': form})


def interview_question(request, interview_id, question_id):

    interview = Interview.objects.get(pk=interview_id)
    question = Question.objects.get(pk=question_id)

    if request.method == 'POST':
        form = QuestionForm(request.POST, question=question)

        if form.is_valid():
            answer = Answer(interview=interview, question=question)
            answer.answer = form.cleaned_data['answer']
            answer.save()

            return HttpResponseRedirect(reverse('interview_question', kwargs={'interview_id': interview.pk, 'question_id': question.pk + 1}))

    else:
        form = QuestionForm(question=question)

    return render(request, 'interviews/interview_question.html', {'form': form})


def interview_update(request, pk):
    return render(request, 'interviews/interview_update.html')


def interview_delete(request, pk):
    return render(request, 'interviews/interview_delete.html')
