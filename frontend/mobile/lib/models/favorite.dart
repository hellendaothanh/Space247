class ToggleFavoriteResponse {
  final String propertyId;
  final bool isFavorite;
  final String message;

  ToggleFavoriteResponse({
    required this.propertyId,
    required this.isFavorite,
    required this.message,
  });

  factory ToggleFavoriteResponse.fromJson(Map<String, dynamic> json) {
    return ToggleFavoriteResponse(
      propertyId: json['property_id'] as String,
      isFavorite: json['is_favorite'] as bool,
      message: (json['message'] as String?) ?? '',
    );
  }
}
