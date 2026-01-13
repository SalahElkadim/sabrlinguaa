from rest_framework import serializers
from .models import (
    Level, Unit, Section, Lesson, Exercise,
    ExerciseMCQQuestion, ExerciseReadingPassage, ExerciseReadingQuestion,
    ExerciseListeningAudio, ExerciseListeningQuestion,
    ExerciseSpeakingVideo, ExerciseSpeakingQuestion,
    ExerciseWritingQuestion
)


# ============================================
# Original Course Serializers
# ============================================

class LevelSerializer(serializers.ModelSerializer):
    units_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Level
        fields = ['id', 'code', 'name', 'description', 'units_count']
    
    def get_units_count(self, obj):
        return obj.units.count()


class UnitSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source='level.name', read_only=True)
    sections_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Unit
        fields = ['id', 'level', 'level_name', 'title', 'number', 'sections_count']
    
    def get_sections_count(self, obj):
        return obj.sections.count()


class SectionSerializer(serializers.ModelSerializer):
    unit_title = serializers.CharField(source='unit.title', read_only=True)
    section_type_display = serializers.CharField(source='get_section_type_display', read_only=True)
    lessons_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Section
        fields = ['id', 'unit', 'unit_title', 'section_type', 'section_type_display', 
                  'title', 'order', 'lessons_count']
    
    def get_lessons_count(self, obj):
        return obj.lessons.count()


class LessonSerializer(serializers.ModelSerializer):
    section_title = serializers.CharField(source='section.title', read_only=True)
    exercises_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ['id', 'section', 'section_title', 'title', 'content', 
                  'file', 'order', 'exercises_count']
    
    def get_exercises_count(self, obj):
        return obj.exercises.count()


class ExerciseSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    total_points = serializers.SerializerMethodField()
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Exercise
        fields = ['id', 'lesson', 'lesson_title', 'title', 'description', 
                  'order', 'is_active', 'created_at', 'updated_at', 
                  'total_points', 'questions_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_points(self, obj):
        return obj.get_total_points()
    
    def get_questions_count(self, obj):
        return obj.get_questions_count()


# ============================================
# Exercise MCQ Serializers
# ============================================

class ExerciseMCQQuestionSerializer(serializers.ModelSerializer):
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    correct_answer_display = serializers.CharField(source='get_correct_answer_display', read_only=True)
    
    class Meta:
        model = ExerciseMCQQuestion
        fields = ['id', 'exercise', 'exercise_title', 'question_text', 'question_image',
                  'choice_a', 'choice_b', 'choice_c', 'choice_d',
                  'correct_answer', 'correct_answer_display', 'explanation',
                  'points', 'order', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


# ============================================
# Exercise Reading Serializers
# ============================================

class ExerciseReadingQuestionSerializer(serializers.ModelSerializer):
    correct_answer_display = serializers.CharField(source='get_correct_answer_display', read_only=True)
    
    class Meta:
        model = ExerciseReadingQuestion
        fields = ['id', 'passage', 'question_text', 'question_image',
                  'choice_a', 'choice_b', 'choice_c', 'choice_d',
                  'correct_answer', 'correct_answer_display', 'explanation',
                  'points', 'order', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ExerciseReadingPassageSerializer(serializers.ModelSerializer):
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    questions = ExerciseReadingQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExerciseReadingPassage
        fields = ['id', 'exercise', 'exercise_title', 'title', 'passage_text',
                  'passage_image', 'source', 'order', 'is_active',
                  'created_at', 'updated_at', 'questions', 'questions_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_questions_count(self, obj):
        return obj.questions.count()


# ============================================
# Exercise Listening Serializers
# ============================================

class ExerciseListeningQuestionSerializer(serializers.ModelSerializer):
    correct_answer_display = serializers.CharField(source='get_correct_answer_display', read_only=True)
    
    class Meta:
        model = ExerciseListeningQuestion
        fields = ['id', 'audio', 'question_text', 'question_image',
                  'choice_a', 'choice_b', 'choice_c', 'choice_d',
                  'correct_answer', 'correct_answer_display', 'explanation',
                  'points', 'order', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ExerciseListeningAudioSerializer(serializers.ModelSerializer):
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    questions = ExerciseListeningQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExerciseListeningAudio
        fields = ['id', 'exercise', 'exercise_title', 'title', 'audio_file',
                  'transcript', 'duration', 'order', 'is_active',
                  'created_at', 'updated_at', 'questions', 'questions_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_questions_count(self, obj):
        return obj.questions.count()


# ============================================
# Exercise Speaking Serializers
# ============================================

class ExerciseSpeakingQuestionSerializer(serializers.ModelSerializer):
    correct_answer_display = serializers.CharField(source='get_correct_answer_display', read_only=True)
    
    class Meta:
        model = ExerciseSpeakingQuestion
        fields = ['id', 'video', 'question_text', 'question_image',
                  'choice_a', 'choice_b', 'choice_c', 'choice_d',
                  'correct_answer', 'correct_answer_display', 'explanation',
                  'points', 'order', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ExerciseSpeakingVideoSerializer(serializers.ModelSerializer):
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    questions = ExerciseSpeakingQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExerciseSpeakingVideo
        fields = ['id', 'exercise', 'exercise_title', 'title', 'video_file',
                  'description', 'duration', 'thumbnail', 'order', 'is_active',
                  'created_at', 'updated_at', 'questions', 'questions_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_questions_count(self, obj):
        return obj.questions.count()


# ============================================
# Exercise Writing Serializers
# ============================================

class ExerciseWritingQuestionSerializer(serializers.ModelSerializer):
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    
    class Meta:
        model = ExerciseWritingQuestion
        fields = ['id', 'exercise', 'exercise_title', 'title', 'question_text',
                  'question_image', 'min_words', 'max_words', 'sample_answer',
                  'rubric', 'points', 'order', 'is_active',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']