import static_ffmpeg
static_ffmpeg.add_paths()
import os
import json
import tempfile
import logging
from django.conf import settings
from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)

MAX_PDF_PAGES = 20


# ============================================================
# TASK 1 — PDF Extraction
# ============================================================

@shared_task(bind=True, max_retries=2)
def extract_book_task(self, book_id: int):
    from .ai_models import ExtractedBook

    book = ExtractedBook.objects.get(id=book_id)
    book.status = 'PROCESSING'
    book.save(update_fields=['status'])

    try:
        import pdfplumber
        import cloudinary.uploader

        import urllib.request
        import cloudinary.utils

        import urllib.request

        pdf_url = book.pdf_file.url
        response = urllib.request.urlopen(pdf_url)
        pdf_bytes = response.read()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            urllib.request.urlretrieve(pdf_url, tmp.name)
            tmp_path = tmp.name

        with pdfplumber.open(tmp_path) as pdf:
            total_pages = len(pdf.pages)

            if total_pages > MAX_PDF_PAGES:
                raise ValueError(
                    f"الملف يحتوي على {total_pages} صفحة. الحد الأقصى المسموح {MAX_PDF_PAGES} صفحة فقط."
                )

            extracted_pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_pages.append(text.strip())

            full_text = "\n\n".join(extracted_pages)

        os.unlink(tmp_path)

        book.extracted_text = full_text
        book.page_count = total_pages
        book.status = 'DONE'
        book.error_message = None
        book.save(update_fields=['extracted_text', 'page_count', 'status', 'error_message'])

        logger.info(f"[ExtractBook] Book #{book_id} extracted successfully. Pages: {total_pages}")

    except Exception as exc:
        logger.error(f"[ExtractBook] Book #{book_id} failed: {str(exc)}")
        book.status = 'FAILED'
        book.error_message = str(exc)
        book.save(update_fields=['status', 'error_message'])
        raise self.retry(exc=exc, countdown=10)


# ============================================================
# TASK 2 — Media Transcription
# ============================================================

@shared_task(bind=True, max_retries=2)
def extract_media_task(self, media_id: int):
    from .ai_models import ExtractedMedia

    media = ExtractedMedia.objects.get(id=media_id)
    media.status = 'PROCESSING'
    media.save(update_fields=['status'])

    tmp_media_path = None
    tmp_audio_path = None

    try:
        import whisper
        import urllib.request

        media_url = media.media_file.url if hasattr(media.media_file, 'url') else str(media.media_file)

        suffix = '.mp4' if media.media_type == 'VIDEO' else '.mp3'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            urllib.request.urlretrieve(media_url, tmp.name)
            tmp_media_path = tmp.name

        audio_path = tmp_media_path

        if media.media_type == 'VIDEO':
            tmp_audio = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
            tmp_audio_path = tmp_audio.name
            tmp_audio.close()

            ret = os.system(f'ffmpeg -i "{tmp_media_path}" -q:a 0 -map a "{tmp_audio_path}" -y -loglevel quiet')
            if ret != 0:
                raise RuntimeError("ffmpeg فشل في استخراج الأوديو من الفيديو")
            audio_path = tmp_audio_path

        whisper_model = whisper.load_model("tiny")
        result = whisper_model.transcribe(audio_path)
        transcript = result.get("text", "").strip()
        duration = int(result.get("duration", 0))

        media.transcript = transcript
        media.duration_seconds = duration
        media.status = 'DONE'
        media.error_message = None
        media.save(update_fields=['transcript', 'duration_seconds', 'status', 'error_message'])

        logger.info(f"[ExtractMedia] Media #{media_id} transcribed. Duration: {duration}s")

    except Exception as exc:
        logger.error(f"[ExtractMedia] Media #{media_id} failed: {str(exc)}")
        media.status = 'FAILED'
        media.error_message = str(exc)
        media.save(update_fields=['status', 'error_message'])
        raise self.retry(exc=exc, countdown=15)

    finally:
        for path in [tmp_media_path, tmp_audio_path]:
            if path and os.path.exists(path):
                os.unlink(path)


