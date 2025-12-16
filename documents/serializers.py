from rest_framework import serializers
from .models import DocumentTemplate, GeneratedDocument


class DocumentTemplateSerializer(serializers.ModelSerializer):
	class Meta:
		model = DocumentTemplate
		fields = "__all__"


class GeneratedDocumentSerializer(serializers.ModelSerializer):
	# optional upload field handled in the view
	file = serializers.FileField(write_only=True, required=False)

	template = serializers.PrimaryKeyRelatedField(queryset=DocumentTemplate.objects.all(), allow_null=True, required=False)

	class Meta:
		model = GeneratedDocument
		fields = (
			"id",
			"template",
			"doc_type",  # ✅ B 프로젝트 병합: doc_type 필드 추가
			"title",
			"user",
			"employee",
			"consultation",
			"filled_data_json",
			"file_url",
			"file",
			"status",
			"created_at",
		)
		read_only_fields = ("user", "created_at", "file_url")


# ===================================================================
# ✅ B 프로젝트 병합: 이력서 자동 생성 기능 추가
# ===================================================================

class ExperienceSerializer(serializers.Serializer):
	"""이력서 경력 사항 Serializer"""
	company = serializers.CharField(required=False, allow_blank=True)
	role = serializers.CharField(required=False, allow_blank=True)
	period = serializers.CharField(required=False, allow_blank=True)
	achievements = serializers.ListField(
		child=serializers.CharField(allow_blank=True), required=False, allow_empty=True, default=list
	)
	description = serializers.CharField(required=False, allow_blank=True)


class EducationSerializer(serializers.Serializer):
	"""이력서 학력 사항 Serializer"""
	school = serializers.CharField(required=False, allow_blank=True)
	major = serializers.CharField(required=False, allow_blank=True)
	period = serializers.CharField(required=False, allow_blank=True)
	description = serializers.CharField(required=False, allow_blank=True)


class ResumeGenerationSerializer(serializers.Serializer):
	"""이력서 자동 생성 요청 Serializer"""
	# 기본 정보
	name = serializers.CharField(required=True)
	title = serializers.CharField(required=False, allow_blank=True)
	phone = serializers.CharField(required=False, allow_blank=True)
	email = serializers.EmailField(required=False, allow_blank=True)
	address = serializers.CharField(required=False, allow_blank=True)
	summary = serializers.CharField(required=False, allow_blank=True)

	# 섹션별 리스트
	experiences = ExperienceSerializer(many=True, required=False, allow_empty=True, default=list)
	educations = EducationSerializer(many=True, required=False, allow_empty=True, default=list)
	skills = serializers.ListField(child=serializers.CharField(allow_blank=True), required=False, allow_empty=True, default=list)
	certifications = serializers.ListField(child=serializers.CharField(allow_blank=True), required=False, allow_empty=True, default=list)
	languages = serializers.ListField(child=serializers.CharField(allow_blank=True), required=False, allow_empty=True, default=list)

	# 저장 옵션
	save_to_documents = serializers.BooleanField(required=False, default=False)
	document_title = serializers.CharField(required=False, allow_blank=True)
	status = serializers.CharField(required=False, allow_blank=True)

	def validate(self, attrs):
		# 기본값 보정
		if not attrs.get("document_title"):
			attrs["document_title"] = "이력서"
		if not attrs.get("status"):
			attrs["status"] = "완료"
		return attrs
