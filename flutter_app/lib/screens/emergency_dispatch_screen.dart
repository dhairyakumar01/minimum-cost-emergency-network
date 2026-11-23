import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class EmergencyDispatchScreen extends StatefulWidget {
  const EmergencyDispatchScreen({super.key});

  @override
  State<EmergencyDispatchScreen> createState() => _EmergencyDispatchScreenState();
}

class _EmergencyDispatchScreenState extends State<EmergencyDispatchScreen> {
  final _latController = TextEditingController(text: '12.9781');
  final _lonController = TextEditingController(text: '77.5696');
  final _labelController = TextEditingController(text: 'Majestic (KSR Railway Station)');

  String _category = 'medical';
  String _agency = 'hospital';
  String _mode = 'time';
  double _radiusKm = 5.0;
  final int _kParam = 5;

  bool _loading = false;
  Map<String, dynamic>? _scenarioResult;

  // Preset Landmarks in Bengaluru
  final List<Map<String, dynamic>> _presets = [
    {'label': 'Majestic (KSR)', 'lat': 12.9781, 'lon': 77.5696},
    {'label': 'Jayanagar 4th Block', 'lat': 12.9298, 'lon': 77.5833},
    {'label': 'Indiranagar 100ft', 'lat': 12.9784, 'lon': 77.6408},
    {'label': 'Banashankari Temple', 'lat': 12.9155, 'lon': 77.5736},
    {'label': 'Whitefield ITPL', 'lat': 12.9863, 'lon': 77.7380},
  ];

  void _applyPreset(Map<String, dynamic> preset) {
    setState(() {
      _labelController.text = preset['label'];
      _latController.text = preset['lat'].toString();
      _lonController.text = preset['lon'].toString();
    });
  }

