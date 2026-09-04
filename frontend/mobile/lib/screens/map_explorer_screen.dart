import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:latlong2/latlong.dart';
import '../providers/app_providers.dart';
import '../models/property.dart';
import '../core/theme.dart';
import '../core/utils.dart';
import 'property_detail_screen.dart';

// Helper aliases to maintain consistency with theme & utils
class AppColors {
  static const Color primary = AppTheme.primaryColor;
  static const Color textPrimary = AppTheme.textPrimary;
  static const Color textSecondary = AppTheme.textSecondary;
  static const Color surface = AppTheme.surfaceColor;
  static const Color background = AppTheme.backgroundColor;
}

class AppUtils {
  static String formatPrice(num price) => Formatters.formatPrice(price);
}

class MapExplorerScreen extends ConsumerStatefulWidget {
  const MapExplorerScreen({super.key});

  @override
  ConsumerState<MapExplorerScreen> createState() => _MapExplorerScreenState();
}

class _MapExplorerScreenState extends ConsumerState<MapExplorerScreen> {
  final MapController _mapController = MapController();

  // Isochrone parameters
  String _landmark = 'Keangnam';
  int _durationMinutes = 15;
  String _transportMode = 'motorcycle';
  bool _isLoadingIsochrone = false;
  List<LatLng> _isochronePolygon = [];
  List<Property> _filteredProperties = [];
  LatLng? _landmarkLocation;
  String? _landmarkName;

  // Amenity POIs
  String? _activeAmenityCategory;
  bool _isLoadingAmenities = false;
  List<Map<String, dynamic>> _amenityPois = [];

  // Selected property to preview
  Property? _selectedProperty;

