class ExtractedSpecs {
  final double? areaSqm;
  final int? numBedrooms;
  final int? numBathrooms;
  final String? orientation;
  final String? legalStatus;
  final double? frontageMeters;
  final double? suggestedPrice;
  final List<String> amenities;

  ExtractedSpecs({
    this.areaSqm,
    this.numBedrooms,
    this.numBathrooms,
    this.orientation,
    this.legalStatus,
    this.frontageMeters,
    this.suggestedPrice,
    this.amenities = const [],
  });

  factory ExtractedSpecs.fromJson(Map<String, dynamic> json) {
    return ExtractedSpecs(
      areaSqm: json['area_sqm'] != null ? (json['area_sqm'] as num).toDouble() : null,
      numBedrooms: json['num_bedrooms'] as int?,
      numBathrooms: json['num_bathrooms'] as int?,
      orientation: json['orientation'] as String?,
      legalStatus: json['legal_status'] as String?,
      frontageMeters: json['frontage_meters'] != null ? (json['frontage_meters'] as num).toDouble() : null,
      suggestedPrice: json['suggested_price'] != null ? (json['suggested_price'] as num).toDouble() : null,
      amenities: (json['amenities'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
    );
  }
}

class GenerateListingResponse {
  final String titleSeo;
  final String descriptionMarkdown;
  final ExtractedSpecs extractedSpecs;

  GenerateListingResponse({
    required this.titleSeo,
    required this.descriptionMarkdown,
    required this.extractedSpecs,
  });

  factory GenerateListingResponse.fromJson(Map<String, dynamic> json) {
    return GenerateListingResponse(
      titleSeo: json['title_seo'] as String? ?? '',
      descriptionMarkdown: json['description_markdown'] as String? ?? '',
      extractedSpecs: ExtractedSpecs.fromJson(
        json['extracted_specs'] as Map<String, dynamic>? ?? {},
      ),
    );
  }
}

class ComparableProperty {
  final String id;
  final String title;
  final double price;
  final double areaSqm;
  final double pricePerSqm;
  final double distanceKm;
  final String address;
  final String propertyType;

  ComparableProperty({
    required this.id,
    required this.title,
    required this.price,
    required this.areaSqm,
    required this.pricePerSqm,
    required this.distanceKm,
    required this.address,
    required this.propertyType,
  });

  factory ComparableProperty.fromJson(Map<String, dynamic> json) {
    return ComparableProperty(
      id: json['id']?.toString() ?? '',
      title: json['title'] as String? ?? '',
      price: (json['price'] as num?)?.toDouble() ?? 0.0,
      areaSqm: (json['area_sqm'] as num?)?.toDouble() ?? 0.0,
      pricePerSqm: (json['price_per_sqm'] as num?)?.toDouble() ?? 0.0,
      distanceKm: (json['distance_km'] as num?)?.toDouble() ?? 0.0,
      address: json['address'] as String? ?? '',
      propertyType: json['property_type'] as String? ?? '',
    );
  }
}

class ValuationResponse {
  final double estimatedPricePerSqm;
  final double estimatedTotalPrice;
  final double priceRangeLow;
  final double priceRangeHigh;
  final double confidenceScore;
  final String marketTrend;
  final double radiusUsedKm;
  final List<ComparableProperty> comparableProperties;
  final double? deviationPercentage;
  final String? pricingAdvice;

  ValuationResponse({
    required this.estimatedPricePerSqm,
    required this.estimatedTotalPrice,
    required this.priceRangeLow,
    required this.priceRangeHigh,
    required this.confidenceScore,
    required this.marketTrend,
    required this.radiusUsedKm,
    required this.comparableProperties,
    this.deviationPercentage,
    this.pricingAdvice,
  });

  factory ValuationResponse.fromJson(Map<String, dynamic> json) {
    return ValuationResponse(
      estimatedPricePerSqm: (json['estimated_price_per_sqm'] as num?)?.toDouble() ?? 0.0,
      estimatedTotalPrice: (json['estimated_total_price'] as num?)?.toDouble() ?? 0.0,
      priceRangeLow: (json['price_range_low'] as num?)?.toDouble() ?? 0.0,
      priceRangeHigh: (json['price_range_high'] as num?)?.toDouble() ?? 0.0,
      confidenceScore: (json['confidence_score'] as num?)?.toDouble() ?? 0.0,
      marketTrend: json['market_trend'] as String? ?? 'stable',
      radiusUsedKm: (json['radius_used_km'] as num?)?.toDouble() ?? 2.5,
      comparableProperties: (json['comparable_properties'] as List<dynamic>?)
              ?.map((e) => ComparableProperty.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      deviationPercentage: (json['deviation_percentage'] as num?)?.toDouble(),
      pricingAdvice: json['pricing_advice'] as String?,
    );
  }
}
