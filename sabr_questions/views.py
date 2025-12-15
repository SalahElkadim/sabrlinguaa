from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import (
    PlacementTest, MCQQuestionSet, MCQQuestion,
    ReadingPassage, ReadingQuestion,
    ListeningAudio, ListeningQuestion,
    SpeakingVideo, SpeakingQuestion,
    WritingQuestion
)
from .serializers import (
    PlacementTestListSerializer, PlacementTestDetailSerializer,
    MCQQuestionSetSerializer, MCQQuestionSerializer,
    ReadingPassageSerializer, ReadingQuestionSerializer,
    ListeningAudioSerializer, ListeningQuestionSerializer,
    SpeakingVideoSerializer, SpeakingQuestionSerializer,
    WritingQuestionSerializer
)


# ============================================
# Placement Test Views
# ============================================

class PlacementTestListCreateView(APIView):
    """قائمة وإنشاء امتحانات تحديد المستوى"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tests = PlacementTest.objects.all()
        serializer = PlacementTestListSerializer(tests, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PlacementTestDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlacementTestDetailView(APIView):
    """عرض وتعديل وحذف امتحان تحديد المستوى"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        test = get_object_or_404(PlacementTest, pk=pk)
        serializer = PlacementTestDetailSerializer(test)
        return Response(serializer.data)

    def put(self, request, pk):
        test = get_object_or_404(PlacementTest, pk=pk)
        serializer = PlacementTestDetailSerializer(test, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        test = get_object_or_404(PlacementTest, pk=pk)
        serializer = PlacementTestDetailSerializer(test, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        test = get_object_or_404(PlacementTest, pk=pk)
        test.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# MCQ Question Set Views
# ============================================

class MCQQuestionSetListCreateView(APIView):
    """قائمة وإنشاء مجموعات أسئلة MCQ"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        question_sets = MCQQuestionSet.objects.all()
        placement_test_id = request.query_params.get('placement_test')
        if placement_test_id:
            question_sets = question_sets.filter(placement_test_id=placement_test_id)
        serializer = MCQQuestionSetSerializer(question_sets, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = MCQQuestionSetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MCQQuestionSetDetailView(APIView):
    """عرض وتعديل وحذف مجموعة أسئلة MCQ"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        question_set = get_object_or_404(MCQQuestionSet, pk=pk)
        serializer = MCQQuestionSetSerializer(question_set)
        return Response(serializer.data)

    def put(self, request, pk):
        question_set = get_object_or_404(MCQQuestionSet, pk=pk)
        serializer = MCQQuestionSetSerializer(question_set, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        question_set = get_object_or_404(MCQQuestionSet, pk=pk)
        serializer = MCQQuestionSetSerializer(question_set, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        question_set = get_object_or_404(MCQQuestionSet, pk=pk)
        question_set.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# MCQ Question Views
# ============================================

class MCQQuestionListCreateView(APIView):
    """قائمة وإنشاء أسئلة MCQ"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questions = MCQQuestion.objects.all()
        question_set_id = request.query_params.get('question_set')
        if question_set_id:
            questions = questions.filter(question_set_id=question_set_id)
        serializer = MCQQuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = MCQQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MCQQuestionDetailView(APIView):
    """عرض وتعديل وحذف سؤال MCQ"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        question = get_object_or_404(MCQQuestion, pk=pk)
        serializer = MCQQuestionSerializer(question)
        return Response(serializer.data)

    def put(self, request, pk):
        question = get_object_or_404(MCQQuestion, pk=pk)
        serializer = MCQQuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        question = get_object_or_404(MCQQuestion, pk=pk)
        serializer = MCQQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        question = get_object_or_404(MCQQuestion, pk=pk)
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# Reading Passage Views
# ============================================

class ReadingPassageListCreateView(APIView):
    """قائمة وإنشاء قطع القراءة"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        passages = ReadingPassage.objects.all()
        placement_test_id = request.query_params.get('placement_test')
        if placement_test_id:
            passages = passages.filter(placement_test_id=placement_test_id)
        serializer = ReadingPassageSerializer(passages, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ReadingPassageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReadingPassageDetailView(APIView):
    """عرض وتعديل وحذف قطعة قراءة"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        passage = get_object_or_404(ReadingPassage, pk=pk)
        serializer = ReadingPassageSerializer(passage)
        return Response(serializer.data)

    def put(self, request, pk):
        passage = get_object_or_404(ReadingPassage, pk=pk)
        serializer = ReadingPassageSerializer(passage, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        passage = get_object_or_404(ReadingPassage, pk=pk)
        serializer = ReadingPassageSerializer(passage, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        passage = get_object_or_404(ReadingPassage, pk=pk)
        passage.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# Reading Question Views
# ============================================

class ReadingQuestionListCreateView(APIView):
    """قائمة وإنشاء أسئلة القراءة"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questions = ReadingQuestion.objects.all()
        passage_id = request.query_params.get('passage')
        if passage_id:
            questions = questions.filter(passage_id=passage_id)
        serializer = ReadingQuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ReadingQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReadingQuestionDetailView(APIView):
    """عرض وتعديل وحذف سؤال قراءة"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        question = get_object_or_404(ReadingQuestion, pk=pk)
        serializer = ReadingQuestionSerializer(question)
        return Response(serializer.data)

    def put(self, request, pk):
        question = get_object_or_404(ReadingQuestion, pk=pk)
        serializer = ReadingQuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        question = get_object_or_404(ReadingQuestion, pk=pk)
        serializer = ReadingQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        question = get_object_or_404(ReadingQuestion, pk=pk)
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# Listening Audio Views
# ============================================

class ListeningAudioListCreateView(APIView):
    """قائمة وإنشاء التسجيلات الصوتية"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        audios = ListeningAudio.objects.all()
        placement_test_id = request.query_params.get('placement_test')
        if placement_test_id:
            audios = audios.filter(placement_test_id=placement_test_id)
        serializer = ListeningAudioSerializer(audios, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ListeningAudioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListeningAudioDetailView(APIView):
    """عرض وتعديل وحذف تسجيل صوتي"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        audio = get_object_or_404(ListeningAudio, pk=pk)
        serializer = ListeningAudioSerializer(audio)
        return Response(serializer.data)

    def put(self, request, pk):
        audio = get_object_or_404(ListeningAudio, pk=pk)
        serializer = ListeningAudioSerializer(audio, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        audio = get_object_or_404(ListeningAudio, pk=pk)
        serializer = ListeningAudioSerializer(audio, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        audio = get_object_or_404(ListeningAudio, pk=pk)
        audio.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# Listening Question Views
# ============================================

class ListeningQuestionListCreateView(APIView):
    """قائمة وإنشاء أسئلة الاستماع"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questions = ListeningQuestion.objects.all()
        audio_id = request.query_params.get('audio')
        if audio_id:
            questions = questions.filter(audio_id=audio_id)
        serializer = ListeningQuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ListeningQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListeningQuestionDetailView(APIView):
    """عرض وتعديل وحذف سؤال استماع"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        question = get_object_or_404(ListeningQuestion, pk=pk)
        serializer = ListeningQuestionSerializer(question)
        return Response(serializer.data)

    def put(self, request, pk):
        question = get_object_or_404(ListeningQuestion, pk=pk)
        serializer = ListeningQuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        question = get_object_or_404(ListeningQuestion, pk=pk)
        serializer = ListeningQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        question = get_object_or_404(ListeningQuestion, pk=pk)
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# Speaking Video Views
# ============================================

class SpeakingVideoListCreateView(APIView):
    """قائمة وإنشاء فيديوهات التحدث"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        videos = SpeakingVideo.objects.all()
        placement_test_id = request.query_params.get('placement_test')
        if placement_test_id:
            videos = videos.filter(placement_test_id=placement_test_id)
        serializer = SpeakingVideoSerializer(videos, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SpeakingVideoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SpeakingVideoDetailView(APIView):
    """عرض وتعديل وحذف فيديو تحدث"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        video = get_object_or_404(SpeakingVideo, pk=pk)
        serializer = SpeakingVideoSerializer(video)
        return Response(serializer.data)

    def put(self, request, pk):
        video = get_object_or_404(SpeakingVideo, pk=pk)
        serializer = SpeakingVideoSerializer(video, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        video = get_object_or_404(SpeakingVideo, pk=pk)
        serializer = SpeakingVideoSerializer(video, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        video = get_object_or_404(SpeakingVideo, pk=pk)
        video.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# Speaking Question Views
# ============================================

class SpeakingQuestionListCreateView(APIView):
    """قائمة وإنشاء أسئلة التحدث"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questions = SpeakingQuestion.objects.all()
        video_id = request.query_params.get('video')
        if video_id:
            questions = questions.filter(video_id=video_id)
        serializer = SpeakingQuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SpeakingQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SpeakingQuestionDetailView(APIView):
    """عرض وتعديل وحذف سؤال تحدث"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        question = get_object_or_404(SpeakingQuestion, pk=pk)
        serializer = SpeakingQuestionSerializer(question)
        return Response(serializer.data)

    def put(self, request, pk):
        question = get_object_or_404(SpeakingQuestion, pk=pk)
        serializer = SpeakingQuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        question = get_object_or_404(SpeakingQuestion, pk=pk)
        serializer = SpeakingQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        question = get_object_or_404(SpeakingQuestion, pk=pk)
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# Writing Question Views
# ============================================

class WritingQuestionListCreateView(APIView):
    """قائمة وإنشاء أسئلة الكتابة"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questions = WritingQuestion.objects.all()
        placement_test_id = request.query_params.get('placement_test')
        if placement_test_id:
            questions = questions.filter(placement_test_id=placement_test_id)
        serializer = WritingQuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = WritingQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WritingQuestionDetailView(APIView):
    """عرض وتعديل وحذف سؤال كتابة"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        question = get_object_or_404(WritingQuestion, pk=pk)
        serializer = WritingQuestionSerializer(question)
        return Response(serializer.data)

    def put(self, request, pk):
        question = get_object_or_404(WritingQuestion, pk=pk)
        serializer = WritingQuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        question = get_object_or_404(WritingQuestion, pk=pk)
        serializer = WritingQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        question = get_object_or_404(WritingQuestion, pk=pk)
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)