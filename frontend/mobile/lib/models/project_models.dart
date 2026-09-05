class ProjectSummary {
  final String id;
  final String name;
  final String slug;
  final String? developer;
  final String status;
  final String city;
  final String? district;
  final List<String> images;
  final double? priceRangeMin;
  final double? priceRangeMax;

  ProjectSummary({
    required this.id,
    required this.name,
    required this.slug,
    this.developer,
    required this.status,
    required this.city,
    this.district,
    this.images = const [],
    this.priceRangeMin,
    this.priceRangeMax,
  });

  factory ProjectSummary.fromJson(Map<String, dynamic> json) {
    return ProjectSummary(
      id: (json['id'] as String?) ?? '',
      name: (json['name'] as String?) ?? '',
      slug: (json['slug'] as String?) ?? '',
      developer: json['developer'] as String?,
      status: (json['status'] as String?) ?? 'under_construction',
      city: (json['city'] as String?) ?? '',
      district: json['district'] as String?,
      images: (json['images'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      priceRangeMin: (json['price_range_min'] as num?)?.toDouble(),
      priceRangeMax: (json['price_range_max'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'slug': slug,
      'developer': developer,
      'status': status,
      'city': city,
      'district': district,
      'images': images,
      'price_range_min': priceRangeMin,
      'price_range_max': priceRangeMax,
    };
  }
}

class Project {
  final String id;
  final String name;
  final String slug;
  final String? developer;
  final String? description;
  final String status;
  final int? totalUnits;
  final int? launchYear;
  final int? handoverYear;
  final String address;
  final String? ward;
  final String? district;
  final String city;
  final double? latitude;
  final double? longitude;
  final List<String> images;
  final String? masterPlanUrl;
  final String? legalStatus;
  final double? priceRangeMin;
  final double? priceRangeMax;
  final List<String> amenities;
  final String? createdAt;
  final String? updatedAt;
  final int activePropertiesCount;
  final int forSaleCount;
  final int forRentCount;
  final double? averagePricePerSqm;

  Project({
    required this.id,
    required this.name,
    required this.slug,
    this.developer,
    this.description,
    required this.status,
    this.totalUnits,
    this.launchYear,
    this.handoverYear,
    required this.address,
    this.ward,
    this.district,
    required this.city,
    this.latitude,
    this.longitude,
    this.images = const [],
    this.masterPlanUrl,
    this.legalStatus,
    this.priceRangeMin,
    this.priceRangeMax,
    this.amenities = const [],
    this.createdAt,
    this.updatedAt,
    this.activePropertiesCount = 0,
    this.forSaleCount = 0,
    this.forRentCount = 0,
    this.averagePricePerSqm,
  });

  factory Project.fromJson(Map<String, dynamic> json) {
    return Project(
      id: (json['id'] as String?) ?? '',
      name: (json['name'] as String?) ?? '',
      slug: (json['slug'] as String?) ?? '',
      developer: json['developer'] as String?,
      description: json['description'] as String?,
      status: (json['status'] as String?) ?? 'under_construction',
      totalUnits: json['total_units'] as int?,
      launchYear: json['launch_year'] as int?,
      handoverYear: json['handover_year'] as int?,
      address: (json['address'] as String?) ?? '',
      ward: json['ward'] as String?,
      district: json['district'] as String?,
      city: (json['city'] as String?) ?? '',
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      images: (json['images'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      masterPlanUrl: json['master_plan_url'] as String?,
      legalStatus: json['legal_status'] as String?,
      priceRangeMin: (json['price_range_min'] as num?)?.toDouble(),
      priceRangeMax: (json['price_range_max'] as num?)?.toDouble(),
      amenities: (json['amenities'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      createdAt: json['created_at'] as String?,
      updatedAt: json['updated_at'] as String?,
      activePropertiesCount: (json['active_properties_count'] as int?) ?? 0,
      forSaleCount: (json['for_sale_count'] as int?) ?? 0,
      forRentCount: (json['for_rent_count'] as int?) ?? 0,
      averagePricePerSqm: (json['average_price_per_sqm'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'slug': slug,
      'developer': developer,
      'description': description,
      'status': status,
      'total_units': totalUnits,
      'launch_year': launchYear,
      'handover_year': handoverYear,
      'address': address,
      'ward': ward,
      'district': district,
      'city': city,
      'latitude': latitude,
      'longitude': longitude,
      'images': images,
      'master_plan_url': masterPlanUrl,
      'legal_status': legalStatus,
      'price_range_min': priceRangeMin,
      'price_range_max': priceRangeMax,
      'amenities': amenities,
      'created_at': createdAt,
      'updated_at': updatedAt,
      'active_properties_count': activePropertiesCount,
      'for_sale_count': forSaleCount,
      'for_rent_count': forRentCount,
      'average_price_per_sqm': averagePricePerSqm,
    };
  }
}

class PaginatedProjects {
  final List<Project> items;
  final int total;
  final int page;
  final int size;
  final int pages;

  PaginatedProjects({
    required this.items,
    required this.total,
    required this.page,
    required this.size,
    required this.pages,
  });

  factory PaginatedProjects.fromJson(Map<String, dynamic> json) {
    return PaginatedProjects(
      items: (json['items'] as List<dynamic>?)
              ?.map((e) => Project.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      total: (json['total'] as int?) ?? 0,
      page: (json['page'] as int?) ?? 1,
      size: (json['size'] as int?) ?? 20,
      pages: (json['pages'] as int?) ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'items': items.map((e) => e.toJson()).toList(),
      'total': total,
      'page': page,
      'size': size,
      'pages': pages,
    };
  }
}
