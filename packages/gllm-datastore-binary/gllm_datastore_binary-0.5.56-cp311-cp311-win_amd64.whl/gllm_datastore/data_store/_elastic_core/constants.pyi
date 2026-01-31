class ELASTIC_RESPONSE_KEYS:
    """Keys used in Elasticsearch/OpenSearch response dictionaries.

    Attributes:
        SUGGEST (str): Key for suggestions in the response.
        AGGREGATIONS (str): Key for aggregations in the response.
        HITS (str): Key for hits in the response.
        HIGHLIGHT (str): Key for highlights in hit objects.
        OPTIONS (str): Key for options in suggestion objects.
        BUCKETS (str): Key for buckets in aggregation objects.
        TEXT (str): Key for text in suggestion option objects.
        SOURCE (str): Key for source document in hit objects.
        ID (str): Key for document ID in hit objects.
        COUNT (str): Key for count in count response.
        INDEX (str): Key for index name in bulk operations.
    """
    SUGGEST: str
    AGGREGATIONS: str
    HITS: str
    HIGHLIGHT: str
    OPTIONS: str
    BUCKETS: str
    TEXT: str
    SOURCE: str
    ID: str
    COUNT: str
    INDEX: str
