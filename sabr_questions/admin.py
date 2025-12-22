from django.contrib import admin
from .models import (
    PlacementTest,
    MCQQuestionSet, MCQQuestion,
    ReadingPassage, ReadingQuestion,
    ListeningAudio, ListeningQuestion,
    SpeakingVideo, SpeakingQuestion,
    WritingQuestion
)
admin.site.register(PlacementTest)
admin.site.register(MCQQuestionSet)
admin.site.register(MCQQuestion)
admin.site.register(ReadingPassage)
admin.site.register(ReadingQuestion)
admin.site.register(ListeningAudio)
admin.site.register(ListeningQuestion)
admin.site.register(SpeakingVideo)
admin.site.register(SpeakingQuestion)
admin.site.register(WritingQuestion)