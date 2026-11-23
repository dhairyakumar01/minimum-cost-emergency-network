import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';

class FacilitiesScreen extends StatefulWidget {
  const FacilitiesScreen({super.key});

  @override
  State<FacilitiesScreen> createState() => _FacilitiesScreenState();
}

class _FacilitiesScreenState extends State<FacilitiesScreen> {
  List<Facility> _facilities = [];
  bool _loading = true;
  String _selectedAgency = 'all';
  String _searchQuery = '';
  String _viewMode = 'map'; // 'map' or 'list'
  Facility? _selectedFacility;

  // Map viewport bounds (Bengaluru BBMP default)
  double _zoomLevel = 1.0;
  double _centerLat = 12.975;
  double _centerLon = 77.60;

  @override
  void initState() {
    super.initState();
    _loadFacilities();
  }

  Future<void> _loadFacilities() async {
    setState(() => _loading = true);
    final list = await ApiService.getFacilities(
      agency: _selectedAgency == 'all' ? null : _selectedAgency,
      search: _searchQuery.isEmpty ? null : _searchQuery,
    );
    if (mounted) {
      setState(() {
        _facilities = list;
        _loading = false;
        if (_facilities.isNotEmpty && _selectedFacility == null) {
          _selectedFacility = _facilities.first;
        }
      });
    }
  }

  Color _getAgencyColor(String agency) {
    switch (agency.toLowerCase()) {
      case 'hospital':
        return AppTheme.hospitalColor;
      case 'fire':
      case 'fire_station':
        return AppTheme.fireColor;
      case 'police':
      case 'police_station':
        return AppTheme.policeColor;
      default:
        return AppTheme.sidebarDark;
    }
  }

  IconData _getAgencyIcon(String agency) {
    switch (agency.toLowerCase()) {
      case 'hospital':
        return Icons.local_hospital;
      case 'fire':
      case 'fire_station':
        return Icons.local_fire_department;
      case 'police':
      case 'police_station':
        return Icons.local_police;
      default:
        return Icons.emergency;
    }
  }