  final List<Map<String, String>> _popularLandmarks = [
    {'name': 'Keangnam Landmark 72 (Hà Nội)', 'query': 'Keangnam'},
    {'name': 'Chợ Bến Thành (TP.HCM)', 'query': 'Chợ Bến Thành'},
    {'name': 'Landmark 81 (TP.HCM)', 'query': 'Landmark 81'},
    {'name': 'Hồ Gươm (Hà Nội)', 'query': 'Hồ Gươm'},
    {'name': 'ĐH Bách Khoa Hà Nội', 'query': 'Đại học Bách Khoa Hà Nội'},
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _runIsochroneSearch();
    });
  }

  Future<void> _runIsochroneSearch() async {
    setState(() {
      _isLoadingIsochrone = true;
    });

    try {
      final dio = ref.read(apiClientProvider).dio;
      final response = await dio.post(
        '/api/v1/spatial/isochrone-search',
        data: {
          'target_landmark': _landmark,
          'max_duration_minutes': _durationMinutes,
          'transport_mode': _transportMode,
        },
      );

      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        final targetLoc = data['target_location'] as Map<String, dynamic>;
        final centerLat = (targetLoc['latitude'] as num).toDouble();
        final centerLng = (targetLoc['longitude'] as num).toDouble();

        // Parse Isochrone GeoJSON coordinates
        final geojson = data['isochrone_geojson'] as Map<String, dynamic>;
        final features = geojson['features'] as List<dynamic>;
        List<LatLng> polygonPts = [];

        if (features.isNotEmpty) {
          final geom = features[0]['geometry'] as Map<String, dynamic>;
          final coordsList = (geom['coordinates'] as List<dynamic>)[0] as List<dynamic>;
          for (final coord in coordsList) {
            final lng = (coord[0] as num).toDouble();
            final lat = (coord[1] as num).toDouble();
            polygonPts.add(LatLng(lat, lng));
          }
        }

        // Parse matching properties
        final propItems = data['properties'] as List<dynamic>;
        List<Property> props = [];
        for (final item in propItems) {
          final propData = item['property'] as Map<String, dynamic>;
          props.add(Property.fromJson(propData));
        }

        setState(() {
          _landmarkLocation = LatLng(centerLat, centerLng);
          _landmarkName = targetLoc['name']?.toString() ?? _landmark;
          _isochronePolygon = polygonPts;
          _filteredProperties = props;
          _isLoadingIsochrone = false;
        });

        // Center map on landmark
        _mapController.move(LatLng(centerLat, centerLng), 13.5);
      }
    } catch (e) {
      setState(() {
        _isLoadingIsochrone = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Lỗi tính toán vùng di chuyển: $e'),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
    }
  }

  Future<void> _toggleAmenity(String category) async {
    if (_activeAmenityCategory == category) {
      setState(() {
        _activeAmenityCategory = null;
        _amenityPois = [];
      });
      return;
    }

    setState(() {
      _activeAmenityCategory = category;
      _isLoadingAmenities = true;
    });

    try {
      final dio = ref.read(apiClientProvider).dio;
      final response = await dio.get(
        '/api/v1/spatial/amenities/heatmap',
        queryParameters: {
          'category': category,
          if (_landmarkLocation != null) ...{
            'center_lat': _landmarkLocation!.latitude,
            'center_lng': _landmarkLocation!.longitude,
            'radius_km': 10.0,
          }
        },
      );

      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;
        final pois = (data['pois'] as List<dynamic>).cast<Map<String, dynamic>>();

        setState(() {
          _amenityPois = pois;
          _isLoadingAmenities = false;
        });
      }
    } catch (e) {
      setState(() {
        _isLoadingAmenities = false;
      });
    }
  }

  void _showIsochroneFilterSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        int tempDuration = _durationMinutes;
        String tempMode = _transportMode;
        TextEditingController landmarkCtrl = TextEditingController(text: _landmark);

        return StatefulBuilder(
          builder: (context, setSheetState) {
            return Container(
              padding: const EdgeInsets.all(20),
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
              ),
              child: SafeArea(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(
                        width: 40,
                        height: 4,
                        decoration: BoxDecoration(
                          color: Colors.grey[300],
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Bộ lọc Di chuyển Thông minh (Isochrone)',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: landmarkCtrl,
                      decoration: InputDecoration(
                        labelText: 'Điểm mốc (Nơi làm việc, trường học)',
                        prefixIcon: const Icon(Icons.location_on, color: AppColors.primary),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      ),
                    ),
                    const SizedBox(height: 10),
                    // Quick landmark chips
                    Wrap(
                      spacing: 8,
                      children: _popularLandmarks.map((lm) {
                        return ActionChip(
                          label: Text(lm['name']!, style: const TextStyle(fontSize: 11)),
                          onPressed: () {
                            setSheetState(() {
                              landmarkCtrl.text = lm['query']!;
                            });
                          },
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Phương tiện di chuyển',
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        _buildModeButton('motorcycle', 'Xe máy', Icons.two_wheeler, tempMode, (m) {
                          setSheetState(() => tempMode = m);
                        }),
                        const SizedBox(width: 8),
                        _buildModeButton('car', 'Ô tô', Icons.directions_car, tempMode, (m) {
                          setSheetState(() => tempMode = m);
                        }),
                        const SizedBox(width: 8),
                        _buildModeButton('walking', 'Đi bộ', Icons.directions_walk, tempMode, (m) {
                          setSheetState(() => tempMode = m);
                        }),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Thời gian di chuyển tối đa',
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                        ),
                        Text(
                          '$tempDuration phút',
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: AppColors.primary,
                          ),
                        ),
                      ],
                    ),
                    Slider(
                      value: tempDuration.toDouble(),
                      min: 5,
                      max: 30,
                      divisions: 5,
                      label: '$tempDuration phút',
                      activeColor: AppColors.primary,
                      onChanged: (val) {
                        setSheetState(() => tempDuration = val.round());
                      },
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        onPressed: () {
                          Navigator.pop(ctx);
                          setState(() {
                            _landmark = landmarkCtrl.text.trim();
                            _durationMinutes = tempDuration;
                            _transportMode = tempMode;
                          });
                          _runIsochroneSearch();
                        },
                        child: const Text(
                          'Áp dụng tìm kiếm theo vùng',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildModeButton(
    String mode,
    String label,
    IconData icon,
    String selectedMode,
    Function(String) onSelect,
  ) {
    final isSelected = mode == selectedMode;
    return Expanded(
      child: InkWell(
        onTap: () => onSelect(mode),
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: isSelected ? AppColors.primary.withValues(alpha: 0.1) : Colors.grey[100],
            border: Border.all(
              color: isSelected ? AppColors.primary : Colors.grey[300]!,
              width: isSelected ? 1.5 : 1,
            ),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Column(
            children: [
              Icon(icon, size: 20, color: isSelected ? AppColors.primary : Colors.grey[600]),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                  color: isSelected ? AppColors.primary : Colors.grey[700],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Bản đồ Tương tác Không gian'),
        actions: [
          IconButton(
            icon: const Icon(Icons.tune),
            tooltip: 'Bộ lọc Isochrone',
            onPressed: _showIsochroneFilterSheet,
          ),
        ],
      ),
      body: Stack(
        children: [
          // 1. Flutter Map
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _landmarkLocation ?? const LatLng(21.0169, 105.7839),
              initialZoom: 13.5,
              onTap: (tapPosition, point) {
                setState(() {
                  _selectedProperty = null;
                });
              },
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.space247.mobile',
              ),
              // Isochrone Polygon Layer
              if (_isochronePolygon.isNotEmpty)
                PolygonLayer(
                  polygons: [
                    Polygon(
                      points: _isochronePolygon,
                      color: const Color(0x336366F1), // Translucent indigo
                      borderColor: const Color(0xFF4F46E5),
                      borderStrokeWidth: 2.5,
                    ),
                  ],
                ),
              // Amenity POI Markers Layer
              if (_amenityPois.isNotEmpty)
                MarkerLayer(
                  markers: _amenityPois.map((poi) {
                    final lat = (poi['latitude'] as num).toDouble();
                    final lng = (poi['longitude'] as num).toDouble();
                    final cat = poi['category']?.toString() ?? '';
                    IconData pIcon = Icons.place;
                    Color pColor = Colors.orange;

                    if (cat == 'school') {
                      pIcon = Icons.school;
                      pColor = Colors.green;
                    } else if (cat == 'hospital') {
                      pIcon = Icons.local_hospital;
                      pColor = Colors.red;
                    } else if (cat == 'metro') {
                      pIcon = Icons.directions_subway;
                      pColor = Colors.blue;
                    } else if (cat == 'supermarket') {
                      pIcon = Icons.shopping_cart;
                      pColor = Colors.amber;
                    }

                    return Marker(
                      point: LatLng(lat, lng),
                      width: 32,
                      height: 32,
                      child: GestureDetector(
                        onTap: () {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('Tiện ích: ${poi['name']} ($cat)'),
                              duration: const Duration(seconds: 2),
                            ),
                          );
                        },
                        child: Container(
                          decoration: BoxDecoration(
                            color: Colors.white,
                            shape: BoxShape.circle,
                            border: Border.all(color: pColor, width: 1.5),
                            boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 4)],
                          ),
                          child: Icon(pIcon, size: 18, color: pColor),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              // Landmark Marker Layer
              if (_landmarkLocation != null)
                MarkerLayer(
                  markers: [
                    Marker(
                      point: _landmarkLocation!,
                      width: 44,
                      height: 44,
                      child: Container(
                        decoration: BoxDecoration(
                          color: Colors.indigo,
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 3),
                          boxShadow: const [BoxShadow(color: Colors.black38, blurRadius: 6)],
                        ),
                        child: const Icon(Icons.my_location, color: Colors.white, size: 24),
                      ),
                    ),
                  ],
                ),
              // Property Markers Layer
              MarkerLayer(
                markers: _filteredProperties.map((prop) {
                  if (prop.latitude == null || prop.longitude == null) {
                    return Marker(point: const LatLng(0, 0), child: const SizedBox());
                  }
                  final isSel = _selectedProperty?.id == prop.id;
                  return Marker(
                    point: LatLng(prop.latitude!, prop.longitude!),
                    width: 90,
                    height: 36,
                    child: GestureDetector(
                      onTap: () {
                        setState(() {
                          _selectedProperty = prop;
                        });
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: isSel ? AppColors.primary : Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: isSel ? Colors.white : AppColors.primary,
                            width: 1.5,
                          ),
                          boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 4)],
                        ),
                        child: Center(
                          child: Text(
                            AppUtils.formatPrice(prop.price),
                            style: TextStyle(
                              color: isSel ? Colors.white : AppColors.primary,
                              fontWeight: FontWeight.bold,
                              fontSize: 10,
                            ),
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ],
          ),

          // 2. Top Banner (Isochrone status & POI Toggles)
          Positioned(
            top: 12,
            left: 12,
            right: 12,
            child: Column(
              children: [
                // Isochrone summary badge
                InkWell(
                  onTap: _showIsochroneFilterSheet,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.95),
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 6)],
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.radar, color: Colors.indigo, size: 20),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            '$_landmarkName • $_durationMinutes phút ($_transportMode)',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: AppColors.textPrimary,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (_isLoadingIsochrone || _isLoadingAmenities)
                          const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        else
                          const Icon(Icons.arrow_drop_down, color: Colors.grey),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                // Amenity POI toggle chips
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildAmenityChip('school', 'Trường học', Icons.school),
                      const SizedBox(width: 6),
                      _buildAmenityChip('hospital', 'Bệnh viện', Icons.local_hospital),
                      const SizedBox(width: 6),
                      _buildAmenityChip('metro', 'Metro / Xe buýt', Icons.directions_subway),
                      const SizedBox(width: 6),
                      _buildAmenityChip('supermarket', 'Siêu thị', Icons.shopping_cart),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // 3. Bottom Preview Card for Selected Property
          if (_selectedProperty != null)
            Positioned(
              bottom: 16,
              left: 16,
              right: 16,
              child: Card(
                elevation: 6,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            AppUtils.formatPrice(_selectedProperty!.price),
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: AppColors.primary,
                            ),
                          ),
                          Text(
                            '${_selectedProperty!.areaSqm} m²',
                            style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: Colors.grey,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _selectedProperty!.title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${_selectedProperty!.district ?? ""}, ${_selectedProperty!.city}',
                        style: const TextStyle(fontSize: 11, color: Colors.grey),
                      ),
                      const SizedBox(height: 8),
                      SizedBox(
                        width: double.infinity,
                        height: 36,
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => PropertyDetailScreen(propertyId: _selectedProperty!.id),
                              ),
                            );
                          },
                          child: const Text('Xem chi tiết', style: TextStyle(color: Colors.white, fontSize: 13)),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildAmenityChip(String category, String label, IconData icon) {
    final isAct = _activeAmenityCategory == category;
    return ActionChip(
      avatar: Icon(icon, size: 14, color: isAct ? Colors.white : Colors.grey[700]),
      label: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: isAct ? FontWeight.bold : FontWeight.normal,
          color: isAct ? Colors.white : Colors.grey[800],
        ),
      ),
      backgroundColor: isAct ? AppColors.primary : Colors.white.withValues(alpha: 0.9),
      side: BorderSide(color: isAct ? AppColors.primary : Colors.grey[300]!),
      onPressed: () => _toggleAmenity(category),
    );
  }
}
