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
  final String? appointmentDate;
  final String? appointmentStart;
  final String? appointmentEnd;
  final String? calendarGoogleUrl;

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
    this.appointmentDate,
    this.appointmentStart,
    this.appointmentEnd,
    this.calendarGoogleUrl,
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
      appointmentDate: json['appointment_date'] as String?,
      appointmentStart: (json['start_time'] ?? json['appointment_start']) as String?,
      appointmentEnd: (json['end_time'] ?? json['appointment_end']) as String?,
      calendarGoogleUrl: (json['google_calendar_url'] ?? json['calendar_google_url']) as String?,
    );
  }
}

class ViewingSlot {
  final String date;
  final String startTime;
  final String endTime;
  const ViewingSlot({required this.date, required this.startTime, required this.endTime});
  factory ViewingSlot.fromJson(Map<String, dynamic> json) => ViewingSlot(date: json['date'] as String, startTime: json['start_time'] as String, endTime: json['end_time'] as String);
}

class ViewingScheduleWindow {
  final int weekday;
  final String startTime;
  final String endTime;
  final int slotDurationMinutes;
  final bool isActive;
  const ViewingScheduleWindow({required this.weekday, required this.startTime, required this.endTime, this.slotDurationMinutes = 30, this.isActive = true});
  factory ViewingScheduleWindow.fromJson(Map<String, dynamic> json) => ViewingScheduleWindow(weekday: json['weekday'] as int, startTime: json['start_time'] as String, endTime: json['end_time'] as String, slotDurationMinutes: json['slot_duration_minutes'] as int? ?? 30, isActive: json['is_active'] as bool? ?? true);
  Map<String, dynamic> toJson() => {'weekday': weekday, 'start_time': startTime, 'end_time': endTime, 'slot_duration_minutes': slotDurationMinutes, 'is_active': isActive};
}

class HostDashboardStats {
  final int totalProperties;
  final int totalUnits;
  final int occupiedUnits;
  final double occupancyRate;
  final double estimatedMonthlyRevenue;
  final int pendingInquiriesCount;
  final int unpaidInvoicesCount;

  HostDashboardStats({
    required this.totalProperties,
    required this.totalUnits,
    required this.occupiedUnits,
    required this.occupancyRate,
    required this.estimatedMonthlyRevenue,
    required this.pendingInquiriesCount,
    this.unpaidInvoicesCount = 0,
  });

  factory HostDashboardStats.fromJson(Map<String, dynamic> json) {
    return HostDashboardStats(
      totalProperties: json['total_properties'] as int? ?? 0,
      totalUnits: json['total_units'] as int? ?? 0,
      occupiedUnits: json['occupied_units'] as int? ?? 0,
      occupancyRate: (json['occupancy_rate'] as num?)?.toDouble() ?? 0.0,
      estimatedMonthlyRevenue: (json['estimated_monthly_revenue'] as num?)?.toDouble() ?? 0.0,
      pendingInquiriesCount: json['pending_inquiries_count'] as int? ?? 0,
      unpaidInvoicesCount: json['unpaid_invoices_count'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'total_properties': totalProperties,
      'total_units': totalUnits,
      'occupied_units': occupiedUnits,
      'occupancy_rate': occupancyRate,
      'estimated_monthly_revenue': estimatedMonthlyRevenue,
      'pending_inquiries_count': pendingInquiriesCount,
      'unpaid_invoices_count': unpaidInvoicesCount,
    };
  }
}

class RentalContract {
  final String id;
  final String unitId;
  final String propertyId;
  final String hostId;
  final String tenantId;
  final String tenantName;
  final String tenantPhone;
  final String startDate;
  final String? endDate;
  final double rentalPrice;
  final double depositAmount;
  final int paymentCycleMonths;
  final double electricityRate;
  final double waterRate;
  final String waterBillingType;
  final double serviceFee;
  final String status;
  final String createdAt;
  final String updatedAt;
  final RentalUnit? unit;

  RentalContract({
    required this.id,
    required this.unitId,
    required this.propertyId,
    required this.hostId,
    required this.tenantId,
    required this.tenantName,
    required this.tenantPhone,
    required this.startDate,
    this.endDate,
    required this.rentalPrice,
    required this.depositAmount,
    this.paymentCycleMonths = 1,
    this.electricityRate = 3500.0,
    this.waterRate = 20000.0,
    this.waterBillingType = 'per_m3',
    this.serviceFee = 0.0,
    this.status = 'active',
    required this.createdAt,
    required this.updatedAt,
    this.unit,
  });

