from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import (
    Level, Unit, Section, Lesson, Exercise,
    ExerciseMCQQuestion, ExerciseReadingPassage, ExerciseReadingQuestion,
    ExerciseListeningAudio, ExerciseListeningQuestion,
    ExerciseSpeakingVideo, ExerciseSpeakingQuestion,
    ExerciseWritingQuestion
)
from .serializers import (
    LevelSerializer, UnitSerializer, SectionSerializer, LessonSerializer,
    ExerciseSerializer, ExerciseMCQQuestionSerializer,
    ExerciseReadingPassageSerializer, ExerciseReadingQuestionSerializer,
    ExerciseListeningAudioSerializer, ExerciseListeningQuestionSerializer,
    ExerciseSpeakingVideoSerializer, ExerciseSpeakingQuestionSerializer,
    ExerciseWritingQuestionSerializer
)


# ============================================
# Level Views
# ============================================

class LevelListCreateAPIView(APIView):
    """
    GET: List all levels
    POST: Create new level
    """
    def get(self, request):
        levels = Level.objects.all()
        serializer = LevelSerializer(levels, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = LevelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LevelDetailAPIView(APIView):
    """
    GET: Retrieve single level
    PUT: Update level
    DELETE: Delete level
    """
    def get_object(self, pk):
        return get_object_or_404(Level, pk=pk)
    
    def get(self, request, pk):
        level = self.get_object(pk)
        serializer = LevelSerializer(level)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        level = self.get_object(pk)
        serializer = LevelSerializer(level, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        level = self.get_object(pk)
        level.delete()
        return Response({"message": "Level deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)


# ============================================
# Unit Views
# ============================================

class UnitListCreateAPIView(APIView):
    def get(self, request):
        units = Unit.objects.all()
        serializer = UnitSerializer(units, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = UnitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnitDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Unit, pk=pk)
    
    def get(self, request, pk):
        unit = self.get_object(pk)
        serializer = UnitSerializer(unit)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        unit = self.get_object(pk)
        serializer = UnitSerializer(unit, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        unit = self.get_object(pk)
        unit.delete()
        return Response({"message": "Unit deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)


# ============================================
# Section Views
# ============================================

class SectionListCreateAPIView(APIView):
    def get(self, request):
        sections = Section.objects.all()
        serializer = SectionSerializer(sections, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = SectionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SectionDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Section, pk=pk)
    
    def get(self, request, pk):
        section = self.get_object(pk)
        serializer = SectionSerializer(section)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        section = self.get_object(pk)
        serializer = SectionSerializer(section, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        section = self.get_object(pk)
        section.delete()
        return Response({"message": "Section deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)


# ============================================
# Lesson Views
# ============================================

class LessonListCreateAPIView(APIView):
    def get(self, request):
        lessons = Lesson.objects.all()
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = LessonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LessonDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Lesson, pk=pk)
    
    def get(self, request, pk):
        lesson = self.get_object(pk)
        serializer = LessonSerializer(lesson)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        lesson = self.get_object(pk)
        serializer = LessonSerializer(lesson, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        lesson = self.get_object(pk)
        lesson.delete()
        return Response({"message": "Lesson deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)


# ============================================
# Exercise Views
# ============================================

class ExerciseListCreateAPIView(APIView):
    def get(self, request):
        exercises = Exercise.objects.all()
        serializer = ExerciseSerializer(exercises, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ExerciseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(Exercise, pk=pk)
    
    def get(self, request, pk):
        exercise = self.get_object(pk)
        serializer = ExerciseSerializer(exercise)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        exercise = self.get_object(pk)
        serializer = ExerciseSerializer(exercise, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        exercise = self.get_object(pk)
        exercise.delete()
        return Response({"message": "Exercise deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)


# ============================================
# Exercise MCQ Question Views
# ============================================

class ExerciseMCQQuestionListCreateAPIView(APIView):
    def get(self, request):
        questions = ExerciseMCQQuestion.objects.all()
        serializer = ExerciseMCQQuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ExerciseMCQQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseMCQQuestionDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(ExerciseMCQQuestion, pk=pk)
    
    def get(self, request, pk):
        question = self.get_object(pk)
        serializer = ExerciseMCQQuestionSerializer(question)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        question = self.get_object(pk)
        serializer = ExerciseMCQQuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        question = self.get_object(pk)
        question.delete()
        return Response({"message": "MCQ Question deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)


# ============================================
# Exercise Reading Passage Views
# ============================================

class ExerciseReadingPassageListCreateAPIView(APIView):
    def get(self, request):
        passages = ExerciseReadingPassage.objects.all()
        serializer = ExerciseReadingPassageSerializer(passages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ExerciseReadingPassageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseReadingPassageDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(ExerciseReadingPassage, pk=pk)
    
    def get(self, request, pk):
        passage = self.get_object(pk)
        serializer = ExerciseReadingPassageSerializer(passage)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        passage = self.get_object(pk)
        serializer = ExerciseReadingPassageSerializer(passage, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        passage = self.get_object(pk)
        passage.delete()
        return Response({"message": "Reading Passage deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)


# ============================================
# Exercise Reading Question Views
# ============================================

class ExerciseReadingQuestionListCreateAPIView(APIView):
    def get(self, request):
        questions = ExerciseReadingQuestion.objects.all()
        serializer = ExerciseReadingQuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ExerciseReadingQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseReadingQuestionDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(ExerciseReadingQuestion, pk=pk)
    
    def get(self, request, pk):
        question = self.get_object(pk)
        serializer = ExerciseReadingQuestionSerializer(question)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        question = self.get_object(pk)
        serializer = ExerciseReadingQuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        question = self.get_object(pk)
        question.delete()
        return Response({"message": "Reading Question deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)


# ============================================
# Exercise Listening Audio Views
# ============================================

class ExerciseListeningAudioListCreateAPIView(APIView):
    def get(self, request):
        audios = ExerciseListeningAudio.objects.all()
        serializer = ExerciseListeningAudioSerializer(audios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ExerciseListeningAudioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseListeningAudioDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(ExerciseListeningAudio, pk=pk)
    
    def get(self, request, pk):
        audio = self.get_object(pk)
        serializer = ExerciseListeningAudioSerializer(audio)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        audio = self.get_object(pk)
        serializer = ExerciseListeningAudioSerializer(audio, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        audio = self.get_object(pk)
        audio.delete()
        return Response({"message": "Listening Audio deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)


# ============================================
# Exercise Listening Question Views
# ============================================

class ExerciseListeningQuestionListCreateAPIView(APIView):
    def get(self, request):
        questions = ExerciseListeningQuestion.objects.all()
        serializer = ExerciseListeningQuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ExerciseListeningQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseListeningQuestionDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(ExerciseListeningQuestion, pk=pk)
    
    def get(self, request, pk):
        question = self.get_object(pk)
        serializer = ExerciseListeningQuestionSerializer(question)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        question = self.get_object(pk)
        serializer = ExerciseListeningQuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        question = self.get_object(pk)
        question.delete()
        return Response({"message": "Listening Question deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)


# ============================================
# Exercise Speaking Video Views
# ============================================

class ExerciseSpeakingVideoListCreateAPIView(APIView):
    def get(self, request):
        videos = ExerciseSpeakingVideo.objects.all()
        serializer = ExerciseSpeakingVideoSerializer(videos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ExerciseSpeakingVideoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseSpeakingVideoDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(ExerciseSpeakingVideo, pk=pk)
    
    def get(self, request, pk):
        video = self.get_object(pk)
        serializer = ExerciseSpeakingVideoSerializer(video)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        video = self.get_object(pk)
        serializer = ExerciseSpeakingVideoSerializer(video, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        video = self.get_object(pk)
        video.delete()
        return Response({"message": "Speaking Video deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)


# ============================================
# Exercise Speaking Question Views
# ============================================

class ExerciseSpeakingQuestionListCreateAPIView(APIView):
    def get(self, request):
        questions = ExerciseSpeakingQuestion.objects.all()
        serializer = ExerciseSpeakingQuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ExerciseSpeakingQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseSpeakingQuestionDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(ExerciseSpeakingQuestion, pk=pk)
    
    def get(self, request, pk):
        question = self.get_object(pk)
        serializer = ExerciseSpeakingQuestionSerializer(question)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        question = self.get_object(pk)
        serializer = ExerciseSpeakingQuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        question = self.get_object(pk)
        question.delete()
        return Response({"message": "Speaking Question deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)


# ============================================
# Exercise Writing Question Views
# ============================================

class ExerciseWritingQuestionListCreateAPIView(APIView):
    def get(self, request):
        questions = ExerciseWritingQuestion.objects.all()
        serializer = ExerciseWritingQuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = ExerciseWritingQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseWritingQuestionDetailAPIView(APIView):
    def get_object(self, pk):
        return get_object_or_404(ExerciseWritingQuestion, pk=pk)
    
    def get(self, request, pk):
        question = self.get_object(pk)
        serializer = ExerciseWritingQuestionSerializer(question)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        question = self.get_object(pk)
        serializer = ExerciseWritingQuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        question = self.get_object(pk)
        question.delete()
        return Response({"message": "Writing Question deleted successfully"}, 
                       status=status.HTTP_204_NO_CONTENT)