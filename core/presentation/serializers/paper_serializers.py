from django.http import QueryDict
from rest_framework import serializers
import re

from core.domain.value_objects import ResourceType, SearchType, SortBy, SortOrder


class TimeRangeSerializer(serializers.Serializer):
    """Serializer for a time range."""

    start = serializers.IntegerField(required=False)
    end = serializers.IntegerField(required=False)


class AuthorSerializer(serializers.Serializer):
    """Serializer for an author."""

    orcid = serializers.CharField(allow_null=True, required=False)
    author_id = serializers.CharField()
    name = serializers.CharField(allow_null=True, required=False)


class ResearchFieldSerializer(serializers.Serializer):
    """Serializer for an author."""

    research_field_id = serializers.CharField(allow_null=True, required=False)
    related_identifier = serializers.CharField()
    label = serializers.CharField(allow_null=True, required=False)


class JournalSerializer(serializers.Serializer):
    """Serializer for an author."""

    journal_id = serializers.CharField(allow_null=True, required=False)
    name = serializers.CharField()
    publisher = serializers.CharField(allow_null=True, required=False)


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

    statement_id = serializers.CharField()
    name = serializers.CharField()
    author = AuthorSerializer(many=True)
    scientific_venue = serializers.CharField()
    article = serializers.CharField()
    date_published = serializers.CharField()
    search_type_used = serializers.CharField()


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


class ScientificVenueSerializer(serializers.Serializer):
    label = serializers.CharField()
    id = serializers.CharField()
    identifier = serializers.URLField()


class PaperSerializer(serializers.Serializer):
    """Serializer for a paper."""

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance

    id = serializers.CharField(allow_null=True, required=False)
    article_id = serializers.CharField(allow_null=True, required=False)

    # Incoming JSON uses "name" — alias to "title"
    title = serializers.CharField(source="name")

    # Incoming JSON has author as string, not nested list
    author = serializers.CharField()

    abstract = serializers.CharField(required=False)
    contributions = ContributionSerializer(many=True, required=False)
    statements = StatementSerializer(many=True, required=False)
    dois = serializers.CharField(allow_null=True, required=False)

    # Accept date as int (year)
    date_published = serializers.IntegerField(allow_null=True, required=False)

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

    # New field in your example
    scientific_venue = ScientificVenueSerializer(required=False)
    search_type_used = serializers.CharField(required=False)


class PaperListSerializer(serializers.Serializer):
    items = PaperSerializer(many=True)
    total = serializers.IntegerField()


class GetArticlesQuerySerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(min_value=1, default=1)
    per_page = serializers.IntegerField(min_value=1, max_value=100, default=10)
    start_year = serializers.IntegerField(
        min_value=2000, max_value=2025, required=False
    )
    end_year = serializers.IntegerField(min_value=2000, max_value=2025, required=False)
    sort = serializers.CharField(required=False, default="a-z", allow_blank=True)
    search_type = serializers.ChoiceField(
        choices=[st.value for st in SearchType], default=SearchType.KEYWORD.value
    )
    sort_by = serializers.ChoiceField(
        choices=[st.value for st in SortBy], default=SortBy.ALPHABET.value
    )
    sort_order = serializers.ChoiceField(
        choices=[st.value for st in SortOrder], default=SortOrder.ASC.value
    )
    resource_type = serializers.ChoiceField(
        choices=[st.value for st in ResourceType], default=ResourceType.LOOM.value
    )
    authors = serializers.ListField(child=serializers.CharField(), required=False)
    scientific_venues = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    research_fields = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    concepts = serializers.ListField(child=serializers.CharField(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ARRAY_KEYS = ["authors", "scientific_venues", "research_fields", "concepts"]

        if isinstance(self.initial_data, QueryDict):
            qd: QueryDict = self.initial_data
            for key in ARRAY_KEYS:
                if key not in qd and f"{key}[]" in qd:
                    # copy list under the canonical key
                    self.initial_data.setlist(key, qd.getlist(f"{key}[]"))

    def validate(self, data):
        s = data.get("start_year")
        e = data.get("end_year")
        if s is not None and e is not None and s > e:
            raise serializers.ValidationError(
                "start_year cannot be greater than end_year."
            )
        return data


class ArticleSerializer(serializers.Serializer):
    id = serializers.CharField(allow_null=True, required=False)
    article_id = serializers.CharField(allow_null=True, required=False)
    name = serializers.CharField()
    authors = AuthorSerializer(many=True)
    abstract = serializers.CharField()
    contributions = ContributionSerializer(many=True, required=False)
    dois = serializers.CharField(allow_null=True, required=False)
    date_published = serializers.CharField(allow_null=True, required=False)
    entity = serializers.CharField(allow_null=True, required=False)
    external = serializers.URLField(allow_null=True, required=False)
    info = serializers.DictField(allow_null=True, required=False)
    timeline = serializers.DictField(allow_null=True, required=False)
    scientific_venue = JournalSerializer(allow_null=True, required=False)
    publisher = serializers.CharField(allow_null=True, required=False)
    research_fields = ResearchFieldSerializer(many=True, required=False)
    reborn_doi = serializers.CharField(allow_null=True, required=False)
    paper_type = serializers.CharField(allow_null=True, required=False)
    concepts = ConceptSerializer(many=True, required=False)
    reborn_date = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField(allow_null=True, required=False)
    updated_at = serializers.DateTimeField(allow_null=True, required=False)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance


class ArticleWrapperSerializer(serializers.Serializer):
    article = ArticleSerializer()
    statements = StatementSerializer(many=True, required=False)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance


class ArticleStatementsSerializer(serializers.Serializer):
    article = ArticleSerializer()
    statements = StatementSerializer(many=True, required=False)

    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance


class PaperFilterSerializer(serializers.Serializer):
    """Serializer for paper filtering."""

    title = serializers.CharField(allow_null=True, required=False)
    time_range = TimeRangeSerializer(allow_null=True, required=False)
    authors = serializers.ListField(child=serializers.CharField(), required=False)
    scientific_venues = serializers.ListField(
        child=serializers.CharField(), required=False
    )
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


class AutoCompleteItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class AutoCompleteSerializer(serializers.Serializer):
    """Serializer for search queries."""

    items = serializers.ListField(child=AutoCompleteItemSerializer(), required=False)


class CountItemSerializer(serializers.Serializer):
    label = serializers.CharField()
    count = serializers.IntegerField()


class InsightItemsSerializer(serializers.Serializer):
    statistics = serializers.DictField(child=serializers.IntegerField())
    num_programming_languages = CountItemSerializer(many=True)
    num_packages = serializers.DictField(child=CountItemSerializer(many=True))
    data_types = CountItemSerializer(many=True)


class InsightSerializer(serializers.Serializer):
    """Serializer for search queries."""

    items = InsightItemsSerializer(required=False)


def validate_domain(value):
    tib_pattern = r"^https?://service\.tib\.eu/ldmservice/dataset/[\w-]+$"
    local_pattern = r"^https?://localhost/data/[\w-]+/?$"
    if re.match(tib_pattern, value) or re.match(local_pattern, value):
        return value
    raise serializers.ValidationError(
        "URL must be from service.tib.eu/ldmservice/dataset"
    )


class ScraperUrlSerializer(serializers.Serializer):
    url = serializers.URLField(validators=[validate_domain])


class ScraperFlagSerializer(serializers.Serializer):
    confirm_action = serializers.BooleanField()


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
