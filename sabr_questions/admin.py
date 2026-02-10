from django.contrib import admin
from .models import (
    VocabularyQuestionSet,
    VocabularyQuestion,
    GrammarQuestionSet,
    GrammarQuestion,
    ReadingPassage,
    ReadingQuestion,
    ListeningAudio,
    ListeningQuestion,
    SpeakingVideo,
    SpeakingQuestion,
    WritingQuestion,
)

admin.site.register(VocabularyQuestionSet)
admin.site.register(VocabularyQuestion)

admin.site.register(GrammarQuestionSet)
admin.site.register(GrammarQuestion)

admin.site.register(ReadingPassage)
admin.site.register(ReadingQuestion)

admin.site.register(ListeningAudio)
admin.site.register(ListeningQuestion)

admin.site.register(SpeakingVideo)
admin.site.register(SpeakingQuestion)

admin.site.register(WritingQuestion)
