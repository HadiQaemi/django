from rest_framework import serializers
import re


class TimeRangeSerializer(serializers.Serializer):
    """Serializer for a time range."""

    start = serializers.IntegerField(required=False)
    end = serializers.IntegerField(required=False)


class AuthorSerializer(serializers.Serializer):
    """Serializer for an author."""

    id = serializers.CharField(allow_null=True, required=False)
    given_name = serializers.CharField()
    family_name = serializers.CharField()
    label = serializers.CharField(allow_null=True, required=False)


class ConceptSerializer(serializers.Serializer):
    """Serializer for a concept."""

    id = serializers.CharField(allow_null=True, required=False)
    label = serializers.CharField()
    identifier = serializers.CharField(allow_null=True, required=False)


class ResearchFieldSerializer(serializers.Serializer):
    """Serializer for a research field."""

    id = serializers.CharField(allow_null=True, required=False)
    label = serializers.CharField()


class NotationSerializer(serializers.Serializer):
    """Serializer for a notation."""

    id = serializers.CharField(allow_null=True, required=False)
    label = serializers.CharField()
    concept = ConceptSerializer(allow_null=True, required=False)


class StatementSerializer(serializers.Serializer):
    """Serializer for a statement."""

    id = serializers.CharField(allow_null=True, required=False)
    statement_id = serializers.CharField(allow_null=True, required=False)
    content = serializers.DictField()
    author = AuthorSerializer(many=True)
    article_id = serializers.CharField()
    supports = serializers.ListField(child=serializers.DictField(), required=False)
    notation = NotationSerializer(allow_null=True, required=False)
    created_at = serializers.DateTimeField(allow_null=True, required=False)
    updated_at = serializers.DateTimeField(allow_null=True, required=False)


class ContributionSerializer(serializers.Serializer):
    """Serializer for a contribution."""

    id = serializers.CharField(allow_null=True, required=False)
    title = serializers.CharField()
    author = AuthorSerializer(many=True)
    info = serializers.DictField()
    paper_id = serializers.CharField(allow_null=True, required=False)
    json_id = serializers.CharField(allow_null=True, required=False)
    json_type = serializers.CharField(allow_null=True, required=False)
    json_context = serializers.DictField(allow_null=True, required=False)
    predicates = serializers.DictField(allow_null=True, required=False)


class JournalSerializer(serializers.Serializer):
    """Serializer for a journal."""

    id = serializers.CharField()
    label = serializers.CharField()
    publisher = serializers.DictField(allow_null=True, required=False)


class ConferenceSerializer(serializers.Serializer):
    """Serializer for a conference."""

    id = serializers.CharField()
    label = serializers.CharField()
    publisher = serializers.DictField(allow_null=True, required=False)


class PaperSerializer(serializers.Serializer):
    """Serializer for a paper."""

    def create(self, validated_data):
        # This method is required for schema generation
        # It doesn't need to actually create anything
        return validated_data

    def update(self, instance, validated_data):
        # This method is required for schema generation
        # It doesn't need to actually update anything
        return instance

    id = serializers.CharField(allow_null=True, required=False)
    article_id = serializers.CharField(allow_null=True, required=False)
    title = serializers.CharField()
    author = AuthorSerializer(many=True)
    abstract = serializers.CharField()
    contributions = ContributionSerializer(many=True, required=False)
    statements = StatementSerializer(many=True, required=False)
    dois = serializers.CharField(allow_null=True, required=False)
    date_published = serializers.DateTimeField(allow_null=True, required=False)
    entity = serializers.CharField(allow_null=True, required=False)
    external = serializers.URLField(allow_null=True, required=False)
    info = serializers.DictField(allow_null=True, required=False)
    timeline = serializers.DictField(allow_null=True, required=False)
    journal = JournalSerializer(allow_null=True, required=False)
    conference = ConferenceSerializer(allow_null=True, required=False)
    publisher = serializers.DictField(allow_null=True, required=False)
    research_fields = ResearchFieldSerializer(many=True, required=False)
    reborn_doi = serializers.CharField(allow_null=True, required=False)
    paper_type = serializers.CharField(allow_null=True, required=False)
    concepts = ConceptSerializer(many=True, required=False)
    created_at = serializers.DateTimeField(allow_null=True, required=False)
    updated_at = serializers.DateTimeField(allow_null=True, required=False)


class PaperFilterSerializer(serializers.Serializer):
    """Serializer for paper filtering."""

    title = serializers.CharField(allow_null=True, required=False)
    time_range = TimeRangeSerializer(allow_null=True, required=False)
    authors = serializers.ListField(child=serializers.CharField(), required=False)
    journals = serializers.ListField(child=serializers.CharField(), required=False)
    conferences = serializers.ListField(child=serializers.CharField(), required=False)
    concepts = serializers.ListField(child=serializers.CharField(), required=False)
    research_fields = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    page = serializers.IntegerField(default=1)
    per_page = serializers.IntegerField(default=10)


class SearchQuerySerializer(serializers.Serializer):
    """Serializer for search queries."""

    query = serializers.CharField()
    search_type = serializers.ChoiceField(
        choices=["hybrid", "semantic", "keyword"], default="hybrid"
    )
    sort_order = serializers.ChoiceField(
        choices=["a-z", "z-a", "newest"], default="a-z"
    )
    page = serializers.IntegerField(default=1)
    page_size = serializers.IntegerField(default=10)
    research_fields = serializers.ListField(
        child=serializers.CharField(), required=False
    )


def validate_domain(value):
    tib_pattern = r"^https?://service\.tib\.eu/ldmservice/dataset/[\w-]+$"
    if re.match(tib_pattern, value) or re.match(tib_pattern, value):
        return value
    raise serializers.ValidationError(
        "URL must be from service.tib.eu/ldmservice/dataset"
    )


class ScraperUrlSerializer(serializers.Serializer):
    url = serializers.URLField(validators=[validate_domain])


class SearchResultItemSerializer(serializers.Serializer):
    """Serializer for a search result item."""

    id = serializers.CharField()
    name = serializers.CharField()
    author = serializers.CharField()
    date = serializers.DateTimeField(allow_null=True, required=False)
    journal = serializers.CharField(allow_null=True, required=False)
    article = serializers.CharField(allow_null=True, required=False)
    publisher = serializers.CharField(allow_null=True, required=False)
    score = serializers.FloatField(allow_null=True, required=False)


class SearchResultsSerializer(serializers.Serializer):
    """Serializer for search results."""

    items = SearchResultItemSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
