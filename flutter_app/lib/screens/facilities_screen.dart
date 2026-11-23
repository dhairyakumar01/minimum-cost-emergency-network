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
      });
    }
  }

  Color _getAgencyColor(String agency) {
    switch (agency.toLowerCase()) {
      case 'hospital':
        return const Color(0xFFDC2626);
      case 'fire':
      case 'fire_station':
        return const Color(0xFFF59E0B);
      case 'police':
        return const Color(0xFF2563EB);
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
        return Icons.local_police;
      default:
        return Icons.emergency;
    }
  }

  void _showFacilityDetails(Facility fac) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: _getAgencyColor(fac.agency).withAlpha(30),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(_getAgencyIcon(fac.agency), color: _getAgencyColor(fac.agency)),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        fac.agency.toUpperCase(),
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: _getAgencyColor(fac.agency),
                        ),
                      ),
                      Text(
                        fac.name,
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            _detailRow('Facility ID', fac.id),
            _detailRow('Latitude', '${fac.latitude.toFixed(5)}° N'),
            _detailRow('Longitude', '${fac.longitude.toFixed(5)}° E'),
            _detailRow('Coverage Area', 'Bengaluru BBMP Municipal Zone'),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => Navigator.pop(ctx),
                icon: const Icon(Icons.check),
                label: const Text('Close'),
              ),
            ),
          ],
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
          Text(label, style: const TextStyle(color: AppTheme.textMuted, fontSize: 13)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Facilities Directory', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: Column(
        children: [
          // Filter & Search Header
          Container(
            padding: const EdgeInsets.all(12),
            color: Colors.white,
            child: Column(
              children: [
                TextField(
                  decoration: const InputDecoration(
                    hintText: 'Search 1,255 emergency facilities...',
                    prefixIcon: Icon(Icons.search, size: 20),
                    isDense: true,
                  ),
                  onChanged: (val) {
                    _searchQuery = val;
                    _loadFacilities();
                  },
                ),
                const SizedBox(height: 10),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _filterChip('All Facilities', 'all'),
                      const SizedBox(width: 8),
                      _filterChip('Hospitals', 'hospital'),
                      const SizedBox(width: 8),
                      _filterChip('Fire Stations', 'fire'),
                      const SizedBox(width: 8),
                      _filterChip('Police Stations', 'police'),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          // Count Strip
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: AppTheme.bgCanvas,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${_facilities.length} Emergency Facilities Found',
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textMuted),
                ),
                if (_loading)
                  const SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
              ],
            ),
          ),

          // Facilities List
          Expanded(
            child: _loading && _facilities.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : _facilities.isEmpty
                    ? const Center(
                        child: Text(
                          'No facilities match the filter criteria.',
                          style: TextStyle(color: AppTheme.textMuted),
                        ),
                      )
                    : ListView.builder(
                        itemCount: _facilities.length,
                        itemBuilder: (ctx, idx) {
                          final f = _facilities[idx];
                          final color = _getAgencyColor(f.agency);
                          return Card(
                            margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: color.withAlpha(30),
                                child: Icon(_getAgencyIcon(f.agency), color: color, size: 20),
                              ),
                              title: Text(
                                f.name,
                                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                              ),
                              subtitle: Text(
                                '${f.agency.toUpperCase()} • (${f.latitude.toStringAsFixed(4)}°N, ${f.longitude.toStringAsFixed(4)}°E)',
                                style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                              ),
                              trailing: const Icon(Icons.chevron_right, size: 18, color: AppTheme.textMuted),
                              onTap: () => _showFacilityDetails(f),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Widget _filterChip(String label, String agencyVal) {
    final selected = _selectedAgency == agencyVal;
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      selectedColor: AppTheme.sidebarDark,
      labelStyle: TextStyle(
        color: selected ? Colors.white : AppTheme.textMain,
        fontWeight: selected ? FontWeight.bold : FontWeight.normal,
        fontSize: 12,
      ),
      onSelected: (_) {
        setState(() => _selectedAgency = agencyVal);
        _loadFacilities();
      },
    );
  }
}

extension DoubleExtension on double {
  String toFixed(int fractionDigits) => toStringAsFixed(fractionDigits);
}
