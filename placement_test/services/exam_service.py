# placement_test/services/exam_service.py

import logging
from typing import Dict, List, Any
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from placement_test.models import (
    StudentPlacementTestAttempt,
    StudentPlacementTestAnswer
)
from sabr_questions.models import WritingQuestion
from .ai_grading import ai_grading_service

logger = logging.getLogger('ai_grading')


class ExamService:
    """
    خدمة معالجة الامتحانات والإجابات
    """
    
    @staticmethod
    def submit_exam_answers(attempt_id: int, answers_data: Dict) -> Dict[str, Any]:
        """
        تقديم إجابات الامتحان وحساب النتيجة
        
        Args:
            attempt_id: معرف المحاولة
            answers_data: {
                'vocabulary': [{'question_id': 1, 'selected_choice': 'A'}, ...],
                'grammar': [...],
                'reading': [...],
                'listening': [...],
                'speaking': [...],
                'writing': [{'question_id': 7, 'text_answer': '...'}, ...]
            }
        
        Returns:
            {
                'attempt_id': int,
                'total_score': int,
                'max_score': int,
                'percentage': float,
                'level': str,
                'details': {...}
            }
        """
        
        with transaction.atomic():
            # الحصول على المحاولة
            attempt = StudentPlacementTestAttempt.objects.select_for_update().get(
                id=attempt_id,
                status='IN_PROGRESS'
            )
            
            # التحقق من صاحب المحاولة (في الـ view)
            
            # التحقق من انتهاء الوقت
            if attempt.is_time_up():
                attempt.status = 'ABANDONED'
                attempt.save()
                raise ValueError('انتهى وقت الامتحان')
            
            # حفظ وتصحيح الإجابات
            results = {
                'vocabulary': ExamService._grade_mcq_questions(
                    attempt, answers_data.get('vocabulary', []), 'vocabularyquestion'
                ),
                'grammar': ExamService._grade_mcq_questions(
                    attempt, answers_data.get('grammar', []), 'grammarquestion'
                ),
                'reading': ExamService._grade_mcq_questions(
                    attempt, answers_data.get('reading', []), 'readingquestion'
                ),
                'listening': ExamService._grade_mcq_questions(
                    attempt, answers_data.get('listening', []), 'listeningquestion'
                ),
                'speaking': ExamService._grade_mcq_questions(
                    attempt, answers_data.get('speaking', []), 'speakingquestion'
                ),
                'writing': ExamService._grade_writing_questions(
                    attempt, answers_data.get('writing', [])
                )
            }
            
            # تحديد الامتحان كمكتمل وحساب النتيجة النهائية
            attempt.mark_completed()
            
            # حساب النتيجة الكلية
            total_score = attempt.score
            max_score = attempt.placement_test.total_questions
            percentage = (total_score / max_score * 100) if max_score > 0 else 0
            
            return {
                'attempt_id': attempt.id,
                'total_score': total_score,
                'max_score': max_score,
                'percentage': round(percentage, 2),
                'level': attempt.level_achieved,
                'completed_at': attempt.completed_at,
                'duration_minutes': round(attempt.get_duration(), 2) if attempt.get_duration() else 0,
                'details': results
            }
    
    @staticmethod
    def _grade_mcq_questions(
        attempt: StudentPlacementTestAttempt,
        answers: List[Dict],
        question_model_name: str
    ) -> Dict[str, Any]:
        """
        تصحيح أسئلة MCQ
        """
        content_type = ContentType.objects.get(model=question_model_name)
        
        correct_count = 0
        total_count = len(answers)
        total_points = 0
        
        for answer_data in answers:
            question_id = answer_data['question_id']
            selected_choice = answer_data['selected_choice']
            
            # إنشاء أو تحديث الإجابة
            answer, created = StudentPlacementTestAnswer.objects.get_or_create(
                attempt=attempt,
                content_type=content_type,
                object_id=question_id,
                defaults={'selected_choice': selected_choice}
            )
            
            if not created:
                answer.selected_choice = selected_choice
            
            # تصحيح الإجابة
            answer.check_answer()
            
            if answer.is_correct:
                correct_count += 1
            
            total_points += answer.points_earned
        
        return {
            'total_questions': total_count,
            'correct_answers': correct_count,
            'wrong_answers': total_count - correct_count,
            'total_points': total_points,
            'accuracy': round((correct_count / total_count * 100), 2) if total_count > 0 else 0
        }
        
    @staticmethod
    def _grade_writing_questions(
        attempt: StudentPlacementTestAttempt,
        answers: List[Dict]
    ) -> Dict[str, Any]:
        """
        تصحيح أسئلة الكتابة باستخدام AI
        ✅ نظام جديد: Binary Grading
        """
        content_type = ContentType.objects.get(model='writingquestion')
        
        total_points = 0
        correct_count = 0  # ← عدد الإجابات الصحيحة
        graded_answers = []
        total_ai_cost = Decimal('0.000000')
        
        for answer_data in answers:
            question_id = answer_data['question_id']
            text_answer = answer_data['text_answer']
            
            # الحصول على السؤال
            writing_question = WritingQuestion.objects.get(id=question_id)
            
            # إنشاء أو تحديث الإجابة
            answer, created = StudentPlacementTestAnswer.objects.get_or_create(
                attempt=attempt,
                content_type=content_type,
                object_id=question_id,
                defaults={'text_answer': text_answer}
            )
            
            if not created:
                answer.text_answer = text_answer
            
            # تصحيح باستخدام AI
            logger.info(f"Grading writing question {question_id} for attempt {attempt.id}")
            
            grading_result = ai_grading_service.grade_writing_question(
                question_text=writing_question.question_text,
                student_answer=text_answer,
                sample_answer=writing_question.sample_answer or '',
                rubric=writing_question.rubric or '',
                max_points=writing_question.points,  # ← أضف ده
                min_words=writing_question.min_words,
                max_words=writing_question.max_words,
                pass_threshold=writing_question.pass_threshold  # ← استخدام الـ threshold
            )
            
            # ✅ حفظ النتيجة (0 or 1 فقط)
            answer.points_earned = grading_result['score']  # ← 0 or 1
            answer.is_correct = grading_result['is_correct']  # ← True/False
            answer.ai_feedback = grading_result['feedback']
            answer.ai_grading_model = ai_grading_service.model
            answer.ai_grading_cost = Decimal(str(grading_result['cost']))
            answer.strengths = grading_result['strengths']
            answer.improvements = grading_result['improvements']
            answer.save()
            
            total_points += answer.points_earned
            if answer.is_correct:
                correct_count += 1
            
            total_ai_cost += answer.ai_grading_cost
            
            graded_answers.append({
                'question_id': question_id,
                'score': grading_result['score'],  # ← 0 or 1
                'raw_score': grading_result.get('raw_score', 0),  # ← الدرجة الأصلية
                'percentage': grading_result.get('percentage', 0),  # ← النسبة المئوية
                'is_correct': grading_result['is_correct'],
                'word_count': grading_result['word_count'],
                'is_within_limit': grading_result['is_within_limit'],
                'feedback': grading_result['feedback'],
                'strengths': grading_result['strengths'],
                'improvements': grading_result['improvements']
            })
        
        return {
            'total_questions': len(answers),
            'correct_answers': correct_count,  # ← عدد الصح
            'wrong_answers': len(answers) - correct_count,  # ← عدد الغلط
            'total_points': total_points,  # ← المجموع (من 4 لو 4 أسئلة)
            'accuracy': round((correct_count / len(answers) * 100), 2) if len(answers) > 0 else 0,
            'total_ai_cost': float(total_ai_cost),
            'graded_answers': graded_answers
        }


# Singleton instance
exam_service = ExamService()