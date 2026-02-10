# placement_test/services/ai_grading.py

import json
import logging
from typing import Dict, Any, Optional
from decimal import Decimal

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger('ai_grading')


class AIGradingService:
    """
    خدمة تصحيح أسئلة الكتابة باستخدام GPT-4o
    """
    
    def __init__(self):
        """
        ✅ تهيئة الخدمة مع التحقق من الإعدادات
        """
        # التحقق من وجود API Key
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in settings")
        
        self.client = OpenAI(api_key=api_key)
        
        # ✅ التحقق من وجود AI_GRADING_CONFIG
        grading_config = getattr(settings, 'AI_GRADING_CONFIG', None)
        
        if grading_config:
            self.model = grading_config.get('model', 'gpt-4o')
            self.temperature = grading_config.get('temperature', 0.3)
            self.max_tokens = grading_config.get('max_tokens', 1000)
        else:
            # ✅ قيم افتراضية إذا لم يتم تعريف AI_GRADING_CONFIG
            self.model = 'gpt-4o'
            self.temperature = 0.3
            self.max_tokens = 1000
            
            logger.warning(
                "AI_GRADING_CONFIG not found in settings. Using default values: "
                f"model={self.model}, temperature={self.temperature}, max_tokens={self.max_tokens}"
            )
        
    def grade_writing_question(
        self,
        question_text: str,
        student_answer: str,
        sample_answer: str,
        rubric: str,
        max_points: int,
        min_words: int = 100,
        max_words: int = 500,
        pass_threshold: int = 60  # ← الـ parameter الجديد
    ) -> Dict[str, Any]:
        """
        تصحيح سؤال Writing باستخدام GPT-4o مع Binary Grading
        
        Args:
            question_text: نص السؤال
            student_answer: إجابة الطالب
            sample_answer: نموذج الإجابة
            rubric: معايير التقييم
            max_points: أقصى درجة للسؤال (usually 10)
            min_words: الحد الأدنى للكلمات
            max_words: الحد الأقصى للكلمات
            pass_threshold: النسبة المئوية المطلوبة للنجاح (default: 60%)
        
        Returns:
            {
                'raw_score': int,           # الدرجة الأصلية من max_points
                'percentage': float,        # النسبة المئوية
                'score': int,               # 0 or 1 (Binary)
                'is_correct': bool,         # True/False
                'feedback': str,
                'strengths': list,
                'improvements': list,
                'word_count': int,
                'is_within_limit': bool,
                'tokens_used': int,
                'cost': float
            }
        """
        
        # حساب عدد الكلمات
        word_count = len(student_answer.split())
        is_within_limit = min_words <= word_count <= max_words
        
        # بناء الـ Prompt
        prompt = self._build_prompt(
            question_text=question_text,
            student_answer=student_answer,
            sample_answer=sample_answer,
            rubric=rubric,
            max_points=max_points,
            min_words=min_words,
            max_words=max_words,
            word_count=word_count,
            is_within_limit=is_within_limit,
            pass_threshold=pass_threshold  # ← مرر الـ threshold للـ prompt
        )
        
        try:
            # استدعاء GPT-4o
            logger.info(f"Grading writing question with {self.model}, threshold={pass_threshold}%")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert English language examiner for placement tests. You provide fair, accurate, and constructive feedback using binary grading system."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # استخراج النتيجة
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # ✅ التحقق من Binary Grading
            # إذا الـ AI ما رجعش score أو is_correct، احسبهم يدوياً
            if 'score' not in result or 'is_correct' not in result:
                raw_score = result.get('raw_score', 0)
                percentage = result.get('percentage', 0)
                
                # حساب Binary Score
                result['score'] = 1 if percentage >= pass_threshold else 0
                result['is_correct'] = percentage >= pass_threshold
            
            # حساب التكلفة
            tokens_used = response.usage.total_tokens
            cost = self._calculate_cost(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens
            )
            
            logger.info(
                f"Grading completed. Raw: {result.get('raw_score', 0)}/{max_points}, "
                f"Percentage: {result.get('percentage', 0)}%, "
                f"Binary Score: {result['score']}/1, "
                f"Cost: ${cost:.6f}"
            )
            
            # إضافة معلومات إضافية
            result['word_count'] = word_count
            result['is_within_limit'] = is_within_limit
            result['tokens_used'] = tokens_used
            result['cost'] = cost
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return self._fallback_grading(word_count, is_within_limit, max_points, pass_threshold)
        
        except Exception as e:
            logger.error(f"AI grading error: {e}", exc_info=True)
            return self._fallback_grading(word_count, is_within_limit, max_points, pass_threshold)
    
    def _build_prompt(
        self,
        question_text: str,
        student_answer: str,
        sample_answer: str,
        rubric: str,
        max_points: int,
        min_words: int,
        max_words: int,
        word_count: int,
        is_within_limit: bool,
        pass_threshold: int  # ← أضف الـ parameter ده
    ) -> str:
        """
        بناء الـ Prompt للـ AI
        """
        return f"""
    You are grading a student's answer for an English placement test writing question.

    **QUESTION:**
    {question_text}

    **WORD LIMIT:**
    Minimum: {min_words} words
    Maximum: {max_words} words
    Student's word count: {word_count} words
    Within limit: {'Yes' if is_within_limit else 'No'}

    **SAMPLE ANSWER (Reference):**
    {sample_answer if sample_answer else 'No sample answer provided.'}

    **GRADING RUBRIC:**
    {rubric if rubric else '''
    - Content Relevance (40%): Does the answer address the question appropriately?
    - Grammar & Vocabulary (30%): Are there significant grammar or vocabulary errors?
    - Coherence & Organization (20%): Is the answer well-structured and easy to follow?
    - Word Count (10%): Is the answer within the required word limit?
    '''}

    **STUDENT'S ANSWER:**
    {student_answer}

    **GRADING SYSTEM (Binary Grading):**
    1. First, grade the answer out of {max_points} points (raw score).
    2. Calculate the percentage: (raw_score / {max_points}) × 100
    3. If percentage >= {pass_threshold}%, the student gets 1 point (PASS)
    4. If percentage < {pass_threshold}%, the student gets 0 points (FAIL)

    **WORD COUNT PENALTIES:**
    - If word count is below {min_words}, deduct 30% from raw score
    - If word count is above {max_words}, deduct 20% from raw score

    **INSTRUCTIONS:**
    1. Calculate the raw score out of {max_points} points
    2. Apply word count penalties if needed
    3. Calculate percentage
    4. Determine if PASS (1 point) or FAIL (0 points) based on {pass_threshold}% threshold
    5. Provide feedback in Arabic (العربية)
    6. List 2-3 strengths in Arabic
    7. List 2-3 areas for improvement in Arabic

    **REQUIRED OUTPUT FORMAT (JSON only, no markdown):**
    {{
    "raw_score": <number between 0 and {max_points}>,
    "percentage": <percentage value>,
    "score": <0 or 1>,
    "is_correct": <true or false>,
    "feedback": "<brief constructive feedback in Arabic explaining the grade>",
    "strengths": ["<strength 1 in Arabic>", "<strength 2 in Arabic>"],
    "improvements": ["<improvement 1 in Arabic>", "<improvement 2 in Arabic>"]
    }}
    """
    
    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        حساب تكلفة الـ API call
        GPT-4o pricing: $2.50/1M input tokens, $10/1M output tokens
        """
        input_cost = (prompt_tokens / 1_000_000) * 2.50
        output_cost = (completion_tokens / 1_000_000) * 10.00
        return input_cost + output_cost
        
    def _fallback_grading(
        self,
        word_count: int,
        is_within_limit: bool,
        max_points: int,
        pass_threshold: int = 60  # ← أضف الـ parameter
    ) -> Dict[str, Any]:
        """
        تصحيح احتياطي في حالة فشل الـ AI
        """
        if word_count == 0:
            raw_score = 0
            percentage = 0
        elif not is_within_limit:
            raw_score = max_points // 2
            percentage = (raw_score / max_points) * 100
        else:
            raw_score = int(max_points * 0.7)  # 70% للإجابات المقبولة
            percentage = 70.0
        
        # Binary grading
        binary_score = 1 if percentage >= pass_threshold else 0
        is_correct = percentage >= pass_threshold
        
        return {
            'raw_score': raw_score,
            'percentage': round(percentage, 2),
            'score': binary_score,
            'is_correct': is_correct,
            'feedback': f'تم التصحيح بشكل تلقائي. النسبة المئوية: {percentage:.1f}%. الحد الأدنى للنجاح: {pass_threshold}%.',
            'strengths': ['تم تقديم إجابة'],
            'improvements': ['يحتاج لمراجعة يدوية من المدرس'],
            'word_count': word_count,
            'is_within_limit': is_within_limit,
            'tokens_used': 0,
            'cost': 0.0
        }


# Singleton instance
ai_grading_service = AIGradingService()