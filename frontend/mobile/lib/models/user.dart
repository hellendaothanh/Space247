class User {
  final String id;
  final String email;
  final String fullName;
  final String? phone;
  final String? avatarUrl;
  final String role;
  final bool isActive;
  final bool phoneVerified;
  final String? lastLoginAt;
  final String? createdAt;
  final String? updatedAt;

  User({
    required this.id,
    required this.email,
    required this.fullName,
    this.phone,
    this.avatarUrl,
    required this.role,
    required this.isActive,
    this.phoneVerified = false,
    this.lastLoginAt,
    this.createdAt,
    this.updatedAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      email: json['email'] as String,
      fullName: (json['full_name'] ?? json['fullName']) as String,
      phone: (json['phone'] ?? json['phone_number']) as String?,
      avatarUrl: json['avatar_url'] as String?,
      role: (json['role'] as String?) ?? 'user',
      isActive: (json['is_active'] ?? json['isActive'] ?? true) as bool,
      phoneVerified: (json['phone_verified'] ?? false) as bool,
      lastLoginAt: json['last_login_at'] as String?,
      createdAt: json['created_at'] as String?,
      updatedAt: json['updated_at'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'phone': phone,
      'avatar_url': avatarUrl,
      'role': role,
      'is_active': isActive,
      'phone_verified': phoneVerified,
      'last_login_at': lastLoginAt,
      'created_at': createdAt,
      'updated_at': updatedAt,
    };
  }
}

class AuthTokenResponse {
  final String accessToken;
  final String tokenType;
  final User user;

  AuthTokenResponse({
    required this.accessToken,
    required this.tokenType,
    required this.user,
  });

  factory AuthTokenResponse.fromJson(Map<String, dynamic> json) {
    return AuthTokenResponse(
      accessToken: json['access_token'] as String,
      tokenType: (json['token_type'] as String?) ?? 'bearer',
      user: User.fromJson(json['user'] as Map<String, dynamic>),
    );
  }
}