  factory RentalContract.fromJson(Map<String, dynamic> json) {
    return RentalContract(
      id: json['id'] as String? ?? '',
      unitId: json['unit_id'] as String? ?? '',
      propertyId: json['property_id'] as String? ?? '',
      hostId: json['host_id'] as String? ?? '',
      tenantId: json['tenant_id'] as String? ?? '',
      tenantName: json['tenant_name'] as String? ?? '',
      tenantPhone: json['tenant_phone'] as String? ?? '',
      startDate: json['start_date'] as String? ?? '',
      endDate: json['end_date'] as String?,
      rentalPrice: (json['rental_price'] as num?)?.toDouble() ?? 0.0,
      depositAmount: (json['deposit_amount'] as num?)?.toDouble() ?? 0.0,
      paymentCycleMonths: json['payment_cycle_months'] as int? ?? 1,
      electricityRate: (json['electricity_rate'] as num?)?.toDouble() ?? 3500.0,
      waterRate: (json['water_rate'] as num?)?.toDouble() ?? 20000.0,
      waterBillingType: json['water_billing_type'] as String? ?? 'per_m3',
      serviceFee: (json['service_fee'] as num?)?.toDouble() ?? 0.0,
      status: json['status'] as String? ?? 'active',
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
      unit: json['unit'] != null ? RentalUnit.fromJson(json['unit'] as Map<String, dynamic>) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'unit_id': unitId,
      'property_id': propertyId,
      'host_id': hostId,
      'tenant_id': tenantId,
      'tenant_name': tenantName,
      'tenant_phone': tenantPhone,
      'start_date': startDate,
      'end_date': endDate,
      'rental_price': rentalPrice,
      'deposit_amount': depositAmount,
      'payment_cycle_months': paymentCycleMonths,
      'electricity_rate': electricityRate,
      'water_rate': waterRate,
      'water_billing_type': waterBillingType,
      'service_fee': serviceFee,
      'status': status,
      'created_at': createdAt,
      'updated_at': updatedAt,
      if (unit != null) 'unit': unit!.toJson(),
    };
  }
}

class MonthlyInvoice {
  final String id;
  final String contractId;
  final String unitId;
  final String hostId;
  final String tenantId;
  final String billingMonth;
  final double roomAmount;
  final double electricityPreviousIndex;
  final double electricityCurrentIndex;
  final double electricityRate;
  final double electricityAmount;
  final double? waterPreviousIndex;
  final double? waterCurrentIndex;
  final double waterRate;
  final double waterAmount;
  final double serviceAmount;
  final double otherAmount;
  final double totalAmount;
  final String status;
  final String dueDate;
  final String? paidAt;
  final String? notes;
  final String? lastRemindedAt;
  final String createdAt;
  final String updatedAt;
  final RentalUnit? unit;
  final RentalContract? contract;

  MonthlyInvoice({
    required this.id,
    required this.contractId,
    required this.unitId,
    required this.hostId,
    required this.tenantId,
    required this.billingMonth,
    required this.roomAmount,
    required this.electricityPreviousIndex,
    required this.electricityCurrentIndex,
    required this.electricityRate,
    required this.electricityAmount,
    this.waterPreviousIndex,
    this.waterCurrentIndex,
    required this.waterRate,
    required this.waterAmount,
    this.serviceAmount = 0.0,
    this.otherAmount = 0.0,
    required this.totalAmount,
    this.status = 'pending',
    required this.dueDate,
    this.paidAt,
    this.notes,
    this.lastRemindedAt,
    required this.createdAt,
    required this.updatedAt,
    this.unit,
    this.contract,
  });

