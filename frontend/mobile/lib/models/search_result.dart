import 'property.dart';

class SearchResultItem {
  final Property property;
  final double similarityScore;
  final double? rrfScore;
  final int? vectorRank;
  final int? ftsRank;

  SearchResultItem({
    required this.property,
    required this.similarityScore,
    this.rrfScore,
    this.vectorRank,
    this.ftsRank,
  });

  factory SearchResultItem.fromJson(Map<String, dynamic> json) {
    return SearchResultItem(
      property: Property.fromJson(json['property'] as Map<String, dynamic>),
      similarityScore: ((json['similarity_score'] as num?) ?? 0).toDouble(),
      rrfScore: (json['rrf_score'] as num?)?.toDouble(),
      vectorRank: json['vector_rank'] as int?,
      ftsRank: json['fts_rank'] as int?,
    );
  }

  int get similarityPercentage => (similarityScore * 100).clamp(0, 100).round();
}

class PropertySearchResponse {
  final int total;
  final int vectorDim;
  final String? query;
  final List<SearchResultItem> results;

  PropertySearchResponse({
    required this.total,
    required this.vectorDim,
    this.query,
    required this.results,
  });

  factory PropertySearchResponse.fromJson(Map<String, dynamic> json) {
    final rawResults = (json['results'] as List<dynamic>?) ?? [];
    return PropertySearchResponse(
      total: (json['total'] as int?) ?? 0,
      vectorDim: (json['vector_dim'] as int?) ?? 768,
      query: json['query'] as String?,
      results: rawResults
          .map((item) => SearchResultItem.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