  void _showFacilityDetails(Facility fac) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(ctx).viewInsets.bottom + 16,
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            physics: const BouncingScrollPhysics(),
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 36,
                    height: 4,
                    decoration: BoxDecoration(
                      color: AppTheme.borderLight,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: _getAgencyColor(fac.agency).withAlpha(25),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(_getAgencyIcon(fac.agency), color: _getAgencyColor(fac.agency), size: 24),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            fac.name,
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppTheme.textMain),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '${fac.agency.toUpperCase()} • ID: ${fac.id}',
                            style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: _getAgencyColor(fac.agency)),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                const Divider(height: 1),
                const SizedBox(height: 14),
                _detailRow('Latitude', '${fac.latitude.toStringAsFixed(6)}° N'),
                _detailRow('Longitude', '${fac.longitude.toStringAsFixed(6)}° E'),
                _detailRow('Jurisdiction', 'BBMP Greater Bengaluru'),
                _detailRow('Network Status', 'Integrated Spanning Node'),
                _detailRow('Incident Response Tier', 'First Responder Core'),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: () => Navigator.pop(ctx),
                    icon: const Icon(Icons.check, size: 18),
                    label: const Text('Close Details'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
          Flexible(
            child: Text(
              value,
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textMain),
              textAlign: TextAlign.end,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Emergency Facilities Map', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: Column(
        children: [
          // Filter & Search Header Card
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            color: Colors.white,
            child: Column(
              children: [
                // View Mode Toggle (Map vs List)
                SizedBox(
                  width: double.infinity,
                  child: SegmentedButton<String>(
                    segments: const [
                      ButtonSegment(
                        value: 'map',
                        label: Text('Map View'),
                        icon: Icon(Icons.map, size: 16),
                      ),
                      ButtonSegment(
                        value: 'list',
                        label: Text('List View'),
                        icon: Icon(Icons.list, size: 16),
                      ),
                    ],
                    selected: {_viewMode},
                    onSelectionChanged: (val) {
                      setState(() => _viewMode = val.first);
                    },
                  ),
                ),
                const SizedBox(height: 10),

                // Search field
                TextField(
                  decoration: InputDecoration(
                    hintText: 'Search 1,255 emergency facilities...',
                    prefixIcon: const Icon(Icons.search, size: 20),
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                    suffixIcon: _searchQuery.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 18),
                            onPressed: () {
                              setState(() => _searchQuery = '');
                              _loadFacilities();
                            },
                          )
                        : null,
                  ),
                  onChanged: (val) {
                    _searchQuery = val;
                    _loadFacilities();
                  },
                ),
                const SizedBox(height: 8),

                // Agency Filter Chips
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  physics: const BouncingScrollPhysics(),
                  child: Row(
                    children: [
                      _filterChip('All (1,255)', 'all'),
                      const SizedBox(width: 6),
                      _filterChip('Hospitals (1,097)', 'hospital'),
                      const SizedBox(width: 6),
                      _filterChip('Police (138)', 'police'),
                      const SizedBox(width: 6),
                      _filterChip('Fire (20)', 'fire'),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1, color: AppTheme.borderLight),

          // Count Strip
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            color: AppTheme.bgCanvas,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    '${_facilities.length} Facilities Displayed',
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textMuted),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                if (_loading)
                  const SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                else
                  Text(
                    _selectedAgency == 'all' ? 'BBMP Comprehensive' : _selectedAgency.toUpperCase(),
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: _getAgencyColor(_selectedAgency),
                    ),
                  ),
              ],
            ),
          ),

          // Body: Map View or List View
          Expanded(
            child: _viewMode == 'map' ? _buildMapView() : _buildListView(),
          ),
        ],
      ),
    );
  }

  Widget _buildMapView() {
    return Stack(
      children: [
        // Interactive Canvas
        GestureDetector(
          onTapUp: (details) {
            final renderBox = context.findRenderObject() as RenderBox?;
            if (renderBox != null) {
              _findNearestFacility(details.localPosition, renderBox.size);
            }
          },
          child: Container(
            width: double.infinity,
            height: double.infinity,
            color: const Color(0xFF0F172A),
            child: CustomPaint(
              painter: FullFacilityMapPainter(
                facilities: _facilities,
                selectedFacility: _selectedFacility,
                zoomLevel: _zoomLevel,
                centerLat: _centerLat,
                centerLon: _centerLon,
              ),
            ),
          ),
        ),

        // Zoom & Reset Floating Controls
        Positioned(
          right: 12,
          top: 12,
          child: Column(
            children: [
              _mapControlBtn(
                icon: Icons.add,
                onPressed: () {
                  setState(() => _zoomLevel = (_zoomLevel * 1.3).clamp(0.8, 8.0));
                },
                tooltip: 'Zoom In',
              ),
              const SizedBox(height: 6),
              _mapControlBtn(
                icon: Icons.remove,
                onPressed: () {
                  setState(() => _zoomLevel = (_zoomLevel / 1.3).clamp(0.8, 8.0));
                },
                tooltip: 'Zoom Out',
              ),
              const SizedBox(height: 6),
              _mapControlBtn(
                icon: Icons.refresh,
                onPressed: () {
                  setState(() {
                    _zoomLevel = 1.0;
                    _centerLat = 12.975;
                    _centerLon = 77.60;
                  });
                },
                tooltip: 'Reset Map View',
              ),
            ],
          ),
        ),

        // Map Legend Indicator (Compile-time constant widgets: zero eval errors)
        Positioned(
          top: 12,
          left: 12,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.black.withAlpha(200),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.white24),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'BENGALURU FACILITIES',
                  style: TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(width: 7, height: 7, decoration: const BoxDecoration(shape: BoxShape.circle, color: AppTheme.hospitalColor)),
                    const SizedBox(width: 3),
                    const Text('Hospital', style: TextStyle(color: Colors.white70, fontSize: 9)),
                    const SizedBox(width: 8),
                    Container(width: 7, height: 7, decoration: const BoxDecoration(shape: BoxShape.circle, color: AppTheme.policeColor)),
                    const SizedBox(width: 3),
                    const Text('Police', style: TextStyle(color: Colors.white70, fontSize: 9)),
                    const SizedBox(width: 8),
                    Container(width: 7, height: 7, decoration: const BoxDecoration(shape: BoxShape.circle, color: AppTheme.fireColor)),
                    const SizedBox(width: 3),
                    const Text('Fire', style: TextStyle(color: Colors.white70, fontSize: 9)),
                  ],
                ),
              ],
            ),
          ),
        ),

        // Floating Selected Facility Card at bottom of map
        if (_selectedFacility != null)
          Positioned(
            bottom: 12,
            left: 12,
            right: 12,
            child: Card(
              color: Colors.white,
              elevation: 4,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: BorderSide(color: _getAgencyColor(_selectedFacility!.agency), width: 1.5),
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: _getAgencyColor(_selectedFacility!.agency).withAlpha(25),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(
                        _getAgencyIcon(_selectedFacility!.agency),
                        color: _getAgencyColor(_selectedFacility!.agency),
                        size: 20,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            _selectedFacility!.name,
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppTheme.textMain),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '${_selectedFacility!.latitude.toStringAsFixed(4)}°N, ${_selectedFacility!.longitude.toStringAsFixed(4)}°E • ${_selectedFacility!.agency.toUpperCase()}',
                            style: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      onPressed: () => _showFacilityDetails(_selectedFacility!),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        visualDensity: VisualDensity.compact,
                        backgroundColor: _getAgencyColor(_selectedFacility!.agency),
                      ),
                      child: const Text('Details', style: TextStyle(fontSize: 11)),
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }

  void _findNearestFacility(Offset tapPos, Size size) {
    if (_facilities.isEmpty) return;

    const spanLat = 0.35;
    const spanLon = 0.40;

    final currentSpanLat = spanLat / _zoomLevel;
    final currentSpanLon = spanLon / _zoomLevel;

    final minLat = _centerLat - (currentSpanLat / 2);
    final maxLat = _centerLat + (currentSpanLat / 2);
    final minLon = _centerLon - (currentSpanLon / 2);
    final maxLon = _centerLon + (currentSpanLon / 2);

    double bestDistSq = double.infinity;
    Facility? nearest;

    for (final f in _facilities) {
      final x = ((f.longitude - minLon) / (maxLon - minLon)) * size.width;
      final y = size.height - (((f.latitude - minLat) / (maxLat - minLat)) * size.height);
      final dx = x - tapPos.dx;
      final dy = y - tapPos.dy;
      final dSq = dx * dx + dy * dy;
      if (dSq < bestDistSq) {
        bestDistSq = dSq;
        nearest = f;
      }
    }

    if (nearest != null && bestDistSq < 1600) {
      setState(() {
        _selectedFacility = nearest;
      });
    }
  }

  Widget _buildListView() {
    if (_loading && _facilities.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_facilities.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.search_off, size: 48, color: AppTheme.textSubtle),
            const SizedBox(height: 12),
            Text(
              'No facilities found matching "$_searchQuery"',
              style: const TextStyle(color: AppTheme.textMuted),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.all(10),
      itemCount: _facilities.length,
      itemBuilder: (ctx, i) {
        final f = _facilities[i];
        final agencyColor = _getAgencyColor(f.agency);
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            leading: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: agencyColor.withAlpha(25),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(_getAgencyIcon(f.agency), color: agencyColor, size: 20),
            ),
            title: Text(
              f.name,
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textMain),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                  decoration: BoxDecoration(
                    color: agencyColor.withAlpha(20),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    f.agency.toUpperCase(),
                    style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: agencyColor),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '${f.latitude.toStringAsFixed(4)}°N, ${f.longitude.toStringAsFixed(4)}°E',
                    style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            trailing: const Icon(Icons.chevron_right, size: 18, color: AppTheme.textMuted),
            onTap: () => _showFacilityDetails(f),
          ),
        );
      },
    );
  }

  Widget _mapControlBtn({required IconData icon, required VoidCallback onPressed, required String tooltip}) {
    return Container(
      width: 34,
      height: 34,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 4)],
      ),
      child: IconButton(
        icon: Icon(icon, size: 18, color: AppTheme.textMain),
        onPressed: onPressed,
        tooltip: tooltip,
        padding: EdgeInsets.zero,
      ),
    );
  }

  Widget _filterChip(String label, String agency) {
    final selected = _selectedAgency == agency;
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) {
        setState(() => _selectedAgency = agency);
        _loadFacilities();
      },
      selectedColor: AppTheme.sidebarDark,
      labelStyle: TextStyle(
        fontSize: 11,
        color: selected ? Colors.white : AppTheme.textMain,
        fontWeight: selected ? FontWeight.bold : FontWeight.normal,
      ),
      backgroundColor: Colors.white,
      side: BorderSide(
        color: selected ? AppTheme.sidebarDark : AppTheme.borderLight,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 4),
    );
  }
}

