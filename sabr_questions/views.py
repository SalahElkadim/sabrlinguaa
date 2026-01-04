from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum
import cloudinary.uploader

from .models import (
    PlacementTest, MCQQuestionSet, MCQQuestion,
    ReadingPassage, ReadingQuestion,
    ListeningAudio, ListeningQuestion,
    SpeakingVideo, SpeakingQuestion,
    WritingQuestion
)
from .serializers import (
    PlacementTestListSerializer, PlacementTestDetailSerializer,
    PlacementTestCreateSerializer,
    MCQQuestionSetSerializer, MCQQuestionSetCreateSerializer,
    MCQQuestionSerializer,
    ReadingPassageSerializer, ReadingPassageCreateSerializer,
    ReadingQuestionSerializer,
    ListeningAudioSerializer, ListeningAudioCreateSerializer,
    ListeningQuestionSerializer,
    SpeakingVideoSerializer, SpeakingVideoCreateSerializer,
    SpeakingQuestionSerializer,
    WritingQuestionSerializer
)


# ============================================
# Placement Test Views
# ============================================

class PlacementTestListCreateAPIView(APIView):
    """
    GET: قائمة جميع الامتحانات
    POST: إنشاء امتحان جديد
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """الحصول على قائمة الامتحانات"""
        tests = PlacementTest.objects.all()
        
        # فلترة حسب الحالة
        is_active = request.query_params.get('is_active', None)
        if is_active is not None:
            tests = tests.filter(is_active=is_active.lower() == 'true')
        
        serializer = PlacementTestListSerializer(tests, many=True)
        return Response({
            'success': True,
            'count': tests.count(),
            'data': serializer.data
        })
    
    def post(self, request):
        """إنشاء امتحان جديد"""
        serializer = PlacementTestCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            test = serializer.save()
            detail_serializer = PlacementTestDetailSerializer(test)
            return Response({
                'success': True,
                'message': 'تم إنشاء الامتحان بنجاح',
                'data': detail_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PlacementTestDetailAPIView(APIView):
    """
    GET: تفاصيل امتحان محدد
    PUT: تحديث امتحان
    DELETE: حذف امتحان
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request, pk):
        """الحصول على تفاصيل امتحان"""
        test = get_object_or_404(PlacementTest, pk=pk)
        serializer = PlacementTestDetailSerializer(test)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request, pk):
        """تحديث امتحان"""
        test = get_object_or_404(PlacementTest, pk=pk)
        serializer = PlacementTestCreateSerializer(test, data=request.data, partial=True)
        
        if serializer.is_valid():
            test = serializer.save()
            detail_serializer = PlacementTestDetailSerializer(test)
            return Response({
                'success': True,
                'message': 'تم تحديث الامتحان بنجاح',
                'data': detail_serializer.data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """حذف امتحان"""
        test = get_object_or_404(PlacementTest, pk=pk)
        test.delete()
        return Response({
            'success': True,
            'message': 'تم حذف الامتحان بنجاح'
        }, status=status.HTTP_200_OK)


# ============================================
# MCQ Question Set Views
# ============================================

class MCQQuestionSetListCreateAPIView(APIView):
    """
    GET: قائمة مجموعات أسئلة MCQ
    POST: إنشاء مجموعة جديدة
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """الحصول على قائمة المجموعات"""
        test_id = request.query_params.get('test_id', None)
        
        if test_id:
            question_sets = MCQQuestionSet.objects.filter(placement_test_id=test_id)
        else:
            question_sets = MCQQuestionSet.objects.all()
        
        serializer = MCQQuestionSetSerializer(question_sets, many=True)
        return Response({
            'success': True,
            'count': question_sets.count(),
            'data': serializer.data
        })
    
    def post(self, request):
        """إنشاء مجموعة أسئلة جديدة"""
        serializer = MCQQuestionSetCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            question_set = serializer.save()
            detail_serializer = MCQQuestionSetSerializer(question_set)
            return Response({
                'success': True,
                'message': 'تم إنشاء مجموعة الأسئلة بنجاح',
                'data': detail_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MCQQuestionSetDetailAPIView(APIView):
    """
    GET: تفاصيل مجموعة أسئلة
    PUT: تحديث مجموعة
    DELETE: حذف مجموعة
    """
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request, pk):
        """الحصول على تفاصيل المجموعة"""
        question_set = get_object_or_404(MCQQuestionSet, pk=pk)
        serializer = MCQQuestionSetSerializer(question_set)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request, pk):
        """تحديث المجموعة"""
        question_set = get_object_or_404(MCQQuestionSet, pk=pk)
        serializer = MCQQuestionSetCreateSerializer(
            question_set, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            question_set = serializer.save()
            detail_serializer = MCQQuestionSetSerializer(question_set)
            return Response({
                'success': True,
                'message': 'تم تحديث المجموعة بنجاح',
                'data': detail_serializer.data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """حذف المجموعة"""
        question_set = get_object_or_404(MCQQuestionSet, pk=pk)
        question_set.delete()
        return Response({
            'success': True,
            'message': 'تم حذف المجموعة بنجاح'
        }, status=status.HTTP_204_NO_CONTENT)


# ============================================
# MCQ Question Views
# ============================================

class MCQQuestionListCreateAPIView(APIView):
    """
    GET: قائمة أسئلة MCQ
    POST: إضافة سؤال جديد
    """
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request):
        """الحصول على قائمة الأسئلة"""
        set_id = request.query_params.get('set_id', None)
        
        if set_id:
            questions = MCQQuestion.objects.filter(question_set_id=set_id)
        else:
            questions = MCQQuestion.objects.all()
        
        serializer = MCQQuestionSerializer(questions, many=True)
        return Response({
            'success': True,
            'count': questions.count(),
            'data': serializer.data
        })
    
    def post(self, request):
        """إضافة سؤال جديد"""
        serializer = MCQQuestionSerializer(data=request.data)
        
        if serializer.is_valid():
            question = serializer.save()
            return Response({
                'success': True,
                'message': 'تم إضافة السؤال بنجاح',
                'data': MCQQuestionSerializer(question).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class MCQQuestionDetailAPIView(APIView):
    """
    GET: تفاصيل سؤال
    PUT: تحديث سؤال
    DELETE: حذف سؤال
    """
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request, pk):
        """الحصول على تفاصيل السؤال"""
        question = get_object_or_404(MCQQuestion, pk=pk)
        serializer = MCQQuestionSerializer(question)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request, pk):
        """تحديث السؤال"""
        question = get_object_or_404(MCQQuestion, pk=pk)
        serializer = MCQQuestionSerializer(question, data=request.data, partial=True)
        
        if serializer.is_valid():
            question = serializer.save()
            return Response({
                'success': True,
                'message': 'تم تحديث السؤال بنجاح',
                'data': MCQQuestionSerializer(question).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """حذف السؤال"""
        question = get_object_or_404(MCQQuestion, pk=pk)
        question.delete()
        return Response({
            'success': True,
            'message': 'تم حذف السؤال بنجاح'
        }, status=status.HTTP_204_NO_CONTENT)


# ============================================
# Reading Passage Views
# ============================================

class ReadingPassageListCreateAPIView(APIView):
    """
    GET: قائمة قطع القراءة
    POST: إضافة قطعة جديدة
    """
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request):
        """الحصول على قائمة القطع"""
        test_id = request.query_params.get('test_id', None)
        
        if test_id:
            passages = ReadingPassage.objects.filter(placement_test_id=test_id)
        else:
            passages = ReadingPassage.objects.all()
        
        serializer = ReadingPassageSerializer(passages, many=True)
        return Response({
            'success': True,
            'count': passages.count(),
            'data': serializer.data
        })
    
    def post(self, request):
        """إضافة قطعة جديدة"""
        serializer = ReadingPassageCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            passage = serializer.save()
            detail_serializer = ReadingPassageSerializer(passage)
            return Response({
                'success': True,
                'message': 'تم إضافة القطعة بنجاح',
                'data': detail_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ReadingPassageDetailAPIView(APIView):
    """
    GET: تفاصيل قطعة قراءة
    PUT: تحديث قطعة
    DELETE: حذف قطعة
    """
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request, pk):
        """الحصول على تفاصيل القطعة"""
        passage = get_object_or_404(ReadingPassage, pk=pk)
        serializer = ReadingPassageSerializer(passage)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request, pk):
        """تحديث القطعة"""
        passage = get_object_or_404(ReadingPassage, pk=pk)
        serializer = ReadingPassageCreateSerializer(
            passage, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            passage = serializer.save()
            detail_serializer = ReadingPassageSerializer(passage)
            return Response({
                'success': True,
                'message': 'تم تحديث القطعة بنجاح',
                'data': detail_serializer.data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """حذف القطعة"""
        passage = get_object_or_404(ReadingPassage, pk=pk)
        passage.delete()
        return Response({
            'success': True,
            'message': 'تم حذف القطعة بنجاح'
        }, status=status.HTTP_204_NO_CONTENT)


# ============================================
# Reading Question Views
# ============================================

class ReadingQuestionListCreateAPIView(APIView):
    """
    GET: قائمة أسئلة القراءة
    POST: إضافة سؤال جديد
    """
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request):
        """الحصول على قائمة الأسئلة"""
        passage_id = request.query_params.get('passage_id', None)
        
        if passage_id:
            questions = ReadingQuestion.objects.filter(passage_id=passage_id)
        else:
            questions = ReadingQuestion.objects.all()
        
        serializer = ReadingQuestionSerializer(questions, many=True)
        return Response({
            'success': True,
            'count': questions.count(),
            'data': serializer.data
        })
    
    def post(self, request):
        """إضافة سؤال جديد"""
        serializer = ReadingQuestionSerializer(data=request.data)
        
        if serializer.is_valid():
            question = serializer.save()
            return Response({
                'success': True,
                'message': 'تم إضافة السؤال بنجاح',
                'data': ReadingQuestionSerializer(question).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ReadingQuestionDetailAPIView(APIView):
    """
    GET: تفاصيل سؤال قراءة
    PUT: تحديث سؤال
    DELETE: حذف سؤال
    """
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request, pk):
        """الحصول على تفاصيل السؤال"""
        question = get_object_or_404(ReadingQuestion, pk=pk)
        serializer = ReadingQuestionSerializer(question)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request, pk):
        """تحديث السؤال"""
        question = get_object_or_404(ReadingQuestion, pk=pk)
        serializer = ReadingQuestionSerializer(
            question, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            question = serializer.save()
            return Response({
                'success': True,
                'message': 'تم تحديث السؤال بنجاح',
                'data': ReadingQuestionSerializer(question).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """حذف السؤال"""
        question = get_object_or_404(ReadingQuestion, pk=pk)
        question.delete()
        return Response({
            'success': True,
            'message': 'تم حذف السؤال بنجاح'
        }, status=status.HTTP_204_NO_CONTENT)


# ============================================
# Listening Audio Views
# ============================================

class ListeningAudioListCreateAPIView(APIView):
    """
    GET: قائمة التسجيلات الصوتية
    POST: إضافة تسجيل جديد
    """
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request):
        """الحصول على قائمة التسجيلات"""
        test_id = request.query_params.get('test_id', None)
        
        if test_id:
            audios = ListeningAudio.objects.filter(placement_test_id=test_id)
        else:
            audios = ListeningAudio.objects.all()
        
        serializer = ListeningAudioSerializer(audios, many=True)
        return Response({
            'success': True,
            'count': audios.count(),
            'data': serializer.data
        })
    
    def post(self, request):
        """إضافة تسجيل جديد"""
        serializer = ListeningAudioCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            audio = serializer.save()
            detail_serializer = ListeningAudioSerializer(audio)
            return Response({
                'success': True,
                'message': 'تم إضافة التسجيل بنجاح',
                'data': detail_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ListeningAudioDetailAPIView(APIView):
    """
    GET: تفاصيل تسجيل صوتي
    PUT: تحديث تسجيل
    DELETE: حذف تسجيل
    """
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request, pk):
        """الحصول على تفاصيل التسجيل"""
        audio = get_object_or_404(ListeningAudio, pk=pk)
        serializer = ListeningAudioSerializer(audio)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request, pk):
        """تحديث التسجيل"""
        audio = get_object_or_404(ListeningAudio, pk=pk)
        serializer = ListeningAudioCreateSerializer(
            audio, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            audio = serializer.save()
            detail_serializer = ListeningAudioSerializer(audio)
            return Response({
                'success': True,
                'message': 'تم تحديث التسجيل بنجاح',
                'data': detail_serializer.data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """حذف التسجيل"""
        audio = get_object_or_404(ListeningAudio, pk=pk)
        audio.delete()
        return Response({
            'success': True,
            'message': 'تم حذف التسجيل بنجاح'
        }, status=status.HTTP_204_NO_CONTENT)


# ============================================
# Listening Question Views
# ============================================

class ListeningQuestionListCreateAPIView(APIView):
    """
    GET: قائمة أسئلة الاستماع
    POST: إضافة سؤال جديد
    """
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request):
        """الحصول على قائمة الأسئلة"""
        audio_id = request.query_params.get('audio_id', None)
        
        if audio_id:
            questions = ListeningQuestion.objects.filter(audio_id=audio_id)
        else:
            questions = ListeningQuestion.objects.all()
        
        serializer = ListeningQuestionSerializer(questions, many=True)
        return Response({
            'success': True,
            'count': questions.count(),
            'data': serializer.data
        })
    
    def post(self, request):
        """إضافة سؤال جديد"""
        serializer = ListeningQuestionSerializer(data=request.data)
        
        if serializer.is_valid():
            question = serializer.save()
            return Response({
                'success': True,
                'message': 'تم إضافة السؤال بنجاح',
                'data': ListeningQuestionSerializer(question).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ListeningQuestionDetailAPIView(APIView):
    """
    GET: تفاصيل سؤال استماع
    PUT: تحديث سؤال
    DELETE: حذف سؤال
    """
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request, pk):
        """الحصول على تفاصيل السؤال"""
        question = get_object_or_404(ListeningQuestion, pk=pk)
        serializer = ListeningQuestionSerializer(question)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def put(self, request, pk):
        """تحديث السؤال"""
        question = get_object_or_404(ListeningQuestion, pk=pk)
        serializer = ListeningQuestionSerializer(
            question, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            question = serializer.save()
            return Response({
                'success': True,
                'message': 'تم تحديث السؤال بنجاح',
                'data': ListeningQuestionSerializer(question).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """حذف السؤال"""
        question = get_object_or_404(ListeningQuestion, pk=pk)
        question.delete()
        return Response({
            'success': True,
            'message': 'تم حذف السؤال بنجاح'
        }, status=status.HTTP_204_NO_CONTENT)


# ============================================
# Speaking Video Views (نفس النمط)
# ============================================

class SpeakingVideoListCreateAPIView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]  # شيل JSONParser من هنا
    
    def get(self, request):
        test_id = request.query_params.get('test_id', None)
        if test_id:
            videos = SpeakingVideo.objects.filter(placement_test_id=test_id)
        else:
            videos = SpeakingVideo.objects.all()
        
        serializer = SpeakingVideoSerializer(videos, many=True)
        return Response({'success': True, 'count': videos.count(), 'data': serializer.data})
    
    def post(self, request):
        try:
            # ارفع الفيديو لـ Cloudinary مع timeout أطول
            video_file = request.FILES.get('video_file')
            if not video_file:
                return Response({
                    'success': False, 
                    'errors': {'video_file': 'Video file is required'}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # رفع الفيديو مع timeout أطول
            upload_result = cloudinary.uploader.upload(
                video_file,
                resource_type="video",
                folder="speaking/videos",
                timeout=300  # 5 دقائق
            )
            
            # إضافة الـ URL للـ data
            data = request.data.copy()
            data['video_file'] = upload_result['secure_url']
            
            serializer = SpeakingVideoCreateSerializer(data=data)
            if serializer.is_valid():
                video = serializer.save()
                return Response({
                    'success': True,
                    'message': 'تم إضافة الفيديو بنجاح',
                    'data': SpeakingVideoSerializer(video).data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False, 
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'success': False,
                'errors': {'detail': str(e)}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class SpeakingVideoDetailAPIView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request, pk):
        video = get_object_or_404(SpeakingVideo, pk=pk)
        return Response({'success': True, 'data': SpeakingVideoSerializer(video).data})
    
    def put(self, request, pk):
        video = get_object_or_404(SpeakingVideo, pk=pk)
        serializer = SpeakingVideoCreateSerializer(video, data=request.data, partial=True)
        if serializer.is_valid():
            video = serializer.save()
            return Response({
                'success': True,
                'message': 'تم تحديث الفيديو بنجاح',
                'data': SpeakingVideoSerializer(video).data
            })
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        video = get_object_or_404(SpeakingVideo, pk=pk)
        video.delete()
        return Response({'success': True, 'message': 'تم حذف الفيديو بنجاح'}, status=status.HTTP_204_NO_CONTENT)


class SpeakingQuestionListCreateAPIView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request):
        video_id = request.query_params.get('video_id', None)
        if video_id:
            questions = SpeakingQuestion.objects.filter(video_id=video_id)
        else:
            questions = SpeakingQuestion.objects.all()
        
        serializer = SpeakingQuestionSerializer(questions, many=True)
        return Response({'success': True, 'count': questions.count(), 'data': serializer.data})
    
    def post(self, request):
        serializer = SpeakingQuestionSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.save()
            return Response({
                'success': True,
                'message': 'تم إضافة السؤال بنجاح',
                'data': SpeakingQuestionSerializer(question).data
            }, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SpeakingQuestionDetailAPIView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request, pk):
        question = get_object_or_404(SpeakingQuestion, pk=pk)
        return Response({'success': True, 'data': SpeakingQuestionSerializer(question).data})
    
    def put(self, request, pk):
        question = get_object_or_404(SpeakingQuestion, pk=pk)
        serializer = SpeakingQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            question = serializer.save()
            return Response({
                'success': True,
                'message': 'تم تحديث السؤال بنجاح',
                'data': SpeakingQuestionSerializer(question).data
            })
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        question = get_object_or_404(SpeakingQuestion, pk=pk)
        question.delete()
        return Response({'success': True, 'message': 'تم حذف السؤال بنجاح'}, status=status.HTTP_204_NO_CONTENT)


# ============================================
# Writing Question Views
# ============================================

class WritingQuestionListCreateAPIView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request):
        test_id = request.query_params.get('test_id', None)
        if test_id:
            questions = WritingQuestion.objects.filter(placement_test_id=test_id)
        else:
            questions = WritingQuestion.objects.all()
        
        serializer = WritingQuestionSerializer(questions, many=True)
        return Response({'success': True, 'count': questions.count(), 'data': serializer.data})
    
    def post(self, request):
        serializer = WritingQuestionSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.save()
            return Response({
                'success': True,
                'message': 'تم إضافة السؤال بنجاح',
                'data': WritingQuestionSerializer(question).data
            }, status=status.HTTP_201_CREATED)
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class WritingQuestionDetailAPIView(APIView):
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get(self, request, pk):
        question = get_object_or_404(WritingQuestion, pk=pk)
        return Response({'success': True, 'data': WritingQuestionSerializer(question).data})
    
    def put(self, request, pk):
        question = get_object_or_404(WritingQuestion, pk=pk)
        serializer = WritingQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            question = serializer.save()
            return Response({
                'success': True,
                'message': 'تم تحديث السؤال بنجاح',
                'data': WritingQuestionSerializer(question).data
            })
        return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        question = get_object_or_404(WritingQuestion, pk=pk)
        question.delete()
        return Response({'success': True, 'message': 'تم حذف السؤال بنجاح'}, status=status.HTTP_204_NO_CONTENT)