# ============================================================
# TASK 3 — AI Generation
# ============================================================

@shared_task(bind=True, max_retries=1)
def generate_skill_task(self, job_id: int):
    from .ai_models import AIGenerationJob
    from .models import IELTSSkill

    job = AIGenerationJob.objects.get(id=job_id)
    job.status = 'PROCESSING'
    job.save(update_fields=['status'])

    skill = None

    try:
        # ① جمع كل الـ content
        content_parts = []

        for book in job.books.filter(status='DONE'):
            content_parts.append(
                f"=== كتاب: {book.name} ===\n{book.extracted_text}"
            )

        for m in job.media.filter(status='DONE'):
            content_parts.append(
                f"=== ترانسكريبت: {m.name} ===\n{m.transcript}"
            )

        if not content_parts:
            raise ValueError("لا يوجد محتوى جاهز (كتب أو ميديا) لإنشاء الأسئلة منه")

        combined_content = "\n\n".join(content_parts)

        # ② إنشاء الـ skill
        with transaction.atomic():
            skill = IELTSSkill.objects.create(
                skill_type=job.skill_type,
                title=job.skill_title,
                description=job.skill_description or '',
                is_active=True,
                order=0,
            )
            job.skill = skill
            job.save(update_fields=['skill'])

        # ③ توليد الأسئلة حسب النوع
        questions_created = _generate_questions_for_skill(
            skill=skill,
            skill_type=job.skill_type,
            content=combined_content,
            no_easy=job.no_easy,
            no_medium=job.no_medium,
            no_hard=job.no_hard,
            additional_notes=job.additional_notes or '',
        )

        job.status = 'DONE'
        job.questions_created = questions_created
        job.error_message = None
        job.save(update_fields=['status', 'questions_created', 'error_message'])

        logger.info(f"[GenerateSkill] Job #{job_id} done. Questions: {questions_created}")

    except Exception as exc:
        logger.error(f"[GenerateSkill] Job #{job_id} failed: {str(exc)}")

        if skill and skill.pk:
            try:
                skill.delete()
            except Exception:
                pass

        job.status = 'FAILED'
        job.skill = None
        job.error_message = str(exc)
        job.save(update_fields=['status', 'skill', 'error_message'])
        raise self.retry(exc=exc, countdown=5)


# ============================================================
# Helper — بيطلب الـ AI ويولد الأسئلة
# ============================================================

