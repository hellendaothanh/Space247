class Property {
  final String id;
  final String? userId;
  final String title;
  final String description;
  final String propertyType;
  final String listingType;
  final double price;
  final String currency;
  final double areaSqm;
  final int? numBedrooms;
  final int? numBathrooms;
  final String address;
  final String? ward;
  final String? district;
  final String city;
  final double? latitude;
  final double? longitude;
  final String status;
  final String? createdAt;
  final String? updatedAt;

  Property({
    required this.id,
    this.userId,
    required this.title,
    required this.description,
    required this.propertyType,
    required this.listingType,
    required this.price,
    this.currency = 'VND',
    required this.areaSqm,
    this.numBedrooms,
    this.numBathrooms,
    required this.address,
    this.ward,
    this.district,
    required this.city,
    this.latitude,
    this.longitude,
    required this.status,
    this.createdAt,
    this.updatedAt,
  });

  factory Property.fromJson(Map<String, dynamic> json) {
    return Property(
      id: json['id'] as String,
      userId: json['user_id'] as String?,
      title: (json['title'] as String?) ?? '',
      description: (json['description'] as String?) ?? '',
      propertyType: (json['property_type'] as String?) ?? 'apartment',
      listingType: (json['listing_type'] as String?) ?? 'sale',
      price: ((json['price'] as num?) ?? 0).toDouble(),
      currency: (json['currency'] as String?) ?? 'VND',
      areaSqm: ((json['area_sqm'] as num?) ?? 0).toDouble(),
      numBedrooms: json['num_bedrooms'] as int?,
      numBathrooms: json['num_bathrooms'] as int?,
      address: (json['address'] as String?) ?? '',
      ward: json['ward'] as String?,
      district: json['district'] as String?,
      city: (json['city'] as String?) ?? '',
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      status: (json['status'] as String?) ?? 'active',
      createdAt: json['created_at'] as String?,
      updatedAt: json['updated_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'title': title,
      'description': description,
      'property_type': propertyType,
      'listing_type': listingType,
      'price': price,
      'currency': currency,
      'area_sqm': areaSqm,
      'num_bedrooms': numBedrooms,
      'num_bathrooms': numBathrooms,
      'address': address,
      'ward': ward,
      'district': district,
      'city': city,
      'latitude': latitude,
      'longitude': longitude,
      'status': status,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }
}