  factory MonthlyInvoice.fromJson(Map<String, dynamic> json) {
    return MonthlyInvoice(
      id: json['id'] as String? ?? '',
      contractId: json['contract_id'] as String? ?? '',
      unitId: json['unit_id'] as String? ?? '',
      hostId: json['host_id'] as String? ?? '',
      tenantId: json['tenant_id'] as String? ?? '',
      billingMonth: json['billing_month'] as String? ?? '',
      roomAmount: (json['room_amount'] as num?)?.toDouble() ?? 0.0,
      electricityPreviousIndex: (json['electricity_previous_index'] as num?)?.toDouble() ?? 0.0,
      electricityCurrentIndex: (json['electricity_current_index'] as num?)?.toDouble() ?? 0.0,
      electricityRate: (json['electricity_rate'] as num?)?.toDouble() ?? 3500.0,
      electricityAmount: (json['electricity_amount'] as num?)?.toDouble() ?? 0.0,
      waterPreviousIndex: (json['water_previous_index'] as num?)?.toDouble(),
      waterCurrentIndex: (json['water_current_index'] as num?)?.toDouble(),
      waterRate: (json['water_rate'] as num?)?.toDouble() ?? 20000.0,
      waterAmount: (json['water_amount'] as num?)?.toDouble() ?? 0.0,
      serviceAmount: (json['service_amount'] as num?)?.toDouble() ?? 0.0,
      otherAmount: (json['other_amount'] as num?)?.toDouble() ?? 0.0,
      totalAmount: (json['total_amount'] as num?)?.toDouble() ?? 0.0,
      status: json['status'] as String? ?? 'pending',
      dueDate: json['due_date'] as String? ?? '',
      paidAt: json['paid_at'] as String?,
      notes: json['notes'] as String?,
      lastRemindedAt: json['last_reminded_at'] as String?,
      createdAt: json['created_at'] as String? ?? '',
      updatedAt: json['updated_at'] as String? ?? '',
      unit: json['unit'] != null ? RentalUnit.fromJson(json['unit'] as Map<String, dynamic>) : null,
      contract: json['contract'] != null ? RentalContract.fromJson(json['contract'] as Map<String, dynamic>) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'contract_id': contractId,
      'unit_id': unitId,
      'host_id': hostId,
      'tenant_id': tenantId,
      'billing_month': billingMonth,
      'room_amount': roomAmount,
      'electricity_previous_index': electricityPreviousIndex,
      'electricity_current_index': electricityCurrentIndex,
      'electricity_rate': electricityRate,
      'electricity_amount': electricityAmount,
      'water_previous_index': waterPreviousIndex,
      'water_current_index': waterCurrentIndex,
      'water_rate': waterRate,
      'water_amount': waterAmount,
      'service_amount': serviceAmount,
      'other_amount': otherAmount,
      'total_amount': totalAmount,
      'status': status,
      'due_date': dueDate,
      'paid_at': paidAt,
      'notes': notes,
      'last_reminded_at': lastRemindedAt,
      'created_at': createdAt,
      'updated_at': updatedAt,
      if (unit != null) 'unit': unit!.toJson(),
      if (contract != null) 'contract': contract!.toJson(),
    };
  }
}

class DepositTransaction {
  final String id;
  final String unitId;
  final String? inquiryId;
  final String tenantId;
  final String hostId;
  final double amount;
  final String referenceCode;
  final String paymentMethod;
  final String vietqrUrl;
  final String status;
  final String expiresAt;
  final String? paidAt;
  final String createdAt;

  DepositTransaction({
    required this.id,
    required this.unitId,
    this.inquiryId,
    required this.tenantId,
    required this.hostId,
    required this.amount,
    required this.referenceCode,
    this.paymentMethod = 'vietqr',
    required this.vietqrUrl,
    this.status = 'pending',
    required this.expiresAt,
    this.paidAt,
    required this.createdAt,
  });

  bool get isSuccess => status == 'success';
  bool get isExpired => status == 'expired';

  factory DepositTransaction.fromJson(Map<String, dynamic> json) {
    return DepositTransaction(
      id: json['id'] as String? ?? '',
      unitId: json['unit_id'] as String? ?? '',
      inquiryId: json['inquiry_id'] as String?,
      tenantId: json['tenant_id'] as String? ?? '',
      hostId: json['host_id'] as String? ?? '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0.0,
      referenceCode: json['reference_code'] as String? ?? '',
      paymentMethod: json['payment_method'] as String? ?? 'vietqr',
      vietqrUrl: json['vietqr_url'] as String? ?? '',
      status: json['status'] as String? ?? 'pending',
      expiresAt: json['expires_at'] as String? ?? '',
      paidAt: json['paid_at'] as String?,
      createdAt: json['created_at'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'unit_id': unitId,
      'inquiry_id': inquiryId,
      'tenant_id': tenantId,
      'host_id': hostId,
      'amount': amount,
      'reference_code': referenceCode,
      'payment_method': paymentMethod,
      'vietqr_url': vietqrUrl,
      'status': status,
      'expires_at': expiresAt,
      'paid_at': paidAt,
      'created_at': createdAt,
    };
  }
}