def _generate_questions_for_skill(skill, skill_type, content, no_easy, no_medium, no_hard, additional_notes):
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    schema = _get_schema_for_skill_type(skill_type)
    prompt = _build_prompt(
        skill_type=skill_type,
        content=content,
        no_easy=no_easy,
        no_medium=no_medium,
        no_hard=no_hard,
        additional_notes=additional_notes,
        schema=schema,
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.choices[0].message.content.strip()

    # نظف الـ JSON لو فيه backticks
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()

    data = json.loads(raw_text)

    return _save_questions(skill=skill, skill_type=skill_type, data=data)


def _build_prompt(skill_type, content, no_easy, no_medium, no_hard, additional_notes, schema):
    total = no_easy + no_medium + no_hard
    notes_section = f"\nملاحظات إضافية يجب مراعاتها:\n{additional_notes}" if additional_notes else ""

    # ✅ GENERAL_PATH له prompt مختلف
    if skill_type == 'GENERAL_PATH':
        type_instruction = (
            f"نوع المهارة: GENERAL_PATH (مسار شامل)\n"
            f"يجب توليد أسئلة من كل الأنواع التالية معاً في نفس الـ JSON:\n"
            f"  - vocabulary_questions: أسئلة مفردات (MCQ)\n"
            f"  - grammar_questions: أسئلة قواعد (MCQ)\n"
            f"  - passages: قطع قراءة مع أسئلة\n"
            f"  - audios: نصوص استماع (transcript فقط، بدون ملف صوتي) مع أسئلة\n"
            f"  - videos: نصوص speaking (transcript فقط، بدون ملف فيديو) مع أسئلة\n"
            f"  - writing_questions: أسئلة كتابة\n\n"
            f"إجمالي الأسئلة المطلوبة: {total}\n"
            f"وزّعها بالتساوي على الأنواع الستة قدر الإمكان.\n"
            f"توزيع الصعوبة الإجمالي — سهل (EASY): {no_easy} / متوسط (MEDIUM): {no_medium} / صعب (HARD): {no_hard}\n"
            f"طبّق توزيع الصعوبة على كل نوع بشكل متناسب."
        )
    else:
        type_instruction = (
            f"نوع المهارة: {skill_type}\n"
            f"- إجمالي الأسئلة: {total}\n"
            f"  - سهل (EASY): {no_easy}\n"
            f"  - متوسط (MEDIUM): {no_medium}\n"
            f"  - صعب (HARD): {no_hard}"
        )

    return f"""أنت مساعد متخصص في إنشاء أسئلة تعليمية لاختبار IELTS (اختبار الكفاءة في اللغة الإنجليزية).

المحتوى المرجعي:
{content}

المطلوب:
{type_instruction}
{notes_section}

التعليمات:
1. استخرج الأسئلة من المحتوى المرجعي المقدم فقط
2. التزم بتوزيع الصعوبة المطلوب بالضبط
3. كل الأسئلة يجب أن تكون باللغة الإنجليزية
4. أرجع JSON فقط بدون أي نص إضافي أو backticks
5. التزم بالـ schema التالي تماماً:

{schema}"""


def _get_schema_for_skill_type(skill_type):
    schemas = {
        'VOCABULARY': '''
{
  "questions": [
    {
      "question_text": "Choose the correct meaning of the word 'abundant':",
      "options": ["scarce", "plentiful", "dangerous", "hidden"],
      "correct_answer": "plentiful",
      "explanation": "Abundant means existing in large quantities.",
      "difficulty": "EASY"
    }
  ]
}''',
        'GRAMMAR': '''
{
  "questions": [
    {
      "question_text": "Choose the correct form: She ___ to school every day.",
      "options": ["go", "goes", "going", "gone"],
      "correct_answer": "goes",
      "explanation": "Third person singular takes 's' in simple present.",
      "difficulty": "MEDIUM"
    }
  ]
}''',
        'READING': '''
{
  "passages": [
    {
      "title": "The Impact of Technology",
      "passage_text": "Technology has transformed...",
      "difficulty": "MEDIUM",
      "questions": [
        {
          "question_text": "What is the main idea of the passage?",
          "options": ["option A", "option B", "option C", "option D"],
          "correct_answer": "option A",
          "explanation": "The passage mainly discusses...",
          "difficulty": "MEDIUM"
        }
      ]
    }
  ]
}''',
        'LISTENING': '''
{
  "audios": [
    {
      "title": "Conversation at the airport",
      "transcript": "Agent: Good morning, may I see your passport please?\\nPassenger: Sure, here you go...",
      "difficulty": "EASY",
      "questions": [
        {
          "question_text": "Where does the conversation take place?",
          "options": ["At a hotel", "At the airport", "At a bank", "At a school"],
          "correct_answer": "At the airport",
          "explanation": "The agent asks for a passport, indicating an airport setting.",
          "difficulty": "EASY"
        }
      ]
    }
  ]
}''',
        'SPEAKING': '''
{
  "videos": [
    {
      "title": "Describing your daily routine",
      "transcript": "Hi, my name is Sarah. Every morning I wake up at 7am...",
      "difficulty": "EASY",
      "questions": [
        {
          "question_text": "What time does Sarah wake up?",
          "options": ["6am", "7am", "8am", "9am"],
          "correct_answer": "7am",
          "explanation": "Sarah clearly states she wakes up at 7am.",
          "difficulty": "EASY"
        }
      ]
    }
  ]
}''',
        'WRITING': '''
{
  "questions": [
    {
      "title": "Essay on Environmental Challenges",
      "question_text": "Write an essay discussing the main environmental challenges facing the world today and suggest possible solutions.",
      "sample_answer": "The world today faces numerous environmental challenges...",
      "rubric": "1. Content (4 points): addresses the topic fully\\n2. Organization (3 points): clear intro, body, conclusion\\n3. Language (3 points): grammar and vocabulary accuracy",
      "difficulty": "HARD",
      "min_words": 200,
      "max_words": 400
    }
  ]
}''',
        # ✅ GENERAL_PATH schema — يجمع كل الأنواع في JSON واحد
        'GENERAL_PATH': '''
{
  "vocabulary_questions": [
    {
      "question_text": "Choose the correct meaning of 'resilient':",
      "options": ["weak", "adaptable", "careless", "loud"],
      "correct_answer": "adaptable",
      "explanation": "Resilient means able to recover quickly from difficulties.",
      "difficulty": "MEDIUM"
    }
  ],
  "grammar_questions": [
    {
      "question_text": "Choose the correct form: By next year, she ___ her degree.",
      "options": ["will complete", "will have completed", "completes", "completed"],
      "correct_answer": "will have completed",
      "explanation": "Future perfect is used for actions completed before a future point.",
      "difficulty": "HARD"
    }
  ],
  "passages": [
    {
      "title": "The Role of Technology in Education",
      "passage_text": "Technology has revolutionized the way students learn...",
      "difficulty": "MEDIUM",
      "questions": [
        {
          "question_text": "What is the main argument of the passage?",
          "options": ["Technology harms education", "Technology improves learning", "Students dislike technology", "Schools ban technology"],
          "correct_answer": "Technology improves learning",
          "explanation": "The passage discusses positive impacts of technology.",
          "difficulty": "MEDIUM"
        }
      ]
    }
  ],
  "audios": [
    {
      "title": "A conversation about travel plans",
      "transcript": "A: Where are you planning to go for your holiday?\\nB: I am thinking of visiting Japan...",
      "difficulty": "EASY",
      "questions": [
        {
          "question_text": "Where does person B want to travel?",
          "options": ["China", "Japan", "Korea", "Thailand"],
          "correct_answer": "Japan",
          "explanation": "Person B clearly states they want to visit Japan.",
          "difficulty": "EASY"
        }
      ]
    }
  ],
  "videos": [
    {
      "title": "Talking about your hometown",
      "transcript": "Hello everyone. Today I want to talk about my hometown, Cairo...",
      "difficulty": "EASY",
      "questions": [
        {
          "question_text": "What city does the speaker talk about?",
          "options": ["Alexandria", "Cairo", "Luxor", "Aswan"],
          "correct_answer": "Cairo",
          "explanation": "The speaker explicitly mentions Cairo as their hometown.",
          "difficulty": "EASY"
        }
      ]
    }
  ],
  "writing_questions": [
    {
      "title": "Opinion Essay",
      "question_text": "Some people believe that technology has made our lives more complicated. Do you agree or disagree? Give your opinion with examples.",
      "sample_answer": "In today\'s world, technology plays an integral role...",
      "rubric": "1. Task Response (4 pts): addresses the prompt fully\\n2. Coherence (3 pts): logical structure\\n3. Language (3 pts): range and accuracy",
      "difficulty": "HARD",
      "min_words": 200,
      "max_words": 400
    }
  ]
}''',
    }
    return schemas.get(skill_type, '{}')


# ============================================================
# Helper — يحفظ الأسئلة في الـ DB
# ============================================================

def _save_questions(skill, skill_type, data):
    count = 0

    if skill_type in ('VOCABULARY', 'GRAMMAR'):
        from sabr_questions.models import (
            VocabularyQuestion, VocabularyQuestionSet,
            GrammarQuestion, GrammarQuestionSet,
        )
        questions = data.get('questions', [])

        if skill_type == 'VOCABULARY':
            q_set, _ = VocabularyQuestionSet.objects.get_or_create(
                title='IELTS Vocabulary Questions',
                usage_type='IELTS',
                defaults={'description': 'Auto-generated set for IELTS'}
            )
        else:
            q_set, _ = GrammarQuestionSet.objects.get_or_create(
                title='IELTS Grammar Questions',
                usage_type='IELTS',
                defaults={'description': 'Auto-generated set for IELTS'}
            )

        for q in questions:
            options = q.get('options', [])
            correct_text = q.get('correct_answer', '')
            correct_letter = _text_to_letter(options, correct_text)
            if not correct_letter:
                continue

            kwargs = dict(
                question_set=q_set,
                question_text=q.get('question_text', ''),
                choice_a=options[0] if len(options) > 0 else '',
                choice_b=options[1] if len(options) > 1 else '',
                choice_c=options[2] if len(options) > 2 else '',
                choice_d=options[3] if len(options) > 3 else '',
                correct_answer=correct_letter,
                explanation=q.get('explanation', ''),
                points=1,
                usage_type='IELTS',
                ielts_skill=skill,
                is_active=True,
                order=0,
                difficulty=q.get('difficulty', 'MEDIUM'),
            )

            if skill_type == 'VOCABULARY':
                VocabularyQuestion.objects.create(**kwargs)
            else:
                GrammarQuestion.objects.create(**kwargs)
            count += 1

    elif skill_type == 'READING':
        from sabr_questions.models import ReadingPassage, ReadingQuestion

        for passage_data in data.get('passages', []):
            passage = ReadingPassage.objects.create(
                title=passage_data.get('title', 'AI Generated Passage'),
                passage_text=passage_data.get('passage_text', ''),
                usage_type='IELTS',
                ielts_skill=skill,
                is_active=True,
                order=0,
                difficulty=passage_data.get('difficulty', 'MEDIUM'),
            )

            for q in passage_data.get('questions', []):
                options = q.get('options', [])
                correct_letter = _text_to_letter(options, q.get('correct_answer', ''))
                if not correct_letter:
                    continue
                ReadingQuestion.objects.create(
                    passage=passage,
                    question_text=q.get('question_text', ''),
                    choice_a=options[0] if len(options) > 0 else '',
                    choice_b=options[1] if len(options) > 1 else '',
                    choice_c=options[2] if len(options) > 2 else '',
                    choice_d=options[3] if len(options) > 3 else '',
                    correct_answer=correct_letter,
                    explanation=q.get('explanation', ''),
                    points=1,
                    is_active=True,
                    order=0,
                    difficulty=q.get('difficulty', 'MEDIUM'),
                )
                count += 1

    elif skill_type == 'LISTENING':
        from sabr_questions.models import ListeningAudio, ListeningQuestion

        for audio_data in data.get('audios', []):
            audio = ListeningAudio.objects.create(
                title=audio_data.get('title', 'AI Generated Audio'),
                audio_file='',
                transcript=audio_data.get('transcript', ''),
                duration=0,
                usage_type='IELTS',
                ielts_skill=skill,
                is_active=True,
                order=0,
                difficulty=audio_data.get('difficulty', 'MEDIUM'),
            )

            for q in audio_data.get('questions', []):
                options = q.get('options', [])
                correct_letter = _text_to_letter(options, q.get('correct_answer', ''))
                if not correct_letter:
                    continue
                ListeningQuestion.objects.create(
                    audio=audio,
                    question_text=q.get('question_text', ''),
                    choice_a=options[0] if len(options) > 0 else '',
                    choice_b=options[1] if len(options) > 1 else '',
                    choice_c=options[2] if len(options) > 2 else '',
                    choice_d=options[3] if len(options) > 3 else '',
                    correct_answer=correct_letter,
                    explanation=q.get('explanation', ''),
                    points=1,
                    is_active=True,
                    order=0,
                )
                count += 1

    elif skill_type == 'SPEAKING':
        from sabr_questions.models import SpeakingVideo, SpeakingQuestion

        for video_data in data.get('videos', []):
            video = SpeakingVideo.objects.create(
                title=video_data.get('title', 'AI Generated Video'),
                video_file='',
                description=video_data.get('transcript', ''),
                duration=0,
                usage_type='IELTS',
                ielts_skill=skill,
                is_active=True,
                order=0,
                difficulty=video_data.get('difficulty', 'MEDIUM'),
            )

            for q in video_data.get('questions', []):
                options = q.get('options', [])
                correct_letter = _text_to_letter(options, q.get('correct_answer', ''))
                if not correct_letter:
                    continue
                SpeakingQuestion.objects.create(
                    video=video,
                    question_text=q.get('question_text', ''),
                    choice_a=options[0] if len(options) > 0 else '',
                    choice_b=options[1] if len(options) > 1 else '',
                    choice_c=options[2] if len(options) > 2 else '',
                    choice_d=options[3] if len(options) > 3 else '',
                    correct_answer=correct_letter,
                    explanation=q.get('explanation', ''),
                    points=1,
                    is_active=True,
                    order=0,
                )
                count += 1

    elif skill_type == 'WRITING':
        from sabr_questions.models import WritingQuestion

        for q in data.get('questions', []):
            WritingQuestion.objects.create(
                title=q.get('title', 'AI Generated Question'),
                question_text=q.get('question_text', ''),
                sample_answer=q.get('sample_answer', ''),
                rubric=q.get('rubric', ''),
                min_words=q.get('min_words', 150),
                max_words=q.get('max_words', 400),
                usage_type='IELTS',
                ielts_skill=skill,
                points=10,
                is_active=True,
                order=0,
                difficulty=q.get('difficulty', 'MEDIUM'),
            )
            count += 1

    # ✅ GENERAL_PATH — يحفظ كل الأنواع الستة من نفس الـ JSON
    elif skill_type == 'GENERAL_PATH':
        from sabr_questions.models import (
            VocabularyQuestion, VocabularyQuestionSet,
            GrammarQuestion, GrammarQuestionSet,
            ReadingPassage, ReadingQuestion,
            ListeningAudio, ListeningQuestion,
            WritingQuestion,
            SpeakingVideo, SpeakingQuestion,
        )

        # ── Vocabulary ──
        if data.get('vocabulary_questions'):
            q_set, _ = VocabularyQuestionSet.objects.get_or_create(
                title='IELTS Vocabulary Questions',
                usage_type='IELTS',
                defaults={'description': 'Auto-generated set for IELTS'}
            )
            for q in data['vocabulary_questions']:
                options = q.get('options', [])
                correct_letter = _text_to_letter(options, q.get('correct_answer', ''))
                if not correct_letter:
                    continue
                VocabularyQuestion.objects.create(
                    question_set=q_set,
                    question_text=q.get('question_text', ''),
                    choice_a=options[0] if len(options) > 0 else '',
                    choice_b=options[1] if len(options) > 1 else '',
                    choice_c=options[2] if len(options) > 2 else '',
                    choice_d=options[3] if len(options) > 3 else '',
                    correct_answer=correct_letter,
                    explanation=q.get('explanation', ''),
                    points=1,
                    usage_type='IELTS',
                    ielts_skill=skill,
                    is_active=True,
                    order=0,
                    difficulty=q.get('difficulty', 'MEDIUM'),
                )
                count += 1

        # ── Grammar ──
        if data.get('grammar_questions'):
            q_set, _ = GrammarQuestionSet.objects.get_or_create(
                title='IELTS Grammar Questions',
                usage_type='IELTS',
                defaults={'description': 'Auto-generated set for IELTS'}
            )
            for q in data['grammar_questions']:
                options = q.get('options', [])
                correct_letter = _text_to_letter(options, q.get('correct_answer', ''))
                if not correct_letter:
                    continue
                GrammarQuestion.objects.create(
                    question_set=q_set,
                    question_text=q.get('question_text', ''),
                    choice_a=options[0] if len(options) > 0 else '',
                    choice_b=options[1] if len(options) > 1 else '',
                    choice_c=options[2] if len(options) > 2 else '',
                    choice_d=options[3] if len(options) > 3 else '',
                    correct_answer=correct_letter,
                    explanation=q.get('explanation', ''),
                    points=1,
                    usage_type='IELTS',
                    ielts_skill=skill,
                    is_active=True,
                    order=0,
                    difficulty=q.get('difficulty', 'MEDIUM'),
                )
                count += 1

        # ── Reading ──
        for passage_data in data.get('passages', []):
            passage = ReadingPassage.objects.create(
                title=passage_data.get('title', 'AI Generated Passage'),
                passage_text=passage_data.get('passage_text', ''),
                usage_type='IELTS',
                ielts_skill=skill,
                is_active=True,
                order=0,
                difficulty=passage_data.get('difficulty', 'MEDIUM'),
            )
            for q in passage_data.get('questions', []):
                options = q.get('options', [])
                correct_letter = _text_to_letter(options, q.get('correct_answer', ''))
                if not correct_letter:
                    continue
                ReadingQuestion.objects.create(
                    passage=passage,
                    question_text=q.get('question_text', ''),
                    choice_a=options[0] if len(options) > 0 else '',
                    choice_b=options[1] if len(options) > 1 else '',
                    choice_c=options[2] if len(options) > 2 else '',
                    choice_d=options[3] if len(options) > 3 else '',
                    correct_answer=correct_letter,
                    explanation=q.get('explanation', ''),
                    points=1,
                    is_active=True,
                    order=0,
                    difficulty=q.get('difficulty', 'MEDIUM'),
                )
                count += 1

        # ── Listening ──
        for audio_data in data.get('audios', []):
            audio = ListeningAudio.objects.create(
                title=audio_data.get('title', 'AI Generated Audio'),
                audio_file='',
                transcript=audio_data.get('transcript', ''),
                duration=0,
                usage_type='IELTS',
                ielts_skill=skill,
                is_active=True,
                order=0,
                difficulty=audio_data.get('difficulty', 'MEDIUM'),
            )
            for q in audio_data.get('questions', []):
                options = q.get('options', [])
                correct_letter = _text_to_letter(options, q.get('correct_answer', ''))
                if not correct_letter:
                    continue
                ListeningQuestion.objects.create(
                    audio=audio,
                    question_text=q.get('question_text', ''),
                    choice_a=options[0] if len(options) > 0 else '',
                    choice_b=options[1] if len(options) > 1 else '',
                    choice_c=options[2] if len(options) > 2 else '',
                    choice_d=options[3] if len(options) > 3 else '',
                    correct_answer=correct_letter,
                    explanation=q.get('explanation', ''),
                    points=1,
                    is_active=True,
                    order=0,
                )
                count += 1

        # ── Speaking ──
        for video_data in data.get('videos', []):
            video = SpeakingVideo.objects.create(
                title=video_data.get('title', 'AI Generated Video'),
                video_file='',
                description=video_data.get('transcript', ''),
                duration=0,
                usage_type='IELTS',
                ielts_skill=skill,
                is_active=True,
                order=0,
                difficulty=video_data.get('difficulty', 'MEDIUM'),
            )
            for q in video_data.get('questions', []):
                options = q.get('options', [])
                correct_letter = _text_to_letter(options, q.get('correct_answer', ''))
                if not correct_letter:
                    continue
                SpeakingQuestion.objects.create(
                    video=video,
                    question_text=q.get('question_text', ''),
                    choice_a=options[0] if len(options) > 0 else '',
                    choice_b=options[1] if len(options) > 1 else '',
                    choice_c=options[2] if len(options) > 2 else '',
                    choice_d=options[3] if len(options) > 3 else '',
                    correct_answer=correct_letter,
                    explanation=q.get('explanation', ''),
                    points=1,
                    is_active=True,
                    order=0,
                )
                count += 1

        # ── Writing ──
        for q in data.get('writing_questions', []):
            WritingQuestion.objects.create(
                title=q.get('title', 'AI Generated Question'),
                question_text=q.get('question_text', ''),
                sample_answer=q.get('sample_answer', ''),
                rubric=q.get('rubric', ''),
                min_words=q.get('min_words', 150),
                max_words=q.get('max_words', 400),
                usage_type='IELTS',
                ielts_skill=skill,
                points=10,
                is_active=True,
                order=0,
                difficulty=q.get('difficulty', 'MEDIUM'),
            )
            count += 1

    return count


def _text_to_letter(options, correct_text):
    """يحول نص الإجابة الصحيحة لحرف A/B/C/D"""
    for idx, option in enumerate(options):
        if option == correct_text:
            return chr(65 + idx)
    return None

# ============================================================
# TASK 4 — Add Questions to Existing Skill
# أضف ده في tasks.py بعد generate_skill_task
# ============================================================

@shared_task(bind=True, max_retries=1)
def add_questions_to_skill_task(self, job_id: int):
    """
    نفس فكرة generate_skill_task بالظبط،
    الفرق الوحيد إنه بيستخدم skill موجودة بدل ما ينشئ واحدة جديدة.
    """
    from .ai_models import AIGenerationJob

    job = AIGenerationJob.objects.get(id=job_id)
    job.status = 'PROCESSING'
    job.save(update_fields=['status'])

    # الـ skill لازم تكون موجودة (بنحددها في الـ view قبل ما نعمل الـ task)
    skill = job.skill
    if not skill:
        job.status = 'FAILED'
        job.error_message = 'لم يتم تحديد مهارة موجودة'
        job.save(update_fields=['status', 'error_message'])
        return

    try:
        # ① جمع كل الـ content
        content_parts = []

        for book in job.books.filter(status='DONE'):
            content_parts.append(
                f"=== كتاب: {book.name} ===\n{book.extracted_text}"
            )

        for m in job.media.filter(status='DONE'):
            content_parts.append(
                f"=== ترانسكريبت: {m.name} ===\n{m.transcript}"
            )

        if not content_parts:
            raise ValueError("لا يوجد محتوى جاهز (كتب أو ميديا) لإنشاء الأسئلة منه")

        combined_content = "\n\n".join(content_parts)

        # ② توليد الأسئلة وإضافتها على الـ skill الموجودة
        questions_created = _generate_questions_for_skill(
            skill=skill,
            skill_type=skill.skill_type,   # نوع الـ skill الموجودة
            content=combined_content,
            no_easy=job.no_easy,
            no_medium=job.no_medium,
            no_hard=job.no_hard,
            additional_notes=job.additional_notes or '',
        )

        job.status = 'DONE'
        job.questions_created = questions_created
        job.error_message = None
        job.save(update_fields=['status', 'questions_created', 'error_message'])

        logger.info(
            f"[AddQuestions] Job #{job_id} done. "
            f"Added {questions_created} questions to Skill #{skill.id} ({skill.title})"
        )

    except Exception as exc:
        logger.error(f"[AddQuestions] Job #{job_id} failed: {str(exc)}")
        job.status = 'FAILED'
        job.error_message = str(exc)
        job.save(update_fields=['status', 'error_message'])
        raise self.retry(exc=exc, countdown=5)