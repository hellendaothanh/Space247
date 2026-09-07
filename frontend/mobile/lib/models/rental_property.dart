class RentalUnit {
  final String id;
  final String propertyId;
  final String unitNumber;
  final int? floor;
  final double areaSqm;
  final double price;
  final double? deposit;
  final String status;
  final String furnishing;
  final bool hasMezzanine;
  final bool hasPrivateBathroom;
  final int? maxOccupants;
  final List<String> images;

  RentalUnit({
    required this.id,
    required this.propertyId,
    required this.unitNumber,
    this.floor,
    required this.areaSqm,
    required this.price,
    this.deposit,
    this.status = 'available',
    this.furnishing = 'basic',
    this.hasMezzanine = false,
    this.hasPrivateBathroom = true,
    this.maxOccupants,
    this.images = const [],
  });

  bool get isAvailable => status == 'available';

  factory RentalUnit.fromJson(Map<String, dynamic> json) {
    return RentalUnit(
      id: json['id'] as String? ?? '',
      propertyId: json['property_id'] as String? ?? '',
      unitNumber: json['unit_number'] as String? ?? '',
      floor: json['floor'] as int?,
      areaSqm: (json['area_sqm'] as num?)?.toDouble() ?? 0.0,
      price: (json['price'] as num?)?.toDouble() ?? 0.0,
      deposit: (json['deposit'] as num?)?.toDouble(),
      status: json['status'] as String? ?? 'available',
      furnishing: json['furnishing'] as String? ?? 'basic',
      hasMezzanine: json['has_mezzanine'] as bool? ?? false,
      hasPrivateBathroom: json['has_private_bathroom'] as bool? ?? true,
      maxOccupants: json['max_occupants'] as int?,
      images: (json['images'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'property_id': propertyId,
      'unit_number': unitNumber,
      'floor': floor,
      'area_sqm': areaSqm,
      'price': price,
      'deposit': deposit,
      'status': status,
      'furnishing': furnishing,
      'has_mezzanine': hasMezzanine,
      'has_private_bathroom': hasPrivateBathroom,
      'max_occupants': maxOccupants,
      'images': images,
    };
  }
}

class RentalProperty {
  final String id;
  final String hostId;
  final String name;
  final String description;
  final String propertyModel; // 'boarding_house' | 'serviced_apartment' | 'homestay'
  final String address;
  final String? ward;
  final String? district;
  final String city;
  final double? latitude;
  final double? longitude;
  final Map<String, dynamic> sharedCosts;
  final Map<String, dynamic> sharedRules;
  final List<String> images;
  final bool isActive;
  final int totalUnitsCount;
  final int availableUnitsCount;
  final double? minPrice;
  final double? maxPrice;
  final List<RentalUnit> units;

  RentalProperty({
    required this.id,
    required this.hostId,
    required this.name,
    this.description = '',
    this.propertyModel = 'boarding_house',
    required this.address,
    this.ward,
    this.district,
    required this.city,
    this.latitude,
    this.longitude,
    this.sharedCosts = const {},
    this.sharedRules = const {},
    this.images = const [],
    this.isActive = true,
    this.totalUnitsCount = 0,
    this.availableUnitsCount = 0,
    this.minPrice,
    this.maxPrice,
    this.units = const [],
  });

  bool get isHomestay => propertyModel == 'homestay';
  String get priceUnitLabel => isHomestay ? '/đêm' : '/tháng';

  factory RentalProperty.fromJson(Map<String, dynamic> json) {
    final rawUnits = json['units'] as List<dynamic>? ?? [];
    return RentalProperty(
      id: json['id'] as String? ?? '',
      hostId: json['host_id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      description: json['description'] as String? ?? '',
      propertyModel: json['property_model'] as String? ?? 'boarding_house',
      address: json['address'] as String? ?? '',
      ward: json['ward'] as String?,
      district: json['district'] as String?,
      city: json['city'] as String? ?? '',
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      sharedCosts: (json['shared_costs'] as Map<String, dynamic>?) ?? {},
      sharedRules: (json['shared_rules'] as Map<String, dynamic>?) ?? {},
      images: (json['images'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      isActive: json['is_active'] as bool? ?? true,
      totalUnitsCount: json['total_units_count'] as int? ?? rawUnits.length,
      availableUnitsCount: json['available_units_count'] as int? ?? 0,
      minPrice: (json['min_price'] as num?)?.toDouble(),
      maxPrice: (json['max_price'] as num?)?.toDouble(),
      units: rawUnits.map((u) => RentalUnit.fromJson(u as Map<String, dynamic>)).toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'host_id': hostId,
      'name': name,
      'description': description,
      'property_model': propertyModel,
      'address': address,
      'ward': ward,
      'district': district,
      'city': city,
      'latitude': latitude,
      'longitude': longitude,
      'shared_costs': sharedCosts,
      'shared_rules': sharedRules,
      'images': images,
      'is_active': isActive,
      'total_units_count': totalUnitsCount,
      'available_units_count': availableUnitsCount,
      'min_price': minPrice,
      'max_price': maxPrice,
      'units': units.map((u) => u.toJson()).toList(),
    };
  }
}

class RentalInquiry {
  final String id;
  final String unitId;
  final String tenantId;
  final String hostId;
  final String inquiryType; // 'view_appointment' | 'booking_request'
  final DateTime? scheduledTime;
  final String? tenantName;
  final String? tenantPhone;
  final String? message;
  final String status;

  RentalInquiry({
    required this.id,
    required this.unitId,
    required this.tenantId,
    required this.hostId,
    this.inquiryType = 'view_appointment',
    this.scheduledTime,
    this.tenantName,
    this.tenantPhone,
    this.message,
    this.status = 'pending',
  });

  factory RentalInquiry.fromJson(Map<String, dynamic> json) {
    return RentalInquiry(
      id: json['id'] as String? ?? '',
      unitId: json['unit_id'] as String? ?? '',
      tenantId: json['tenant_id'] as String? ?? '',
      hostId: json['host_id'] as String? ?? '',
      inquiryType: json['inquiry_type'] as String? ?? 'view_appointment',
      scheduledTime: json['scheduled_time'] != null
          ? DateTime.tryParse(json['scheduled_time'] as String)
          : null,
      tenantName: json['tenant_name'] as String?,
      tenantPhone: json['tenant_phone'] as String?,
      message: json['message'] as String?,
      status: json['status'] as String? ?? 'pending',
    );
  }
}