  Future<void> _runDispatch() async {
    final lat = double.tryParse(_latController.text.trim()) ?? 12.9781;
    final lon = double.tryParse(_lonController.text.trim()) ?? 77.5696;

    setState(() => _loading = true);

    try {
      final res = await ApiService.runScenario(
        lat: lat,
        lon: lon,
        label: _labelController.text.trim(),
        category: _category,
        agency: _agency,
        mode: _mode,
        kParam: _kParam,
      );

      if (mounted) {
        setState(() {
          _scenarioResult = res['data'] ?? res;
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Dispatch Error: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final ranking = (_scenarioResult?['dispatch_ranking'] as List<dynamic>? ?? []);
    final topFacility = ranking.isNotEmpty ? ranking[0] : null;

    final lat = double.tryParse(_latController.text.trim()) ?? 12.9781;
    final lon = double.tryParse(_lonController.text.trim()) ?? 77.5696;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Emergency Simulation & Dispatch', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        physics: const BouncingScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Incident Setup Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.crisis_alert, size: 18, color: AppTheme.accentRed),
                        SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Incident Location & Landmark',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),

                    // Preset Chips
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      physics: const BouncingScrollPhysics(),
                      child: Row(
                        children: _presets.map((p) {
                          final isSelected = _labelController.text == p['label'];
                          return Padding(
                            padding: const EdgeInsets.only(right: 6),
                            child: ActionChip(
                              label: Text(p['label']),
                              avatar: const Icon(Icons.location_on, size: 14, color: AppTheme.accentRed),
                              backgroundColor: isSelected ? const Color(0xFFEFF6FF) : Colors.white,
                              side: BorderSide(color: isSelected ? AppTheme.accentNavy : AppTheme.borderLight),
                              labelStyle: TextStyle(
                                fontSize: 11,
                                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                color: isSelected ? AppTheme.accentNavy : AppTheme.textMain,
                              ),
                              visualDensity: VisualDensity.compact,
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              onPressed: () => _applyPreset(p),
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                    const SizedBox(height: 10),

                    // Incident Label Textfield
                    TextField(
                      controller: _labelController,
                      decoration: const InputDecoration(
                        labelText: 'Incident Location / Landmark',
                        prefixIcon: Icon(Icons.edit_location_alt, size: 20),
                        isDense: true,
                      ),
                    ),
                    const SizedBox(height: 10),

                    // Coordinates Row
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _latController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              labelText: 'Latitude (°N)',
                              isDense: true,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: TextField(
                            controller: _lonController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              labelText: 'Longitude (°E)',
                              isDense: true,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Emergency Service & Vehicle Selection
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Emergency Service Category:', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.textMuted)),
                    const SizedBox(height: 6),
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      physics: const BouncingScrollPhysics(),
                      child: Row(
                        children: [
                          _categoryChip('Medical (Hospital)', 'medical', 'hospital', Icons.local_hospital),
                          const SizedBox(width: 6),
                          _categoryChip('Fire & Rescue', 'fire', 'fire', Icons.local_fire_department),
                          const SizedBox(width: 6),
                          _categoryChip('Police / Security', 'security', 'police', Icons.local_police),
                        ],
                      ),
                    ),
                    const SizedBox(height: 10),

                    // Dedicated Fleet & Vehicle Spec Card
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppTheme.bgCanvas,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppTheme.borderLight),
                      ),
                      child: Row(
                        children: [
                          Icon(_getVehicleIcon(), size: 20, color: _getCategoryColor()),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(_getVehicleName(), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                                Text(_getVehicleRate(), style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Routing Goal Segmented Control
                    const Text('Routing Optimization Goal:', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.textMuted)),
                    const SizedBox(height: 6),
                    SizedBox(
                      width: double.infinity,
                      child: SegmentedButton<String>(
                        segments: const [
                          ButtonSegment(
                            value: 'time',
                            label: Text('Fastest Time'),
                            icon: Icon(Icons.speed, size: 16),
                          ),
                          ButtonSegment(
                            value: 'distance',
                            label: Text('Shortest Path'),
                            icon: Icon(Icons.route, size: 16),
                          ),
                          ButtonSegment(
                            value: 'compromise',
                            label: Text('Balanced'),
                            icon: Icon(Icons.balance, size: 16),
                          ),
                        ],
                        selected: {_mode},
                        onSelectionChanged: (val) {
                          setState(() => _mode = val.first);
                        },
                      ),
                    ),
                    const SizedBox(height: 12),

                    // Search Radius Slider
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Search Radius:', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.textMuted)),
                        Text('${_radiusKm.toStringAsFixed(1)} km', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.sidebarDark)),
                      ],
                    ),
                    Slider(
                      value: _radiusKm,
                      min: 3.0,
                      max: 10.0,
                      divisions: 7,
                      activeColor: AppTheme.sidebarDark,
                      onChanged: (val) => setState(() => _radiusKm = val),
                    ),

                    // Run Dispatch Button
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: _loading ? null : _runDispatch,
                        icon: _loading
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                              )
                            : const Icon(Icons.flash_on, size: 18),
                        label: Text(_loading ? 'Computing Optimal Dispatch...' : 'Run Emergency Dispatch Simulation'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppTheme.accentRed,
                          padding: const EdgeInsets.symmetric(vertical: 13),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Visual Dispatch Route Canvas
            if (topFacility != null) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.alt_route, size: 18, color: AppTheme.accentNavy),
                          SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              'Dispatch Trajectory & Radius Map',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textMain),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Container(
                        height: 160,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          color: const Color(0xFF0F172A),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(color: AppTheme.borderLight),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(10),
                          child: CustomPaint(
                            painter: DispatchRoutePainter(
                              incidentLat: lat,
                              incidentLon: lon,
                              topFacility: topFacility,
                              alternatives: ranking.skip(1).take(4).toList(),
                              radiusKm: _radiusKm,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 6),
                      const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Flexible(
                            child: Text(
                              '🚨 Incident  •  ⭐ #1 Station  •  ⚡ Direct Route  •  ⚪ Standby',
                              style: TextStyle(fontSize: 10, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // Top #1 Recommended Card
              Card(
                color: const Color(0xFFFFFBEB),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: const BorderSide(color: Color(0xFFFDE68A), width: 1.5),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Flexible(
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: AppTheme.accentAmber,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Text(
                                '⭐ #1 RECOMMENDED DISPATCH',
                                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 10),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            topFacility['agency']?.toString().toUpperCase() ?? 'EMERGENCY',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 10, color: AppTheme.textMuted),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        topFacility['facility_name'] ?? 'Facility',
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textMain),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'ID: ${topFacility['facility_id']}',
                        style: const TextStyle(fontSize: 11, color: AppTheme.textMuted, fontFamily: 'monospace'),
                      ),
                      const Divider(height: 18),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          Expanded(
                            child: _statItem(
                              'EST. TIME',
                              '${(topFacility['travel_time_min'] ?? (topFacility['travel_time_ds'] != null ? topFacility['travel_time_ds'] / 600.0 : 0.0)).toStringAsFixed(1)} min',
                              AppTheme.accentRed,
                            ),
                          ),
                          Container(width: 1, height: 26, color: const Color(0xFFFDE68A)),
                          Expanded(
                            child: _statItem(
                              'DISTANCE',
                              '${(topFacility['road_distance_km'] ?? (topFacility['road_distance_dm'] != null ? topFacility['road_distance_dm'] / 10000.0 : 0.0)).toStringAsFixed(2)} km',
                              AppTheme.accentNavy,
                            ),
                          ),
                          Container(width: 1, height: 26, color: const Color(0xFFFDE68A)),
                          Expanded(
                            child: _statItem(
                              'SCORE',
                              '${topFacility['compromise_score'] ?? topFacility['weight'] ?? 100}',
                              AppTheme.sidebarDark,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // Alternative Ranked Facilities
              const Text(
                'Alternative Standby Stations (Rank #2 - #5)',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
              ),
              const SizedBox(height: 6),

              ...ranking.skip(1).take(4).toList().asMap().entries.map((entry) {
                final idx = entry.key + 2;
                final f = entry.value;
                return Card(
                  margin: const EdgeInsets.only(bottom: 6),
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
                    leading: CircleAvatar(
                      radius: 16,
                      backgroundColor: Colors.blue.withAlpha(25),
                      child: Text(
                        '#$idx',
                        style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blue, fontSize: 12),
                      ),
                    ),
                    title: Text(
                      f['facility_name'] ?? 'Alternative Facility',
                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Text(
                      'Travel: ${(f['travel_time_min'] ?? 0.0).toStringAsFixed(1)} min • Dist: ${(f['road_distance_km'] ?? 0.0).toStringAsFixed(2)} km',
                      style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                    ),
                  ),
                );
              }),
            ],
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  IconData _getVehicleIcon() {
    switch (_category) {
      case 'medical':
        return Icons.medical_services_outlined;
      case 'fire':
        return Icons.fire_truck_outlined;
      case 'security':
        return Icons.local_police_outlined;
      default:
        return Icons.emergency_outlined;
    }
  }

  Color _getCategoryColor() {
    switch (_category) {
      case 'medical':
        return AppTheme.hospitalColor;
      case 'fire':
        return AppTheme.fireColor;
      case 'security':
        return AppTheme.policeColor;
      default:
        return AppTheme.sidebarDark;
    }
  }

  String _getVehicleName() {
    switch (_category) {
      case 'medical':
        return 'Ambulance (Force Traveller BLS/ALS)';
      case 'fire':
        return 'Fire Engine Appliance (Water Tender)';
      case 'security':
        return 'Police Patrol (Mahindra Bolero Hoysala)';
      default:
        return 'Emergency Response Vehicle';
    }
  }

  String _getVehicleRate() {
    switch (_category) {
      case 'medical':
        return 'Dispatch Cost: ₹12.50 / km • Avg Speed: 42.0 km/h';
      case 'fire':
        return 'Dispatch Cost: ₹18.00 / km • Avg Speed: 35.0 km/h';
      case 'security':
        return 'Dispatch Cost: ₹6.25 / km • Avg Speed: 48.0 km/h';
      default:
        return 'Standard Emergency Protocol';
    }
  }

  Widget _categoryChip(String label, String cat, String agency, IconData icon) {
    final selected = _category == cat;
    return ChoiceChip(
      avatar: Icon(icon, size: 15, color: selected ? Colors.white : AppTheme.sidebarDark),
      label: Text(label),
      selected: selected,
      selectedColor: AppTheme.sidebarDark,
      labelStyle: TextStyle(
        color: selected ? Colors.white : AppTheme.textMain,
        fontWeight: selected ? FontWeight.bold : FontWeight.normal,
        fontSize: 11,
      ),
      visualDensity: VisualDensity.compact,
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      onSelected: (_) {
        setState(() {
          _category = cat;
          _agency = agency;
        });
      },
    );
  }

  Widget _statItem(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: AppTheme.textMuted)),
        const SizedBox(height: 2),
        FittedBox(
          fit: BoxFit.scaleDown,
          child: Text(value, style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: color)),
        ),
      ],
    );
  }
}

class DispatchRoutePainter extends CustomPainter {
  final double incidentLat;
  final double incidentLon;
  final Map<String, dynamic> topFacility;
  final List<dynamic> alternatives;
  final double radiusKm;

  DispatchRoutePainter({
    required this.incidentLat,
    required this.incidentLon,
    required this.topFacility,
    required this.alternatives,
    required this.radiusKm,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // 5km is approx 0.045 deg lat/lon
    final span = (radiusKm / 111.0) * 1.6;
    final minLat = incidentLat - span;
    final maxLat = incidentLat + span;
    final minLon = incidentLon - span;
    final maxLon = incidentLon + span;

    double projectX(double lon) => ((lon - minLon) / (maxLon - minLon)) * size.width;
    double projectY(double lat) => size.height - (((lat - minLat) / (maxLat - minLat)) * size.height);

    // Subtle coordinate grid background
    final gridPaint = Paint()
      ..color = Colors.white.withAlpha(12)
      ..strokeWidth = 0.5;

    for (int i = 1; i < 4; i++) {
      canvas.drawLine(Offset(0, size.height * (i / 4)), Offset(size.width, size.height * (i / 4)), gridPaint);
      canvas.drawLine(Offset(size.width * (i / 4), 0), Offset(size.width * (i / 4), size.height), gridPaint);
    }

    final ix = projectX(incidentLon);
    final iy = projectY(incidentLat);

    // Draw radius boundary circle
    final radiusPixels = ((radiusKm / 111.0) / (maxLon - minLon)) * size.width;
    final radiusPaint = Paint()
      ..color = Colors.blue.withAlpha(35)
      ..style = PaintingStyle.fill;
    final radiusStroke = Paint()
      ..color = Colors.blue.withAlpha(80)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    canvas.drawCircle(Offset(ix, iy), radiusPixels, radiusPaint);
    canvas.drawCircle(Offset(ix, iy), radiusPixels, radiusStroke);

    // Draw alternative standby facilities
    final altPaint = Paint()..color = Colors.white70;
    for (final alt in alternatives) {
      final alat = (alt['latitude'] ?? alt['lat'])?.toDouble();
      final alon = (alt['longitude'] ?? alt['lon'])?.toDouble();
      if (alat != null && alon != null) {
        canvas.drawCircle(Offset(projectX(alon), projectY(alat)), 3.0, altPaint);
      }
    }

    // Top recommended facility
    final topLat = (topFacility['latitude'] ?? topFacility['lat'] ?? (incidentLat + 0.015)).toDouble();
    final topLon = (topFacility['longitude'] ?? topFacility['lon'] ?? (incidentLon - 0.012)).toDouble();
    final tx = projectX(topLon);
    final ty = projectY(topLat);

    // Draw connecting direct dispatch route line (Glowing Amber)
    final routePaint = Paint()
      ..color = const Color(0xFFF59E0B)
      ..strokeWidth = 3.0
      ..style = PaintingStyle.stroke;
    canvas.drawLine(Offset(tx, ty), Offset(ix, iy), routePaint);

    // Top station marker (Gold star/circle)
    final topMarkerPaint = Paint()..color = const Color(0xFFF59E0B);
    canvas.drawCircle(Offset(tx, ty), 6.0, topMarkerPaint);
    final topInnerPaint = Paint()..color = Colors.white;
    canvas.drawCircle(Offset(tx, ty), 3.0, topInnerPaint);

    // Incident marker (Red alert circle with pulse ring)
    final incPulsePaint = Paint()
      ..color = AppTheme.accentRed.withAlpha(80)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    canvas.drawCircle(Offset(ix, iy), 10.0, incPulsePaint);
    final incPaint = Paint()..color = AppTheme.accentRed;
    canvas.drawCircle(Offset(ix, iy), 5.0, incPaint);
  }

  @override
  bool shouldRepaint(covariant DispatchRoutePainter oldDelegate) {
    return oldDelegate.incidentLat != incidentLat ||
        oldDelegate.incidentLon != incidentLon ||
        oldDelegate.radiusKm != radiusKm ||
        oldDelegate.topFacility['facility_id'] != topFacility['facility_id'];
  }
}