class FullFacilityMapPainter extends CustomPainter {
  final List<Facility> facilities;
  final Facility? selectedFacility;
  final double zoomLevel;
  final double centerLat;
  final double centerLon;

  FullFacilityMapPainter({
    required this.facilities,
    this.selectedFacility,
    required this.zoomLevel,
    required this.centerLat,
    required this.centerLon,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // Subtle dark map background grid
    final gridPaint = Paint()
      ..color = Colors.white.withAlpha(12)
      ..strokeWidth = 0.5;

    for (int i = 1; i < 5; i++) {
      canvas.drawLine(Offset(0, size.height * (i / 5)), Offset(size.width, size.height * (i / 5)), gridPaint);
      canvas.drawLine(Offset(size.width * (i / 5), 0), Offset(size.width * (i / 5), size.height), gridPaint);
    }

    if (facilities.isEmpty) return;

    const spanLat = 0.35;
    const spanLon = 0.40;

    final currentSpanLat = spanLat / zoomLevel;
    final currentSpanLon = spanLon / zoomLevel;

    final minLat = centerLat - (currentSpanLat / 2);
    final maxLat = centerLat + (currentSpanLat / 2);
    final minLon = centerLon - (currentSpanLon / 2);
    final maxLon = centerLon + (currentSpanLon / 2);

    double projectX(double lon) => ((lon - minLon) / (maxLon - minLon)) * size.width;
    double projectY(double lat) => size.height - (((lat - minLat) / (maxLat - minLat)) * size.height);

    final hospPaint = Paint()..color = AppTheme.hospitalColor.withAlpha(200);
    final polPaint = Paint()..color = AppTheme.policeColor.withAlpha(220);
    final firePaint = Paint()..color = AppTheme.fireColor;

    for (final f in facilities) {
      final x = projectX(f.longitude);
      final y = projectY(f.latitude);
      if (x >= 0 && x <= size.width && y >= 0 && y <= size.height) {
        Paint p = hospPaint;
        double radius = 2.0 * zoomLevel.clamp(1.0, 2.5);
        if (f.agency == 'police' || f.agency == 'police_station') {
          p = polPaint;
          radius = 2.4 * zoomLevel.clamp(1.0, 2.5);
        } else if (f.agency == 'fire' || f.agency == 'fire_station') {
          p = firePaint;
          radius = 3.0 * zoomLevel.clamp(1.0, 2.5);
        }
        canvas.drawCircle(Offset(x, y), radius, p);
      }
    }

    // Highlight selected facility
    if (selectedFacility != null) {
      final sx = projectX(selectedFacility!.longitude);
      final sy = projectY(selectedFacility!.latitude);
      if (sx >= 0 && sx <= size.width && sy >= 0 && sy <= size.height) {
        final highlightPaint = Paint()
          ..color = Colors.amber
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.5;
        canvas.drawCircle(Offset(sx, sy), 8.0, highlightPaint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant FullFacilityMapPainter oldDelegate) {
    return oldDelegate.facilities.length != facilities.length ||
        oldDelegate.selectedFacility?.id != selectedFacility?.id ||
        oldDelegate.zoomLevel != zoomLevel ||
        oldDelegate.centerLat != centerLat ||
        oldDelegate.centerLon != centerLon;
  }
}
